"""Atlas sampling in the physical plane of a probe (distances in micrometers)."""

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import map_coordinates

from .coordinates import probe_to_atlas
from .regions import spinal_display_hidden


@dataclass
class ProbeSection:
    reference: np.ndarray
    annotation: np.ndarray
    pixel_um: tuple[float, float]
    origin_uv: tuple[float, float]
    face_z_um: float
    display_mask: np.ndarray | None = None


def probe_section(atlas, frame, instance, interrupted=lambda: False):
    """Use native voxel containment for labels; interpolate only MRI intensity.

    The plane follows probe XY at the median contact-face Z of the reference
    shank. Display V points toward the tip. A 5 mm margin gives wider context
    around all contacts and the physical tip, without sampling a whole volume.
    """
    geometry = instance.geometry
    points = geometry.points
    face_z = float(np.median(points[[c.shank_id == instance.selected_shank_id
                                    for c in geometry.contacts], 2]))
    uv = points[:, :2] * (1, -geometry.y_to_base)
    tip_uv = np.asarray(geometry.tip_um[:2]) * (1, -geometry.y_to_base)
    bounds = np.vstack((uv, tip_uv))
    pitch = float(min(atlas.resolution_um))
    lower = np.floor((bounds.min(axis=0) - 5000) / pitch) * pitch
    upper = np.ceil((bounds.max(axis=0) + 5000) / pitch) * pitch
    width, height = np.ceil((upper - lower) / pitch).astype(int)
    reference = np.zeros((height, width), dtype=np.float32)
    annotation = np.zeros((height, width), dtype=atlas.annotation.dtype)
    display_mask = np.ones((height, width), dtype=bool)
    matrix = probe_to_atlas(geometry, instance.pose, frame)
    resolution = np.asarray(atlas.resolution_um)
    shape = np.asarray(atlas.annotation.shape)
    x = lower[0] + (np.arange(width) + 0.5) * pitch
    # Chunking bounds working memory independently of the total plane height.
    for start in range(0, height, 64):
        if interrupted():
            return None
        stop = min(start + 64, height)
        y = -geometry.y_to_base * (lower[1] + (np.arange(start, stop) + 0.5) * pitch)
        xyz = (x[None, :, None] * matrix[:3, 0]
               + y[:, None, None] * matrix[:3, 1]
               + face_z * matrix[:3, 2] + matrix[:3, 3])
        voxels = xyz / resolution
        inside = np.all((voxels >= 0) & (voxels < shape), axis=2)
        indices = np.floor(voxels[inside]).astype(int)
        annotation[start:stop][inside] = atlas.annotation[tuple(indices.T)]
        display_mask[start:stop][inside] = ~spinal_display_hidden(atlas, indices)
        # Existing atlas positions identify voxel cells; sample at cell centers.
        reference[start:stop][inside] = map_coordinates(
            atlas.reference, (voxels[inside] - 0.5).T, order=1,
            output=np.float32, mode="nearest", prefilter=False)
    return ProbeSection(reference, annotation, (pitch, pitch), tuple(lower), face_z, display_mask)
