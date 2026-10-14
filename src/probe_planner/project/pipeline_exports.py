"""PreprocessPipeline channel geometry and XML-ordered anatomical labels."""

import csv
import io

import numpy as np
from scipy.io import savemat

from probe_planner.atlas.coordinates import probe_to_stereotaxic_matrix, transform_points


def prepare_pipeline_exports(probes, xml_root, region_rows):
    """Return processing files and reasons confirmed channel geometry is unavailable.

    Each probe keeps its native XY distances. Consecutive probe-tip AP/ML
    separation is unfolded along +x; tip DV offsets shift y. Nonplanar probes
    retain native z in the standard zcoords field for downstream 3D distances.
    Inter-probe distances are approximate. Physical XYZ retain AP/right-ML/DV.
    """
    regions = {(row["probe"], row["contact_id"]): row["region_acronym"]
               for row in region_rows}
    groups = xml_root.findall("./anatomicalDescription/channelGroups/group")
    labels, rows, tips, issues = {}, [], [], []
    offset, shank_offset, horizontal_offset = 0, 0, 0.0
    has_3d = False
    for number, probe in enumerate(probes, 1):
        geometry, mapping = probe.geometry, probe.channel_map
        count = mapping.n_channels or len(geometry.contacts)
        routing = mapping.contact_to_channel
        contacts = {contact.contact_id: contact for contact in geometry.contacts}
        by_channel = {channel: contacts[site] for site, channel in routing.items()}
        missing = set(range(count)) - set(by_channel)
        if missing:
            issues.append(f"{probe.id}: no confirmed site geometry for {len(missing)} hardware channels.")
        points = np.array([[contact.x_um, contact.y_um, contact.z_um]
                           for contact in by_channel.values()], dtype=float).reshape(-1, 3)
        z_origin = float(points[:, 2].min()) if len(points) else 0.0
        has_3d = has_3d or (len(points) > 0 and np.ptp(points[:, 2]) != 0)
        transform = probe_to_stereotaxic_matrix(geometry, probe.pose)
        tip = transform_points([geometry.tip_um], transform)[0]
        if tips:
            horizontal_offset += float(np.linalg.norm(tip[:2] - tips[-1][:2]))
        tips.append(tip)
        shanks = sorted({contact.shank_id for contact in geometry.contacts})
        shank_groups = {shank: shank_offset + index for index, shank in enumerate(shanks, 1)}
        for channel in range(count):
            contact = by_channel.get(channel)
            if contact is None:
                continue
            label = regions.get((probe.id, contact.contact_id), "")
            labels[offset + channel] = "" if label == "—" else label
            physical = transform_points([[contact.x_um, contact.y_um, contact.z_um]], transform)[0]
            rows.append((offset + channel,
                         contact.x_um - geometry.tip_um[0] + horizontal_offset,
                         geometry.y_to_base * (contact.y_um - geometry.tip_um[1]) - (tip[2] - tips[0][2]),
                         shank_groups[contact.shank_id], number, contact.contact_id, physical,
                         contact.z_um - z_origin))
        offset += count
        shank_offset += len(shanks)
    # CSV columns and row order exactly follow the generated XML groups.
    channel_groups = [[int(channel.text) for channel in group.findall("channel")] for group in groups]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    for index in range(max((len(group) for group in channel_groups), default=0)):
        writer.writerow([labels.get(group[index], "") if index < len(group) else ""
                         for group in channel_groups])
    files = {"anatomical_map.csv": stream.getvalue()}
    if issues:
        return files, issues
    connected = {int(channel.text): channel.get("skip", "0") != "1"
                 for group in groups for channel in group.findall("channel")}
    rows.sort(key=lambda row: row[0])
    ids = np.array([row[0] for row in rows], dtype=np.int64)
    payload = {
        "chanMap": (ids + 1).reshape(-1, 1).astype(float),
        "chanMap0ind": ids.reshape(-1, 1),
        "connected": np.array([connected[channel] for channel in ids], dtype=bool).reshape(-1, 1),
        "xcoords": np.array([row[1] for row in rows]).reshape(-1, 1),
        "ycoords": np.array([row[2] for row in rows]).reshape(-1, 1),
        "kcoords": np.array([row[3] for row in rows], dtype=np.int64).reshape(-1, 1),
        "probe_ids": np.array([row[4] for row in rows], dtype=np.int64).reshape(-1, 1),
        "contact_ids": np.array([row[5] for row in rows], dtype=object).reshape(-1, 1),
        "physical_xyz_um": np.array([row[6] for row in rows]),
        "probe_tip_xyz_um": np.array(tips),
        "units": "um",
        "physical_coordinate_system": "Bregma AP anterior+, ML right+, DV ventral+",
        "sorting_coordinate_system": "Native probe XYZ; consecutive tip AP/ML distances unfolded along +x; y toward base with tip DV offsets; z relative to each probe's minimum native z",
        "distance_note": "Within-probe distances preserved in XYZ when zcoords is present, otherwise in XY; inter-probe distances approximate; 2D-only sorters do not use zcoords",
    }
    if has_3d:
        payload["zcoords"] = np.array([row[7] for row in rows]).reshape(-1, 1)
    binary = io.BytesIO()
    savemat(binary, payload, do_compression=True)
    files["channelmap.mat"] = binary.getvalue()
    return files, issues
