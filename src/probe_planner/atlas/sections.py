"""Orthogonal section geometry and projected probe coordinates (no Qt)."""

from dataclasses import dataclass

import numpy as np

from .coordinates import (
    probe_to_atlas, probe_to_stereotaxic_matrix, transform_points, um_to_mm, shank_reference_um,
)
from .regions import spinal_display_hidden


@dataclass
class Section:
    name: str
    horizontal: int
    vertical: int
    normal: int
    index: int
    reference: np.ndarray
    annotation: np.ndarray
    pixel_um: tuple[float, float]
    caption: str
    axis_labels: str
    display_mask: np.ndarray | None = None


def probe_positions(instance, atlas=None, frame=None):
    matrix = (probe_to_atlas(instance.geometry, instance.pose, frame) if frame is not None
              else probe_to_stereotaxic_matrix(instance.geometry, instance.pose))
    return matrix, transform_points(instance.geometry.points, matrix)


def contact_center(instance, points):
    return points[[c.shank_id == instance.selected_shank_id for c in instance.geometry.contacts]].mean(axis=0)


def shank_tip_atlas_position(instance, frame):
    """Selected physical tip in atlas micrometers, including insertion travel."""
    tip = shank_reference_um(instance.geometry, instance.selected_shank_id)
    matrix = probe_to_atlas(instance.geometry, instance.pose, frame)
    return transform_points(tip[None, :], matrix)[0]


def section_axes(orientation, name):
    def axis(letters):
        return next(i for i, letter in enumerate(orientation) if letter in letters)
    ap, ml, dv = axis("ap"), axis("lr"), axis("si")
    return (ml, dv, ap) if name == "Coronal" else (ap, dv, ml)


def section_at(atlas, frame, center, name, *, slice_index=None):
    """Native section through a position, or at an explicit integer voxel index."""
    horizontal, vertical, normal = section_axes(atlas.orientation, name)
    requested = (int(np.floor(center[normal] / atlas.resolution_um[normal]))
                 if slice_index is None else int(slice_index))
    index = int(np.clip(requested, 0, atlas.annotation.shape[normal] - 1))
    slicing = [slice(None)] * 3
    slicing[normal] = index
    remaining = [i for i in range(3) if i != normal]
    order = [remaining.index(vertical), remaining.index(horizontal)]
    annotation = atlas.annotation[tuple(slicing)].transpose(order)
    reference = atlas.reference[tuple(slicing)].transpose(order)
    rows, columns = np.nonzero(annotation)
    indices = np.empty((len(rows), 3), dtype=int)
    indices[:, normal], indices[:, vertical], indices[:, horizontal] = index, rows, columns
    display_mask = np.ones(annotation.shape, dtype=bool)
    display_mask[rows, columns] = ~spinal_display_hidden(atlas, indices)
    # Describe the actual displayed section, not an out-of-bounds requested one.
    location = center.copy()
    location[normal] = index * atlas.resolution_um[normal]
    if frame is not None:
        stereo = um_to_mm(frame.atlas_to_stereotaxic(location[None, :]))[0]
        coordinate = 0 if name == "Coronal" else 1
        label = "AP" if name == "Coronal" else "ML"
        if name == "Coronal" and frame.pitch_correction_deg:
            label = "AP at center"
        caption = f"{name} · {label} {stereo[coordinate]:.2f} mm"
    else:
        caption = f"{name} · atlas slice {index}"
    if requested != index:
        caption += " · nearest atlas edge (requested position outside volume)"
    ends = {"a": "A → P", "p": "P → A", "r": "R → L", "l": "L → R",
            "s": "Dorsal ↓ Ventral", "i": "Ventral ↓ Dorsal"}
    return Section(name, horizontal, vertical, normal, index, reference, annotation,
                   (atlas.resolution_um[horizontal], atlas.resolution_um[vertical]), caption,
                   f"{ends[atlas.orientation[horizontal]]}   |   {ends[atlas.orientation[vertical]]}", display_mask)
