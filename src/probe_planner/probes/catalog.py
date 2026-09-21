"""Reproducible physical layouts; sources and provisional dimensions travel with JSON.

Run ``python -m probe_planner.probes.catalog`` from the repository to regenerate
the library. Site IDs describe physical locations, never acquisition wiring.
"""

from dataclasses import asdict
import argparse
import json
from math import sqrt
from pathlib import Path

from .model import ChannelMap, Contact, ProbeBody, ProbeGeometry


NEURONEXUS = "https://solutions.neuronexus.com/hubfs/Penetrating_Probe_Catalog_V2.1.pdf"
CAMBRIDGE = "https://www.cambridgeneurotech.com/assets/files/Cambridge-NeuroTech-Product-Catalog.pdf"
H20_MAP = "https://www.cambridgeneurotech.com/assets/files/ASSY-350-H20-map.pdf"
E1_MAP = "https://www.cambridgeneurotech.com/assets/files/ASSY-325D-E-1_E-2-map.pdf"
NP1 = "https://www.neuropixels.org/_files/ugd/328966_9f784121a69f4f56bd314ffdf7f86d2b.pdf"
NP2 = "https://www.neuropixels.org/_files/ugd/328966_2b39661f072d405b8d284c3c73588bc6.pdf"
PROBE_TABLE = "https://github.com/billkarsh/ProbeTable/blob/main/Tables/probe_features.json"
NP_LAYOUT = "https://github.com/cortex-lab/neuropixels/wiki/Selecting-recording-electrodes"


def _body(shank, x, length, thickness, profile, tip_y=0):
    """Symmetric schematic silhouette, profile = (distance from tip, half width)."""
    outline = [[x, tip_y, 0]]
    outline += [[x - half, tip_y + y, 0] for y, half in profile]
    outline += [[x - profile[-1][1], tip_y + length, 0],
                [x + profile[-1][1], tip_y + length, 0]]
    outline += [[x + half, tip_y + y, 0] for y, half in reversed(profile)]
    return ProbeBody(outline, thickness, shank)


def _sites(shank, center_x, xy, thickness, face="front"):
    z = -thickness / 2 if face == "front" else thickness / 2
    return [Contact(f"s{shank}_{face}_{i:04d}", shank, center_x + x, y, z)
            for i, (x, y) in enumerate(xy)]


def _probe(name, manufacturer, contacts, bodies, source, page, layout, **extra):
    metadata = {
        "manufacturer": manufacturer,
        "sources": [{"url": source, "pdf_page": page}],
        "source_accessed": "2026-09-20",
        "site_id_convention": "Zero-based shank and physical site index; front/back in local z.",
        "coordinate_convention": "um; first shank tip at origin; +x across shanks; +y toward base; front is -z.",
        "layout_note": layout,
        "body_note": "Schematic shaft silhouettes from catalog dimensions; taper transitions are interpolated. Connector and headstage omitted.",
        "routing_note": "Physical site IDs only. Acquisition wiring is unassigned.",
        **extra,
    }
    return ProbeGeometry(name, contacts, bodies=bodies, metadata=metadata)


