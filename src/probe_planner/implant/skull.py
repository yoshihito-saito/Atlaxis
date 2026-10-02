"""Editable skull surfaces in Bregma-relative AP/ML/DV millimeters."""

from dataclasses import asdict, dataclass, field
from functools import cached_property
from pathlib import Path

import numpy as np
import pyvista as pv
from scipy.spatial.transform import Rotation


def cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def simple_polygon(points):
    """Validate a simple polygon and return a counterclockwise boundary."""
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3 or not np.isfinite(points).all():
        raise ValueError("Draw at least three finite polygon vertices.")
    # Redundant collinear vertices carry no geometry, but reversals are invalid.
    points = list(points)
    changed = True
    while changed and len(points) > 3:
        changed = False
        for i in range(len(points)):
            a, b, c = points[i - 1], points[i], points[(i + 1) % len(points)]
            if abs(cross2(b - a, c - b)) < 1e-10 and np.dot(b - a, c - b) >= 0:
                del points[i]
                changed = True
                break
    points = np.asarray(points)
    edges = np.roll(points, -1, axis=0) - points
    if np.any(np.linalg.norm(edges, axis=1) < 1e-8):
        raise ValueError("Polygon vertices must be distinct.")
    if any(abs(cross2(edge, edges[i - 1])) < 1e-10 and np.dot(edge, edges[i - 1]) < 0
           for i, edge in enumerate(edges)):
        raise ValueError("Adjacent polygon edges must not overlap.")
    for i, (a, edge) in enumerate(zip(points, edges)):
        for j in range(i + 1, len(points)):
            if j == i + 1 or (i == 0 and j == len(points) - 1):
                continue
            c, other = points[j], edges[j]
            b, d = a + edge, c + other
            if np.any(np.maximum(np.minimum(a, b), np.minimum(c, d)) >
                      np.minimum(np.maximum(a, b), np.maximum(c, d)) + 1e-10):
                continue
            if (cross2(edge, c - a) * cross2(edge, d - a) <= 0 and
                    cross2(other, a - c) * cross2(other, b - c) <= 0):
                raise ValueError("Polygon edges must not cross or touch each other.")
    area2 = sum(cross2(a, b) for a, b in zip(points, np.roll(points, -1, axis=0)))
    if abs(area2) < 1e-10:
        raise ValueError("The opening must have positive area.")
    return points if area2 > 0 else points[::-1]


def convex_parts(polygon):
    """Ear triangulation of concave polygons; preserve convex boundaries intact."""
    vertices = list(polygon)
    if all(cross2(vertices[i] - vertices[i - 1], vertices[(i + 1) % len(vertices)] - vertices[i])
           >= 0 for i in range(len(vertices))):
        return [polygon]
    parts = []
    while len(vertices) > 3:
        for i in range(len(vertices)):
            a, b, c = vertices[i - 1], vertices[i], vertices[(i + 1) % len(vertices)]
            if cross2(b - a, c - b) <= 1e-10:
                continue
            others = [p for j, p in enumerate(vertices)
                      if j not in ((i - 1) % len(vertices), i, (i + 1) % len(vertices))]
            if any(min(cross2(b - a, p - a), cross2(c - b, p - b), cross2(a - c, p - c))
                   >= -1e-10 for p in others):
                continue
            parts.append(np.array([a, b, c]))
            del vertices[i]
            break
        else:
            raise ValueError("Cannot triangulate this polygon; remove overlapping or nearly collinear vertices.")
    return [*parts, np.asarray(vertices)]


@dataclass
class Craniotomy:
    id: str
    name: str
    shape: str
    points_mm: list

    def __post_init__(self):
        if not self.id or not self.name.strip():
            raise ValueError("An opening needs an ID and name.")
        self.polygon

    @property
    def polygon(self):
        p = np.asarray(self.points_mm, dtype=float)
        if p.ndim != 2 or p.shape[1] != 2 or not np.isfinite(p).all():
            raise ValueError("Opening coordinates must be finite AP/ML pairs in mm.")
        if self.shape == "Polygon":
            return simple_polygon(p)
        if self.shape not in ("Rectangle", "Circle") or len(p) != 2:
            raise ValueError("Rectangle and Circle require two points.")
        if self.shape == "Rectangle":
            low, high = np.min(p, axis=0), np.max(p, axis=0)
            return simple_polygon([low, [high[0], low[1]], high, [low[0], high[1]]])
        radius = np.linalg.norm(p[1] - p[0])
        if radius < 1e-6:
            raise ValueError("The circle radius must be positive.")
        angles = np.arange(128) * (2 * np.pi / 128)
        return p[0] + radius * np.column_stack((np.cos(angles), np.sin(angles)))


