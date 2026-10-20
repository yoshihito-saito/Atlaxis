from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

import numpy as np
import tifffile

from .catalogue import S3_VERSIONS, local_atlases


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
    spinal_display_cache: dict[int, np.ndarray] = field(default_factory=dict, repr=False, compare=False)

    @property
    def reference(self):
        return self.reference_volume if self.reference_volume is not None else self.backend.reference

    @property
    def hierarchy(self):
        return self.backend.hierarchy


class _AtlasFiles:
    """Keep the application's TIFF/OBJ interface for both distribution formats."""

    def __init__(self, root_dir, metadata, structures, native=None, origin_um=(0, 0, 0)):
        self.root_dir = root_dir
        self.metadata = metadata
        self.structures = structures
        self.native = native
        self.origin_um = np.asarray(origin_um, dtype=float)
        self.hierarchy = structures.tree
        self.reference = None

    def meshfile_from_structure(self, structure):
        import meshio

        region = self.structures[structure]
        path = self.root_dir / "meshes" / f"{region['id']}.obj"
        if self.native is not None and not path.is_file():
            try:
                mesh = region["mesh"]
            except RuntimeError as error:
                if isinstance(error.__cause__, FileNotFoundError):
                    return path  # The existing label-surface path handles absent meshes.
                raise
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp.obj")
            try:
                # The official reader already converts nm/XYZ to um/ASR. Express
                # those physical points relative to this image level's first voxel.
                mesh.points = mesh.points - self.origin_um
                meshio.write(temporary, mesh, file_format="obj")
                temporary.replace(path)
            finally:
                region.data["mesh"] = None
                temporary.unlink(missing_ok=True)
        return path

    def root_meshfile(self):
        return self.meshfile_from_structure("root")


def _legacy_atlas(root, name, version):
    import meshio
    from brainglobe_atlasapi.structure_class import Structure, StructuresDict

    class LocalStructure(Structure):
        @staticmethod
        def _read_mesh(path):
            return meshio.read(path)

        def _download_mesh(self, path):
            raise FileNotFoundError(f"Restore the original legacy atlas mesh: {path}")

    folder = root / f"{name}_v{version}"
    if not (folder / "metadata.json").is_file():
        raise FileNotFoundError(
            f"This plan requires {name} v{version}. Restore its original atlas folder at {folder}. "
            "New downloads use BrainGlobe 3 versions; existing plans are not upgraded automatically."
        )
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    structures_list = json.loads((folder / "structures.json").read_text(encoding="utf-8"))
    for region in structures_list:
        region["mesh_filename"] = folder / "meshes" / f"{region['id']}.obj"
    structures = StructuresDict(structures_list)
    structures.data = {region["id"]: LocalStructure(**region, mesh=None) for region in structures_list}
    return _AtlasFiles(folder, metadata, structures)


def _s3_image(native, cache, kind, report):
    import ngff_zarr
    from brainglobe_atlasapi import descriptors
    from fsspec.callbacks import Callback

    annotation = kind == "annotation"
    component = native.metadata["annotation_set"]
    if not annotation:
        component = component["template"]
    location = component["location"].lstrip("/")
    filename = descriptors.V3_ANNOTATION_NAME if annotation else descriptors.V3_TEMPLATE_NAME
    level = native._annotation_pyramid_level if annotation else native._template_pyramid_level
    multiscale = ngff_zarr.from_ngff_zarr(native.root_dir / location / filename)
    image = multiscale.images[level]
    origin_um = np.array([image.translation[dim] for dim in image.dims]) * 1000
    if image.data.shape != tuple(native.shape) or len(image.dims) != 3:
        raise ValueError(f"The S3 {kind} grid does not match the requested atlas.")
    destination = cache / ("annotation.tiff" if annotation else "reference.tiff")
    if not destination.is_file():
        dataset = multiscale.metadata.datasets[level].path
        relative = f"{location}/{filename}/{dataset}"
        report(f"Downloading {kind} from BrainGlobe S3…")
        last_step = -1

        def update(size, value):
            nonlocal last_step
            step = int(100 * value / size) if size else 0
            if step != last_step:
                report(f"Downloading {kind} from BrainGlobe S3… {step}%")
                last_step = step

        # Fetch the entire selected level even if an earlier attempt left a 'c'
        # directory: missing Zarr chunks can otherwise silently become fill values.
        native.fs.get(descriptors.remote_url_s3.format(relative + "/"),
                      native.root_dir / relative, recursive=True,
                      callback=Callback(hooks={"progress": update}))
        temporary = destination.with_suffix(".tmp.tiff")
        mapped = None
        try:
            mapped = tifffile.memmap(temporary, shape=image.data.shape,
                                     dtype=image.data.dtype, bigtiff=True)
            slab = max(1, (32 * 1024 * 1024) // (np.prod(mapped.shape[1:]) * mapped.dtype.itemsize))
            for start in range(0, len(mapped), slab):
                stop = min(start + slab, len(mapped))
                report(f"Preparing {kind} disk cache… {stop * 100 // len(mapped)}%")
                mapped[start:stop] = image.data[start:stop].compute()
            mapped.flush()
            mapped._mmap.close()
            mapped = None
            temporary.replace(destination)
        finally:
            if mapped is not None:
                mapped._mmap.close()
            temporary.unlink(missing_ok=True)
    return origin_um


def _s3_atlas(root, name, version, report):
    from brainglobe_atlasapi import BrainGlobeAtlas

    native = BrainGlobeAtlas(name, version=version, brainglobe_dir=root,
                             check_latest=False, dask=True)
    manifest = json.dumps(native.metadata, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(manifest).hexdigest()[:16]
    cache = root / "probe_planner_cache" / "atlases" / f"{name}_v{version}-v1-{digest}"
    cache.mkdir(parents=True, exist_ok=True)
    annotation_origin = _s3_image(native, cache, "annotation", report)
    reference_origin = _s3_image(native, cache, "reference", report)
    if not np.array_equal(annotation_origin, reference_origin):
        raise ValueError("The S3 reference and annotation have different physical origins.")
    provenance = cache / "metadata.json"
    if not provenance.exists():
        temporary = provenance.with_suffix(".tmp.json")
        temporary.write_bytes(manifest)
        temporary.replace(provenance)
    return _AtlasFiles(cache, native.metadata, native.structures, native, annotation_origin)


def load_atlas(name: str, version: str | None = None, progress=None) -> AtlasModel:
    from brainglobe_atlasapi import config
    from brainglobe_atlasapi.descriptors import ANNOTATION_FILENAME, REFERENCE_FILENAME

    report = progress or (lambda message: None)
    root = config.get_brainglobe_dir()
    if version is None:
        installed = [value for atlas_name, value in local_atlases(root) if atlas_name == name]
        version = (max(installed, key=lambda value: tuple(map(int, value.split("."))))
                   if installed else S3_VERSIONS.get(name))
    if version is None:
        raise ValueError(f"Specify an atlas version for {name}.")
    version = version.replace("_", ".")
    report(f"Opening {name} v{version} (download on first use)…")
    atlas = (_legacy_atlas(root, name, version) if int(version.split(".")[0]) < 3
             else _s3_atlas(root, name, version, report))
    actual_version = atlas.metadata["version"].replace("_", ".")
    if version != actual_version:
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
    atlas.reference = reference
    return AtlasModel(
        name, actual_version, tuple(atlas.metadata["resolution"]),
        atlas.metadata["orientation"], annotation, atlas.structures, Path(atlas.root_meshfile()), atlas, reference,
    )
