from dataclasses import dataclass
from pathlib import Path

import numpy as np
import tifffile


@dataclass
class AtlasModel:
    name: str
    version: str
    resolution_um: tuple[float, float, float]
    orientation: str
    annotation: np.ndarray
    structures: dict
    root_mesh_path: Path
    backend: object
    reference_volume: np.ndarray | None = None

    @property
    def reference(self):
        return self.reference_volume if self.reference_volume is not None else self.backend.reference

    @property
    def hierarchy(self):
        return self.backend.hierarchy


def load_atlas(name: str, version: str | None = None, progress=None) -> AtlasModel:
    from brainglobe_atlasapi import BrainGlobeAtlas
    from brainglobe_atlasapi.descriptors import ANNOTATION_FILENAME, REFERENCE_FILENAME

    report = progress or (lambda message: None)
    last_percent = -1

    def download_progress(completed, total):
        nonlocal last_percent
        percent = int(100 * completed / total) if total else 0
        if percent != last_percent:
            report(f"Downloading {name}: {percent}%")
            last_percent = percent

    report(f"Opening {name} (download on first use)…")
    atlas = BrainGlobeAtlas(name, check_latest=False, fn_update=download_progress)
    actual_version = ".".join(map(str, atlas.local_version))
    if version is not None and version != actual_version:
        raise ValueError(f"Project needs atlas version {version}; installed version is {actual_version}.")
    report("Opening annotation without loading the whole volume into RAM…")
    # Uncompressed TIFFs (including Waxholm) map directly; compressed TIFFs are
    # decoded into a temporary disk-backed map by tifffile. Labels stay exact.
    annotation = tifffile.imread(atlas.root_dir / ANNOTATION_FILENAME, out="memmap")
    if annotation.ndim != 3:
        raise ValueError("Atlas annotation must be three-dimensional.")
    report("Opening reference images for coronal and sagittal sections…")
    reference = tifffile.imread(atlas.root_dir / REFERENCE_FILENAME, out="memmap")
    if reference.shape != annotation.shape:
        raise ValueError("Reference and annotation volumes must have the same shape.")
    return AtlasModel(
        name, actual_version, tuple(atlas.resolution),
        atlas.orientation, annotation, atlas.structures, Path(atlas.root_meshfile()), atlas, reference,
    )