@dataclass
class Skull:
    source_name: str
    points_mm: list
    triangles: list
    # Each native mesh axis maps to a signed stereo axis, numbered 1..3.
    axes: tuple[int, int, int] = (1, 2, 3)
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    translation_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    visible: bool = False
    opacity: float = 1.0
    openings: list[Craniotomy] = field(default_factory=list)
    approximate: bool = False
    scale: float = 1.0
    landmarks_mm: dict = field(default_factory=dict)
    reference_info: dict = field(default_factory=dict)

    def __post_init__(self):
        points, faces = np.asarray(self.points_mm, dtype=float), np.asarray(self.triangles)
        if points.ndim != 2 or points.shape[1] != 3 or not len(points) or not np.isfinite(points).all():
            raise ValueError("The skull must contain finite 3D vertices.")
        if (faces.ndim != 2 or faces.shape[1] != 3 or not len(faces) or
                not np.issubdtype(faces.dtype, np.integer) or faces.min() < 0 or faces.max() >= len(points)):
            raise ValueError("The skull must contain valid triangle indices.")
        self.validate_settings()
        for point in self.landmarks_mm.values():
            if np.asarray(point).shape != (3,) or not np.isfinite(point).all():
                raise ValueError("Skull landmarks must be finite AP/ML/DV triples in mm.")

    def validate_settings(self):
        """Check editable settings without rescanning the imported surface."""
        if sorted(abs(x) for x in self.axes) != [1, 2, 3]:
            raise ValueError("Map each skull axis to a different anatomical axis.")
        for value in (self.rotation_deg, self.translation_mm):
            if np.asarray(value).shape != (3,) or not np.isfinite(value).all():
                raise ValueError("Skull placement requires three finite values per vector.")
        if not 0 <= self.opacity <= 1:
            raise ValueError("Skull opacity must be between zero and one.")
        if not np.isfinite(self.scale) or self.scale <= 0:
            raise ValueError("Skull scale must be finite and positive.")
        ids = [opening.id for opening in self.openings]
        if len(ids) != len(set(ids)):
            raise ValueError("Opening IDs must be unique.")

    @classmethod
    def read(cls, path, units):
        path = Path(path)
        if path.suffix.lower() not in (".stl", ".obj", ".vtp") or units not in ("mm", "µm"):
            raise ValueError("Choose an STL, OBJ or VTP surface and its units (mm or µm).")
        mesh = pv.read(path)
        if not isinstance(mesh, pv.PolyData):
            raise ValueError("The file must contain a polygonal skull surface.")
        mesh = mesh.triangulate()
        if mesh.n_lines or mesh.n_verts or not len(mesh.faces):
            raise ValueError("The skull must be a surface, without line or point cells.")
        points = np.asarray(mesh.points, dtype=float) / (1000 if units == "µm" else 1)
        return cls(path.name, points.tolist(), mesh.faces.reshape(-1, 4)[:, 1:].tolist())

    @classmethod
    def from_dict(cls, data):
        # The initial version-3 preview stored depth limits. Openings now cut
        # through the entire DV projection, including when loading those plans.
        openings = [Craniotomy(**{key: value for key, value in item.items()
                                  if key not in ("dv_min_mm", "dv_max_mm")})
                    for item in data.get("openings", [])]
        return cls(**{**data, "openings": openings})

    def to_dict(self):
        return asdict(self)

    @property
    def base_landmark_distance(self):
        if not all(name in self.landmarks_mm for name in ("Bregma", "Lambda")):
            return None
        return float(np.linalg.norm(np.subtract(self.landmarks_mm["Bregma"], self.landmarks_mm["Lambda"])))

    def _placement(self):
        axes = np.zeros((3, 3))
        for column, signed_axis in enumerate(self.axes):
            axes[abs(signed_axis) - 1, column] = np.sign(signed_axis)
        return Rotation.from_euler("xyz", self.rotation_deg, degrees=True).as_matrix() @ axes

    def landmark_points(self):
        rotation = self._placement()
        return {name: (np.asarray(point) * self.scale) @ rotation.T + self.translation_mm
                for name, point in self.landmarks_mm.items()}

    @cached_property
    def _display_surface(self):
        """Simplify once in native mm; source arrays remain unchanged for saving."""
        mesh = pv.PolyData(np.asarray(self.points_mm, dtype=float),
                           np.column_stack((np.full(len(self.triangles), 3), self.triangles)))
        if mesh.n_cells > 20_000:
            from vtkmodules.vtkFiltersCore import vtkDecimatePro

            decimator = vtkDecimatePro()
            decimator.SetInputData(mesh)
            decimator.SetTargetReduction(1 - 20_000 / mesh.n_cells)
            decimator.PreserveTopologyOn()
            decimator.SplittingOff()
            decimator.BoundaryVertexDeletionOff()
            decimator.AccumulateErrorOn()
            decimator.SetErrorIsAbsolute(1)
            decimator.SetAbsoluteError(0.025)
            decimator.Update()
            mesh = pv.wrap(decimator.GetOutput())
        return mesh

    def source_mesh(self, *, display=False):
        mesh = (self._display_surface.copy() if display else
                pv.PolyData(np.asarray(self.points_mm, dtype=float),
                            np.column_stack((np.full(len(self.triangles), 3), self.triangles))))
        rotation = self._placement()
        mesh.points = (mesh.points * self.scale) @ rotation.T + self.translation_mm
        # A reflected axis mapping also reverses face winding.
        if np.linalg.det(rotation) < 0:
            faces = mesh.faces.reshape(-1, 4).copy()
            faces[:, 1:] = faces[:, :0:-1]
            mesh.faces = faces
        return mesh

    def cut_mesh(self, *, display=False):
        # Clip AFTER simplification so the chosen AP/ML boundary stays intact.
        mesh = self.source_mesh(display=display)
        for opening in self.openings:
            for boundary in convex_parts(opening.polygon):
                mesh = subtract_prism(mesh, boundary)
        return mesh


