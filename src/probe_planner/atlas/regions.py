"""Region scope shared by mask and channel-selection controls."""

import numpy as np
from scipy.ndimage import binary_fill_holes


def include_unknown_regions(atlas, labels):
    """Describe orphan annotation IDs without inventing anatomical metadata.

    Keep placeholders local to Atlaxis, leaving BrainGlobe's source ontology and
    annotation unchanged. Standalone paths deliberately assert no known parent.
    """
    missing = set(labels).difference(atlas.structures) - {0}
    if missing:
        atlas.structures = dict(atlas.structures)
        for region_id in sorted(missing):
            atlas.structures[region_id] = {
                "id": region_id, "name": f"Unknown region {region_id} (metadata missing)",
                "acronym": f"Unknown {region_id}", "rgb_triplet": [160, 160, 160],
                "structure_id_path": [region_id], "metadata_missing": True,
            }


def brain_region_ids(structures):
    """Use the explicit Brain subtree when supplied by the atlas ontology."""
    roots = {rid for rid, region in structures.items()
             if region.get("name", "").casefold() == "brain"
             or region.get("acronym", "").casefold() == "brain"}
    if not roots:
        return set(structures)
    return {rid for rid, region in structures.items()
            if rid in roots or roots.intersection(region.get("structure_id_path", []))}


def spinal_display_interior(atlas, ap_index):
    """Sparse transverse indices of non-cord labels enclosed by Waxholm SpC.

    PVG and central canal extend from the brain into the cord. Only their parts
    enclosed by the cord in native AP cross-sections are hidden. This is display
    geometry, never a change to annotation values or contact-region lookup.
    """
    if not atlas.name.startswith("whs_sd_rat_") or atlas.orientation[0] not in "ap":
        return np.empty(0, dtype=np.int64)
    if ap_index not in atlas.spinal_display_cache:
        cord_ids = [rid for rid, region in atlas.structures.items() if region["acronym"] == "SpC"]
        plane = atlas.annotation[ap_index]
        cord = np.isin(plane, cord_ids)
        interior = (np.flatnonzero(binary_fill_holes(cord) & ~cord & (plane != 0))
                    if cord.any() else np.empty(0, dtype=np.int64))
        atlas.spinal_display_cache[ap_index] = interior
    return atlas.spinal_display_cache[ap_index]


def spinal_display_hidden(atlas, indices):
    """Display exclusion at N native voxel indices, without a volume-sized mask."""
    hidden = np.zeros(len(indices), dtype=bool)
    if (not len(indices) or not atlas.name.startswith("whs_sd_rat_")
            or atlas.orientation[0] not in "ap"):
        return hidden
    order = np.argsort(indices[:, 0], kind="stable")
    planes, starts = np.unique(indices[order, 0], return_index=True)
    stops = np.r_[starts[1:], len(order)]
    for plane, start, stop in zip(planes, starts, stops):
        excluded = spinal_display_interior(atlas, int(plane))
        if len(excluded):
            selected = order[start:stop]
            flat = indices[selected, 1] * atlas.annotation.shape[2] + indices[selected, 2]
            hidden[selected] = np.isin(flat, excluded)
    return hidden
