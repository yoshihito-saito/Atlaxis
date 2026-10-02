"""Probe-attached planning drives; millimeters except probe-local attachment_um."""

from dataclasses import dataclass, replace

import numpy as np
import pyvista as pv


@dataclass(frozen=True)
class DriveModel:
    name: str
    body_width_mm: float
    body_depth_mm: float
    body_height_mm: float | None
    arm_width_mm: float
    arm_height_mm: float
    travel_mm: float
    raised_lower_mm: float | None
    source: str
    side_mount: bool = False
    arm_thickness_mm: float | None = None

    @property
    def mounting_cross_section(self):
        """Fixed-body span along the mounting face and normal to it, in mm."""
        return ((self.body_depth_mm, self.body_width_mm) if self.side_mount else
                (self.body_width_mm, self.body_depth_mm))


# Nano: corrected user measurements. Pico: shared +3 mm raised lower-edge
# assumption. Metal: user-measured regular arm/travel; NP uses published L arm.
# Metal body/plate envelopes reference public v10 CAD; the user's regular-arm
# measurements override its arm height/travel. NP arm-to-bottom datum is unknown.
METAL_REFERENCE = "https://github.com/buzsakilab/3d_print_designs/tree/ba4f327a46518d0353838d9f9539b0c2418effd6/Microdrives/Metal_recoverable/v10/step_files"
MODELS = {
    "nano": DriveModel("Cambridge NeuroTech nano-Drive", 4, 2, 10, 2, 7.5, 7.5, 3,
        "User measurements; side-mounted carriage, 1 mm thick; illustrative screw, with a 1 mm cap.",
        side_mount=True, arm_thickness_mm=1),
    "pico": DriveModel("Cambridge NeuroTech pico-Drive", 4, 2, 6, 2, 3.5, 3.5, 3,
        "User dimensions; 1 mm carriage thickness; 3.5 mm arm inferred from shared raised lower edge +3 mm.",
        side_mount=True, arm_thickness_mm=1),
    "metal": DriveModel("3Dneuro Metal drive", 4.3, 4.35, 14.1, 3.6, 8.5, 6.5, 6.5,
        "User-measured arm/travel; width: https://3dneuro.com/products/r2drive\n"
        "Body envelope and 0.65 mm plate: public v10 CAD reference; current hardware revision unverified. "
        + METAL_REFERENCE, arm_thickness_mm=.65),
    "metal_np": DriveModel("3Dneuro Metal drive NP", 4.3, 4.35, 14.1, 5, 10, 7, None,
        "R2drive L / NP1.0 arm: https://3dneuro.com/products/r2drive-l\n"
        "Body envelope and 0.65 mm plate: public v10 CAD reference; current hardware revision unverified. "
        + METAL_REFERENCE, arm_thickness_mm=.65),
}


@dataclass
class DriveMount:
    model_id: str
    attachment_um: tuple[float, float, float]
    mount_height_mm: float = 0.0
    travel_mm: float = 0.0
    body_height_mm: float | None = None
    raised_lower_mm: float | None = None
    body_gap_mm: float = 0.0  # Clearance from carriage back face to fixed body.
    # Legacy mounts used the center of the carriage and no assembly offsets.
    lateral_offset_mm: float = 0.0
    position_offset_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self):
        if self.model_id not in MODELS:
            raise ValueError("Unknown microdrive model.")
        model = MODELS[self.model_id]
        if np.asarray(self.attachment_um).shape != (3,) or not np.isfinite(self.attachment_um).all():
            raise ValueError("Probe attachment requires three finite local coordinates.")
        if (not np.isfinite([self.mount_height_mm, self.travel_mm, self.body_gap_mm]).all()
                or not 0 <= self.travel_mm <= model.travel_mm or self.body_gap_mm < 0):
            raise ValueError("Mount offset must be finite, travel within range and body gap nonnegative.")
        lateral_limit = max(model.arm_width_mm, model.mounting_cross_section[0]) / 2
        if not np.isfinite(self.lateral_offset_mm) or abs(self.lateral_offset_mm) > lateral_limit:
            raise ValueError("The lateral attachment must lie within the drive's width.")
        if np.asarray(self.position_offset_mm).shape != (3,) or not np.isfinite(self.position_offset_mm).all():
            raise ValueError("Drive position offsets must be three finite millimeter values.")
        if self.body_height_mm is not None and (not np.isfinite(self.body_height_mm) or self.body_height_mm <= 0):
            raise ValueError("Fixed-body height must be positive, or left unspecified.")
        if self.raised_lower_mm is not None and not np.isfinite(self.raised_lower_mm):
            raise ValueError("Raised carriage lower edge must be finite, or left unspecified.")

    @property
    def body_mount_offset_mm(self):
        """Current base height above the fixed-body bottom; None if uncalibrated."""
        if self.raised_lower_mm is None:
            return None
        return self.mount_height_mm + self.raised_lower_mm - self.travel_mm