def build_catalog():
    """Return curated and source-mapped library entries."""
    entries = []

    def add(geometry, n_channels=None, mapping=None):
        path = Path(geometry.metadata["manufacturer"]) / f"{geometry.name}.json"
        entries.append((path, geometry, mapping if mapping is not None else
                        ChannelMap(n_channels=n_channels or len(geometry.contacts))))

    # Alternating rows are 23 um apart, not 23 um within each column.
    contacts, bodies = [], []
    for s in range(4):
        contacts += _sites(s, 200 * s, [(15 * (-1)**i, 50 + 23 * i) for i in range(16)], 15)
        bodies.append(_body(s, 200 * s, 5000, 15, [(50, 26), (395, 43)]))
    add(_probe("A4x16-poly2-5mm-23s-200-177", "NeuroNexus", contacts, bodies,
               NEURONEXUS, 89, "4 x 16 sites; 200 um shank pitch; 30 um column separation; 50 um tip offset.",
               site_area_um2=177, xml_reference="A4x16-Poly2-5mm-23s-200-177.xml"))

    # The dimensioned 20 um nearest-neighbor diagonal and 10 um vertical
    # stagger imply sqrt(20^2 - 10^2) um column separation.
    buz_cluster = [(sqrt(300) / 2 * (-1)**i, 35 + 10 * i) for i in range(12)]
    contacts, bodies = [], []
    for s in range(5):
        xy = list(buz_cluster)
        if s == 2:
            xy += [(0, 145 + 200 * i) for i in range(1, 5)]
        contacts += _sites(s, 200 * s, xy, 15)
        bodies.append(_body(s, 200 * s, 5000, 15,
                            [(35, 21.5), (145, 25 if s == 2 else 21.5)]))
    add(_probe("Buzsaki-5x12", "NeuroNexus", contacts, bodies, NEURONEXUS, 102,
               "12 distal sites on each of 5 shanks plus 4 proximal center-shank sites: 64 total. 200 um shank pitch.",
               site_area_um2=160))

    contacts, bodies = [], []
    for s in range(5):
        if s == 2:
            tip = -1200
            xy = [(0, tip + 50 + 100 * i) for i in range(13)]
            xy += [(0, tip + y) for y in (1750, 2250, 2750)]
            bodies.append(_body(s, 200 * s, 6200, 15, [(50, 29)], tip_y=tip))
        else:
            xy = buz_cluster
            bodies.append(_body(s, 200 * s, 5000, 15, [(35, 24)]))
        contacts += _sites(s, 200 * s, xy, 15)
    add(_probe("A5x12-16-Buz-Lin-5mm-100-200-160-177", "NeuroNexus", contacts, bodies,
               NEURONEXUS, 95, "12/12/16/12/12 sites; center shank extends 1.2 mm beyond 5 mm outer shanks. 200 um shank pitch.",
               site_area_um2={"outer_shanks": 160, "center_shank": 177},
               xml_reference="A5x12_16-Buz_lin-5mm-100-200-160_177_version1.xml; version2.xml",
               geometry_note="Central shaft width is schematic (58 um); the catalog does not fully dimension its proximal taper."))

    contacts, bodies = [], []
    buz64_x = [0, -8.5, 8.5, -12.5, 12.5, -16.5, 16.5, -20.5]
    for s in range(8):
        contacts += _sites(s, 200 * s, [(x, 22 + 20 * i) for i, x in enumerate(buz64_x)], 50)
        bodies.append(_body(s, 200 * s, 10000, 50, [(22, 14.5), (162, 26), (1000, 80)]))
    add(_probe("Buzsaki64L", "NeuroNexus", contacts, bodies, NEURONEXUS, 104,
               "8 x 8 sites; 200 um shank pitch; 20 um staggered row spacing; 22 um tip offset.",
               site_area_um2=160, thickness_variant_um=50,
               geometry_note="50 um thickness variant selected; the catalog also offers 15 um.",
               xml_reference="Buzsaki64L.xml"))

    contacts, bodies = [], []
    a6_x = [0, -8.5, 8.5, -12.5, 12.5, -14.5, 14.5] + [-15, 15] * 7
    for s in range(6):
        xy = [(x, 35.5 + 25 * i) for i, x in enumerate(a6_x)]
        if s == 2:
            xy += [(0, 635.5), (0, 735.5)]
        contacts += _sites(s, 200 * s, xy, 50)
        bodies.append(_body(s, 200 * s, 10000, 50, [(35.5, 14.5), (535.5, 51.5)]))
    add(_probe("A6x21-poly2-10mm-50-200-160", "NeuroNexus", contacts, bodies,
               NEURONEXUS, 119, "21 distal sites per shank plus 2 proximal sites on shank 2 (third from left, electrode-facing): 128 total. 200 um shank pitch; 25 um staggered rows.",
               site_area_um2=160, provisional=True,
               geometry_note="Provisional: 35.5 um tip-to-first-site distance digitized from catalog (~2 um reading repeatability, not a manufacturing tolerance)."))

    contacts, bodies, assignments = [], [], {}
    # ASSY-350 map: A-to-D electrode-facing order (opposite the headstage
    # front-view photo). Read each shank from tip to base, left site first.
    h20_channels = [26, 27, 6, 25, 28, 7, 24, 29, 8, 23, 30, 9, 22, 5, 10, 21,
                    4, 11, 20, 3, 12, 19, 2, 15, 16, 1, 14, 17, 31, 13, 18, 0]
    for s in range(4):
        xy = [(0, 22.5 + 30 * i) for i in range(11)]
        xy += [(x, 22.5 + 45 + 30 * i) for i in range(10) for x in (-18.5, 18.5)]
        xy += [(0, 22.5 + 315 + (1200, 1000, 800, 600)[s])]
        xy.sort(key=lambda p: (p[1], p[0]))
        sites = _sites(s, 150 * s, xy, 15)
        contacts += sites
        assignments.update({site.contact_id: channel + 32 * s
                            for site, channel in zip(sites, h20_channels, strict=True)})
        bodies.append(_body(s, 150 * s, 6500, 15, [(22.5, 25), (337.5, 30)]))
    geometry = _probe("ASSY-350-H20", "Cambridge NeuroTech", contacts, bodies, CAMBRIDGE, 50,
               "4 x 32 single-sided sites. 31-site three-column cluster plus one remote site per shank; 150 um shank pitch; 6.5 mm standard length.",
               provisional=True, assembly="ASSY-350", shank_labels=["A", "B", "C", "D"],
               routing_note="Official ASSY-350 H20 digital SPI map; zero-based Intan/Open Ephys acquisition channels. Shanks 0..3 are A..D in the electrode-facing schematic, opposite the headstage front-view photo.",
               geometry_note="Provisional: 22.5 um tip offset digitized (~3 um reading repeatability). Remote-site gaps are 1200/1000/800/600 um; middle two inferred from drawing scale. Actual uncertainty is unknown.",
               faces=1)
    geometry.metadata["sources"].append({"url": H20_MAP, "pdf_page": 1, "updated": "2024-07-01"})
    add(geometry, mapping=ChannelMap(contact_to_channel=assignments, n_channels=128))

    contacts, bodies, assignments = [], [], {}
    e1_x = [1.6, -5.4, 8.8, -8.8, 11.2, -11.5, 14.6, -14.4,
            18.1, -18.4, 20.8, -20.8, 24.2, -24.5, 27.7, -28.0]
    # Both face tables use D, C, B, A in a common front projection. Do not
    # mirror the back sites a second time. Rows are stored tip to base.
    e1_channels = [7, 8, 6, 9, 5, 10, 4, 11, 3, 12, 2, 13, 1, 14, 0, 15]
    e1_bases = {"front": (96, 112, 0, 16), "back": (80, 64, 48, 32)}
    for s in range(4):
        for face in ("front", "back"):
            xy = [(x, 22.5 + 20 * i) for i, x in enumerate(e1_x)]
            sites = _sites(s, 250 * s, xy, 30, face)
            contacts += sites
            assignments.update({site.contact_id: channel + e1_bases[face][s]
                                for site, channel in zip(sites, e1_channels, strict=True)})
        bodies.append(_body(s, 250 * s, 6000, 30, [(22.5, 10), (322.5, 35)]))
    geometry = _probe("ASSY-325D-E-1", "Cambridge NeuroTech", contacts, bodies, CAMBRIDGE, 40,
               "4 physical shanks, 16 sites on each face: 128 total. 250 um shank pitch; 6 mm length; 30 um thickness.",
               provisional=True, faces=2, assembly="ASSY-325D", shank_labels=["D", "C", "B", "A"],
               routing_note="Official ASSY-325D E-1/E-2 digital SPI map; zero-based Intan/Open Ephys acquisition channels. Shanks 0..3 are D..A in the common front projection used by both face tables.",
               geometry_note="Provisional: x positions and 22.5 um tip offset digitized (~5 um reading repeatability, not an accuracy bound). Both faces follow the map's common front projection; exact face registration and lateral offsets require a dimensioned drawing.")
    geometry.metadata["sources"].append({"url": E1_MAP, "pdf_page": 1, "updated": "2024-07-01"})
    add(geometry, mapping=ChannelMap(contact_to_channel=assignments, n_channels=128))

    for version, shanks, count, pitch, name in (
        (1, 1, 960, 20, "Neuropixels-1.0-single-shank"),
        (2, 1, 1280, 15, "Neuropixels-2.0-single-shank"),
        (2, 4, 1280, 15, "Neuropixels-2.0-four-shank"),
    ):
        contacts, bodies = [], []
        for s in range(shanks):
            # Left shaft edge is -35; NP2 columns are asymmetric, not +/-16.
            xy = [(((11, 43, 27, 59)[i % 4] if version == 1 else (27, 59)[i % 2]) - 35,
                   200 + pitch * (i // 2)) for i in range(count)]
            contacts += _sites(s, 250 * s, xy, 24)
            bodies.append(_body(s, 250 * s, 10000, 24, [(175, 35)]))
        geometry = _probe(name, "Neuropixels", contacts, bodies, NP1 if version == 1 else NP2, 2,
                          f"{shanks} shank(s), {count} physical sites per shank; 12 x 12 um sites; 384 simultaneous recording channels across the probe.",
                          site_size_um=[12, 12], part_number="NP1000" if version == 1 else "NP2003" if shanks == 1 else "NP2013",
                          routing_note="All physical sites shown. Use Select to generate up to 384 active channels with NeuroCarto, or import an IMRO map.")
        geometry.metadata["sources"] += [{"url": PROBE_TABLE}, {"url": NP_LAYOUT}]
        if version == 2:
            geometry.metadata.update(provisional=True, geometry_note=
                "Provisional: 200 um tip-to-first-site offset. Official NP2 documentation specifies a 175 um taper but not the first site-center offset; exact registration needs a dimensioned drawing.")
        add(geometry, 384)
    from .neuronexus_catalog import extend_neuronexus
    extend_neuronexus(entries)
    from .probemaps import extend_probemaps
    extend_probemaps(entries)
    return entries


def write_catalog(destination, manufacturer=None):
    for relative, geometry, mapping in build_catalog():
        if manufacturer is not None and geometry.metadata["manufacturer"] != manufacturer:
            continue
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"geometry": asdict(geometry), "channel_map": asdict(mapping)},
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manufacturer", choices=["NeuroNexus", "Cambridge NeuroTech", "Neuropixels"])
    write_catalog(Path.cwd() / "probes", parser.parse_args().manufacturer)
