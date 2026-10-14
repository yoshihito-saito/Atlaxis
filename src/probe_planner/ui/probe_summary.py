"""Per-probe Geometry and Channel map tabs."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox, QPushButton)

from probe_planner.probes.neuropixels import (
    is_neuropixels, active_site_ids, reference_description, site_channel_ids, import_imro,
)
from probe_planner.rendering.probe_view import ProbeView, ACTIVE_COLOR, AVAILABLE_COLOR


class ProbeSummary(QWidget):
    selectRequested = Signal()
    importRequested = Signal()
    exportRequested = Signal()
    siteToggled = Signal(str, bool)

    def __init__(self, probe):
        super().__init__()
        self.probe, self.rows = probe, []
        self.site_channels = site_channel_ids(probe.geometry) if is_neuropixels(probe.geometry) else {}
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
        self.view.site_channels = self.site_channels
        self.view.siteToggled.connect(self.siteToggled)
        geometry_layout.addWidget(self.view, 1)
        if self.site_channels:
            self.view.setToolTip("Scroll to zoom · Drag to pan · Double-click a site to turn ON/OFF · Double-click background to fit")
        legend = QLabel(
            "Magenta: active · Green: can activate · Gray: blocked\n"
            "Double-click a site to turn ON/OFF · Hover for Site ID / region\n"
            "Cyan edge: coordinate reference shank · Scroll to zoom" if self.site_channels else
            "Magenta: active · Cyan edge: coordinate reference shank\nScroll to zoom · Hover for site / ch / region")
        legend.setWordWrap(True)
        geometry_layout.addWidget(legend)
        tabs.addTab(geometry, "Geometry")
        channel_page = QWidget()
        channel_layout = QVBoxLayout(channel_page)
        channel_layout.setContentsMargins(0, 0, 0, 0)
        self.show_alternatives = QCheckBox("Show alternative sites")
        self.show_alternatives.setVisible(bool(self.site_channels))
        self.show_alternatives.setToolTip(
            "Show physical site candidates. Multiple sites may route to the same hardware channel; "
            "only one can be ON at a time.")
        self.show_alternatives.toggled.connect(self.fill_table)
        channel_layout.addWidget(self.show_alternatives)
        self.active_only = QCheckBox("Active / available only")
        self.active_only.setChecked(is_neuropixels(probe.geometry))
        self.active_only.setVisible(False)
        self.active_only.toggled.connect(self.fill_table)
        channel_layout.addWidget(self.active_only)
        if self.site_channels:
            hint = QLabel("Current sites: check ON/OFF to edit.\n"
                          "Show alternative sites to change its physical electrode. Green: can turn ON.\n"
                          "Blocked: turn OFF the site using the same channel first.")
            hint.setWordWrap(True)
            channel_layout.addWidget(hint)
        self.table = QTableWidget(0, 6 if self.site_channels else 4)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().hide()
        self.table.setWordWrap(False)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(40)
        if self.site_channels:
            for column, width in enumerate((50, 45, 120, 55)):
                header.setSectionResizeMode(column, QHeaderView.Fixed)
                self.table.setColumnWidth(column, width)
            header.setSectionResizeMode(4, QHeaderView.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        else:
            for column, width in enumerate((50, 90, 55)):
                header.setSectionResizeMode(column, QHeaderView.Fixed)
                self.table.setColumnWidth(column, width)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.sortItems(0, Qt.AscendingOrder)
        self.table.itemChanged.connect(self.channel_item_changed)
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
        alternatives = self.site_channels and self.show_alternatives.isChecked()
        self.active_only.setVisible(bool(alternatives))
        selected = active_site_ids(self.probe.geometry, self.probe.channel_map)
        occupied = {self.probe.channel_map.contact_to_channel[site]: site for site in selected} if self.site_channels else {}
        id_key = "device_channel" if self.probe.channel_map.contact_to_channel else "contact_id"
        keys = ("order", "on", "contact_id", "shank", "region_acronym", "status") if self.site_channels else (
            "order", id_key, "shank", "region_acronym")
        table.blockSignals(True)
        table.setHorizontalHeaderLabels(["Order", "ON", "Site ID", "Shank", "Region", "Status"]
            if self.site_channels else ["Order", "Channel ID" if id_key == "device_channel" else "Site ID", "Shank", "Region"])
        if self.site_channels and not alternatives:
            # The complete acquisition template keeps the routed OFF site visible
            # without expanding a free channel into every possible physical input.
            mapping = self.probe.channel_map
            current_sites = set(import_imro(self.probe.geometry, mapping.source_imro, {}).contact_to_channel
                                if mapping.source_imro is not None else mapping.contact_to_channel)
            rows = [row for row in self.rows if row["contact_id"] in current_sites]
        else:
            rows = [row for row in self.rows if not self.active_only.isChecked() or row["contact_id"] in selected
                    or (self.site_channels and self.site_channels[row["contact_id"]] not in occupied)]
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            site = row["contact_id"]
            active = site in selected
            channel = self.site_channels[site] if self.site_channels else row["device_channel"]
            available = self.site_channels and channel not in occupied
            status = "ON" if active else "OFF"
            if alternatives and not active:
                status = "Available" if available else "Blocked"
            tooltip = f"Site: {site} · {row['region_name']} · " + (status if self.site_channels else "Active")
            if self.site_channels and not active and not available:
                tooltip += f"\nChannel {channel} is ON at {occupied[channel]}. Turn that site OFF first."
            for column, key in enumerate(keys):
                item = QTableWidgetItem()
                if key == "on":
                    item.setData(Qt.UserRole, site)
                    item.setFlags(Qt.ItemIsSelectable | (Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
                                                        if active or available else Qt.NoItemFlags))
                    item.setCheckState(Qt.Checked if active else Qt.Unchecked)
                    item.setToolTip(tooltip)
                    table.setItem(row_index, column, item)
                    continue
                value = row_index if key == "order" else status if key == "status" else row[key]
                if key == "region_acronym" and value == "—":
                    value = "Outside" if row["region_id"] == -1 else "Unannotated" if row["region_id"] == 0 else "Unknown"
                item.setData(Qt.DisplayRole, "—" if value is None else value)
                item.setToolTip(tooltip)
                if active and key in ("device_channel", "contact_id", "status"):
                    color = QColor(ACTIVE_COLOR)
                    color.setAlphaF(0.5)
                    item.setForeground(color)
                elif available and key in ("device_channel", "contact_id", "status"):
                    item.setForeground(QColor(AVAILABLE_COLOR))
                table.setItem(row_index, column, item)
        table.setSortingEnabled(True)
        table.blockSignals(False)

    def channel_item_changed(self, item):
        if self.site_channels and item.column() == 1:
            self.siteToggled.emit(item.data(Qt.UserRole), item.checkState() == Qt.Checked)

    def reset_view(self):
        self.show_alternatives.setChecked(False)
        self.active_only.setChecked(is_neuropixels(self.probe.geometry))
        self.tabs.setCurrentIndex(0)
        self.view.fit()
