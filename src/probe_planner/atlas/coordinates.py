"""All axis changes, origins, rotations and unit conversions live here.

Stereo axes: AP anterior+, ML right+, DV ventral+. Atlas axes follow array order.
Probe axes at zero angles: x right+, y toward base, z posterior+.
Elevation is tilt FROM ventral; azimuth runs anterior (0) toward right (90).
"""

from dataclasses import dataclass, replace
import warnings

import numpy as np
from scipy.spatial.transform import Rotation

from probe_planner.implant.pose import ImplantPose
from probe_planner.probes.model import ProbeGeometry


def transform_points(points, matrix) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("Coordinates must be a finite N x 3 array.")
    return points @ matrix[:3, :3].T + matrix[:3, 3]


def um_to_mm(points):
    return np.asarray(points) / 1000.0


def mm_to_um(points):
    return np.asarray(points) * 1000.0


@dataclass
class AtlasCoordinates:
    resolution_um: tuple[float, float, float]
    orientation: str
    bregma_atlas_um: tuple[float, float, float]
    pitch_correction_deg: float = 0.0

    def __post_init__(self):
        for value in (self.resolution_um, self.bregma_atlas_um):
            if np.asarray(value).shape != (3,) or not np.isfinite(value).all():
                raise ValueError("Calibration requires finite three-component vectors.")
        if np.any(np.asarray(self.resolution_um) <= 0):
            raise ValueError("Atlas resolution must be positive.")
        if np.asarray(self.pitch_correction_deg).shape != () or not np.isfinite(self.pitch_correction_deg):
            raise ValueError("Atlas pitch correction must be finite degrees.")
        self.stereo_to_atlas_matrix

    @property
    def stereo_to_atlas_matrix(self):
        # BrainGlobe letters name the origin side, so increasing a-axis is posterior.
        axes = {"a": (0, -1), "p": (0, 1), "l": (1, 1),
                "r": (1, -1), "s": (2, 1), "i": (2, -1)}
        if len(self.orientation) != 3 or any(c not in axes for c in self.orientation):
            raise ValueError("Invalid BrainGlobe atlas orientation.")
        mapping = [axes[c] for c in self.orientation]
        if len({axis for axis, _ in mapping}) != 3:
            raise ValueError("Atlas orientation must include three distinct anatomical axes.")
        matrix = np.eye(4)
        matrix[:3, :3] = 0
        for row, (axis, sign) in enumerate(mapping):
            matrix[row, axis] = sign
        # Skull-level -> native atlas, about Bregma. Positive pitch sends a
        # ventral skull trajectory anteriorward in native anatomical axes.
        matrix[:3, :3] = matrix[:3, :3] @ Rotation.from_euler(
            "y", self.pitch_correction_deg, degrees=True).as_matrix()
        matrix[:3, 3] = self.bregma_atlas_um
        return matrix

    def stereotaxic_to_atlas(self, stereo_um):
        return transform_points(stereo_um, self.stereo_to_atlas_matrix)

    def atlas_to_stereotaxic(self, atlas_um):
        return transform_points(atlas_um, np.linalg.inv(self.stereo_to_atlas_matrix))

    def atlas_to_voxel(self, atlas_um):
        return np.asarray(atlas_um, dtype=float) / np.asarray(self.resolution_um)


def insertion_direction(pose: ImplantPose):
    """Unit insertion direction in stereotaxic AP/ML/DV axes."""
    azimuth, tilt = np.deg2rad([pose.azimuth_deg, pose.elevation_deg])
    return np.array([np.sin(tilt) * np.cos(azimuth),
                     np.sin(tilt) * np.sin(azimuth), np.cos(tilt)])


def probe_to_stereotaxic_matrix(geometry: ProbeGeometry, pose: ImplantPose):
    azimuth, roll = np.deg2rad([pose.azimuth_deg, pose.roll_deg])
    direction = insertion_direction(pose)
    lateral = np.array([-np.sin(azimuth), np.cos(azimuth), 0.0])
    proximal = -direction
    rotation = np.column_stack((lateral, proximal, np.cross(lateral, proximal)))
    rotation = rotation @ Rotation.from_rotvec([0.0, -roll, 0.0]).as_matrix()
    rotation = rotation @ np.diag([1, geometry.y_to_base, geometry.y_to_base])
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = (mm_to_um([pose.ap_mm, pose.ml_mm, pose.dv_mm])
                     + mm_to_um(pose.depth_mm) * direction - rotation @ geometry.tip_um)
    return matrix


def probe_to_atlas(geometry: ProbeGeometry, pose: ImplantPose, frame: AtlasCoordinates):
    return frame.stereo_to_atlas_matrix @ probe_to_stereotaxic_matrix(geometry, pose)


