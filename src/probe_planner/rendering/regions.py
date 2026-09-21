"""Prepare native atlas region surfaces off the GUI thread."""

from pathlib import Path

import numpy as np
import pyvista as pv
from scipy.ndimage import binary_closing, binary_fill_holes
from probe_planner.atlas.regions import brain_region_ids, include_unknown_regions, spinal_display_interior


def default_hidden_regions(atlas):
    """Omit protruding Waxholm nerves and spinal cord from display."""
    if not atlas.name.startswith("whs_sd_rat_"):
        return set()
    return {region_id for region_id, region in atlas.structures.items()
            if region["acronym"] in {"5n", "2n", "7n-u", "SpC"}}


def brain_display_region_ids(atlas):
    """Share the visible brain scope across region surfaces and slice textures."""
    return brain_region_ids(atlas.structures) - default_hidden_regions(atlas)


def label_surface(atlas, region_id, *, excluded_ids=()):
    """Contour an exact label, or the nonzero union when region_id is None.

    Exclusions apply only to the display outline, never to atlas annotations.
    """
    excluded_ids = list(excluded_ids)

    def inside(data, index):
        if region_id is not None:
            mask = data == region_id
        else:
            mask = (data != 0) & ~np.isin(data, excluded_ids)
        mask.flat[spinal_display_interior(atlas, index)] = False
        return mask

    shape = np.asarray(atlas.annotation.shape)
    lower, upper = shape.copy(), np.zeros(3, dtype=int)
    # Locate the occupied box without allocating a mask of the full volume.
    for index, plane in enumerate(atlas.annotation):
        rows, columns = np.nonzero(inside(plane, index))
        if rows.size:
            lower = np.minimum(lower, (index, rows.min(), columns.min()))
            upper = np.maximum(upper, (index + 1, rows.max() + 1, columns.max() + 1))
    if np.any(upper <= lower):
        raise ValueError(f"Atlas label {region_id} has no voxels.")
    # Fill one plane at a time in VTK's storage order, avoiding full-volume
    # temporary masks and an extra transposed copy of the large brain outline.
    padding = 3 if region_id is None else 1
    mask = np.zeros(tuple(upper - lower + 2 * padding), dtype=np.uint8, order="F")
    for index in range(int(lower[0]), int(upper[0])):
        plane = inside(atlas.annotation[index], index)[lower[1]:upper[1], lower[2]:upper[2]]
        mask[index - lower[0] + padding, padding:-padding, padding:-padding] = plane
    if region_id is None:
        # Only the display envelope: seal narrow label gaps and enclosed voids
        # so their inner walls do not show through the transparent surface.
        binary_closing(mask, iterations=2, output=mask)
        binary_fill_holes(mask, output=mask)
    grid = pv.ImageData(dimensions=mask.shape, spacing=atlas.resolution_um,
                        origin=(lower - padding) * np.asarray(atlas.resolution_um))
    grid.point_data["inside"] = mask.ravel(order="F")
    mesh = grid.contour([0.5], scalars="inside", method="flying_edges")
    mesh.clear_data()
    return mesh


def load_region_meshes(atlas, progress):
    """Return one mesh per nonzero label, without overlapping group envelopes."""
    labels, clipped_labels = set(), set()
    count = atlas.annotation.shape[0]
    for start in range(0, count, 16):
        progress(f"Finding annotated regions… {min(start + 16, count) * 100 // count}%")
        labels.update(int(value) for value in np.unique(atlas.annotation[start:start + 16]))
        for index in range(start, min(start + 16, count)):
            excluded = spinal_display_interior(atlas, index)
            if len(excluded):
                clipped_labels.update(int(value) for value in np.unique(atlas.annotation[index].flat[excluded]))
    labels.discard(0)
    include_unknown_regions(atlas, labels)
    parents = {ancestor for region in atlas.structures.values()
               for ancestor in region.get("structure_id_path", [])[:-1]}
    meshes = {}
    if clipped_labels:
        from brainglobe_atlasapi.descriptors import ANNOTATION_FILENAME

        stat = (atlas.backend.root_dir / ANNOTATION_FILENAME).stat()
        cache_dir = atlas.root_mesh_path.parent.parent / "probe_planner_cache"
        cache_dir.mkdir(exist_ok=True)
    for index, region_id in enumerate(sorted(labels), 1):
        region = atlas.structures[region_id]
        progress(f"Preparing 3D regions… {index}/{len(labels)} · {region['acronym']}")
        path = (None if region.get("metadata_missing") else
                Path(atlas.backend.meshfile_from_structure(region_id)))
        # Parent mesh files include their descendants; using them for a direct
        # parent label would make unchecked children remain visible.
        if region_id in clipped_labels:
            # Native meshes contain the spinal portions of PVG/CC as well.
            cache = cache_dir / f"{region_id}-spinal-interior-v1-{stat.st_size}-{stat.st_mtime_ns}.vtp"
            if cache.exists():
                mesh = pv.read(cache)
            else:
                mesh = label_surface(atlas, region_id)
                temporary = cache.with_suffix(".tmp.vtp")
                mesh.save(temporary)
                temporary.replace(cache)
        else:
            mesh = (label_surface(atlas, region_id) if region_id in parents or path is None or not path.is_file()
                    else pv.read(path))
        if not mesh.n_cells:
            raise ValueError(f"Empty 3D surface for {region['acronym']} ({region_id}).")
        meshes[region_id] = mesh
    return meshes