def carriage_mount_height_mm(body_offset_mm, travel_mm, raised_lower_mm):
    """Convert a fixed-body-bottom offset to the persisted carriage datum."""
    if raised_lower_mm is None:
        raise ValueError("Set the raised carriage lower edge in Dimensions before aligning to the drive body.")
    return body_offset_mm + travel_mm - raised_lower_mm


def base_reference(geometry):
    """Minimum-X/lower/back datum: the lower-left corner from the probe side."""
    from probe_planner.probes.mounting import is_acute_package

    if is_acute_package(geometry):
        return None, "Microdrive mounting is available for chronic probe packages only."
    if geometry.mounting_base is None:
        return None, "Probe base dimensions required."
    vertices = geometry.mounting_base.vertices
    sign = geometry.y_to_base
    point = (float(vertices[:, 0].min()), float((vertices[:, 1]*sign).min()*sign),
             float((vertices[:, 2]*sign).max()*sign))
    return point, "Reference: lower-left corner viewed from the probe side."


def default_attachment_um(geometry):
    point, _ = base_reference(geometry)
    if point is None:
        raise ValueError("Probe base dimensions are required before attaching a drive.")
    return point


def translated_pose(pose, distance_mm):
    from probe_planner.atlas.coordinates import insertion_direction

    position = np.array([pose.ap_mm, pose.ml_mm, pose.dv_mm]) + distance_mm * insertion_direction(pose)
    # Keep canonical depth nonnegative, including retraction through q=0.
    return replace(pose, ap_mm=float(position[0]), ml_mm=float(position[1]), dv_mm=float(position[2]))


def updated_mount_pose(geometry, pose, previous, mount, *, align_base=False):
    """Move assembly offsets, attachment adjustments and travel coherently."""
    from probe_planner.atlas.coordinates import probe_to_stereotaxic_matrix

    if mount is None:
        return pose
    same_model = previous is not None and previous.model_id == mount.model_id
    signs = np.array([1, geometry.y_to_base, geometry.y_to_base])
    offset = np.asarray(mount.position_offset_mm, dtype=float)
    local = offset.copy()
    travel = 0.
    attachment = np.zeros(3)
    if same_model:
        local -= previous.position_offset_mm
        # Moving the point on the carriage repositions the probe, leaving the
        # drive in place; moving the whole assembly moves both together.
        if not align_base:
            local += [mount.lateral_offset_mm - previous.lateral_offset_mm,
                      mount.mount_height_mm - previous.mount_height_mm, 0.]
            attachment = (np.asarray(previous.attachment_um) - mount.attachment_um) / 1000
        travel = mount.travel_mm - previous.travel_mm
    rotation = probe_to_stereotaxic_matrix(geometry, pose)[:3, :3]
    displacement = rotation @ (local * signs + attachment)
    moved = translated_pose(pose, travel)
    return replace(moved, ap_mm=float(moved.ap_mm + displacement[0]),
                   ml_mm=float(moved.ml_mm + displacement[1]), dv_mm=float(moved.dv_mm + displacement[2]))


