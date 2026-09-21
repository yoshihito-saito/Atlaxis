from dataclasses import fields, asdict, astuple, replace
from copy import deepcopy
from functools import wraps
from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox, QSplitter,
    QFileDialog, QMessageBox, QDialog, QToolButton,
    QProgressBar, QComboBox, QTabWidget, QStackedWidget,
    QCheckBox, QSlider, QProgressDialog,
)

from probe_planner.atlas.brainglobe_backend import load_atlas
from probe_planner.atlas.coordinates import (
    AtlasCoordinates, atlas_default_coordinates, um_to_mm, reference_pose, canonical_pose,
    brain_surface_dv_mm, shank_surface_reference, insertion_direction,
    insertion_surface_entry_mm, pose_at_shank_insertion, pose_axis_tilts, pose_with_axis_tilts,
)
from probe_planner.implant.pose import ImplantPose
from probe_planner.atlas.regions import brain_region_ids
from probe_planner.implant.instance import ProbeInstance
from probe_planner.implant.region_mapping import map_contacts
from probe_planner.probes.importers import load_geometry_json, load_cellexplorer
from probe_planner.probes.library import probe_import_path, probe_library_path, planning_path
from probe_planner.storage import active_paths, default_paths, saved_paths
from probe_planner.probes.favorites import FavoriteProbes
from probe_planner.probes.wiring import headstage_map
from probe_planner.probes.model import ChannelMap
from probe_planner.probes.neuropixels import (
    activate_roi, activate_rois_balanced, remove_roi, import_imro, is_neuropixels, active_site_ids,
    import_selection,
)
from probe_planner.project.save_load import Plan, load_plan, export_contacts
from probe_planner.project.bundle import save_planning_bundle, prepare_channel_export, write_channel_export
from probe_planner.rendering.slice_view import SliceWorkspace
from probe_planner.rendering.regions import load_region_meshes, default_hidden_regions, brain_display_region_ids
from probe_planner.rendering.scene import load_display_mesh
from .dialogs import CoordinateDialog, ProbeImportDialog, HeadstageSelector, ProbeLibraryFilter
from .atlas_dialog import AtlasDialog
from .storage_dialog import DataFoldersDialog
from .region_dialog import RegionDialog
from .probe_plane import ProbePlanePanel
from .probe_summary import ProbeSummary
from .probe_selection import ProbeSelector, FavoriteProbesDialog
from .style import STYLE, question


def guarded(function):
    @wraps(function)
    def call(self, *args, **kwargs):
        try:
            return function(self, *args, **kwargs)
        except Exception as error:
            QMessageBox.critical(self, "Unable to complete action", str(error))
            return False
    return call


class AtlasLoader(QThread):
    loaded = Signal(object, object, object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, name, version=None, parent=None):
        super().__init__(parent)
        self.name, self.version = name, version

    def run(self):
        try:
            atlas = load_atlas(self.name, self.version, self.progress.emit)
            outline = load_display_mesh(atlas.root_mesh_path, self.progress.emit, atlas=atlas)
            meshes = load_region_meshes(atlas, self.progress.emit)
            self.progress.emit("Preparing atlas sections…")
            self.loaded.emit(atlas, meshes, outline)
        except Exception as error:
            self.failed.emit(str(error))