def shank_reference_um(geometry: ProbeGeometry, shank_id: int):
    """Physical distal center when supplied, otherwise the declared tip plane.

    Geometry-only imports define a shaft axis from the median contact x/z and
    the explicitly imported tip y; the lowest electrode is never a tip.
    """
    bodies = [np.asarray(body.outline_um, dtype=float) for body in geometry.bodies
              if body.shank_id == shank_id]
    if bodies:
        points = np.vstack(bodies)
        longitudinal = points[:, 1] * geometry.y_to_base
        return points[longitudinal == longitudinal.min()].mean(axis=0)
    points = geometry.points[[contact.shank_id == shank_id for contact in geometry.contacts]]
    if not len(points):
        raise ValueError("Reference shank does not exist in the probe.")
    reference = np.median(points, axis=0)
    reference[1] = geometry.tip_um[1]
    return reference


def reference_pose(geometry: ProbeGeometry, pose: ImplantPose, shank_id: int):
    """Selected shank's saved zero-travel point, not necessarily on the surface."""
    rotation = probe_to_stereotaxic_matrix(geometry, pose)[:3, :3]
    offset = rotation @ (shank_reference_um(geometry, shank_id) - np.asarray(geometry.tip_um))
    entry = np.array([pose.ap_mm, pose.ml_mm, pose.dv_mm]) + um_to_mm(offset)
    return replace(pose, ap_mm=entry[0], ml_mm=entry[1], dv_mm=entry[2])


def canonical_pose(geometry: ProbeGeometry, displayed: ImplantPose, shank_id: int):
    """Convert reference-shank controls to the unchanged saved pose convention."""
    rotation = probe_to_stereotaxic_matrix(geometry, displayed)[:3, :3]
    offset = rotation @ (shank_reference_um(geometry, shank_id) - np.asarray(geometry.tip_um))
    entry = np.array([displayed.ap_mm, displayed.ml_mm, displayed.dv_mm]) - um_to_mm(offset)
    return replace(displayed, ap_mm=entry[0], ml_mm=entry[1], dv_mm=entry[2])


def shank_tip_stereotaxic_mm(geometry: ProbeGeometry, pose: ImplantPose, shank_id: int):
    """Current physical tip after axis travel, in Bregma-relative AP/ML/DV mm."""
    tip = shank_reference_um(geometry, shank_id)
    return um_to_mm(transform_points(tip[None, :], probe_to_stereotaxic_matrix(geometry, pose))[0])


def insertion_surface_entry_mm(atlas, frame: AtlasCoordinates, tip_mm, direction):
    """First annotated cell on the full directed insertion line, in stereo mm.

    Intersect the atlas box, then inspect each interval between voxel boundaries.
    This follows the native floor-index cells exactly, without fixed-step sampling.
    Hidden annotation labels still count as tissue. A line missing tissue returns
    None, including a line merely touching a voxel corner/edge with zero length.
    """
    tip_mm = np.asarray(tip_mm, dtype=float)
    direction = np.asarray(direction, dtype=float)
    position = frame.atlas_to_voxel(frame.stereotaxic_to_atlas(mm_to_um(tip_mm)[None, :]))[0]
    velocity = (frame.stereo_to_atlas_matrix[:3, :3] @ direction
                * 1000.0 / np.asarray(frame.resolution_um))
    shape = np.asarray(atlas.annotation.shape)
    moving = np.abs(velocity) > 8 * np.finfo(float).eps * 1000 / np.asarray(frame.resolution_um)
    velocity[~moving] = 0.0
    if not moving.any() or np.any((~moving) & ((position < 0) | (position >= shape))):
        return None
    ends = np.stack((-position[moving] / velocity[moving],
                     (shape[moving] - position[moving]) / velocity[moving]))
    start, stop = ends.min(axis=0).max(), ends.max(axis=0).min()
    if stop <= start:
        return None
    boundaries = [np.array([start, stop])]
    for axis in np.flatnonzero(moving):
        crossings = (np.arange(shape[axis] + 1) - position[axis]) / velocity[axis]
        boundaries.append(crossings[(crossings > start) & (crossings < stop)])
    distances = np.unique(np.concatenate(boundaries))
    # Ignore only floating-point splits of coincident cell boundaries.
    roundoff = 32 * np.finfo(float).eps * max(1.0, abs(start), abs(stop))
    intervals = np.flatnonzero(np.diff(distances) > roundoff)
    midpoints = (distances[intervals] + distances[intervals + 1]) / 2
    indices = np.floor(position + midpoints[:, None] * velocity).astype(int)
    valid = np.all((indices >= 0) & (indices < shape), axis=1)
    intervals, indices = intervals[valid], indices[valid]
    occupied = np.flatnonzero(atlas.annotation[tuple(indices.T)])
    if not len(occupied):
        return None
    return tip_mm + distances[intervals[occupied[0]]] * direction


