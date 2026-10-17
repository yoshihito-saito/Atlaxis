"""Planning coordinates, combined NeuroSuite channel groups and NP routing."""

import csv
import io
import json
import re
import tempfile
from os.path import commonpath
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree as ET

from probe_planner.atlas.coordinates import (
    shank_surface_reference, shank_tip_stereotaxic_mm, pose_axis_tilts,
)
from probe_planner.probes.neuropixels import (
    is_neuropixels, active_site_ids, export_acquisition_imro, export_selection, import_imro,
    reference_description,
)
from probe_planner.probes.wiring import headstage_label
from probe_planner.probes.companions import channel_companions
from .save_load import save_plan
from .pipeline_exports import prepare_pipeline_exports


SUPPORT_DIRECTORY = "atlaxis"


def planning_bundle_directory(plan_path):
    """Resolve legacy root plans and plans in the version-2 support folder."""
    parent = Path(plan_path).parent
    manifest_path = parent / "bundle_manifest.json"
    if parent.name.casefold() == SUPPORT_DIRECTORY and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("format") == "atlaxis-planning-bundle" and manifest.get("version") == 2:
            return parent.parent
    return parent


def _stage_files(staging, files):
    for name, content in files.items():
        destination = staging / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            destination.write_bytes(content)
        else:
            destination.write_text(content, encoding="utf-8")


def _csv(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def prepare_channel_export(path, probe, region_rows):
    """Build a manual NP export and its description from one current selection."""
    path = Path(path)
    support = path.parent / SUPPORT_DIRECTORY
    geometry, mapping = probe.geometry, probe.channel_map
    active = active_site_ids(geometry, mapping)
    regions = {row["contact_id"]: row["region_acronym"]
               for row in region_rows if row["probe"] == probe.id}
    suffix = path.suffix.lower()
    if suffix in (".imro", ".csv"):
        source = export_acquisition_imro(geometry, mapping)
        # Decode the exported acquisition map itself so filler sites and shanks
        # match the actual IMRO, including hardware-channel ordering.
        acquisition = import_imro(geometry, source, {})
        rows = [{"channel_id": acquisition.contact_to_channel[contact.contact_id],
                 "site_id": contact.contact_id, "shank": contact.shank_id,
                 "region": regions.get(contact.contact_id, ""),
                 "is_target": int(contact.contact_id in active)}
                for contact in geometry.contacts if contact.contact_id in acquisition.contact_to_channel]
        csv_source = _csv(["channel_id", "site_id", "shank", "region", "is_target"],
                          sorted(rows, key=lambda row: row["channel_id"]))
    if suffix == ".imro":
        xml, _ = channel_companions(
            geometry, acquisition, active_sites=active,
            note='Routing matches the companion IMRO; skip=1 marks non-target acquisition channels.')
        files = {path: source,
                 path.with_suffix(".xml"): xml,
                 support / path.with_suffix(".selection.json").name: export_selection(geometry, mapping, acquisition_imro=source),
                 support / path.with_suffix(".active_channels.csv").name: csv_source}
        # The processing CSV follows this export's XML rather than the descriptive
        # channel list kept with the selection JSON in the support folder.
        processing, issues = prepare_pipeline_exports(
            [replace(probe, channel_map=acquisition)], ET.fromstring(xml), region_rows)
        files[path.with_suffix(".anatomical_map.csv")] = processing["anatomical_map.csv"]
        if "chanMap.mat" in processing:
            files[path.with_suffix(".channelmap.mat")] = processing["chanMap.mat"]
    elif suffix == ".json":
        files = {support / path.name: export_selection(geometry, mapping)}
    elif suffix == ".csv":
        files = {path: csv_source}
    else:
        raise ValueError("Choose IMRO, selection JSON or CSV for channel export.")
    readme = support / path.with_suffix(".README.txt").name
    files[readme] = (
        "Atlaxis manual channel export\n\n"
        f"Exported at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"Probe: {probe.id} · {geometry.name}\n"
        f"Selected targets: {len(active)}/384\n"
        f"Electrical reference: {reference_description(geometry, mapping)}\n"
        + (f"Additional acquisition channels: {384 - len(active)}\n"
           "CSV includes all 384 acquisition channels, including filler sites outside the target ROI.\n"
           "is_target=1 identifies user-selected sites; is_target=0 identifies filler sites.\n"
           + ("IMRO records all 384 channels. Selection JSON restores only the original targets.\n"
              "The XML has the same basename and routing as the IMRO; skip=1 marks non-target channels.\n"
              if suffix == ".imro" else "CSV uses the same completed routing as IMRO; no IMRO file is written here.\n")
           if suffix in (".imro", ".csv") else "Selected targets only; no acquisition map is generated by this export.\n")
        + "Channel IDs are zero-based hardware IDs local to this probe.\n"
        "IMRO reference IDs identify the electrical reference, not recording-channel IDs.\n"
        "Re-export after changing the selection to update these files together.\n"
        "Other previously exported formats/names remain separate snapshots.\n\n"
        + ("No channelmap MAT was written: " + " ".join(issues) + "\n" if suffix == ".imro" and issues else "")
        + "Files from this export:\n" + "\n".join(str(file.relative_to(path.parent)) for file in [*files, readme]) + "\n")
    return files


def write_channel_export(files):
    """Prepare every companion before replacing any existing export file."""
    directory = Path(commonpath([str(path.parent) for path in files]))
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".atlaxis-export-", dir=directory) as temporary:
        staging = Path(temporary)
        _stage_files(staging, {path.relative_to(directory): content for path, content in files.items()})
        for path in files:
            path.parent.mkdir(parents=True, exist_ok=True)
            (staging / path.relative_to(directory)).replace(path)