def default_skull(atlas, brain_outline, progress=lambda message: None):
    """Load a prepared CT reference, or use the schematic dorsal cap.

    Fallback cap size follows the brain's bounds in its default stereotaxic frame. The cap
    passes through Bregma and is symmetric about ML=0; it has no basal closing
    face, facial bones, or inferred bone thickness.
    """
    from probe_planner.atlas.coordinates import atlas_default_coordinates

    species = "mouse" if "_mouse_" in atlas.name else "rat" if "_rat_" in atlas.name else None
    frame = atlas_default_coordinates(atlas) if species else None
    if frame is None:
        return None
    from probe_planner.storage import active_paths

    paths = active_paths()
    failure = None
    if paths is not None:
        from .skull_reference import load_reference

        try:
            return load_reference(species, paths.root / "skulls", progress)
        except (OSError, ValueError, RuntimeError) as error:
            failure = f"CT unavailable: {error}"
            progress(f"{species.title()} {failure}; using schematic skull.")
    points = frame.atlas_to_stereotaxic(brain_outline.points) / 1000
    low, high = points.min(axis=0), points.max(axis=0)
    center_ap = (low[0] + high[0]) / 2
    radius_ap = (high[0] - low[0]) * 0.525
    radius_ml = max(abs(low[1]), abs(high[1])) * 1.05
    height = (high[2] - low[2]) / 2
    if min(radius_ap, radius_ml, height) <= 0 or abs(center_ap) >= radius_ap:
        raise ValueError("The brain outline cannot define a cap around Bregma.")
    base_dv = height * np.sqrt(1 - (center_ap / radius_ap) ** 2)
    segments, rings = 96, 32
    theta = np.arange(segments) * (2 * np.pi / segments)
    phi = np.arange(1, rings + 1)[:, None] * (np.pi / (2 * rings))
    cap = np.stack(np.broadcast_arrays(
        center_ap + radius_ap * np.sin(phi) * np.cos(theta),
        radius_ml * np.sin(phi) * np.sin(theta),
        base_dv - height * np.cos(phi)), axis=-1).reshape(-1, 3)
    vertices = np.vstack(([center_ap, 0, base_dv - height], cap))
    faces = [[0, 1 + (j + 1) % segments, 1 + j] for j in range(segments)]
    for ring in range(rings - 1):
        for j in range(segments):
            a = 1 + ring * segments + j
            d = 1 + ring * segments + (j + 1) % segments
            b, c = a + segments, d + segments
            faces.extend(([a, c, b], [a, d, c]))
    name = f"{species.title()} skull" + (f" · {failure}" if failure else "")
    return Skull(name, vertices.tolist(), faces, approximate=True)


def subtract_prism(mesh, boundary):
    """Subtract an AP/ML polygon's full DV projection, without caps.

    A single implicit-function clip can miss a hole inside a coarse triangle.
    Retaining the outside at EACH plane finds those intersections as well.
    """
    if not mesh.n_cells:
        return mesh
    low = boundary.min(axis=0)
    high = boundary.max(axis=0)
    faces = mesh.faces.reshape(-1, 4)[:, 1:]
    vertices = mesh.points[faces, :2]
    candidates = np.all(vertices.max(axis=1) >= low, axis=1) & np.all(vertices.min(axis=1) <= high, axis=1)
    if not candidates.any():
        return mesh
    kept = []
    if not candidates.all():
        kept.append(mesh.extract_cells(~candidates).extract_surface())
    remaining = mesh.extract_cells(candidates).extract_surface()
    planes = []
    for a, b in zip(boundary, np.roll(boundary, -1, axis=0)):
        edge = b - a
        planes.append(((edge[1], -edge[0], 0), (*a, 0)))
    for normal, origin in planes:
        if not remaining.n_cells:
            break
        distances = (remaining.points - origin) @ normal
        if np.all(distances <= 0):
            continue
        if np.all(distances >= 0):
            kept.append(remaining)
            break
        remaining, outside = remaining.clip(normal=normal, origin=origin, invert=True, return_clipped=True)
        if outside.n_cells:
            kept.append(outside)
    # What remains inside every plane is removed. There is deliberately no cap
    # across the opening and no inferred sidewall or skull thickness.
    if not kept:
        return pv.PolyData()
    for part in kept:
        part.clear_data()
    return kept[0].append_polydata(*kept[1:]).triangulate() if len(kept) > 1 else kept[0].triangulate()