def screw_surfaces(model, mount, height_offset):
    """Illustrative fixed screw at zero travel; dimensions are not clearance data."""
    if mount.raised_lower_mm is not None and mount.body_height_mm is not None:
        bottom = -height_offset - mount.raised_lower_mm
        height = mount.body_height_mm
    else:
        # This spans the carriage envelope, not an inferred body dimension.
        bottom = -height_offset - model.travel_mm
        height = model.travel_mm + model.arm_height_mm
    shaft_radius, head_radius = .35, .75
    cap = 1.0 if model.name.startswith("Cambridge") else .8
    z = (model.arm_thickness_mm or 0) + mount.body_gap_mm + model.mounting_cross_section[1] / 2
    shaft = pv.Cylinder(center=(0, bottom + height/2, z), direction=(0, 1, 0),
                        radius=shaft_radius, height=height, resolution=24)
    # A shallow slot leaves the lower part of the head intact.
    head_base = pv.Cylinder(center=(0, bottom + height + cap*.325, z), direction=(0, 1, 0),
                            radius=head_radius, height=cap*.65, resolution=32)
    head = pv.Cylinder(center=(0, bottom + height + cap*.825, z), direction=(0, 1, 0),
                       radius=head_radius, height=cap*.35, resolution=32)
    slot = .10
    left = head.clip(normal=(1, 0, 0), origin=(-slot, 0, 0))
    right = head.clip(normal=(1, 0, 0), origin=(slot, 0, 0), invert=False)
    pitch = .25 if model.name.startswith("Cambridge") else .282
    turns = height / pitch
    phase = np.linspace(0, 2*np.pi*turns, max(2, int(np.ceil(turns*16)) + 1))
    helix = np.column_stack((shaft_radius*np.cos(phase),
                            bottom + height * phase / phase[-1], z + shaft_radius*np.sin(phase)))
    thread = pv.lines_from_points(helix).tube(radius=.055, n_sides=6)
    return [(shaft, "screw"), (head_base, "screw"), (left, "screw"), (right, "screw"), (thread, "screw")]


def drive_surfaces(geometry, mount):
    """Return native probe-local surfaces in um at the current carriage position.

    The probe follows +q along insertion. Fixed surfaces are offset by +q toward
    the base in probe-local coordinates, exactly cancelling that translation.
    Carriages with a specified thickness have an independent cuboid volume;
    otherwise only their mounting face is represented.
    """
    model = MODELS[mount.model_id]
    width, height = model.arm_width_mm, model.arm_height_mm
    h = mount.mount_height_mm
    thickness = model.arm_thickness_mm
    if thickness is not None:
        arm = pv.Box(bounds=(-width/2, width/2, -h, height-h, 0, thickness))
    else:
        arm = pv.PolyData([[-width/2, -h, 0], [width/2, -h, 0],
                           [width/2, height-h, 0], [-width/2, height-h, 0]], [4, 0, 1, 2, 3])
    parts = [(arm, "carriage")]
    lower = mount.raised_lower_mm
    if lower is not None:
        y = -h - lower
        w, d = model.mounting_cross_section
        gap = (thickness or 0) + mount.body_gap_mm
        if mount.body_height_mm is not None:
            parts.append((pv.Box(bounds=(-w/2, w/2, y, y+mount.body_height_mm, gap, gap+d)), "body"))
        else:
            footprint = pv.PolyData([[-w/2, y, gap], [w/2, y, gap],
                                    [w/2, y, gap+d], [-w/2, y, gap+d]], [4, 0, 1, 2, 3])
            parts.append((footprint, "footprint"))
    else:
        # Uncalibrated NP body datum: only show the fixed zero-travel reference,
        # not a guessed body volume or footprint at an invented bottom height.
        parts.append((pv.Line((-width/2, -h, 0), (width/2, -h, 0)), "reference"))
    parts.extend(screw_surfaces(model, mount, h))
    signs = np.array([1, geometry.y_to_base, geometry.y_to_base])
    for mesh, role in parts:
        points = np.asarray(mesh.points, dtype=float).copy()
        points[:, 0] -= mount.lateral_offset_mm
        if role != "carriage":
            # Compensate travel after generating the fixed geometry, avoiding
            # position-dependent float32 rounding in VTK primitives.
            points[:, 1] += mount.travel_mm
        mesh.points = points * signs * 1000 + mount.attachment_um
    return parts