@dataclass(frozen=True)
class ShankSurfaceReference:
    entry_mm: np.ndarray
    depth_mm: float
    dv_mm: float


def shank_surface_reference(geometry, pose, shank_id, atlas, frame):
    """Per-shank surface entry, signed axis travel and vertical tip depth.

    This is a read-only view of the physical pose; selecting a shank never moves it.
    """
    if atlas is None or frame is None:
        return None
    tip = shank_tip_stereotaxic_mm(geometry, pose, shank_id)
    direction = insertion_direction(pose)
    entry = insertion_surface_entry_mm(atlas, frame, tip, direction)
    if entry is None:
        return None
    return ShankSurfaceReference(entry, float(np.dot(tip - entry, direction)), float(tip[2] - entry[2]))


def pose_at_shank_insertion(geometry, pose, shank_id, entry_mm, depth_mm):
    """Place a rigid probe from a shank's surface origin and signed travel.

    Keep the saved nonnegative canonical travel contract: negative surface travel
    is represented by an entry translated back along the same axis. The other
    shanks retain their rigid offsets; no geometry or orientation is changed.
    """
    if not np.isfinite(depth_mm):
        raise ValueError("Insertion depth must be finite millimeters.")
    position = np.asarray(entry_mm) + min(0.0, depth_mm) * insertion_direction(pose)
    displayed = replace(pose, ap_mm=position[0], ml_mm=position[1], dv_mm=position[2],
                        depth_mm=max(0.0, depth_mm))
    return canonical_pose(geometry, displayed, shank_id)


def entry_pose_at_tip_dv(entry: ImplantPose, surface_dv_mm: float, tip_dv_mm: float):
    """Set surface-relative tip DV by advancing along the unchanged entry axis.

    The entry must belong to the selected reference shank. Saved entry offsets
    remain intact; negative travel and unreachable horizontal targets are errors.
    """
    if not np.isfinite([surface_dv_mm, tip_dv_mm]).all():
        raise ValueError("Surface and tip DV must be finite millimeters.")
    angle = np.deg2rad(entry.elevation_deg)
    vertical = float(np.cos(angle))
    progress_dv = tip_dv_mm + surface_dv_mm - entry.dv_mm
    # Account only for floating-point cancellation and trig argument roundoff.
    roundoff = 8 * np.finfo(float).eps
    dv_roundoff = roundoff * max(1.0, abs(tip_dv_mm), abs(surface_dv_mm), abs(entry.dv_mm))
    if abs(vertical) <= roundoff * max(1.0, abs(angle)):
        if abs(progress_dv) <= dv_roundoff:
            return entry
        raise ValueError("A horizontal probe cannot change DV by insertion. Change the tilt first.")
    depth = float(progress_dv / vertical)
    if depth < -dv_roundoff / abs(vertical):
        raise ValueError("This DV is behind the insertion start and would require negative insertion depth.")
    return replace(entry, depth_mm=max(0.0, depth))


def _euler_degrees(rotation, axes):
    # At Euler singularities SciPy chooses a zero third angle; the rotation
    # remains defined. This expected ambiguity is not a failed conversion.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Gimbal lock detected.*", category=UserWarning)
        return rotation.as_euler(axes, degrees=True)


def pose_axis_tilts(pose: ImplantPose):
    """GUI AP/ML tilt and axial roll, preserving the complete saved orientation.

    Intrinsic YXZ angles correspond to Ry(AP) Rx(ML) Rz(roll). ML lies in
    [-90, 90]; AP and roll in [-180, 180]. Positive AP/ML tilt anterior/left.
    """
    rotation = Rotation.from_euler("ZYZ", [pose.azimuth_deg, pose.elevation_deg, pose.roll_deg], degrees=True)
    ap, ml, roll = _euler_degrees(rotation, "YXZ")
    return float(ap), float(ml), float(roll)


def pose_with_axis_tilts(pose: ImplantPose, ap_deg, ml_deg, roll_deg):
    """Convert GUI tilts to saved angles, retaining entry and insertion travel."""
    rotation = Rotation.from_euler("YXZ", [ap_deg, ml_deg, roll_deg], degrees=True)
    azimuth, elevation, roll = _euler_degrees(rotation, "ZYZ")
    return replace(pose, azimuth_deg=float(azimuth), elevation_deg=float(elevation), roll_deg=float(roll))


