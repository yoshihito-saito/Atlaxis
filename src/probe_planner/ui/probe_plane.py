"""Lazy, asynchronous probe-plane section and site-range selection controls."""

from copy import copy, deepcopy
from dataclasses import astuple
from uuid import uuid4

from PySide6.QtCore import QThread, Signal, QTimer, Qt, QRectF
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)

from probe_planner.atlas.probe_section import probe_section
from probe_planner.probes.neuropixels import CATEGORIES, is_neuropixels, active_site_ids
from probe_planner.probes.model import SelectionROI
from probe_planner.rendering.probe_view import ProbeView
from probe_planner.rendering.slice_view import section_rgba


class PlaneWorker(QThread):
    sampled = Signal(object, object)
    failed = Signal(object, str)

    def __init__(self, key, atlas, frame, probe, parent):
        super().__init__(parent)
        self.key, self.atlas, self.frame, self.probe = key, atlas, frame, probe

    def run(self):
        try:
            section = probe_section(self.atlas, self.frame, self.probe, self.isInterruptionRequested)
            if section is not None:
                self.sampled.emit(self.key, section)
        except Exception as error:
            self.failed.emit(self.key, str(error))


class ProbePlanePanel(QWidget):
    blueprintChanged = Signal()
    generateRequested = Signal(str)
    removeRequested = Signal(str)
    resetRequested = Signal()

    def __init__(self):
        super().__init__()
        self.atlas = self.frame = self.probe = None
        self.rows = []
        self.key = self.sampled_key = None
        self.worker = None
        self.section = None
        self.colors, self.opacity = {}, 0.25
        self.active = False
        self.needs_fit = True
        self.selected_roi_id = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.controls = QWidget()
        controls = QVBoxLayout(self.controls)
        controls.setContentsMargins(0, 0, 0, 0)
        header = QHBoxLayout()
        self.count = QLabel("Mapped 0/384")
        header.addWidget(self.count)
        header.addStretch()
        add = QPushButton("Add ROI")
        add.clicked.connect(self.add_roi)
        header.addWidget(add)
        controls.addLayout(header)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ROI", "Region", "Density", "Sites / Ch", "", "", ""])
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setWordWrap(False)
        self.table.setStyleSheet("QPushButton { padding: 3px 5px; font-size: 11px; } "
                                 "QComboBox { padding: 3px; font-size: 11px; }")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.currentCellChanged.connect(self.select_roi)
        controls.addWidget(self.table)
        footer = QHBoxLayout()
        reset = QPushButton("Reset all")
        reset.setToolTip("Clear active channels and selection, and restore the default view")
        reset.clicked.connect(self.resetRequested)
        footer.addWidget(reset)
        footer.addStretch()
        controls.addLayout(footer)
        layout.addWidget(self.controls)
        self.view = ProbeView(labels=False)
        self.view.selectionStarted.connect(self.start_range)
        self.view.sitesSelected.connect(self.apply_range)
        layout.addWidget(self.view, 1)
        self.status = QLabel("Select a probe to show its plane.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.start_sampling)

    def reset_view(self):
        self.selected_roi_id = None
        self.view.selection_start = self.view.selection_rect = None
        self.view.pan_position = None
        self.view.unsetCursor()
        self.view.fit()
        self.view.viewport().update()
        self.refresh_rois()
        self.status.setText("Selection cleared. Drag to draw the first ROI.")

    def set_active(self, active):
        self.active = active
        if active:
            self.timer.start()
        else:
            self.timer.stop()
            if self.worker:
                self.worker.requestInterruption()

    def set_context(self, atlas, frame, probe, rows):
        previous = self.probe
        self.atlas, self.frame, self.probe, self.rows = atlas, frame, probe, rows
        if previous is not probe:
            self.selected_roi_id = None
            self.view.selection_start = self.view.selection_rect = None
        self.view.set_probe(probe, rows)
        ready = atlas is not None and frame is not None and probe is not None
        key = (id(atlas), repr(frame), id(probe.geometry), astuple(probe.pose),
               probe.selected_shank_id) if ready else None
        self.needs_fit |= previous is None or probe is None or previous.id != probe.id
        if key != self.key:
            self.key = key
            self.sampled_key = None
            self.section = None
            self.view.set_section_image(None, None, None)
            if self.worker:
                self.worker.requestInterruption()
            self.status.setText("Updating probe plane…" if ready else "Load an atlas and select a probe.")
        np_probe = probe is not None and is_neuropixels(probe.geometry)
        self.controls.setVisible(np_probe)
        self.controls.setEnabled(ready and self.section is not None)
        self.refresh_rois()
        if self.active and ready and self.sampled_key != self.key:
            self.timer.start()

    def set_mask(self, colors, opacity):
        self.colors, self.opacity = dict(colors), opacity
        if self.section is not None:
            self.display_section()

    def start_sampling(self):
        if not self.active or self.key is None or self.worker is not None or self.sampled_key == self.key:
            return
        # Geometry/atlas are read-only; pose/reference are snapshots for this job.
        probe = copy(self.probe)
        probe.pose = deepcopy(self.probe.pose)
        self.worker = PlaneWorker(self.key, self.atlas, deepcopy(self.frame), probe, self)
        self.worker.sampled.connect(self.sampled)
        self.worker.failed.connect(self.failed)
        self.worker.finished.connect(self.finished)
        self.worker.start()

    def sampled(self, key, section):
        if key != self.key:
            return
        self.sampled_key, self.section = key, section
        self.display_section()
        self.controls.setEnabled(True)
        self.update_ranges()
        if self.needs_fit:
            self.view.fit()
            self.needs_fit = False
        off_plane = max(abs(c.z_um - section.face_z_um) for c in self.probe.geometry.contacts)
        note = f" · projected sites up to {off_plane:.2f} µm off plane" if off_plane > 0.01 else ""
        hint = ("Drag a range → Register → Activate Channels. Add ROI for another range; right-drag to pan."
                if is_neuropixels(self.probe.geometry) else "Site tooltips report regions at their true 3D positions.")
        self.status.setText(f"Probe plane · {section.pixel_um[0]:g} µm pixels{note}. {hint}")

    def display_section(self):
        self.view.set_section_image(self.section,
            section_rgba(self.section, self.colors, self.opacity), self.atlas)

    def failed(self, key, message):
        if key == self.key:
            self.sampled_key = key  # Do not retry a failing job in a busy loop.
            self.status.setText(f"Unable to sample probe plane: {message}")

    def finished(self):
        self.worker.deleteLater()
        self.worker = None
        if self.active and self.key is not None and self.sampled_key != self.key:
            self.timer.start()

    def roi(self, roi_id=None):
        return next((roi for roi in self.probe.channel_map.rois
                     if roi.id == (roi_id or self.selected_roi_id)), None) if self.probe else None

    def add_roi(self):
        if self.probe is None or not is_neuropixels(self.probe.geometry):
            return
        names = {roi.name for roi in self.probe.channel_map.rois}
        number = 1
        while f"ROI {number}" in names:
            number += 1
        roi = SelectionROI(uuid4().hex, f"ROI {number}")
        self.probe.channel_map.rois.append(roi)
        self.selected_roi_id = roi.id
        self.refresh_rois()
        self.blueprintChanged.emit()
        self.status.setText("Drag to draw this ROI. Register fixes its range, region and density.")

    def select_roi(self, row, *_):
        if self.probe and 0 <= row < len(self.probe.channel_map.rois):
            self.selected_roi_id = self.probe.channel_map.rois[row].id
        self.update_ranges()

    def refresh_rois(self):
        rois = self.probe.channel_map.rois if self.probe else []
        if not any(roi.id == self.selected_roi_id for roi in rois):
            self.selected_roi_id = rois[-1].id if rois else None
        count = len(active_site_ids(self.probe.geometry, self.probe.channel_map)) if self.probe else 0
        self.count.setText(f"Mapped {count}/384")
        region_ids = {row["region_id"] for row in self.rows if row["region_id"] > 0}
        if self.atlas:
            region_ids |= {parent for rid in list(region_ids)
                           for parent in self.atlas.structures.get(rid, {}).get("structure_id_path", [])}
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.setRowCount(len(rois))
        for index, roi in enumerate(rois):
            self.table.setItem(index, 0, QTableWidgetItem(roi.name))
            region = QComboBox()
            region.setMinimumContentsLength(6)
            region.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            region.addItem("All regions", None)
            ids = region_ids | ({roi.region_id} if roi.region_id else set())
            for rid in sorted(ids, key=lambda rid: self.atlas.structures.get(rid, {}).get("acronym", "") if self.atlas else ""):
                metadata = self.atlas.structures.get(rid, {}) if self.atlas else {}
                region.addItem(metadata.get("acronym", str(rid)), rid)
                region.setItemData(region.count() - 1, metadata.get("name", ""), Qt.ToolTipRole)
            region.setCurrentIndex(max(0, region.findData(roi.region_id)))
            region.setEnabled(not roi.registered)
            region.currentIndexChanged.connect(lambda _, r=roi, box=region: self.edit_roi(r, region_id=box.currentData()))
            self.table.setCellWidget(index, 1, region)
            density = QComboBox()
            density.addItems(CATEGORIES[:-1])
            density.setCurrentText(roi.density)
            density.setEnabled(not roi.registered)
            density.currentTextChanged.connect(lambda value, r=roi: self.edit_roi(r, density=value))
            self.table.setCellWidget(index, 2, density)
            self.table.setItem(index, 3, QTableWidgetItem(f"{len(roi.sites)} / {len(roi.assigned_sites)}"))
            register = QPushButton("Registered" if roi.registered else "Register")
            register.setEnabled(not roi.registered and bool(roi.sites))
            register.clicked.connect(lambda _, rid=roi.id: self.register_roi(rid))
            self.table.setCellWidget(index, 4, register)
            activate = QPushButton("Active" if roi.assigned_sites else "Activate Channels")
            activate.setEnabled(roi.registered and not roi.assigned_sites and count < 384)
            activate.clicked.connect(lambda _, rid=roi.id: self.generateRequested.emit(rid))
            self.table.setCellWidget(index, 5, activate)
            remove = QPushButton("Remove")
            remove.clicked.connect(lambda _, rid=roi.id: self.removeRequested.emit(rid))
            self.table.setCellWidget(index, 6, remove)
            if roi.id == self.selected_roi_id:
                self.table.setCurrentCell(index, 0)
        self.table.setFixedHeight(32 + 34 * min(4, max(1, len(rois))) + 14)
        self.table.blockSignals(False)
        self.update_ranges()

    def edit_roi(self, roi, **changes):
        if roi.registered:
            return
        for key, value in changes.items():
            setattr(roi, key, value)
        self.selected_roi_id = roi.id
        self.table.setCurrentCell(self.probe.channel_map.rois.index(roi), 0)
        self.update_ranges()
        self.blueprintChanged.emit()

    def update_ranges(self):
        rois = self.probe.channel_map.rois if self.probe else []
        self.view.roi_rects = [(QRectF(b[0], b[1], b[2] - b[0], b[3] - b[1]),
                                roi.registered, roi.id == self.selected_roi_id)
                               for roi in rois if (b := roi.bounds_um) is not None]
        selected = self.roi()
        self.view.draw_selection = (self.probe is not None and is_neuropixels(self.probe.geometry)
                                    and self.section is not None and (selected is None or not selected.registered))
        self.view.viewport().update()

    def start_range(self):
        if self.roi() is None:
            self.add_roi()
        roi = self.roi()
        if roi and not roi.registered:
            roi.bounds_um, roi.sites = None, []
            self.refresh_rois()
            self.blueprintChanged.emit()

    def apply_range(self, sites, bounds):
        roi = self.roi()
        if roi is None or roi.registered:
            return
        roi.bounds_um, roi.sites = bounds, sites
        self.refresh_rois()
        self.blueprintChanged.emit()

    def register_roi(self, roi_id):
        roi = self.roi(roi_id)
        if roi is None or roi.registered or self.atlas is None:
            return
        if roi.region_id is not None:
            regions = {row["contact_id"]: row["region_id"] for row in self.rows}
            sites = [site for site in roi.sites if regions.get(site) == roi.region_id or roi.region_id in
                     self.atlas.structures.get(regions.get(site), {}).get("structure_id_path", [])]
        else:
            sites = list(roi.sites)
        if not sites:
            self.status.setText("No sites match this range and region. Change the region or redraw.")
            return
        roi.sites, roi.registered = sites, True
        self.selected_roi_id = roi.id
        self.refresh_rois()
        self.blueprintChanged.emit()
        self.status.setText(f"{roi.name} registered · {len(sites)} sites · {roi.density}. Activate Channels to assign.")
