import numpy as np

from probe_planner.atlas.coordinates import (
    probe_to_atlas, transform_points, um_to_mm,
)
from probe_planner.probes.neuropixels import active_site_ids


def map_contacts(geometry, channel_map, pose, atlas, frame, probe_id=None):
    points = transform_points(geometry.points, probe_to_atlas(geometry, pose, frame))
    stereo = um_to_mm(frame.atlas_to_stereotaxic(points))
    voxels = frame.atlas_to_voxel(points)
    inside = np.all((voxels >= 0) & (voxels < atlas.annotation.shape), axis=1)
    ids = np.full(len(points), -1, dtype=np.int64)
    indices = np.floor(voxels[inside]).astype(np.int64)
    ids[inside] = atlas.annotation[tuple(indices.T)]
    rows = []
    active_sites = active_site_ids(geometry, channel_map)
    for index, contact in enumerate(geometry.contacts):
        region_id = int(ids[index])
        region = atlas.structures.get(region_id, {})
        channel = channel_map.contact_to_channel.get(contact.contact_id)
        rows.append({
            "probe": probe_id or geometry.name, "model": geometry.name, "shank": contact.shank_id,
            "contact_id": contact.contact_id, "device_channel": channel,
            "active": contact.contact_id in active_sites,
            "atlas_x_um": float(points[index, 0]), "atlas_y_um": float(points[index, 1]),
            "atlas_z_um": float(points[index, 2]), "ap_mm": float(stereo[index, 0]),
            "ml_mm": float(stereo[index, 1]), "dv_mm": float(stereo[index, 2]),
            "region_id": region_id,
            "region_name": region.get("name", "Outside atlas" if region_id == -1 else
                                      "Unannotated" if region_id == 0 else "Unknown region"),
            "region_acronym": region.get("acronym", "—"),
        })
    return rows
