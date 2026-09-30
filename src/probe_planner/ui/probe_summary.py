"""Per-probe Geometry and Channel map tabs."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox, QPushButton)

from probe_planner.probes.neuropixels import is_neuropixels, active_site_ids, reference_description
from probe_planner.rendering.probe_view import ProbeView, ACTIVE_COLOR


class ProbeSummary(QWidget):
    selectRequested = Signal()
    importRequested = Signal()
    exportRequested = Signal()

    def __init__(self, probe):
        super().__init__()
        self.probe, self.rows = probe, []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 0)
        actions = QHBoxLayout()
        if is_neuropixels(probe.geometry):
            for label, tooltip, signal in (
                ("Select…", "Select atlas ranges in the probe plane and generate with NeuroCarto", self.selectRequested),
                ("Import", "Import an IMRO map or an Atlaxis selection JSON", self.importRequested),
            ):
                button = QPushButton(label)
                button.setToolTip(tooltip)
                button.clicked.connect(signal)
                actions.addWidget(button)
        self.export_button = QPushButton("Export")
        self.export_button.setToolTip("Manually export current channels; also update an already-saved plan and its README")
        self.export_button.clicked.connect(self.exportRequested)
        actions.addWidget(self.export_button)
        layout.addLayout(actions)
        self.reference_label = None
        if is_neuropixels(probe.geometry):
            self.reference_label = QLabel(f"Electrical reference: {reference_description(probe.geometry, probe.channel_map)}")
            self.reference_label.setWordWrap(True)
            self.reference_label.setToolTip(
                "IMRO reference IDs are separate from recording-channel IDs and the coordinate reference shank. "
                "ROI activation retains imported IMRO reference settings.")
            layout.addWidget(self.reference_label)
        tabs = QTabWidget()
        self.tabs = tabs
        layout.addWidget(tabs, 1)
        geometry = QWidget()
        geometry_layout = QVBoxLayout(geometry)
        geometry_layout.setContentsMargins(0, 0, 0, 0)
        self.view = ProbeView()
        geometry_layout.addWidget(self.view, 1)
        legend = QLabel("Magenta: active · Cyan edge: coordinate reference shank\nScroll to zoom · Hover for site / ch / region")
        legend.setWordWrap(True)
        geometry_layout.addWidget(legend)
        tabs.addTab(geometry, "Geometry")
        channel_page = QWidget()
        channel_layout = QVBoxLayout(channel_page)
        channel_layout.setContentsMargins(0, 0, 0, 0)
        self.active_only = QCheckBox("Active only")
        self.active_only.setChecked(is_neuropixels(probe.geometry))
        self.active_only.setVisible(is_neuropixels(probe.geometry))
        self.active_only.toggled.connect(self.fill_table)
        channel_layout.addWidget(self.active_only)
        self.table = QTableWidget(0, 3)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().hide()
        self.table.setWordWrap(False)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(40)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 90)
        self.table.setColumnWidth(1, 55)
        self.table.sortItems(0, Qt.AscendingOrder)
        channel_layout.addWidget(self.table, 1)
        tabs.addTab(channel_page, "Channel map")

    def update_probe(self, probe, rows):
        self.probe, self.rows = probe, rows
        active = len(active_site_ids(probe.geometry, probe.channel_map))
        self.export_button.setEnabled(active > 0 if is_neuropixels(probe.geometry) else bool(rows))
        if self.reference_label is not None:
            self.reference_label.setText(f"Electrical reference: {reference_description(probe.geometry, probe.channel_map)}")
        self.view.set_probe(probe, rows)
        self.fill_table()

    def fill_table(self, *_):
        table = self.table
        id_key = "device_channel" if self.probe.channel_map.contact_to_channel else "contact_id"
        table.setHorizontalHeaderLabels([
            "Channel ID" if id_key == "device_channel" else "Site ID", "Shank", "Region"])
        rows = [row for row in self.rows if row["active"] or not self.active_only.isChecked()]
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, key in enumerate((id_key, "shank", "region_acronym")):
                item = QTableWidgetItem()
                value = row[key]
                if key == "region_acronym" and value == "—":
                    value = "Outside" if row["region_id"] == -1 else "Unannotated" if row["region_id"] == 0 else "Unknown"
                item.setData(Qt.DisplayRole, "—" if value is None else value)
                item.setToolTip(f"Site: {row['contact_id']} · {row['region_name']} · " +
                                ("Active" if row["active"] else "Inactive"))
                if column == 0 and row["active"]:
                    color = QColor(ACTIVE_COLOR)
                    color.setAlphaF(0.5)
                    item.setForeground(color)
                table.setItem(row_index, column, item)
        table.setSortingEnabled(True)

    def reset_view(self):
        self.active_only.setChecked(is_neuropixels(self.probe.geometry))
        self.tabs.setCurrentIndex(0)
        self.view.fit()
