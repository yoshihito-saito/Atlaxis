"""Download and prepare CT reference surfaces once, outside application assets."""

import hashlib
import json
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

import numpy as np
import pyvista as pv

from .skull import Skull


def reference_definition(species):
    path = Path(__file__).resolve().parents[1] / "data" / "skulls" / f"{species}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def reference_cache_path(species, folder, definition):
    # Changed landmarks, reference size, source or preparation version need a
    # fresh asset; a cached surface must never silently use obsolete placement.
    digest = hashlib.sha256(json.dumps(definition, sort_keys=True).encode()).hexdigest()[:12]
    return folder / f"{species}-{digest}.npz"


def prepare_reference(source, definition, target, progress):
    """Rigid placement + uniform reference sizing, then offline simplification."""
    progress("Preparing lightweight CT skull (first use only)…")
    mesh = pv.read(source).triangulate()
    if not isinstance(mesh, pv.PolyData) or not mesh.n_cells:
        raise ValueError("The downloaded skull has no polygonal surface.")
    if "native_z_max" in definition:
        faces = mesh.faces.reshape(-1, 4)[:, 1:]
        keep = np.all(mesh.points[faces, 2] < definition["native_z_max"], axis=1)
        mesh = pv.PolyData(mesh.points, np.column_stack((np.full(keep.sum(), 3), faces[keep]))).clean()
    original_faces = mesh.n_cells
    matrix = np.asarray(definition["source_to_stereotaxic_rigid_matrix"], dtype=float)
    landmarks = {name: np.asarray(point, dtype=float) for name, point in definition["source_landmarks"].items()}
    source_distance = np.linalg.norm(landmarks["Bregma"] - landmarks["Lambda"])
    scale = definition["reference_bl_mm"] / source_distance
    mesh.points = (np.asarray(mesh.points, dtype=float) @ matrix[:3, :3].T + matrix[:3, 3]) * scale
    landmarks = {name: ((point @ matrix[:3, :3].T + matrix[:3, 3]) * scale).tolist()
                 for name, point in landmarks.items()}
    from probe_planner.rendering.skull_projection import encoded_projection

    progress("Preparing CT surface detail (first use only)…")
    projection = encoded_projection(mesh)
    # This is an intentionally reduced display reference. Quantify a deterministic
    # sample of source-vertex distances to the reduced surface and retain it in
    # provenance; these samples are not a Hausdorff bound or landmark accuracy.
    sample = mesh.points[np.linspace(0, mesh.n_points - 1, min(mesh.n_points, 5000), dtype=int)].copy()
    if mesh.n_cells > definition["display_triangles"]:
        mesh = mesh.decimate(1 - definition["display_triangles"] / mesh.n_cells,
                             volume_preservation=True)
    mesh.clear_data()
    _, closest = mesh.find_closest_cell(sample, return_closest_point=True)
    errors = np.linalg.norm(sample - closest, axis=1)
    metadata = {**definition, "dorsal_projection": projection, "landmarks_mm": landmarks, "native_to_reference_scale": float(scale),
                "source_triangles": original_faces, "prepared_triangles": mesh.n_cells,
                "simplification_sample_mm": {"samples": len(sample), "median": float(np.median(errors)),
                    "p95": float(np.quantile(errors, .95)), "max": float(errors.max())}}
    # Validate before replacing any existing cache entry.
    skull = Skull(definition["name"], mesh.points.tolist(), mesh.faces.reshape(-1, 4)[:, 1:].tolist(),
                  approximate=True, landmarks_mm=landmarks, reference_info=metadata)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp.npz")
    try:
        np.savez_compressed(temporary, points_mm=np.asarray(skull.points_mm, dtype=np.float32),
                            triangles=np.asarray(skull.triangles, dtype=np.int32),
                            metadata=np.array(json.dumps(metadata)))
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return skull


def load_reference(species, folder, progress):
    definition = reference_definition(species)
    target = reference_cache_path(species, folder, definition)
    if target.is_file():
        progress(f"Loading cached {species} CT skull…")
        with np.load(target, allow_pickle=False) as data:
            metadata = json.loads(str(data["metadata"].item()))
            return Skull(metadata["name"], data["points_mm"].tolist(), data["triangles"].tolist(),
                         approximate=True, landmarks_mm=metadata["landmarks_mm"], reference_info=metadata)
    folder.mkdir(parents=True, exist_ok=True)
    progress(f"Downloading {species} CT skull from {definition['provider']} (first use only)…")
    with tempfile.TemporaryDirectory(prefix=f"{species}-", dir=folder) as temporary:
        source = Path(temporary) / "skull.stl"
        request = Request(definition["download_url"], headers={"User-Agent": "Atlaxis/0.1 (CT reference download)"})
        with urlopen(request, timeout=60) as response, source.open("wb") as stream:
            total = int(response.headers.get("Content-Length", 0))
            received = 0
            last_mb = -1
            checksum = hashlib.sha256()
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
                checksum.update(chunk)
                received += len(chunk)
                mb = received // (1024 * 1024)
                if mb != last_mb:
                    size = f" / {total // (1024 * 1024)} MiB" if total else " MiB"
                    progress(f"Downloading {species} CT skull: {mb}{size}")
                    last_mb = mb
        if checksum.hexdigest() != definition["source_sha256"]:
            raise ValueError("The CT file differs from the source used for landmark registration.")
        return prepare_reference(source, definition, target, progress)
