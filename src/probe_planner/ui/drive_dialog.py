"""Drive attachment and bounded carriage travel for the selected probe."""

from dataclasses import replace

from PySide6.QtWidgets import QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from probe_planner.implant.drive import DriveMount, MODELS, base_reference
from probe_planner.probes.mounting import base_dimensions, base_specification, is_acute_package, make_base
from .skull_dialog import number


class DriveDialog(QDialog):
    def __init__(self, probe, apply, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Microdrive · " + probe.geometry.name)
        self.probe, self.apply_callback = probe, apply
        self.loading = True
        self.attached = probe.drive is not None
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.model = QComboBox()
        for key, model in MODELS.items():
            self.model.addItem(model.name, key)
        form.addRow("Drive", self.model)
        root.addWidget(QLabel("Simplified model based on published dimensions."))
        root.addLayout(form)
        self.reference_um, self.reference_note = base_reference(probe.geometry)
        self.attachment_um = probe.drive.attachment_um if probe.drive else self.reference_um
        align = QPushButton("Align base")
        align.setToolTip("Align the lower-left corners of the probe base and moving carriage, viewed from the probe side; keep electrode positions unchanged.")
        align.clicked.connect(self.align_base)
        form.addRow(align)
        self.height = number()
        self.height.setToolTip("Probe-base height from the moving carriage's lower edge: positive = up, negative = down. Zero aligns their lower edges. This offset stays constant during drive travel.")
        self.height.valueChanged.connect(self.changed)
        form.addRow("Mount offset", self.height)
        dimensions_button = QPushButton("Dimensions…")
        dimensions_button.setCheckable(True)
        root.addWidget(dimensions_button)
        self.dimensions = QWidget()
        dimensions = QFormLayout(self.dimensions)
        self.base_controls = []
        for label in ("Base width", "Base height", "Base thickness"):
            spin = number(minimum=0)
            spin.setSpecialValueText("Not specified")
            spin.setToolTip("Chronic probe mounting base, not the connector or headstage. Dimensions in mm.")
            spin.valueChanged.connect(self.changed)
            self.base_controls.append(spin)
            dimensions.addRow(label, spin)
        self.body_height = number(minimum=0)
        self.body_height.setSpecialValueText("Not specified")
        self.body_height.setToolTip("Unknown height: show only the fixed footprint; do not infer body volume.")
        self.lower = number(minimum=-1000)
        self.lower.setSpecialValueText("Not specified")
        self.lower.setToolTip("Fully raised carriage lower edge above the fixed-body bottom. Unknown NP datum: reference line only.")
        self.gap = number(minimum=0)
        self.gap.setToolTip("Gap between the carriage back face and fixed body; zero means touching surfaces.")
        for label, control in (("Fixed body height", self.body_height), ("Raised lower edge", self.lower), ("Body gap", self.gap)):
            dimensions.addRow(label, control)
            control.valueChanged.connect(self.changed)
        self.note = QLabel()
        self.note.setWordWrap(True)
        dimensions.addRow(self.note)
        root.addWidget(self.dimensions)
        self.dimensions.hide()
        dimensions_button.toggled.connect(self.dimensions.setVisible)
        buttons = QHBoxLayout()
        remove = QPushButton("Detach")
        remove.clicked.connect(self.remove)
        buttons.addWidget(remove)
        attach = QPushButton("Attach to probe")
        attach.clicked.connect(lambda: self.attach(close=True))
        buttons.addWidget(attach)
        root.addLayout(buttons)
        self.model.currentIndexChanged.connect(self.model_changed)
        if probe.drive:
            self.model.setCurrentIndex(self.model.findData(probe.drive.model_id))
        self.populate(probe.drive)
        if probe.geometry.mounting_base is None:
            dimensions_button.setChecked(True)
            self.dimensions.show()
        self.loading = False

    def populate(self, mount=None):
        model = MODELS[self.model.currentData()]
        self.loading = True
        self.alignment_reset = mount is None
        self.height.setValue(mount.mount_height_mm if mount else 0)
        self.attachment_um = mount.attachment_um if mount else self.reference_um
        for spin, value in zip(self.base_controls, base_dimensions(self.probe.geometry)):
            spin.setValue(value)
        body = mount.body_height_mm if mount and mount.body_height_mm is not None else model.body_height_mm
        lower = mount.raised_lower_mm if mount else model.raised_lower_mm
        self.body_height.setValue(body or 0)
        self.lower.setValue(lower if lower is not None else self.lower.minimum())
        self.gap.setValue(mount.body_gap_mm if mount else 0)
        self.update_note()
        self.loading = False

    def update_note(self):
        model = MODELS[self.model.currentData()]
        self.note.setText("Reference: moving carriage's lower-left corner (probe-side view).")
        self.note.setToolTip(base_specification(self.probe.geometry)[1] + "\n"
            + self.probe.geometry.metadata.get("mounting_base_source", "")
            + "\nBase envelope centered on shaft roots, front faces aligned; package-to-site offset is approximate.\n"
            + model.source + "\nScrew geometry is illustrative.")

    def model_changed(self):
        if not self.loading:
            self.attached = False
            self.populate()

    def align_base(self):
        self.loading = True
        self.alignment_reset = True
        self.attachment_um = self.reference_um
        self.height.setValue(0)
        self.loading = False
        self.changed()

    def candidate(self):
        geometry = self.probe.geometry
        if is_acute_package(geometry):
            raise ValueError("Microdrive mounting is available for chronic probe packages only.")
        old_dimensions = base_dimensions(geometry)
        dimensions = tuple(old if round(old, spin.decimals()) == spin.value() else spin.value()
                           for old, spin in zip(old_dimensions, self.base_controls))
        if geometry.mounting_base is None or dimensions != tuple(old_dimensions):
            geometry = replace(geometry, mounting_base=make_base(geometry, dimensions),
                               metadata={**geometry.metadata, "mounting_base_source": "User-entered base dimensions."})
        reference, _ = base_reference(geometry)
        if reference is None:
            raise ValueError("Enter probe base dimensions before attaching a drive.")
        realign = self.alignment_reset or geometry is not self.probe.geometry
        attachment = reference if realign else self.attachment_um
        previous = self.probe.drive
        if previous is not None and previous.model_id != self.model.currentData():
            previous = None

        def exact_value(control, old):
            # Editing one displacement must not quantize unchanged saved values.
            return old if old is not None and round(old, control.decimals()) == control.value() else control.value()

        lower = (None if self.lower.value() == self.lower.minimum() else
                 exact_value(self.lower, previous.raised_lower_mm if previous else None))
        travel = previous.travel_mm if previous else 0
        height = exact_value(self.height, previous.mount_height_mm
                             if previous and not self.alignment_reset else None)
        mount = DriveMount(self.model.currentData(), tuple(attachment),
                          mount_height_mm=height,
                          travel_mm=travel,
                          body_height_mm=exact_value(self.body_height, previous.body_height_mm if previous else None) or None,
                          raised_lower_mm=lower,
                          body_gap_mm=exact_value(self.gap, previous.body_gap_mm if previous else None),
                          lateral_offset_mm=(previous.lateral_offset_mm if previous and not realign
                                             else -MODELS[self.model.currentData()].arm_width_mm / 2),
                          position_offset_mm=previous.position_offset_mm if previous else (0, 0, 0))
        return mount, geometry, realign

    def changed(self):
        if self.loading:
            return
        if self.attached and all(spin.value() > 0 for spin in self.base_controls):
            self.attach(close=False)

    def attach(self, *, close=True):
        try:
            self.apply_callback(*self.candidate())
            self.attached = True
            self.alignment_reset = False
            self.attachment_um = self.probe.drive.attachment_um
            self.reference_um, self.reference_note = base_reference(self.probe.geometry)
            self.update_note()
            if close:
                self.accept()
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Cannot attach drive", str(error))

    def remove(self):
        self.apply_callback(None)
        self.attached = False
