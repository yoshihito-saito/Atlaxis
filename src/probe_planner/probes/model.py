from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Contact:
    contact_id: str
    shank_id: int
    x_um: float
    y_um: float
    z_um: float = 0.0

    def __post_init__(self):
        if not isinstance(self.contact_id, str) or not self.contact_id:
            raise ValueError("Contact IDs must be nonempty strings.")
        if type(self.shank_id) is not int or self.shank_id < 0:
            raise ValueError("Shank IDs must be nonnegative integers.")
        if not np.isfinite([self.x_um, self.y_um, self.z_um]).all():
            raise ValueError("Contact coordinates must be finite micrometers.")


@dataclass
class ProbeBody:
    outline_um: list[list[float]]
    thickness_um: float
    shank_id: int | None = None

    def __post_init__(self):
        points = np.asarray(self.outline_um)
        if points.ndim != 2 or points.shape[1] != 3 or len(points) < 3 or not np.isfinite(points).all():
            raise ValueError("A probe-body outline requires at least three finite local xyz vertices.")
        if not np.isfinite(self.thickness_um) or self.thickness_um <= 0:
            raise ValueError("Probe-body thickness must be positive micrometers.")

    @property
    def vertices(self):
        points = np.asarray(self.outline_um, dtype=float)
        offset = np.array([0, 0, self.thickness_um / 2])
        return np.vstack((points - offset, points + offset))


@dataclass
class ProbeGeometry:
    name: str
    contacts: list[Contact]
    tip_um: tuple[float, float, float] = (0.0, 0.0, 0.0)
    y_to_base: int = 1
    units: str = "um"
    bodies: list[ProbeBody] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    mounting_base: ProbeBody | None = None

    def __post_init__(self):
        ids = [c.contact_id for c in self.contacts]
        if not self.name or not ids or len(set(ids)) != len(ids):
            raise ValueError("A named probe requires nonempty, unique contacts.")
        if self.units != "um":
            raise ValueError("Probe coordinates must use units='um'.")
        if np.asarray(self.tip_um).shape != (3,) or not np.isfinite(self.tip_um).all():
            raise ValueError("The probe tip must contain three finite coordinates.")
        if self.y_to_base not in (-1, 1):
            raise ValueError("y_to_base must be +1 or -1.")
        shanks = {c.shank_id for c in self.contacts}
        if any(body.shank_id is not None and body.shank_id not in shanks for body in self.bodies):
            raise ValueError("Probe body references a shank without contacts.")
        if self.mounting_base is not None and self.mounting_base.shank_id is not None:
            raise ValueError("The mounting base is shared by the probe, not an individual shank.")
        if self.mounting_base is None:
            from .mounting import base_specification, make_base

            dimensions, source = base_specification(self)
            if all(dimensions):
                self.mounting_base = make_base(self, dimensions)
                self.metadata = {**self.metadata, "mounting_base_source": source}

    @property
    def points(self) -> np.ndarray:
        return np.array([[c.x_um, c.y_um, c.z_um] for c in self.contacts], dtype=float)

    @property
    def display_bodies(self):
        from .mounting import is_acute_package

        return self.shaft_bodies + ([self.mounting_base]
            if self.mounting_base is not None and not is_acute_package(self) else [])

    @property
    def shaft_bodies(self):
        if self.bodies:
            return self.bodies
        # Geometry-only formats lack shaft dimensions. Keep an explicitly
        # schematic 5 mm shaft, extended when the contact span requires it.
        bodies = []
        for shank in sorted({c.shank_id for c in self.contacts}):
            points = self.points[[c.shank_id == shank for c in self.contacts]]
            x, _, z = np.median(points, axis=0)
            tip = self.tip_um[1]
            length = max(5000.0, float(np.max(np.abs(points[:, 1] - tip))) + 500.0)
            width = max(75.0, float(np.ptp(points[:, 0])) + 30.0)
            vertices = [[x, tip, z], [x - width / 2, tip + self.y_to_base * 100, z],
                        [x - width / 2, tip + self.y_to_base * length, z],
                        [x + width / 2, tip + self.y_to_base * length, z],
                        [x + width / 2, tip + self.y_to_base * 100, z]]
            bodies.append(ProbeBody(vertices, 50.0, shank))
        return bodies


@dataclass
class SelectionROI:
    id: str
    name: str
    density: str = "Full"
    region_id: int | None = None
    bounds_um: list[float] | None = None  # Local plane left, top, right, bottom.
    sites: list[str] = field(default_factory=list)
    registered: bool = False
    assigned_sites: list[str] = field(default_factory=list)
    polygon_um: list[list[float]] | None = None  # Local plane vertices; None for rectangles.
    selection_mode: str | None = None
    region_ids: list[int] | None = None  # Selected subtree roots; None uses legacy region_id.

    def __post_init__(self):
        if self.selection_mode is None:
            self.selection_mode = "Polygon" if self.polygon_um is not None else "Rectangle"

    @property
    def selected_region_ids(self):
        if self.region_ids is not None:
            return self.region_ids
        return [self.region_id] if self.region_id is not None else None


