"""Skull-level atlas sections and projected probe coordinates (no Qt)."""

from dataclasses import asdict, dataclass
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import tempfile

import numpy as np
from scipy.ndimage import map_coordinates

from .coordinates import (
    probe_to_atlas, probe_to_stereotaxic_matrix, transform_points, shank_reference_um,
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
    corners_um: np.ndarray | None = None  # Physical native atlas coordinates.
    index_range: tuple[int, int] | None = None
    normal_step_um: float | None = None
    orientation: str | None = None


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


def _level_grid(atlas, frame):
    """Enclose the transformed native voxel box in skull-level ASR axes."""
    extent = np.asarray(atlas.annotation.shape) * atlas.resolution_um
    corners = np.array(list(product(*[(0., value) for value in extent])))
    stereo = frame.atlas_to_stereotaxic(corners)
    grid = stereo[:, [0, 2, 1]] * [-1, 1, -1]
    pitch = float(min(atlas.resolution_um) * min(frame.in_vivo_scale_ap_ml_dv))
    return np.floor(grid.min(axis=0) / pitch).astype(int), np.ceil(grid.max(axis=0) / pitch).astype(int), pitch


def section_cache_key(atlas, frame, center, name, *, slice_index=None):
    """Memory-cache identity within one atlas/frame, before any resampling."""
    if slice_index is not None:
        return name, int(slice_index)
    if frame is None:
        normal = section_axes(atlas.orientation, name)[2]
        return name, int(np.floor(center[normal] / atlas.resolution_um[normal]))
    pitch = min(atlas.resolution_um) * min(frame.in_vivo_scale_ap_ml_dv)
    stereo = frame.atlas_to_stereotaxic(np.asarray(center)[None, :])[0]
    coordinate = stereo[0 if name == "Coronal" else 1]
    return name, int(np.floor(-coordinate / pitch))


def _section_cache_file(atlas, frame, cache_dir, name, index):
    from brainglobe_atlasapi.descriptors import ANNOTATION_FILENAME, REFERENCE_FILENAME

    sources = []
    for filename in (ANNOTATION_FILENAME, REFERENCE_FILENAME):
        path = atlas.backend.root_dir / filename
        stat = path.stat()
        sources.append((str(path.resolve()), stat.st_size, stat.st_mtime_ns))
    descriptor = json.dumps({"algorithm": "skull-level-sections-v1", "atlas": atlas.name,
        "version": atlas.version, "shape": list(atlas.annotation.shape),
        "frame": asdict(frame), "sources": sources}, sort_keys=True)
    digest = hashlib.sha256(descriptor.encode()).hexdigest()[:20]
    folder = Path(cache_dir) / "sections-v1" / digest
    folder.mkdir(parents=True, exist_ok=True)
    metadata = folder / "transform.json"
    if not metadata.exists():
        metadata.write_text(descriptor + "\n", encoding="utf-8")
    return folder / f"{name}-{index}.npz"


def _level_section(atlas, frame, center, name, slice_index, cache_dir):
    horizontal, vertical, normal = section_axes("asr", name)
    lower, upper, pitch = _level_grid(atlas, frame)
    requested = section_cache_key(atlas, frame, center, name, slice_index=slice_index)[1]
    index = int(np.clip(requested, lower[normal], upper[normal]))
    width, height = int(upper[horizontal] - lower[horizontal]), int(upper[vertical] - lower[vertical])
    # Grid axes are posterior+, ventral+, left+; convert to AP/ML/DV before
    # inverse atlas lookup. Keeping this explicit prevents a second ML flip.
    grid_to_stereo = np.array([[-1., 0, 0], [0, 0, -1.], [0, 1., 0]])
    matrix = frame.stereo_to_atlas_matrix
    basis = matrix[:3, :3] @ grid_to_stereo
    origin = matrix[:3, 3] + basis[:, normal] * (index * pitch)
    corners = np.tile(origin, (4, 1))
    corners += np.array([lower[horizontal], upper[horizontal], upper[horizontal], lower[horizontal]])[:, None] * pitch * basis[:, horizontal]
    corners += np.array([lower[vertical], lower[vertical], upper[vertical], upper[vertical]])[:, None] * pitch * basis[:, vertical]
    cache = _section_cache_file(atlas, frame, cache_dir, name, index) if cache_dir is not None else None
    if cache is not None and cache.exists():
        with np.load(cache, allow_pickle=False) as saved:
            reference, annotation, display_mask = saved["reference"], saved["annotation"], saved["display_mask"]
    else:
        reference = np.zeros((height, width), dtype=np.float32)
        annotation = np.zeros((height, width), dtype=atlas.annotation.dtype)
        display_mask = np.ones((height, width), dtype=bool)
        x = (lower[horizontal] + np.arange(width) + .5) * pitch
        resolution, shape = np.asarray(atlas.resolution_um), np.asarray(atlas.annotation.shape)
        for start in range(0, height, 64):
            stop = min(height, start + 64)
            y = (lower[vertical] + np.arange(start, stop) + .5) * pitch
            positions = origin + x[None, :, None] * basis[:, horizontal] + y[:, None, None] * basis[:, vertical]
            voxels = positions / resolution
            inside = np.all((voxels >= 0) & (voxels < shape), axis=2)
            indices = np.floor(voxels[inside]).astype(int)
            annotation[start:stop][inside] = atlas.annotation[tuple(indices.T)]
            display_mask[start:stop][inside] = ~spinal_display_hidden(atlas, indices)
            reference[start:stop][inside] = map_coordinates(atlas.reference,
                (voxels[inside] - .5).T, order=1, output=np.float32, mode="nearest", prefilter=False)
        if cache is not None:
            descriptor, temporary = tempfile.mkstemp(prefix=".section-", suffix=".npz", dir=cache.parent)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    np.savez_compressed(stream, reference=reference, annotation=annotation, display_mask=display_mask)
                Path(temporary).replace(cache)
            finally:
                Path(temporary).unlink(missing_ok=True)
    coordinate = -index * pitch / 1000
    caption = f"{name} · {'AP' if name == 'Coronal' else 'ML'} {coordinate:.2f} mm"
    if requested != index:
        caption += " · nearest atlas edge (requested position outside volume)"
    labels = ("R → L" if name == "Coronal" else "A → P") + "   |   Dorsal ↓ Ventral"
    return Section(name, horizontal, vertical, normal, index, reference, annotation,
        (pitch, pitch), caption, labels, display_mask, corners,
        (int(lower[normal]), int(upper[normal])), pitch, "asr")


def section_at(atlas, frame, center, name, *, slice_index=None, cache_dir=None):
    """Calibrated constant-AP/ML section; native sections without a frame."""
    if frame is not None:
        return _level_section(atlas, frame, center, name, slice_index, cache_dir)
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
    caption = f"{name} · atlas slice {index}"
    if requested != index:
        caption += " · nearest atlas edge (requested position outside volume)"
    ends = {"a": "A → P", "p": "P → A", "r": "R → L", "l": "L → R",
            "s": "Dorsal ↓ Ventral", "i": "Ventral ↓ Dorsal"}
    return Section(name, horizontal, vertical, normal, index, reference, annotation,
                   (atlas.resolution_um[horizontal], atlas.resolution_um[vertical]), caption,
                   f"{ends[atlas.orientation[horizontal]]}   |   {ends[atlas.orientation[vertical]]}", display_mask,
                   index_range=(0, atlas.annotation.shape[normal] - 1),
                   normal_step_um=atlas.resolution_um[normal], orientation=atlas.orientation)