def save_planning_bundle(path, plan, atlas, region_rows):
    """Save one bundle, keeping hardware IDs distinct from combined XML IDs.

    The XML is a channel-group template: acquisition timing/gain are not known
    from an implantation plan. It must be merged with actual recording metadata.
    Saving never generates acquisition IMRO or guesses inactive NP routing.
    Return the saved plan path in the support folder.
    """
    path = Path(path)
    directory = planning_bundle_directory(path)
    plan_name = f"{SUPPORT_DIRECTORY}/{path.name}"
    saved_path = directory / plan_name
    xml_name = f"{directory.name}.xml"
    probes = plan.probes
    for probe in probes:
        probe.channel_map.validate(probe.geometry)
    root = ET.Element("parameters", {"version": "1.0"})
    root.append(ET.Comment("Channel-group template. Add actual acquisition timing/gain before loading recording data."))
    acquisition = ET.SubElement(root, "acquisitionSystem")
    count_element = ET.SubElement(acquisition, "nChannels")
    groups = ET.SubElement(ET.SubElement(root, "anatomicalDescription"), "channelGroups")
    files, coordinates, channel_rows, manifest_probes, notes = {}, [], [], [], []
    offset = 0
    for number, probe in enumerate(probes, 1):
        geometry, mapping = probe.geometry, probe.channel_map
        np_probe = is_neuropixels(geometry)
        active = active_site_ids(geometry, mapping)
        count = mapping.n_channels or len(geometry.contacts)
        prefix = f"probe_{number}"
        routed = dict(mapping.contact_to_channel)
        if np_probe:
            notes.append(f"{prefix}: {len(active)}/384 selected targets in this saved plan. "
                         "Acquisition files are created only by manual Export.")
            notes.append(f"{prefix}: electrical reference: {reference_description(geometry, mapping)}.")
            if active:
                xml, mat = channel_companions(
                    geometry, mapping, active_sites=active, xml_channel_offset=offset,
                    note='Current NP selection only. Unassigned inputs have no inferred site; no filler routing is generated.')
                files[f"{SUPPORT_DIRECTORY}/{prefix}.channels.xml"] = xml
                files[f"{SUPPORT_DIRECTORY}/{prefix}.chanCoords.channelInfo.mat"] = mat
                notes.append(f"{prefix}: chanCoords rows use local device channel + 1; "
                             f"combined {xml_name} offset is {offset}.")
        contacts = {contact.contact_id: contact for contact in geometry.contacts}
        by_channel = {channel: contacts[site] for site, channel in routed.items()}
        # Verified XML groups take precedence for ordinary probes. Otherwise use
        # known physical wiring by shank and keep all unknown wiring in one group.
        probe_groups = []
        if mapping.groups and not np_probe:
            probe_groups = [(f"group {index}", list(channels))
                            for index, channels in enumerate(mapping.groups, 1)]
            used = {channel for _, channels in probe_groups for channel in channels}
        else:
            used = set(by_channel)
            for shank in sorted({contact.shank_id for contact in by_channel.values()}):
                probe_groups.append((f"shank {shank}", sorted(channel for channel, contact in by_channel.items()
                                                             if contact.shank_id == shank)))
        ungrouped = sorted(set(range(count)) - used)
        if ungrouped:
            probe_groups.append(("unassigned wiring", ungrouped))
            if not np_probe:
                notes.append(f"{prefix}: hardware-to-site wiring is missing for {len(ungrouped)} channels; "
                             "these form one probe-level group, not inferred shank groups.")
        for label, channels in probe_groups:
            if not channels:
                continue
            # Generated groups follow physical base-to-tip order. Imported XML
            # order and groups lacking complete site correspondence stay intact.
            if (np_probe or mapping.source_xml is None) and all(channel in by_channel for channel in channels):
                channels = sorted(channels, key=lambda channel: (
                    -geometry.y_to_base * by_channel[channel].y_um, by_channel[channel].x_um))
            groups.append(ET.Comment(f"Probe {number}: {label}"))
            group = ET.SubElement(groups, "group")
            for channel in channels:
                contact = by_channel.get(channel)
                target = not np_probe or (contact is not None and contact.contact_id in active)
                ET.SubElement(group, "channel", {"skip": "0" if target else "1"}).text = str(offset + channel)
        for channel in range(count):
            contact = by_channel.get(channel)
            channel_rows.append({"probe_number": number, "probe_id": probe.id, "model": geometry.name,
                "headstage_id": mapping.headstage_id or "", "headstage": headstage_label(geometry, mapping),
                "xml_channel": offset + channel, "device_channel": channel,
                "site_id": contact.contact_id if contact else "", "shank": contact.shank_id if contact else "",
                "target_active": int(not np_probe or (contact is not None and contact.contact_id in active))})
        ap_tilt, ml_tilt, roll = pose_axis_tilts(probe.pose)
        for shank in sorted({contact.shank_id for contact in geometry.contacts}):
            tip = shank_tip_stereotaxic_mm(geometry, probe.pose, shank)
            surface = shank_surface_reference(geometry, probe.pose, shank, atlas, plan.coordinates)
            coordinates.append({"probe_number": number, "probe_id": probe.id, "model": geometry.name,
                "shank": shank, "reference_shank": int(shank == probe.selected_shank_id),
                "entry_ap_mm": "" if surface is None else surface.entry_mm[0],
                "entry_ml_mm": "" if surface is None else -surface.entry_mm[1],
                "entry_dv_bregma_mm": "" if surface is None else surface.entry_mm[2],
                "tip_ap_mm": tip[0], "tip_ml_mm": -tip[1], "tip_dv_bregma_mm": tip[2],
                "tip_dv_below_entry_surface_mm": "" if surface is None else surface.dv_mm,
                "ap_tilt_deg": ap_tilt, "ml_tilt_deg": ml_tilt, "roll_deg": roll,
                "atlas_pitch_correction_deg": plan.coordinates.pitch_correction_deg,
                "atlas_scale_ap": plan.coordinates.in_vivo_scale_ap_ml_dv[0],
                "atlas_scale_ml": plan.coordinates.in_vivo_scale_ap_ml_dv[1],
                "atlas_scale_dv": plan.coordinates.in_vivo_scale_ap_ml_dv[2],
                "insertion_depth_mm": "" if surface is None else surface.depth_mm})
        manifest_probes.append({"number": number, "id": probe.id, "model": geometry.name,
                                "headstage_id": mapping.headstage_id,
                                "xml_channel_offset": offset, "n_channels": count})
        offset += count
    count_element.text = str(offset)
    ET.indent(root)
    files[xml_name] = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
    processing, issues = prepare_pipeline_exports(probes, root, region_rows)
    files.update(processing)
    notes.extend(f"No chanMap.mat: {issue}" for issue in issues)
    files[f"{SUPPORT_DIRECTORY}/planned_coordinates.csv"] = _csv(list(coordinates[0]), coordinates)
    files[f"{SUPPORT_DIRECTORY}/channel_index.csv"] = _csv(list(channel_rows[0]), channel_rows)
    files[f"{SUPPORT_DIRECTORY}/README.txt"] = (
        "Atlaxis planning bundle\n\n"
        f"Saved at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"Atlas: {plan.atlas_name}, version {plan.atlas_version}\n"
        f"Atlas pitch correction: {plan.coordinates.pitch_correction_deg:g} degrees (skull to scaled atlas axes).\n"
        f"Native AP/ML/DV scale about Bregma: {tuple(plan.coordinates.in_vivo_scale_ap_ml_dv)}.\n"
        f"Open {plan_name} in Atlaxis to restore probes, poses and ROI selections.\n"
        "Processing inputs stay in the plan folder; Atlaxis support files are in atlaxis/.\n"
        "anatomical_map.csv has no header: each XML group is a column, with labels in XML channel order.\n"
        "Blank anatomical cells mean unknown wiring, outside/unannotated tissue, or an absent channel.\n"
        "chanMap.mat is written only when every hardware input has confirmed site geometry.\n"
        "chanMap0ind uses zero-based combined XML/DAT IDs; chanMap uses those same IDs plus one.\n"
        "connected follows XML skip flags. probe_ids identify physical probes; kcoords are unique shank IDs.\n"
        "Coordinates are in um. Nonplanar/double-sided probes also have standard zcoords, retaining native XYZ distances.\n"
        "Consecutive probe-tip AP/ML separations unfold along +x; tip DV differences shift y.\n"
        "Inter-probe distances are approximate. Full 3D positions are physical_xyz_um (AP/right-ML/DV).\n"
        "PreprocessPipeline uses standard XYZ for 3D local reference and postprocess sparsity; 2D-only sorters do not use zcoords.\n"
        "CSV coordinates match the controls: mm, Bregma AP anterior+, ML anatomical left+, DV ventral+.\n"
        "Angles: degrees, AP tilt anterior+, ML tilt anatomical left+.\n"
        "Plan JSON retains canonical anatomical right-positive ML and azimuth/elevation/roll angles.\n"
        "Each shank's entry is the first annotated brain boundary along its insertion axis.\n"
        "Insertion depth is signed axis travel from that entry; tip DV is its vertical component.\n"
        "Depth is negative before entry, zero at the surface, positive after entry.\n"
        "Blank entry/depth fields mean that the shank's axis misses annotated tissue.\n"
        "Plan JSON retains the canonical pose transform; its depth field is not the per-shank surface depth.\n"
        f"{xml_name} combines all probes in plan order. Hardware and XML channels are zero-based;\n"
        "channel_index.csv records each probe's headstage, offset and any known site/shank correspondence.\n"
        "Generated, fully mapped XML groups follow physical base-to-tip order, retaining hardware IDs.\n"
        "Imported XML group order and groups with unknown site correspondence are preserved.\n"
        "This is a channelGroups template, not complete recording metadata. Merge it with\n"
        "the recording's XML (sampling rate, bit depth, gain, auxiliary/sync channels, etc.).\n"
        "Offsets assume concatenated neural channels, excluding auxiliary/sync channels.\n"
        "Ordinary probes use all channels; A6x21 IDs are provisional until verified.\n"
        "Save updates this plan and its coordinate/XML/index/README files.\n"
        "Selected NP probes also have atlaxis/probe_N.channels.xml and atlaxis/probe_N.chanCoords.channelInfo.mat.\n"
        "These reflect the saved selection; unmapped inputs keep NaN coordinates without renumbering.\n"
        "Those chanCoords MAT XYZ are probe-local micrometers, not atlas coordinates; channel IDs are one-based.\n"
        "Clearing a selection/removing a probe removes its previously saved selection companions.\n"
        "Use Export to write NP IMRO, selection JSON and target CSV manually.\n"
        "Each manual export has atlaxis/<name>.README.txt with the exported target count.\n"
        "IMRO exports also write <name>.xml with matching acquisition routing and target skip flags.\n"
        "Earlier exports (including files from older automatic saves) are kept unchanged by Save.\n"
        "Re-export after edits; old acquisition files may not match this saved plan.\n"
        "XML skip=1 marks non-target NP channels; no filler sites are assigned on Save.\n"
        "An exported IMRO records all 384 channels, including any non-target filler sites.\n\n"
        "IMRO reference IDs identify the electrical reference, not recording-channel IDs.\n\n"
        + "\n".join(notes) + "\n")
    manifest_name = f"{SUPPORT_DIRECTORY}/bundle_manifest.json"
    manifest_path = directory / manifest_name
    if not manifest_path.exists():
        manifest_path = directory / "bundle_manifest.json"
    old_manifest = {}
    if manifest_path.exists():
        old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old_manifest.get("format") != "atlaxis-planning-bundle":
            raise ValueError("The destination contains an unrelated bundle_manifest.json.")
    # Acquisition exports are independent snapshots, not owned by Save.
    managed = set(files) | {plan_name, manifest_name}
    manifest = {"format": "atlaxis-planning-bundle", "version": 2, "plan": plan_name,
                "files": sorted(managed), "probes": manifest_probes, "channelmap_issues": issues}
    files[manifest_name] = json.dumps(manifest, indent=2) + "\n"
    if plan_name in files:
        raise ValueError("The plan filename conflicts with a companion output; use plan.json.")
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".atlaxis-save-", dir=directory) as temporary:
        staging = Path(temporary)
        _stage_files(staging, files)
        save_plan(staging / plan_name, plan)
        for name in files:
            destination = directory / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            (staging / name).replace(destination)
        (staging / plan_name).replace(saved_path)
    # Retire only known obsolete outputs and support files owned by this bundle.
    # Manual IMRO/CSV/selection exports remain independent snapshots.
    for name in set(old_manifest.get("files", [])) - managed:
        if (name in {"probes.xml", "README.txt", "planned_coordinates.csv", "channel_index.csv", "bundle_manifest.json", "channelmap.mat", "chanMap.mat"}
                or name == path.name
                or re.fullmatch(r"(?:atlaxis/)?probe_\d+\.(?:channels\.xml|chanCoords\.channelInfo\.mat)", name)):
            (directory / name).unlink(missing_ok=True)
    return saved_path