@dataclass
class ChannelMap:
    contact_to_channel: dict[str, int] = field(default_factory=dict)
    n_channels: int = 0
    groups: list[list[int]] = field(default_factory=list)
    skipped: list[int] = field(default_factory=list)
    source_xml: str | None = None
    blueprint: dict[str, str] = field(default_factory=dict)
    source_imro: str | None = None
    pending_sites: list[str] = field(default_factory=list)
    rois: list[SelectionROI] = field(default_factory=list)
    headstage_id: str | None = None

    def __post_init__(self):
        self.rois = [SelectionROI(**roi) if isinstance(roi, dict) else roi for roi in self.rois]
        if self.pending_sites and not self.rois:
            for density in ("Full", "Half", "Quarter", "Low"):
                sites = [site for site in self.pending_sites if self.blueprint.get(site, "Low") == density]
                if sites:
                    self.rois.append(SelectionROI(f"pending-{density}", f"Imported {density}",
                                                  density=density, sites=sites, registered=True))

    def validate(self, geometry: ProbeGeometry):
        if self.headstage_id is not None and (not isinstance(self.headstage_id, str) or not self.headstage_id):
            raise ValueError("Headstage ID must be a nonempty string or None.")
        if type(self.n_channels) is not int or self.n_channels < 0:
            raise ValueError("n_channels must be a nonnegative integer.")
        known = {c.contact_id for c in geometry.contacts}
        roi_ids, owned = set(), set()
        for roi in self.rois:
            if not isinstance(roi, SelectionROI) or not roi.id or roi.id in roi_ids or not roi.name:
                raise ValueError("ROI IDs must be unique and nonempty, with a display name.")
            roi_ids.add(roi.id)
            if roi.density not in {"Full", "Half", "Quarter", "Low"}:
                raise ValueError("Invalid ROI density.")
            if roi.selection_mode not in {"Rectangle", "Polygon"}:
                raise ValueError("ROI selection mode must be Rectangle or Polygon.")
            if roi.region_id is not None and (type(roi.region_id) is not int or roi.region_id <= 0):
                raise ValueError("ROI region IDs must be positive integers.")
            if roi.region_ids is not None and (not isinstance(roi.region_ids, list)
                    or any(type(rid) is not int or rid <= 0 for rid in roi.region_ids)
                    or len(set(roi.region_ids)) != len(roi.region_ids)):
                raise ValueError("ROI region IDs must be a list of unique positive integers.")
            if type(roi.registered) is not bool:
                raise ValueError("ROI registration must be boolean.")
            if roi.bounds_um is not None:
                bounds = np.asarray(roi.bounds_um)
                if (bounds.shape != (4,) or not np.isfinite(bounds).all()
                        or bounds[2] < bounds[0] or bounds[3] < bounds[1]):
                    raise ValueError("ROI bounds must be ordered, finite plane coordinates in µm.")
            if roi.polygon_um is not None:
                polygon = np.asarray(roi.polygon_um)
                if (polygon.ndim != 2 or polygon.shape[1] != 2 or len(polygon) < 3
                        or not np.isfinite(polygon).all()):
                    raise ValueError("ROI polygons require at least three finite plane vertices in µm.")
            sites, assigned = set(roi.sites), set(roi.assigned_sites)
            if not sites.issubset(known) or len(sites) != len(roi.sites):
                raise ValueError("ROI sites must be unique known contacts.")
            if (not assigned.issubset(sites & set(self.contact_to_channel)) or assigned & owned
                    or len(assigned) != len(roi.assigned_sites) or (assigned and not roi.registered)):
                raise ValueError("ROI assignments must have one registered owner and exist in the channel map.")
            owned.update(assigned)
        if not set(self.pending_sites).issubset(known) or len(set(self.pending_sites)) != len(self.pending_sites):
            raise ValueError("Pending ROI sites must be unique, known contacts.")
        if not set(self.blueprint).issubset(known) or not set(self.blueprint.values()).issubset(
                {"Full", "Half", "Quarter", "Low", "Excluded"}):
            raise ValueError("Invalid Neuropixels site selection blueprint.")
        if not set(self.contact_to_channel).issubset(known):
            raise ValueError("Channel map references unknown physical contacts.")
        channels = list(self.contact_to_channel.values())
        if len(channels) != len(set(channels)):
            raise ValueError("Duplicate device-channel assignments are unsupported.")
        grouped = [c for group in self.groups for c in group]
        if len(grouped) != len(set(grouped)):
            raise ValueError("Channels may occur in only one anatomical group.")
        for channel in channels + grouped + self.skipped:
            if type(channel) is not int or not 0 <= channel < self.n_channels:
                raise ValueError("Device channels must be zero-based integers below n_channels.")
        if self.groups and not set(channels).issubset(grouped):
            raise ValueError("Mapped contacts are missing from the XML anatomical groups.")
        if not set(self.skipped).issubset(grouped):
            raise ValueError("Skipped channels must belong to an anatomical group.")
