"""Craniotomy cut faces from the existing bone surface, in stereo millimeters."""

import numpy as np
import pyvista as pv
from vtkmodules.vtkFiltersGeneral import vtkContourTriangulator

from probe_planner.implant.skull import cross2


def _inside(point, polygon):
    """Odd/even containment; callers handle boundary points separately."""
    a, b = polygon, np.roll(polygon, -1, axis=0)
    crosses = (a[:, 1] > point[1]) != (b[:, 1] > point[1])
    a, b = a[crosses], b[crosses]
    x = a[:, 0] + (point[1] - a[:, 1]) * (b[:, 0] - a[:, 0]) / (b[:, 1] - a[:, 1])
    return bool(np.count_nonzero(x > point[0]) % 2)


def _union_edges(polygons):
    """Split ROI edges at intersections; emit only the boundary of their union."""
    extent = max(1.0, max(float(np.abs(p).max()) for p in polygons))
    tolerance = 64 * np.finfo(float).eps * extent
    for index, polygon in enumerate(polygons):
        others = [(j, p) for j, p in enumerate(polygons) if j != index]
        for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
            edge = b - a
            length = np.linalg.norm(edge)
            breaks = [0.0, 1.0]
            for _, other in others:
                for c, d in zip(other, np.roll(other, -1, axis=0)):
                    delta = d - c
                    denominator = cross2(edge, delta)
                    if abs(denominator) > tolerance * max(length, np.linalg.norm(delta)):
                        t = cross2(c - a, delta) / denominator
                        u = cross2(c - a, edge) / denominator
                        if 0 < t < 1 and 0 <= u <= 1:
                            breaks.append(t)
                    elif abs(cross2(c - a, edge)) <= tolerance * length:
                        breaks.extend(np.clip([(c - a) @ edge / length**2,
                                               (d - a) @ edge / length**2], 0, 1))
            breaks = sorted(breaks)
            for start, end in zip(breaks, breaks[1:]):
                if (end - start) * length <= tolerance:
                    continue
                midpoint = a + (start + end) * .5 * edge
                hidden = False
                for other_index, other in others:
                    on_boundary = False
                    for c, d in zip(other, np.roll(other, -1, axis=0)):
                        delta = d - c
                        if (abs(cross2(delta, midpoint - c)) <= tolerance * np.linalg.norm(delta)
                                and np.dot(midpoint - c, midpoint - d) <= tolerance**2):
                            on_boundary = True
                            # Opposite edges are internal to a touching union.
                            # Coincident exterior edges are emitted once.
                            hidden = edge @ delta < 0 or other_index < index
                            break
                    if hidden or (not on_boundary and _inside(midpoint, other)):
                        hidden = True
                        break
                if not hidden:
                    yield a + start * edge, a + end * edge


def _section(mesh, start, end, direction, normal):
    """Fill closed bone contours, with nested contours retained as cavities.

    Restrict contours to the ROI edge before closing them at its two endpoints.
    Pair successive surface crossings along each vertical endpoint line, starting
    in air above the skull. Odd crossing counts or gaps inside the section cannot
    establish thickness, so leave that section uncapped.
    """
    section = mesh.slice(normal=normal, origin=(*start, 0))
    section = section.clip(normal=(*direction, 0), origin=(*start, 0), invert=False)
    section = section.clip(normal=(*direction, 0), origin=(*end, 0), invert=True).clean()
    if not section.n_lines:
        return pv.PolyData(), False
    section = section.strip(join=True, max_length=max(4, section.n_lines))
    lines, segments = section.lines, []
    endpoints = [[], []]
    projected = (section.points[:, :2] - start) @ direction
    length = np.linalg.norm(end - start)
    # VTK preserves the input point dtype. Account only for its interpolation
    # roundoff when recognizing endpoints on the two clipping planes.
    tolerance = 32 * np.finfo(section.points.dtype).eps * max(1., float(np.abs(section.points).max()))
    cursor = 0
    while cursor < len(lines):
        count = int(lines[cursor])
        ids = lines[cursor + 1:cursor + 1 + count]
        cursor += count + 1
        segments.extend(np.column_stack((np.full(count - 1, 2), ids[:-1], ids[1:])).ravel())
        if ids[0] == ids[-1]:
            continue
        for point_id in (ids[0], ids[-1]):
            if abs(projected[point_id]) <= tolerance:
                endpoints[0].append(point_id)
            elif abs(projected[point_id] - length) <= tolerance:
                endpoints[1].append(point_id)
            else:
                return pv.PolyData(), True
    for boundary in endpoints:
        if len(boundary) % 2:
            return pv.PolyData(), True
        ordered = sorted(boundary, key=lambda point_id: section.points[point_id, 2])
        for a, b in zip(ordered[::2], ordered[1::2]):
            segments.extend((2, a, b))
    section = pv.PolyData(section.points, lines=np.asarray(segments, dtype=np.int64)).strip(
        join=True, max_length=max(4, len(segments) // 3))
    lines, loops = section.lines, []
    cursor = 0
    while cursor < len(lines):
        count = int(lines[cursor])
        ids = lines[cursor + 1:cursor + 1 + count]
        cursor += count + 1
        if count < 4 or ids[0] != ids[-1]:
            return pv.PolyData(), True
        loops.append(ids[:-1])
    points2 = np.column_stack((section.points[:, :2] @ direction, section.points[:, 2]))
    segments = []
    for i, ids in enumerate(loops):
        polygon = points2[ids]
        nested = sum(_inside(polygon[0], points2[other]) for j, other in enumerate(loops) if j != i)
        area = sum(cross2(a, b) for a, b in zip(polygon, np.roll(polygon, -1, axis=0)))
        if (area > 0) != (nested % 2 == 0):
            ids = ids[::-1]
        segments.extend(np.column_stack((np.full(len(ids), 2), ids, np.roll(ids, -1))).ravel())
    contours = pv.PolyData(section.points, lines=np.asarray(segments, dtype=np.int64))
    triangulator = vtkContourTriangulator()
    triangulator.SetInputData(contours)
    triangulator.Update()
    if triangulator.GetTriangulationError():
        raise ValueError("Cannot triangulate the skull cut face; the surface contours intersect or are degenerate.")
    return pv.wrap(triangulator.GetOutput()), False


def craniotomy_walls(mesh, openings):
    """Return cut faces and the number of edges with incomplete source contours.

    The surface shader retains analytic circles. These walls use the same
    128-segment footprint as CPU clipping: maximum radial error 0.0302% of radius.
    No skull, brain, or ROI coordinates are modified.
    """
    if not openings:
        return pv.PolyData(), 0
    walls, incomplete = [], 0
    for start, end in _union_edges([opening.polygon for opening in openings]):
        direction = (end - start) / np.linalg.norm(end - start)
        normal = np.array([direction[1], -direction[0], 0])
        face, is_open = _section(mesh, start, end, direction, normal)
        incomplete += int(is_open)
        if not face.n_cells:
            continue
        if face.n_cells:
            face.clear_data()
            walls.append(face)
    return (walls[0].append_polydata(*walls[1:]) if walls else pv.PolyData()), incomplete
