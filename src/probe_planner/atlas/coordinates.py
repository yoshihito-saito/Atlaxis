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

    def __post_init__(self):
        for value in (self.resolution_um, self.bregma_atlas_um):
            if np.asarray(value).shape != (3,) or not np.isfinite(value).all():
                raise ValueError("Calibration requires finite three-component vectors.")
        if np.any(np.asarray(self.resolution_um) <= 0):
            raise ValueError("Atlas resolution must be positive.")
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
        matrix[:3, 3] = self.bregma_atlas_um
        return matrix

    def stereotaxic_to_atlas(self, stereo_um):
        return transform_points(stereo_um, self.stereo_to_atlas_matrix)

    def atlas_to_stereotaxic(self, atlas_um):
        return transform_points(atlas_um, np.linalg.inv(self.stereo_to_atlas_matrix))

    def atlas_to_voxel(self, atlas_um):
        return np.asarray(atlas_um, dtype=float) / np.asarray(self.resolution_um)


def probe_to_stereotaxic_matrix(geometry: ProbeGeometry, pose: ImplantPose):
    azimuth, tilt, roll = np.deg2rad([pose.azimuth_deg, pose.elevation_deg, pose.roll_deg])
    direction = np.array([np.sin(tilt) * np.cos(azimuth),
                          np.sin(tilt) * np.sin(azimuth), np.cos(tilt)])
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
    """Display the selected shank's entry point without moving the probe."""
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

    Intrinsic YXZ angles correspond to Ry(AP) Rx(-ML) Rz(roll). ML lies in
    [-90, 90]; AP and roll in [-180, 180]. Positive AP/ML tilt anterior/right.
    """
    rotation = Rotation.from_euler("ZYZ", [pose.azimuth_deg, pose.elevation_deg, pose.roll_deg], degrees=True)
    ap, negative_ml, roll = _euler_degrees(rotation, "YXZ")
    return float(ap), float(-negative_ml), float(roll)


def pose_with_axis_tilts(pose: ImplantPose, ap_deg, ml_deg, roll_deg):
    """Convert GUI tilts to saved angles, retaining entry and insertion travel."""
    rotation = Rotation.from_euler("YXZ", [ap_deg, -ml_deg, roll_deg], degrees=True)
    azimuth, elevation, roll = _euler_degrees(rotation, "ZYZ")
    return replace(pose, azimuth_deg=float(azimuth), elevation_deg=float(elevation), roll_deg=float(roll))


def brain_surface_dv_mm(atlas, frame: AtlasCoordinates, ap_mm: float, ml_mm: float):
    """Dorsal annotated voxel-cell boundary at AP/ML, or None without tissue.

    Follow the same floor-index cells as region lookup and section textures.
    Hidden regions still count as tissue. Only one native DV column is read.
    """
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
    """Published WHS v1.01 Bregma mapped by the packaged atlas transform.

    Source: https://www.nitrc.org/docman/view.php/1081/2095/Coordinates_v1-v1.01.pdf
    Native x/y/z voxel landmark: (246, 653, 440). BrainGlobe v1.2 records the
    physical-coordinate reorientation in metadata['trasform_to_bg'] (sic).
    This sets the Bregma origin, not animal registration or flat-skull leveling.
    """
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