def brain_surface_dv_mm(atlas, frame: AtlasCoordinates, ap_mm: float, ml_mm: float):
    """Dorsal annotated voxel-cell boundary at AP/ML, or None without tissue.

    Follow the same floor-index cells as region lookup and section textures.
    Hidden regions still count as tissue. A corrected frame requires a ray
    through native voxel cells instead of an axis-aligned DV column.
    """
    if frame.pitch_correction_deg:
        entry = insertion_surface_entry_mm(atlas, frame, [ap_mm, ml_mm, 0], [0, 0, 1])
        return None if entry is None else float(entry[2])
    position = frame.stereotaxic_to_atlas([[ap_mm * 1000, ml_mm * 1000, 0]])[0]
    indices = np.floor(frame.atlas_to_voxel(position)).astype(int)
    dv_axis = next(axis for axis, letter in enumerate(frame.orientation) if letter in "si")
    for axis in range(3):
        if axis != dv_axis and not 0 <= indices[axis] < atlas.annotation.shape[axis]:
            return None
    column = list(indices)
    column[dv_axis] = slice(None)
    tissue = np.flatnonzero(atlas.annotation[tuple(column)])
    if not len(tissue):
        return None
    boundary = tissue[0] if frame.orientation[dv_axis] == "s" else tissue[-1] + 1
    position[dv_axis] = boundary * frame.resolution_um[dv_axis]
    return float(frame.atlas_to_stereotaxic(position[None, :])[0, 2] / 1000)


def atlas_default_coordinates(atlas):
    """Atlas-specific origins and skull-level pitch for recognized volumes.

    Allen uses cortex-lab's estimated Bregma [540, 0, 570] in 10 um voxels,
    converted to physical AP/DV/LR coordinates, never scaled by the loaded
    resolution. It is an estimate, not individual-animal registration.
    Source: https://github.com/cortex-lab/allenCCF/blob/master/Browsing%20Functions/allenCCFbregma.m
    Allen also uses Pinpoint's nominal 5-degree pitch correction, without its
    optional in-vivo scaling. This is not individual skull registration.
    Source: https://virtualbrainlab.org/pinpoint/in_vivo_alignment.html

    WHS v1.01 Bregma is mapped by the packaged atlas transform.
    Source: https://www.nitrc.org/docman/view.php/1081/2095/Coordinates_v1-v1.01.pdf
    Native x/y/z voxel landmark: (246, 653, 440). BrainGlobe v1.2 records the
    physical-coordinate reorientation in metadata['trasform_to_bg'] (sic).
    WHS sets only the Bregma origin, without a skull-level rotation.
    """
    allen_resolution = {"allen_mouse_10um": 10.0, "allen_mouse_25um": 25.0,
                        "allen_mouse_50um": 50.0, "allen_mouse_100um": 100.0}.get(atlas.name)
    if allen_resolution is not None:
        expected_shape = tuple(int(size / allen_resolution) for size in (13200, 8000, 11400))
        if (atlas.version == "1.2" and atlas.orientation == "asr"
                and tuple(atlas.resolution_um) == (allen_resolution,) * 3
                and atlas.annotation.shape == expected_shape):
            return AtlasCoordinates(atlas.resolution_um, atlas.orientation, (5400.0, 0.0, 5700.0),
                                    pitch_correction_deg=5.0)
        return None
    if atlas.name == "whs_sd_swc_female_rat_39um":
        if (atlas.version != "1.0" or atlas.orientation != "asr"
                or atlas.annotation.shape != (1024, 512, 512)
                or tuple(atlas.resolution_um) != (39.0, 39.0, 39.0)):
            return None
        # The registered SWC NIfTI maps the WHS landmark to (653, 440, 246).
        # Its v1.0 packager declares PIR, unlike the original WHS LPI input.
        # PIR -> ASR flips AP/DV only; use BrainGlobe's full-extent point
        # convention and packaged 39 um spacing. No transform is in metadata.
        # Source: brainglobe/brainglobe-atlasapi, atlas_scripts/whs_sd_swc_female_rat.py
        bregma = np.array([1024.0 - 653.0, 512.0 - 440.0, 246.0]) * 39.0
        return AtlasCoordinates(atlas.resolution_um, atlas.orientation, tuple(bregma))
    if (atlas.name != "whs_sd_rat_39um" or atlas.version != "1.2"
            or atlas.orientation != "asr" or atlas.annotation.shape != (1024, 512, 512)
            or tuple(atlas.resolution_um) != (39.0, 39.0, 39.0)):
        return None
    matrix = np.asarray(atlas.backend.metadata.get("trasform_to_bg"), dtype=float)
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
        return None
    native_bregma_um = np.array([[246.0, 653.0, 440.0]]) * 39.0
    bregma = transform_points(native_bregma_um, matrix)[0]
    return AtlasCoordinates(atlas.resolution_um, atlas.orientation, tuple(bregma))