class ChannelSelector(QThread):
    selected = Signal(object)
    failed = Signal(str)

    def __init__(self, geometry, mapping, roi_id, eligible_sites, parent):
        super().__init__(parent)
        self.geometry, self.mapping, self.eligible_sites = geometry, deepcopy(mapping), set(eligible_sites)
        self.roi_id = roi_id

    def run(self):
        try:
            mapping = (activate_rois_balanced(self.geometry, self.mapping, self.eligible_sites)
                       if self.roi_id is None else
                       activate_roi(self.geometry, self.mapping, self.roi_id, self.eligible_sites))
            self.selected.emit(mapping)
        except Exception as error:
            self.failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Atlaxis[*]")
        available = self.screen().availableGeometry()
        self.resize(min(1320, available.width() - 40), min(800, available.height() - 60))
        self.setStyleSheet(STYLE)
        self.atlas = self.frame = None
        self.probes = []
        self.favorite_probes = FavoriteProbes()
        self.surface_pending_probes = set()
        self.current_probe_id = None
        self.calibration_source = ""
        self.selected_mask_ids = set()
        self.available_region_ids = set()
        self.rows = []
        self.worker = self.pending_plan = None
        self.channel_worker = None
        self.save_path = None
        self.busy = False
        toolbar = self.addToolBar("Plan")
        toolbar.setMovable(False)
        self.actions = []
        for label, handler, shortcut in (
            ("Open plan", self.open_project, "Ctrl+O"),
            ("Save && Update", self.save_project, "Ctrl+S"),
        ):
            action = QAction(label, self)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(handler)
            toolbar.addAction(action)
            self.actions.append(action)

        settings_menu = self.menuBar().addMenu("Settings")
        self.storage_action = settings_menu.addAction("Data folder…", self.configure_data_folders)
        settings_menu.addAction("Open data folder", lambda: self.open_data_folder(False))
        settings_menu.addAction("Open atlas folder", lambda: self.open_data_folder(True))

        root = QSplitter(Qt.Horizontal)
        left = QWidget()
        left.setMinimumWidth(260)
        left.setMaximumWidth(330)
        layout = QVBoxLayout(left)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        title = QLabel("Atlaxis")
        title.setObjectName("title")
        layout.addWidget(title)
        atlas_box = QGroupBox("Atlas")
        form = QVBoxLayout(atlas_box)
        self.atlas_name = QLabel("—")
        self.atlas_name.setWordWrap(True)
        form.addWidget(self.atlas_name)
        self.load_button = QPushButton("Load atlas")
        self.load_button.setToolTip("Open the atlas selection window")
        self.load_button.clicked.connect(self.start_atlas)
        form.addWidget(self.load_button)
        self.atlas_info = QLabel("Atlas not loaded")
        self.atlas_info.setToolTip("First load downloads atlas data through BrainGlobe.")
        self.atlas_info.setWordWrap(True)
        form.addWidget(self.atlas_info)
        self.calibrate_button = QPushButton("Bregma settings…")
        self.calibrate_button.setToolTip("AP / ML / DV zero point. The atlas preset is applied automatically; "
                                         "change only for a verified custom registration.")
        self.calibrate_button.clicked.connect(self.calibrate)
        form.addWidget(self.calibrate_button)
        self.calibration_info = QLabel("Bregma preset loads with atlas")
        self.calibration_info.setWordWrap(True)
        form.addWidget(self.calibration_info)
        layout.addWidget(atlas_box)
        probe_box = QGroupBox("Probe")
        probe_layout = QVBoxLayout(probe_box)
        probe_actions = QHBoxLayout()
        probe_actions.setSpacing(6)
        self.add_probe_button = QToolButton()
        self.add_probe_button.setObjectName("addProbe")
        self.add_probe_button.setText("+")
        self.add_probe_button.setFixedSize(22, 22)
        self.add_probe_button.setAccessibleName("Add probe")
        self.add_probe_button.setToolTip("Add probe")
        self.add_probe_button.clicked.connect(self.import_geometry)
        probe_actions.addWidget(self.add_probe_button)
        self.favorites_button = QPushButton("Favorite")
        self.favorites_button.setToolTip("Open the list of registered favorite probes")
        self.favorites_button.clicked.connect(self.show_favorites)
        probe_actions.addWidget(self.favorites_button)
        probe_actions.addStretch()
        self.favorite_star = QToolButton()
        self.favorite_star.setObjectName("favoriteProbe")
        self.favorite_star.setCheckable(True)
        self.favorite_star.setFixedSize(22, 22)
        self.favorite_star.clicked.connect(lambda checked=False: self.toggle_favorite(self.selected_probe))
        probe_actions.addWidget(self.favorite_star)
        probe_layout.addLayout(probe_actions)
        self.probe_selector = ProbeSelector(removable=True)
        self.probe_selector.setAccessibleName("Probe")
        self.probe_selector.currentIndexChanged.connect(self.select_probe)
        self.probe_selector.removeRequested.connect(self.remove_probe)
        probe_layout.addWidget(self.probe_selector)
        self.probe_page = QWidget()
        self.probe_page.setObjectName("probePage")
        page_layout = QVBoxLayout(self.probe_page)
        page_layout.setContentsMargins(8, 10, 8, 8)
        page_layout.setSpacing(8)
        self.headstage_row = QWidget()
        headstage_form = QFormLayout(self.headstage_row)
        headstage_form.setContentsMargins(0, 0, 0, 0)
        self.headstage_selector = HeadstageSelector()
        self.headstage_selector.currentIndexChanged.connect(self.change_headstage)
        self.headstage_label = QLabel("Headstage")
        headstage_form.addRow(self.headstage_label, self.headstage_selector)
        page_layout.addWidget(self.headstage_row)
        page_layout.addWidget(QLabel("Reference shank"))
        self.shank_selector = QComboBox()
        self.shank_selector.setMinimumHeight(27)
        self.shank_selector.setToolTip("Coordinate reference and section tip. Switching shanks restores tip following and preserves probe placement.")
        self.shank_selector.currentIndexChanged.connect(self.select_shank)
        page_layout.addWidget(self.shank_selector)
        heading = QLabel("Coordinates")
        heading.setObjectName("muted")
        page_layout.addWidget(heading)
        self.pose_box = QWidget()
        form = QFormLayout(self.pose_box)
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(6)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.controls = {}
        controls = [("ap_mm", "AP", -10000, 10000), ("ml_mm", "ML", -10000, 10000),
                    ("dv_mm", "DV (tip)", -1e9, 1e9),
                    ("ap_tilt_deg", "AP tilt", -180, 180), ("ml_tilt_deg", "ML tilt", -90, 90),
                    ("roll_deg", "Roll", -180, 180), ("depth_mm", "Insertion depth", -10000, 10000)]
        for name, label, minimum, maximum in controls:
            spin = QDoubleSpinBox()
            spin.setRange(minimum, maximum)
            spin.setDecimals(2)
            spin.setSingleStep(0.01 if name.endswith("mm") else 1.0)
            spin.setSuffix(" mm" if name.endswith("mm") else " °")
            spin.setKeyboardTracking(False)
            spin.valueChanged.connect(lambda value, name=name: self.update_pose(name, value))
            form.addRow(label, spin)
            self.controls[name] = spin
        page_layout.addWidget(self.pose_box)
        probe_layout.addWidget(self.probe_page)
        layout.addWidget(probe_box)
        layout.addStretch()
        root.addWidget(left)

        canvas = QWidget()
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(4, 6, 4, 0)
        view_controls = QHBoxLayout()
        self.slices = SliceWorkspace()
        self.view_checks = {}
        for name in ("Brain outline", "3D regions", "Coronal", "Sagittal"):
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkbox.toggled.connect(lambda visible, name=name: self.slices.set_view_visible(name, visible))
            view_controls.addWidget(checkbox)
            self.view_checks[name] = checkbox
        self.regions_button = QPushButton("Region mask")
        self.regions_button.clicked.connect(self.select_regions)
        view_controls.addWidget(self.regions_button)
        view_controls.addStretch()
        canvas_layout.addLayout(view_controls)
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Mask opacity"))
        self.mask_opacity = QSlider(Qt.Horizontal)
        self.mask_opacity.setRange(0, 100)
        self.mask_opacity.setValue(25)
        self.mask_opacity.setMaximumWidth(110)
        self.mask_opacity_label = QLabel("25%")
        self.mask_opacity.setToolTip("Opacity of both 2D masks and 3D regions")
        self.mask_opacity_timer = QTimer(self)
        self.mask_opacity_timer.setSingleShot(True)
        self.mask_opacity_timer.setInterval(60)
        self.mask_opacity_timer.timeout.connect(self.update_region_mask)
        self.mask_opacity.valueChanged.connect(self.queue_mask_opacity)
        opacity_row.addWidget(self.mask_opacity)
        opacity_row.addWidget(self.mask_opacity_label)
        opacity_row.addStretch()
        canvas_layout.addLayout(opacity_row)
        self.workspace_tabs = QTabWidget()
        self.workspace_tabs.addTab(self.slices, "3D")
        self.probe_plane = ProbePlanePanel()
        self.probe_plane.blueprintChanged.connect(lambda: self.setWindowModified(True))
        self.probe_plane.generateRequested.connect(self.generate_channels)
        self.probe_plane.generateBalancedRequested.connect(lambda: self.generate_channels(None))
        self.probe_plane.removeRequested.connect(self.remove_selection_roi)
        self.probe_plane.resetRequested.connect(self.reset_channel_selection)
        self.workspace_tabs.addTab(self.probe_plane, "Probe plane")
        self.workspace_tabs.currentChanged.connect(lambda index: self.probe_plane.set_active(index == 1))
        canvas_layout.addWidget(self.workspace_tabs, 1)
        self.slices.set_navigation_speed(1.0)
        root.addWidget(canvas)

        right = QWidget()
        right.setMinimumWidth(220)
        layout = QVBoxLayout(right)
        layout.setContentsMargins(6, 6, 6, 0)
        layout.addWidget(QLabel("Channel regions"))
        self.summary_selector = ProbeSelector()
        self.summary_selector.setAccessibleName("Channel regions probe")
        self.summary_pages = QStackedWidget()
        self.summary_pages.setObjectName("probeSummaryPages")
        self.summary_selector.currentIndexChanged.connect(self.select_summary)
        self.probe_summaries = {}
        layout.addWidget(self.summary_selector)
        layout.addWidget(self.summary_pages, 1)
        root.addWidget(right)
        root.setStretchFactor(1, 1)
        root.setSizes([310, 870, 270])
        self.setCentralWidget(root)
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)
        self.loading_progress.setMaximumWidth(150)
        self.statusBar().addPermanentWidget(self.loading_progress)
        self.loading_progress.hide()
        self.refresh_probe_selector()
        self.statusBar().showMessage("Load an atlas, then use + to import a probe.")

    @property
    def selected_probe(self):
        return next((probe for probe in self.probes if probe.id == self.current_probe_id), None)

    @property
    def geometry(self):
        return self.selected_probe.geometry if self.selected_probe else None

    @property
    def mapping(self):
        return self.selected_probe.channel_map if self.selected_probe else None

    @property
    def pose(self):
        return self.selected_probe.pose if self.selected_probe else ImplantPose()

    def _add_probe(self, geometry, mapping, mark_modified=True):
        number = 1
        ids = {probe.id for probe in self.probes}
        while f"probe_{number}" in ids:
            number += 1
        probe = ProbeInstance(f"probe_{number}", geometry, mapping)
        probe.pose = canonical_pose(geometry, probe.pose, probe.selected_shank_id)
        self.probes.append(probe)
        self.surface_pending_probes.add(probe.id)
        self.place_pending_probes_on_surface()
        self.current_probe_id = probe.id
        self.refresh_probe_selector()
        if mark_modified:
            self.setWindowModified(True)

    @staticmethod
    def probe_label(probe):
        number = probe.id.removeprefix("probe_")
        return f"{number} · {probe.geometry.name}"

    def refresh_probe_selector(self):
        self.probe_selector.blockSignals(True)
        self.summary_selector.blockSignals(True)
        self.probe_selector.clear()
        self.summary_selector.clear()
        # Keep each probe's views and zoom while entries are reordered/removed.
        while self.summary_pages.count():
            self.summary_pages.removeWidget(self.summary_pages.widget(0))
        valid_ids = {probe.id for probe in self.probes}
        for probe_id in list(self.probe_summaries):
            if probe_id not in valid_ids:
                self.probe_summaries.pop(probe_id).deleteLater()
        for index, probe in enumerate(self.probes):
            label = self.probe_label(probe)
            for selector in (self.probe_selector, self.summary_selector):
                selector.addItem(label, probe.id)
                selector.setItemData(index, label, Qt.ToolTipRole)
            if (probe.id not in self.probe_summaries or
                    self.probe_summaries[probe.id].probe.geometry is not probe.geometry):
                old_summary = self.probe_summaries.pop(probe.id, None)
                if old_summary is not None:
                    old_summary.deleteLater()
                summary = ProbeSummary(probe)
                summary.selectRequested.connect(lambda: self.workspace_tabs.setCurrentIndex(1))
                summary.importRequested.connect(self.import_channel_map)
                summary.exportRequested.connect(self.export_channel_map)
                self.probe_summaries[probe.id] = summary
            self.summary_pages.addWidget(self.probe_summaries[probe.id])
        index = next((i for i, p in enumerate(self.probes) if p.id == self.current_probe_id),
                     0 if self.probes else -1)
        self.probe_selector.setCurrentIndex(index)
        self.summary_selector.setCurrentIndex(index)
        self.probe_selector.blockSignals(False)
        self.summary_selector.blockSignals(False)
        self.select_probe(index)

    def refresh_favorite_button(self):
        probe = self.selected_probe
        self.favorite_star.setVisible(probe is not None)
        favorite = probe is not None and self.favorite_probes.contains(probe.geometry)
        self.favorite_star.setChecked(favorite)
        self.favorite_star.setText("★" if favorite else "☆")
        action = "Remove from Favorite probes" if favorite else "Add to Favorite probes"
        self.favorite_star.setToolTip(f"{self.probe_label(probe)}\n{action}" if probe else action)

    @guarded
    def toggle_favorite(self, probe):
        if probe is None:
            return
        try:
            self.favorite_probes.toggle(probe.geometry, probe.channel_map)
        finally:
            self.refresh_favorite_button()

    @guarded
    def show_favorites(self, checked=False):
        dialog = FavoriteProbesDialog(self.favorite_probes.entries, self)
        accepted = dialog.exec() == QDialog.Accepted
        key = dialog.selected_key
        dialog.deleteLater()
        if accepted and key is not None:
            self.import_favorite(key)

    @guarded
    def import_favorite(self, key):
        geometry, mapping = self.favorite_probes.load(key)
        self.confirm_probe_import(geometry, mapping)

    def select_summary(self, index):
        if 0 <= index < len(self.probes):
            self.probe_selector.setCurrentIndex(index)

    @guarded
    def select_probe(self, index=None):
        if index is None:
            index = self.probe_selector.currentIndex()
        probe_id = self.probe_selector.itemData(index)
        self.current_probe_id = probe_id
        self.summary_selector.blockSignals(True)
        self.summary_selector.setCurrentIndex(index if self.probes else -1)
        self.summary_selector.blockSignals(False)
        self.summary_pages.setCurrentIndex(index if self.probes else -1)
        for selector in (self.probe_selector, self.summary_selector):
            selector.setToolTip(selector.currentText())
        self.refresh_favorite_button()
        self.shank_selector.blockSignals(True)
        self.shank_selector.clear()
        if self.selected_probe:
            for shank in sorted({contact.shank_id for contact in self.geometry.contacts}):
                self.shank_selector.addItem(f"Shank {shank}", shank)
            self.shank_selector.setCurrentIndex(self.shank_selector.findData(self.selected_probe.selected_shank_id))
        self.refresh_pose_controls()
        self.shank_selector.blockSignals(False)
        self.refresh_headstage()
        self.recompute(fit=True)

    def refresh_headstage(self):
        probe = self.selected_probe
        self.headstage_selector.set_probe(probe.geometry if probe else None, probe.channel_map if probe else None)
        self.headstage_label.setText(probe.geometry.metadata.get("connection_label", "Headstage") if probe else "Headstage")
        self.headstage_row.setVisible(bool(probe and probe.geometry.metadata.get("headstage_profiles")))

    @guarded
    def change_headstage(self, index):
        probe = self.selected_probe
        if probe is None or self.headstage_selector.itemData(index) == "saved":
            return
        probe.channel_map = headstage_map(probe.geometry, self.headstage_selector.itemData(index))
        self.refresh_headstage()
        self.recompute()
        self.setWindowModified(True)

    def refresh_pose_controls(self):
        probe = self.selected_probe
        displayed = (reference_pose(probe.geometry, probe.pose, probe.selected_shank_id)
                     if probe else ImplantPose())
        surface = (shank_surface_reference(probe.geometry, probe.pose, probe.selected_shank_id,
                                           self.atlas, self.frame) if probe else None)
        values = asdict(displayed)
        if surface is not None:
            values["ap_mm"], values["ml_mm"] = surface.entry_mm[:2]
            values["dv_mm"], values["depth_mm"] = surface.dv_mm, surface.depth_mm
        # Controls use left-positive ML; saved poses retain right-positive ML.
        values["ml_mm"] = -values["ml_mm"]
        values["ap_tilt_deg"], values["ml_tilt_deg"], values["roll_deg"] = pose_axis_tilts(displayed)
        for name, control in self.controls.items():
            control.blockSignals(True)
            value = values[name]
            if name in ("dv_mm", "depth_mm"):
                control.setSpecialValueText("No surface" if surface is None else "")
                value = control.minimum() if surface is None else value
                control.setEnabled(surface is not None)
            control.setValue(value)
            control.blockSignals(False)
        self.controls["ap_mm"].setToolTip("Entry coordinate of the reference shank, relative to Bregma")
        self.controls["ml_mm"].setToolTip(
            "Entry coordinate of the reference shank, relative to Bregma: "
            "positive = anatomical left, negative = anatomical right")
        self.controls["dv_mm"].setToolTip(
            "Vertical tip depth from this shank's insertion-axis intersection with the brain surface. "
            "Editing DV adjusts insertion depth along the current axis; positive = ventral."
            if surface is not None else
            "No annotated surface along this shank's axis, or atlas/Bregma not loaded. Adjust AP/ML or tilt.")
        self.controls["depth_mm"].setToolTip(
            "Distance along this shank's axis from the brain surface: negative before entry, "
            "zero at the surface, positive after entry. Editing moves the whole probe.")
        self.controls["ap_tilt_deg"].setToolTip("Sagittal tilt: positive = anterior, negative = posterior")
        self.controls["ml_tilt_deg"].setToolTip("Tilt out of the sagittal plane: positive = anatomical left, negative = anatomical right")
        self.controls["roll_deg"].setToolTip("Rotation about the tilted probe axis")

    def entry_surface_dv(self, entry):
        if self.atlas is None or self.frame is None:
            return None
        return brain_surface_dv_mm(self.atlas, self.frame, entry.ap_mm, entry.ml_mm)

    def place_pending_probes_on_surface(self):
        if self.atlas is None or self.frame is None:
            return
        for probe in self.probes:
            if probe.id not in self.surface_pending_probes:
                continue
            entry = reference_pose(probe.geometry, probe.pose, probe.selected_shank_id)
            surface = self.entry_surface_dv(entry)
            if surface is not None:
                entry.dv_mm += surface
                origin = insertion_surface_entry_mm(self.atlas, self.frame,
                    [entry.ap_mm, entry.ml_mm, entry.dv_mm], insertion_direction(entry))
                probe.pose = (canonical_pose(probe.geometry, entry, probe.selected_shank_id) if origin is None else
                              pose_at_shank_insertion(probe.geometry, entry, probe.selected_shank_id,
                                                      origin, entry.depth_mm))
            self.surface_pending_probes.discard(probe.id)

    @guarded
    def select_shank(self, index=None):
        if self.selected_probe and self.shank_selector.currentData() is not None:
            self.selected_probe.selected_shank_id = self.shank_selector.currentData()
            self.refresh_pose_controls()
            self.recompute()
            self.setWindowModified(True)

    @guarded
    def remove_probe(self, index):
        probe_id = self.probe_selector.itemData(index)
        if probe_id is None:
            return
        self.probes = [probe for probe in self.probes if probe.id != probe_id]
        self.surface_pending_probes.discard(probe_id)
        if self.current_probe_id == probe_id:
            self.current_probe_id = self.probes[min(index, len(self.probes) - 1)].id if self.probes else None
        self.refresh_probe_selector()
        self.setWindowModified(True)

    def queue_mask_opacity(self, value):
        self.mask_opacity_label.setText(f"{value}%")
        if not self.mask_opacity_timer.isActive():
            self.mask_opacity_timer.start()

    @guarded
    def select_regions(self, checked=False):
        dialog = RegionDialog(self.atlas.structures, self.selected_mask_ids,
                              self.atlas.name, self, available_ids=self.available_region_ids)
        if dialog.exec() == QDialog.Accepted:
            self.selected_mask_ids = dialog.selected_ids
            self.update_region_mask()
        dialog.deleteLater()

    def update_region_mask(self, *_):
        self.mask_opacity_timer.stop()
        self.slices.outline.select_regions(self.selected_mask_ids)
        self.slices.outline.set_region_opacity(self.mask_opacity.value() / 100)
        self.slices.set_mask(self.selected_mask_ids, True, self.mask_opacity.value() / 100, expand=False)
        self.slices.show_probes(self.atlas, self.frame, self.probes, self.selected_probe)
        self.probe_plane.set_mask(self.slices.mask_colors, self.mask_opacity.value() / 100)

    def refresh_enabled(self):
        self.load_button.setEnabled(not self.busy)
        self.storage_action.setEnabled(not self.busy)
        self.probe_selector.setEnabled(bool(self.probes) and not self.busy)
        self.add_probe_button.setEnabled(not self.busy)
        self.favorites_button.setEnabled(not self.busy)
        self.favorite_star.setEnabled(self.selected_probe is not None and not self.busy)
        self.summary_selector.setEnabled(bool(self.probes) and not self.busy)
        self.shank_selector.setEnabled(self.selected_probe is not None and not self.busy)
        self.calibrate_button.setEnabled(self.atlas is not None and not self.busy)
        self.regions_button.setEnabled(self.atlas is not None and not self.busy)
        self.mask_opacity.setEnabled(self.atlas is not None and not self.busy)
        ready = all(x is not None for x in (self.atlas, self.frame, self.geometry, self.mapping))
        self.pose_box.setEnabled(self.selected_probe is not None and not self.busy)
        self.headstage_row.setEnabled(not self.busy)
        self.probe_page.setVisible(self.selected_probe is not None)
        for action in self.actions:
            action.setEnabled(not self.busy)
        for action in self.actions[1:]:
            action.setEnabled(ready and not self.busy)

    def discard_changes(self):
        if not self.isWindowModified():
            return True
        answer = question(self, "Unsaved plan", "Save changes before continuing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
        return answer == QMessageBox.Discard or (answer == QMessageBox.Save and self.save_project())

    @guarded
    def configure_data_folders(self):
        dialog = DataFoldersDialog(saved_paths() or active_paths() or default_paths(), self)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "Data folder saved",
                "Restart Atlaxis to use this folder. The current plan and data have not been moved.")
        dialog.deleteLater()

    @guarded
    def open_data_folder(self, atlas=False):
        paths = active_paths()
        if paths is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(paths.atlases if atlas else paths.root)))

    @guarded
    def start_atlas(self, checked=False):
        current = self.atlas.name if self.atlas is not None else "whs_sd_rat_39um"
        dialog = AtlasDialog(current, self)
        accepted = dialog.exec() == QDialog.Accepted
        name = dialog.selected_name
        dialog.deleteLater()
        if not accepted:
            return
        if not name:
            raise ValueError("Enter a BrainGlobe atlas name.")
        if self.atlas is not None and not self.discard_changes():
            return
        self.pending_plan = None
        self.begin_load(name)

    def begin_load(self, name, version=None):
        if not name:
            raise ValueError("Enter a BrainGlobe atlas name.")
        self.pre_load_modified = self.isWindowModified()
        self.busy = True
        self.loading_progress.show()
        self.refresh_enabled()
        self.statusBar().showMessage(f"Loading {name}… first download can take several minutes.")
        self.worker = AtlasLoader(name, version, self)
        self.worker.loaded.connect(self.atlas_loaded)
        self.worker.failed.connect(self.atlas_failed)
        self.worker.progress.connect(self.statusBar().showMessage)
        self.worker.finished.connect(self.load_finished)
        self.worker.start()

    @guarded
    def atlas_loaded(self, atlas, meshes, outline):
        plan = self.pending_plan
        if plan and (plan.coordinates.orientation != atlas.orientation or
                     not np.array_equal(plan.coordinates.resolution_um, atlas.resolution_um)):
            raise ValueError("Project calibration does not match the loaded atlas coordinate system.")
        same_atlas = (self.atlas is not None and self.atlas.name == atlas.name
                      and self.atlas.version == atlas.version)
        self.atlas = atlas
        self.available_region_ids = set(meshes) & brain_display_region_ids(atlas)
        if not same_atlas:
            self.selected_mask_ids = self.available_region_ids - default_hidden_regions(atlas)
        else:
            self.selected_mask_ids.intersection_update(self.available_region_ids)
        self.slices.set_region_meshes(meshes, atlas.structures)
        self.slices.set_brain_outline(outline)
        if plan:
            self.frame, self.calibration_source = plan.coordinates, "Saved project Bregma"
        elif not same_atlas or self.frame is None:
            self.frame = atlas_default_coordinates(atlas)
            self.calibration_source = "Waxholm Bregma preset · atlas-aligned axes" if self.frame else ""
        self.atlas_name.setText(atlas.name)
        resolution = " × ".join(f"{value:g}" for value in atlas.resolution_um)
        self.atlas_info.setText(f"Loaded · {resolution} µm voxels")
        self.atlas_info.setToolTip(f"{atlas.name} · v{atlas.version}\n"
                                  f"Shape: {atlas.annotation.shape}\nOrigin: {atlas.orientation}")
        if plan:
            self.probes = plan.probes
            self.surface_pending_probes.clear()
            self.current_probe_id = plan.selected_probe_id
            self.save_path = self.pending_path
        else:
            self.save_path = None
        self.place_pending_probes_on_surface()
        self.refresh_probe_selector()
        self.update_region_mask()
        self.update_calibration_label()
        self.setWindowModified(self.pre_load_modified if plan is None else False)
        self.statusBar().showMessage("Atlas ready · Bregma loaded." if self.frame else
                                     "Atlas loaded. No Bregma preset is available; open Bregma settings.")

    def atlas_failed(self, message):
        self.statusBar().showMessage("Atlas loading failed; previous plan retained.")
        QMessageBox.critical(self, "Atlas loading failed", message)

    def load_finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.pending_plan = None
        self.busy = False
        self.loading_progress.hide()
        self.refresh_enabled()

    @guarded
    def calibrate(self, checked=False):
        if self.frame and self.calibration_source.startswith("Waxholm"):
            registration_hint = "The Waxholm atlas preset is applied automatically, so normally no edit is needed. "
        elif self.frame:
            registration_hint = "This atlas already has a saved or custom Bregma origin. "
        else:
            registration_hint = "This atlas has no automatic Bregma preset; enter a verified landmark position. "
        dialog = CoordinateDialog("Bregma — coordinate origin",
            "Bregma sets atlas registration and the AP/ML origin. The probe's DV is measured "
            "from the local brain surface. " + registration_hint +
            "Change these values only for a verified custom registration. "
            "These are the origin's atlas XYZ positions, not probe coordinates.",
            ["Atlas x (µm)", "Atlas y (µm)", "Atlas z (µm)"],
            self.frame.bregma_atlas_um if self.frame else None, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        self.frame = AtlasCoordinates(self.atlas.resolution_um, self.atlas.orientation, dialog.values)
        self.calibration_source = "Custom Bregma · atlas-aligned axes"
        self.place_pending_probes_on_surface()
        self.refresh_pose_controls()
        self.update_calibration_label()
        self.rebuild_probe()
        self.setWindowModified(True)

    def update_calibration_label(self):
        if self.frame:
            position = ", ".join(f"{v:.2f}" for v in um_to_mm(self.frame.bregma_atlas_um))
            self.calibration_info.setText("Bregma: automatic atlas preset" if self.calibration_source.startswith("Waxholm")
                                          else "Bregma: saved origin" if self.calibration_source.startswith("Saved")
                                          else "Bregma: custom origin")
            self.calibration_info.setToolTip(f"{self.calibration_source}\nAtlas x/y/z: {position} mm")
        else:
            self.calibration_info.setText("Bregma not set · open Bregma settings")

    @guarded
    def import_geometry(self, checked=False):
        chooser = QFileDialog(self)
        # The native macOS chooser can restore its last directory instead.
        chooser.setOption(QFileDialog.DontUseNativeDialog, True)
        chooser.setWindowTitle("Import probe geometry")
        chooser.setFileMode(QFileDialog.ExistingFile)
        chooser.setNameFilter("Probe geometry (*.json)")
        library_filter = ProbeLibraryFilter(probe_library_path(), chooser)
        chooser.setProxyModel(library_filter)
        chooser.setDirectory(str(probe_import_path()))
        accepted = chooser.exec() == QDialog.Accepted
        filenames = chooser.selectedFiles() if accepted else []
        chooser.deleteLater()
        if not filenames:
            return
        path = Path(filenames[0])
        if path.suffix.lower() == ".mat":
            dialog = CoordinateDialog("Probe-local frame",
                "Specify the physical tip in the file's local coordinates (µm). "
                "Do not substitute the lowest electrode for the physical tip. "
                "x is lateral; y follows the shaft. Missing z means planar; missing shank means one shank. "
                "chanCoords.channel must contain 1-based acquisition IDs.",
                ["Tip x (µm)", "Tip y (µm)", "Tip z (µm)"], probe=True, parent=self)
            if dialog.exec() != QDialog.Accepted:
                return
            geometry, mapping = load_cellexplorer(path, dialog.values,
                                                   1 if dialog.direction.isChecked() else -1)
        else:
            geometry, mapping = load_geometry_json(path)
        self.confirm_probe_import(geometry, mapping)

    def confirm_probe_import(self, geometry, mapping):
        confirmation = ProbeImportDialog(geometry, mapping, self)
        if confirmation.exec() == QDialog.Accepted:
            self._add_probe(geometry, confirmation.mapping)
        confirmation.deleteLater()

    def rebuild_probe(self):
        self.recompute(fit=True)

    @guarded
    def update_pose(self, name, value):
        probe = self.selected_probe
        if name == "ml_mm":
            value = -value
        entry = reference_pose(probe.geometry, probe.pose, probe.selected_shank_id)
        surface = shank_surface_reference(probe.geometry, probe.pose, probe.selected_shank_id,
                                          self.atlas, self.frame)
        depth = entry.depth_mm
        if surface is not None:
            entry = replace(entry, ap_mm=surface.entry_mm[0], ml_mm=surface.entry_mm[1],
                            dv_mm=surface.entry_mm[2], depth_mm=0.0)
            depth = surface.depth_mm
        if name in ("dv_mm", "depth_mm"):
            try:
                if surface is None:
                    raise ValueError("Choose an AP/ML and tilt whose insertion axis meets the annotated brain.")
                depth = value
                if name == "dv_mm":
                    vertical = insertion_direction(entry)[2]
                    if abs(vertical) <= 8 * np.finfo(float).eps:
                        if value != 0:
                            raise ValueError("A horizontal probe cannot change DV by insertion. Change the tilt first.")
                        depth = 0.0
                    else:
                        depth = value / vertical
                if not self.controls["depth_mm"].minimum() <= depth <= self.controls["depth_mm"].maximum():
                    raise ValueError("This DV exceeds the insertion depth limits for the current tilt.")
            except ValueError:
                self.refresh_pose_controls()
                raise
            edited = entry
        elif name in ("ap_tilt_deg", "ml_tilt_deg", "roll_deg"):
            angles = dict(zip(("ap_tilt_deg", "ml_tilt_deg", "roll_deg"), pose_axis_tilts(entry)))
            angles[name] = value
            edited = pose_with_axis_tilts(entry, angles["ap_tilt_deg"], angles["ml_tilt_deg"], angles["roll_deg"])
        else:
            values = asdict(entry)
            values[name] = value
            edited = ImplantPose(**values)
        if name in ("ap_mm", "ml_mm"):
            new_surface = self.entry_surface_dv(edited)
            if new_surface is not None:
                edited.dv_mm = new_surface
        origin = [edited.ap_mm, edited.ml_mm, edited.dv_mm]
        if name not in ("dv_mm", "depth_mm") and self.atlas is not None and self.frame is not None:
            # The new axis can cross a different voxel boundary even when its
            # pivot was on the old surface. Preserve signed travel from the new entry.
            new_origin = insertion_surface_entry_mm(self.atlas, self.frame, origin, insertion_direction(edited))
            if new_origin is not None:
                origin = new_origin
        probe.pose = pose_at_shank_insertion(probe.geometry, edited, probe.selected_shank_id,
                                             origin, depth)
        self.refresh_pose_controls()
        self.recompute()
        self.setWindowModified(True)

    def recompute(self, fit=False):
        self.rows = []
        if self.frame and self.atlas:
            for probe in self.probes:
                self.rows.extend(map_contacts(probe.geometry, probe.channel_map, probe.pose,
                                              self.atlas, self.frame, probe.id))
        self.slices.show_probes(self.atlas, self.frame, self.probes, self.selected_probe, fit=fit)
        selected_rows = [row for row in self.rows if row["probe"] == self.current_probe_id]
        self.probe_plane.set_context(self.atlas, self.frame, self.selected_probe, selected_rows,
                                     available_ids=self.available_region_ids)
        for probe in self.probes:
            rows = [row for row in self.rows if row["probe"] == probe.id]
            self.probe_summaries[probe.id].update_probe(probe, rows)
        self.refresh_enabled()
        if self.rows:
            outside = sum(row["region_id"] == -1 for row in self.rows)
            self.statusBar().showMessage(f"{len(self.rows)} sites · {outside} outside atlas")
        elif self.atlas:
            self.statusBar().showMessage("Atlas ready · + to import." if not self.probes else
                                        "Set Bregma to place probes in this atlas.")

    @guarded
    def reset_channel_selection(self):
        probe = self.selected_probe
        if probe is None or not is_neuropixels(probe.geometry) or self.channel_worker is not None:
            return
        probe.channel_map = ChannelMap(n_channels=384)
        self.recompute()
        self.probe_plane.reset_view()
        self.probe_summaries[probe.id].reset_view()
        self.slices.follow_tip()
        self.slices.set_view("Oblique")
        self.slices.plotter.render()
        self.setWindowModified(True)

    @guarded
    def remove_selection_roi(self, roi_id):
        probe = self.selected_probe
        if probe is None or self.channel_worker is not None:
            return
        probe.channel_map = remove_roi(probe.geometry, probe.channel_map, roi_id)
        self.recompute()
        self.setWindowModified(True)
        self.probe_plane.status.setText("ROI removed. Other channel assignments are unchanged.")

    @guarded
    def import_channel_map(self):
        probe = self.selected_probe
        if probe is None or not is_neuropixels(probe.geometry):
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Import Neuropixels channel selection", "",
            "Channel maps (*.imro *.json);;IMRO (*.imro);;Atlaxis selection (*.json)")
        if filename:
            path = Path(filename)
            source = path.read_text(encoding="utf-8")
            probe.channel_map = (import_selection(probe.geometry, source) if path.suffix.lower() == ".json"
                else import_imro(probe.geometry, source, probe.channel_map.blueprint))
            self.recompute()
            self.setWindowModified(True)

    @guarded
    def export_channel_map(self):
        probe = self.selected_probe
        if probe is None:
            return
        export_directory = self.save_path.parent if self.save_path else planning_path()
        if not is_neuropixels(probe.geometry):
            filename, _ = QFileDialog.getSaveFileName(self, "Export probe channels",
                str(export_directory / f"{probe.id}.csv"), "Channels CSV (*.csv)")
            if filename:
                path = Path(filename)
                if not path.suffix:
                    path = path.with_suffix(".csv")
                self.check_export_destination([path])
                if self.save_path and not self.save_project():
                    return
                export_contacts(path, [row for row in self.rows if row["probe"] == probe.id])
                self.statusBar().showMessage(f"Exported {path.name}")
            return
        filename, selected_filter = QFileDialog.getSaveFileName(self, "Export Neuropixels channel selection",
            str(export_directory / f"{probe.id}.imro"),
            "IMRO + selection (*.imro);;Selection JSON (*.json);;All channels CSV (*.csv)")
        if not filename:
            return
        suffix = ".json" if "JSON" in selected_filter else ".csv" if "CSV" in selected_filter else ".imro"
        path = Path(filename)
        if not path.suffix:
            path = path.with_suffix(suffix)
        if path.suffix.lower() != suffix:
            raise ValueError(f"Use the {suffix} extension for the selected export format.")
        active = active_site_ids(probe.geometry, probe.channel_map)
        files = prepare_channel_export(path, probe, self.rows)
        self.check_export_destination(files)
        companions_exist = any(file.exists() for file in files if file != path)
        if (suffix == ".imro" and len(active) < 384) or companions_exist:
            message = f"Selected targets: {len(active)}/384.\n"
            if suffix == ".imro":
                message += (f"IMRO will record {384 - len(active)} additional channels to fill 384 slots.\n"
                    "CSV includes all 384 channels; is_target marks your ROI selection.\n"
                    "Selection JSON restores only your chosen targets.\n")
            message += "Export updates these files together:\n" + "\n".join(file.name for file in files)
            if self.save_path:
                message += "\nThe open plan and its README will also be saved with the current selection."
            if question(self, "Export channel selection", message,
                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel) != QMessageBox.Ok:
                return
        if self.save_path and not self.save_project():
            return
        write_channel_export(files)
        count = 384 if suffix in (".imro", ".csv") else len(active)
        self.statusBar().showMessage(f"Exported {count} channels · {len(active)} targets · {path.name}")

    def check_export_destination(self, paths):
        if self.save_path is None:
            return
        reserved = {self.save_path.resolve()} | {
            (self.save_path.parent / name).resolve() for name in
            ("bundle_manifest.json", "README.txt", "planned_coordinates.csv", "channel_index.csv", "probes.xml")}
        if any(path.resolve() in reserved for path in paths):
            raise ValueError("Choose an export filename that does not replace a saved-plan file.")

    @guarded
    def generate_channels(self, roi_id):
        probe = self.selected_probe
        if probe is None or not is_neuropixels(probe.geometry) or self.channel_worker is not None:
            return
        if self.atlas is None or self.frame is None:
            raise ValueError("Load an atlas before selecting channels from brain regions.")
        existing = active_site_ids(probe.geometry, probe.channel_map)
        rois = [roi for roi in probe.channel_map.rois if roi.registered and not roi.assigned_sites
                and (roi_id is None or roi.id == roi_id)]
        if not rois:
            return
        if len(existing) == 384:
            self.probe_plane.status.setText("All 384 channels are assigned. Remove an ROI or Reset all to free channels.")
            return
        sites = {site for roi in rois for site in roi.sites}
        if not sites - existing:
            self.probe_plane.status.setText("These ROIs contain no new sites. Existing channels are unchanged.")
            return
        allowed_regions = brain_region_ids(self.atlas.structures)
        eligible = {row["contact_id"] for row in self.rows
                    if row["probe"] == probe.id and row["region_id"] in allowed_regions}
        if not (eligible & sites) - existing:
            self.probe_plane.status.setText("No new ROI sites are inside annotated tissue. Existing channels are unchanged.")
            return
        self.channel_previous_active = len(existing)
        self.channel_roi_snapshot = [asdict(roi) for roi in probe.channel_map.rois]
        self.channel_activation_ids = [roi.id for roi in rois]
        self.channel_target = (probe.id, id(probe.geometry), astuple(probe.pose), id(self.atlas),
                               repr(self.frame), id(probe.channel_map))
        self.channel_worker = ChannelSelector(probe.geometry, probe.channel_map, roi_id, eligible, self)
        message = ("Sharing free channels equally across ROIs; existing channels are locked…" if roi_id is None else
                   "Adding ROI channels with NeuroCarto; existing channels are locked…")
        self.channel_progress = QProgressDialog(message, "", 0, 0, self)
        self.channel_progress.setWindowTitle("Channel selection")
        self.channel_progress.setCancelButton(None)
        self.channel_progress.setWindowModality(Qt.WindowModal)
        self.channel_progress.show()
        self.channel_worker.selected.connect(self.channels_selected)
        self.channel_worker.failed.connect(lambda message: QMessageBox.critical(self, "Channel selection", message))
        self.channel_worker.finished.connect(self.channel_selection_finished)
        self.channel_worker.start()

    @guarded
    def channels_selected(self, mapping):
        probe = next((p for p in self.probes if p.id == self.channel_target[0]), None)
        if probe is None or self.channel_target != (probe.id, id(probe.geometry), astuple(probe.pose),
                                                    id(self.atlas), repr(self.frame), id(probe.channel_map)):
            return  # Never apply an obsolete result to another pose or atlas.
        if [asdict(roi) for roi in probe.channel_map.rois] != self.channel_roi_snapshot:
            return
        probe.channel_map = mapping
        self.recompute()
        self.setWindowModified(True)
        count = len(active_site_ids(probe.geometry, mapping))
        added = count - self.channel_previous_active
        counts = ", ".join(f"{roi.name}: {len(roi.assigned_sites)}" for roi in mapping.rois
                           if roi.id in self.channel_activation_ids)
        self.probe_plane.status.setText(f"Added {added} · {counts}. Existing channels preserved. " +
            ("No free hardware channels match these ROIs." if added == 0 else
             "Counts depend on available sites, density and shared hardware channels."))

    def channel_selection_finished(self):
        self.channel_progress.close()
        self.channel_progress.deleteLater()
        self.channel_worker.deleteLater()
        self.channel_worker = None

    @guarded
    def save_project(self, checked=False, *, save_as=False):
        if not all(x is not None for x in (self.atlas, self.frame, self.geometry, self.mapping)):
            raise ValueError("Load an atlas and geometry, then calibrate Bregma before saving a plan.")
        path = self.save_path
        if path is None or save_as:
            name = f"{path.parent.name}_copy.json" if path else "implant_plan.json"
            filename, _ = QFileDialog.getSaveFileName(self, "Save planning bundle (new name creates a folder)",
                str(planning_path() / name), "Implantation plan (*.json)")
            if not filename:
                return False
            path = Path(filename)
            if not path.suffix:
                path = path.with_suffix(".json")
            if path.suffix.lower() != ".json":
                raise ValueError("Use the .json extension for a plan.")
            if path != self.save_path:
                path = path.with_suffix("") / "plan.json"
                if path.parent.exists() and any(path.parent.iterdir()):
                    if question(self, "Replace planning bundle",
                            f"Update the plan and companion outputs in {path.parent}?",
                            QMessageBox.Save | QMessageBox.Cancel, QMessageBox.Cancel) != QMessageBox.Save:
                        return False
        save_planning_bundle(path,
            Plan.from_instances(self.atlas, self.frame, self.probes, self.current_probe_id), self.atlas, self.rows)
        self.save_path = path
        self.setWindowModified(False)
        self.statusBar().showMessage(f"Saved planning bundle · {path.parent}")
        return True

    @guarded
    def open_project(self, checked=False):
        filename, _ = QFileDialog.getOpenFileName(self, "Open implantation plan", str(planning_path()), "Plan (*.json)")
        if not filename:
            return
        plan = load_plan(Path(filename))
        if not self.discard_changes():
            return
        # Reject clipping; editing one control preserves all other stored values.
        if any(abs(getattr(probe.pose, field.name)) > 10000
               for probe in plan.probes for field in fields(ImplantPose)):
            raise ValueError("Project pose exceeds the supported numerical control range.")
        self.pending_plan, self.pending_path = plan, Path(filename)
        self.begin_load(plan.atlas_name, plan.atlas_version)

    def reset_camera(self, checked=False):
        self.slices.fit_views()

    def closeEvent(self, event):
        if self.busy or self.channel_worker is not None:
            self.statusBar().showMessage("Background work is still running. Close after it completes.")
            event.ignore()
        elif self.probe_plane.worker is not None:
            self.probe_plane.set_active(False)
            self.probe_plane.worker.finished.connect(self.close)
            self.statusBar().showMessage("Stopping the section worker…")
            event.ignore()
        else:
            self.probe_plane.set_active(False)
            if self.discard_changes():
                self.slices.plotter.close()
                event.accept()
            else:
                self.probe_plane.set_active(self.workspace_tabs.currentIndex() == 1)
                event.ignore()
