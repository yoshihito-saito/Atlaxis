"""Development-only conversion of a pinned ProbeInterface JSON library.

No ProbeInterface package is needed: its public JSON representation is read
directly. Run with --source-dir PATH; --download fills that temporary directory
from the pinned revision. The app only reads the generated Atlaxis files.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np

from .catalog import build_catalog
from .model import ChannelMap, Contact, ProbeBody, ProbeGeometry
from .wiring import headstage_map


ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / "third_party" / "probeinterface_cambridge.lock.json"
WIRING = ROOT / "third_party" / "cambridge_wiring.json"
REVISION = "bb40894cdf55787fed7b7198ea854497d52ca687"


def _read_pinned(path, blob_sha1):
    data = path.read_bytes()
    digest = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    if digest != blob_sha1:
        raise ValueError(f"Source differs from pinned library: {path}")
    return data


def _clip_x(polygon, boundary, keep_right):
    """Clip to one vertical half-plane, preserving the supplied outline."""
    clipped = []
    previous = polygon[-1]
    was_inside = previous[0] >= boundary if keep_right else previous[0] <= boundary
    for point in polygon:
        inside = point[0] >= boundary if keep_right else point[0] <= boundary
        if inside != was_inside:
            fraction = (boundary - previous[0]) / (point[0] - previous[0])
            clipped.append([boundary, previous[1] + fraction * (point[1] - previous[1])])
        if inside:
            clipped.append(list(point))
        previous, was_inside = point, inside
    return clipped


def _shank_outlines(points):
    # Remove repeated vertices without changing the outline's geometry.
    contour = []
    for point in points:
        if not contour or point != contour[-1]:
            contour.append(point)
    if contour[-1] == contour[0]:
        contour.pop()
    tips = sorted((point for i, point in enumerate(contour)
                   if point[1] < contour[i - 1][1]
                   and point[1] < contour[(i + 1) % len(contour)][1]), key=lambda p: p[0])
    if not tips or len({p[0] for p in tips}) != len(tips):
        raise ValueError("Outline must identify distinct physical shank tips.")
    boundaries = [(a[0] + b[0]) / 2 for a, b in zip(tips, tips[1:])]
    outlines = []
    for shank in range(len(tips)):
        polygon = contour
        if shank:
            polygon = _clip_x(polygon, boundaries[shank - 1], True)
        if shank < len(boundaries):
            polygon = _clip_x(polygon, boundaries[shank], False)
        outlines.append(polygon)
    return tips, boundaries, outlines


def convert_probe(name, source):
    """Translate source x/y into a tip-based frame without resampling sites."""
    if source["ndim"] != 2 or source["si_units"] != "um":
        raise ValueError(f"Unexpected coordinate convention: {name}")
    if source.get("device_channel_indices"):
        raise ValueError(f"New wiring data needs explicit review: {name}")
    positions = source["contact_positions"]
    site_ids = source["contact_ids"]
    sides = source.get("contact_sides") or ["front"] * len(positions)
    if len(site_ids) != len(positions) or len(sides) != len(positions):
        raise ValueError(f"Site metadata length mismatch: {name}")
    if set(sides) - {"front", "back"}:
        raise ValueError(f"Unknown contact face: {name}")
    tips, boundaries, outlines = _shank_outlines(source["probe_planar_contour"])
    origin_x, origin_y = tips[0]
    thickness = 30.0 if "back" in sides else 15.0
    contacts = [Contact(str(site_id), int(np.searchsorted(boundaries, x, side="right")),
                        x - origin_x, y - origin_y, (-1 if side == "front" else 1) * thickness / 2)
                for site_id, (x, y), side in zip(site_ids, positions, sides, strict=True)]
    bodies = [ProbeBody([[x - origin_x, y - origin_y, 0.0] for x, y in outline], thickness, shank)
              for shank, outline in enumerate(outlines)]
    if {c.shank_id for c in contacts} != set(range(len(bodies))):
        raise ValueError(f"Outline contains a shank without contacts: {name}")
    metadata = {
        "manufacturer": "Cambridge NeuroTech",
        "assembly": "-".join(name.split("-")[:2]),
        "provisional": True,
        "geometry_status": "upstream_unverified",
        "coordinate_convention": "um; leftmost contour tip at origin; +x across shanks; +y toward base; front is -z.",
        "site_id_convention": "Source ProbeInterface site/connector labels, not acquisition-channel indices.",
        "source_origin_um": [origin_x, origin_y, 0.0],
        "source_annotations": source["annotations"],
        "source_shank_ids": source.get("shank_ids", []),
        "shank_note": "Zero-based left-to-right shanks recovered from sharp contour tips; common base partitioned at inter-tip midpoints. Source labels retained separately.",
        "faces": len(set(sides)),
        "contact_sides": sides,
        "contact_shapes": source["contact_shapes"],
        "contact_shape_params": source["contact_shape_params"],
        "display_thickness_um": thickness,
        "body_note": "Upstream 2D outline retained, including any common base. Nominal extrusion only: 15 um single-sided / 30 um double-sided; exact physical thickness is unspecified.",
        "geometry_note": "Unverified upstream dimensions and tip origin. x/y are translated without scaling; face z uses nominal half-thickness with unknown physical error. No manufacturer-wide dimensional audit performed.",
        "routing_note": "Acquisition wiring is unassigned; source contact IDs are not treated as recording channels.",
    }
    if name == "ASSY-350-H12":
        metadata["shank_note"] += " Upstream labels all sites shank 0 although its contour has two tips."
    if len(contacts) == 63:
        metadata["geometry_note"] += " Source supplies 63 sites; no additional site has been invented."
    return ProbeGeometry(name, contacts, bodies=bodies, metadata=metadata), ChannelMap(n_channels=len(contacts))


def generate(source_dir, destination, *, download=False):
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    wiring_document = json.loads(WIRING.read_text(encoding="utf-8"))
    wiring = wiring_document["models"]
    connections = wiring_document.get("connections", {})
    if lock["revision"] != REVISION:
        raise ValueError("Converter and source lock revisions differ.")
    files = [(model["path"], model["blob_sha1"]) for model in lock["models"]]
    files.append(("LICENSE", lock["license_blob_sha1"]))
    if download:
        def fetch(entry):
            relative, digest = entry
            path = source_dir / relative
            if not path.exists():
                url = f"https://raw.githubusercontent.com/SpikeInterface/probeinterface_library/{REVISION}/{relative}"
                with urlopen(url, timeout=60) as response:
                    data = response.read()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            _read_pinned(path, digest)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(fetch, files))

    corrections = {geometry.name: (geometry, mapping)
                   for _, geometry, mapping in build_catalog()
                   if geometry.metadata["manufacturer"] == "Cambridge NeuroTech"}
    outputs, manifest = {}, []
    for entry in lock["models"]:
        name = entry["name"]
        doc = json.loads(_read_pinned(source_dir / entry["path"], entry["blob_sha1"]))
        if len(doc["probes"]) != 1:
            raise ValueError(f"Expected one probe: {name}")
        source = doc["probes"][0]
        if source["annotations"]["model_name"] != name:
            raise ValueError(f"Source model name mismatch: {name}")
        corrected = name in corrections
        geometry, mapping = corrections[name] if corrected else convert_probe(name, source)
        if name in wiring:
            route = wiring[name]
            connection = connections[route["connection_id"]] if "connection_id" in route else None
            if connection is not None:
                route = {**connection, **route}
            if route["source_blob_sha1"] != entry["blob_sha1"]:
                raise ValueError(f"Wiring needs review for changed source geometry: {name}")
            channels = {}
            pins = {}
            for group in route["groups"]:
                group_channels = ([route["pin_to_channel"][str(pin)]
                                   for pin in group["connector_pins_top_to_bottom"]]
                                  if connection is not None else group["channels_top_to_bottom"])
                for site, channel in zip(group["site_ids_top_to_bottom"], group_channels, strict=True):
                    if site in channels:
                        raise ValueError(f"Repeated wiring site: {name} / {site}")
                    channels[site] = channel
                if "connector_pins_top_to_bottom" in group:
                    pins.update(zip(group["site_ids_top_to_bottom"], group["connector_pins_top_to_bottom"], strict=True))
            if set(channels) != {c.contact_id for c in geometry.contacts}:
                raise ValueError(f"Wiring does not cover the supplied physical sites: {name}")
            profile = {"id": route["headstage_id"], "label": route["headstage_label"],
                       "n_channels": route["n_channels"], "contact_to_channel": channels,
                       "source_url": route["source_url"], "source_sha256": route["source_sha256"],
                       "note": route["note"], "missing_channels": route["missing_channels"]}
            if pins:
                profile.update(headstage_source_url=route["headstage_source_url"],
                               headstage_source_sha256=route["headstage_source_sha256"])
                geometry.metadata["contact_to_connector_pin"] = pins
            if "adapter_source_url" in route:
                profile.update(adapter_source_url=route["adapter_source_url"],
                               adapter_source_sha256=route["adapter_source_sha256"])
            geometry.metadata["headstage_profiles"] = [profile]
            geometry.metadata["headstage_fixed"] = route["fixed"]
            verified = headstage_map(geometry, profile["id"])
            if route["fixed"]:
                mapping = verified
            geometry.metadata["routing_note"] = (
                "Manufacturer zero-based Intan / Open Ephys channels. " if route["fixed"] else
                "Select the connected headstage to assign recording channels. "
            ) + route["note"]
            geometry.metadata.setdefault("sources", []).append({"url": route["source_url"],
                                                                 "sha256": route["source_sha256"]})
            geometry.metadata["site_id_convention"] = "Physical source IDs retained; recording channels are assigned by the selected official wiring profile."
        else:
            unavailable = {
                "ASSY-37-H3": "This 64-site source entry has no matching current ASSY-37 manufacturer map.",
                "ASSY-236-H1": "No current manufacturer map identifies the H1 variant of ASSY-236.",
                "ASSY-350-H15_2": "The published H15 map does not identify the staggered H15_2 variant.",
            }
            geometry.metadata["wiring_unavailable_reason"] = unavailable.get(
                name, "This legacy or unverified revision is outside the registered current connection profiles.")
        provenance = {"url": f"{lock['repository']}/blob/{REVISION}/{entry['path']}",
                      "revision": REVISION, "blob_sha1": entry["blob_sha1"]}
        geometry.metadata.setdefault("sources", []).append(provenance)
        geometry.metadata["source_license"] = "MIT; see LICENSE-ProbeInterface.txt in this directory."
        geometry.metadata["upstream_model"] = name
        geometry.metadata["conversion"] = "Atlaxis curated correction" if corrected else "ProbeInterface JSON to Atlaxis"
        mapping.validate(geometry)
        outputs[name + ".json"] = {"geometry": asdict(geometry), "channel_map": asdict(mapping)}
        manifest.append({"model": name, "file": name + ".json", "sites": len(geometry.contacts),
                         "shanks": len({c.shank_id for c in geometry.contacts}),
                         "mapped_channels": len(mapping.contact_to_channel), "curated_correction": corrected,
                         "headstage_profiles": [p["id"] for p in geometry.metadata.get("headstage_profiles", [])],
                         "source_blob_sha1": entry["blob_sha1"]})
    license_text = _read_pinned(source_dir / "LICENSE", lock["license_blob_sha1"]).decode()
    destination.mkdir(parents=True, exist_ok=True)
    for filename, payload in outputs.items():
        (destination / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Hidden so the file chooser does not present this as a probe geometry.
    (destination / ".manifest.json").write_text(json.dumps({
        "repository": lock["repository"], "revision": REVISION, "model_count": len(manifest),
        "models": manifest}, indent=2) + "\n", encoding="utf-8")
    (destination / "LICENSE-ProbeInterface.txt").write_text(license_text, encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=ROOT / "probes" / "Cambridge NeuroTech")
    parser.add_argument("--download", action="store_true", help="Download pinned JSONs into the source directory first")
    args = parser.parse_args()
    manifest = generate(args.source_dir, args.destination, download=args.download)
    print(f"Generated {len(manifest)} Cambridge models ({sum(item['sites'] for item in manifest)} sites); "
          f"{sum(item['curated_correction'] for item in manifest)} curated corrections.")


if __name__ == "__main__":
    main()
