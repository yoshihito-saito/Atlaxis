from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QMessageBox, QCheckBox,
    QVBoxLayout, QGraphicsItem, QComboBox,
)
from PySide6.QtGui import QColor, QPen, QBrush, QPolygonF
from PySide6.QtCore import QPointF, Qt, QSortFilterProxyModel
from html import escape
from pathlib import Path
import numpy as np

from probe_planner.rendering.slice_view import SectionView
from probe_planner.probes.wiring import headstage_map
from probe_planner.probes.mounting import with_package_base
from probe_planner.probes.neuropixels import is_neuropixels


class ProbeLibraryFilter(QSortFilterProxyModel):
    """Hide companion folders beneath the library's flat manufacturer folders."""

    def __init__(self, library_root, parent=None):
        super().__init__(parent)
        self.library_root = Path(library_root).resolve()

    def filterAcceptsRow(self, row, parent):
        model = self.sourceModel()
        index = model.index(row, 0, parent)
        if model.isDir(index):
            path = Path(model.filePath(index)).resolve()
            if path.parent.parent == self.library_root:
                return False
        return super().filterAcceptsRow(row, parent)


class HeadstageSelector(QComboBox):
    def set_probe(self, geometry, mapping):
        self.blockSignals(True)
        self.clear()
        profiles = geometry.metadata.get("headstage_profiles", []) if geometry else []
        fixed = geometry.metadata.get("headstage_fixed", False) if geometry else False
        if not fixed:
            self.addItem("Unassigned", None)
        for profile in profiles:
            self.addItem(profile["label"], profile["id"])
        if mapping and mapping.contact_to_channel and mapping.headstage_id is None:
            self.addItem("Saved wiring", "saved")
            selected = "saved"
        else:
            selected = mapping.headstage_id if mapping else None
        self.setCurrentIndex(self.findData(selected))
        self.setEnabled(bool(profiles) and not fixed)
        self.setToolTip("Select the actual package / headstage combination. Unassigned keeps physical Site IDs."
                        if profiles else "No verified headstage map is registered for this model.")
        self.blockSignals(False)


class ProbeImportDialog(QDialog):
    """Preview immutable imported data; only acceptance adds it to the plan."""

    def __init__(self, geometry, mapping, parent=None):
        super().__init__(parent)
        geometry = with_package_base(geometry, mapping)
        self.geometry, self.mapping = geometry, mapping
        self.imported_mapping = mapping
        self.setWindowTitle("Import probe")
        self.resize(650, 680)
        layout = QVBoxLayout(self)
        name = QLabel(geometry.name)
        name.setWordWrap(True)
        name.setObjectName("title")
        layout.addWidget(name)
        details = QFormLayout()
        details.addRow("Shanks", QLabel(str(len({c.shank_id for c in geometry.contacts}))))
        details.addRow("Sites", QLabel(str(len(geometry.contacts))))
        lengths = [np.ptp(np.asarray(body.outline_um)[:, 1]) / 1000 for body in geometry.display_bodies
                   if body.shank_id is not None]
        details.addRow("Shaft length", QLabel(", ".join(f"{value:.2f} mm" for value in sorted(set(lengths)))))
        thicknesses = sorted({body.thickness_um for body in geometry.display_bodies})
        self.thickness_label = QLabel(", ".join(f"{value:g} µm" for value in thicknesses))
        details.addRow("Thickness", self.thickness_label)
        self.headstage = HeadstageSelector()
        self.headstage.set_probe(geometry, mapping)
        if geometry.metadata.get("headstage_profiles"):
            details.addRow(geometry.metadata.get("connection_label", "Headstage"), self.headstage)
        else:
            self.headstage.hide()
        layout.addLayout(details)
        self.preview = SectionView()
        self.preview.setToolTip("Local front view · scroll to zoom, drag to pan")
        # Use local x/y, including the supplied shaft direction, not an atlas transform.
        scene = self.preview.scene()
        self.body_items = []
        self.update_bodies()
        self.contact_markers = []
        for contact in geometry.contacts:
            color = QColor("#88cce5" if contact.z_um > 0 else "#e5c888")
            marker = scene.addEllipse(-2.5, -2.5, 5, 5, QPen(color), QBrush(color))
            marker.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            marker.setPos(contact.x_um, -geometry.y_to_base * contact.y_um)
            marker.setToolTip(f"{contact.contact_id} · Shank {contact.shank_id}\n"
                              f"Local z: {contact.z_um:g} µm\n"
                              f"Channel: {mapping.contact_to_channel.get(contact.contact_id, 'unassigned')}")
            self.contact_markers.append((contact, marker))
        self.headstage.currentIndexChanged.connect(self.change_headstage)
        layout.addWidget(self.preview, 1)
        self.wiring_status = QLabel()
        self.wiring_status.setTextFormat(Qt.PlainText)
        self.wiring_status.setWordWrap(True)
        layout.addWidget(self.wiring_status)
        reminder = QLabel("Before each use, verify Channel ID ↔ physical Site against the manufacturer’s "
                          "documents for your probe revision, headstage and adapter. Check the recording "
                          "software’s numbering and channel order.")
        reminder.setWordWrap(True)
        layout.addWidget(reminder)
        self.wiring_sources = QLabel()
        self.wiring_sources.setTextFormat(Qt.RichText)
        self.wiring_sources.setOpenExternalLinks(True)
        self.wiring_sources.setWordWrap(True)
        layout.addWidget(self.wiring_sources)
        self.update_wiring_status()
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.import_button = buttons.addButton("Import", QDialogButtonBox.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_bodies(self):
        scene = self.preview.scene()
        for item in self.body_items:
            scene.removeItem(item)
        self.body_items = []
        for body in self.geometry.display_bodies:
            polygon = QPolygonF([QPointF(float(x), float(-self.geometry.y_to_base * y))
                                 for x, y, _ in body.outline_um])
            pen = QPen(QColor("#9ab8eb"), 1.2)
            pen.setCosmetic(True)
            item = scene.addPolygon(polygon, pen, QBrush(QColor("#33435e")))
            item.setZValue(-1)
            self.body_items.append(item)
        thicknesses = sorted({body.thickness_um for body in self.geometry.display_bodies})
        self.thickness_label.setText(", ".join(f"{value:g} µm" for value in thicknesses))

    def change_headstage(self, index):
        profile_id = self.headstage.itemData(index)
        if profile_id == "saved":
            self.mapping = self.imported_mapping
        else:
            self.mapping = headstage_map(self.geometry, profile_id)
        geometry = with_package_base(self.geometry, self.mapping)
        if geometry is not self.geometry:
            self.geometry = geometry
            self.update_bodies()
        for contact, marker in self.contact_markers:
            marker.setToolTip(f"{contact.contact_id} · Shank {contact.shank_id}\n"
                              f"Local z: {contact.z_um:g} µm\n"
                              f"Channel: {self.mapping.contact_to_channel.get(contact.contact_id, 'unassigned')}")
        self.update_wiring_status()

    def update_wiring_status(self):
        profiles = self.geometry.metadata.get("headstage_profiles", [])
        profile = next((p for p in profiles if p["id"] == self.mapping.headstage_id), None)
        if profile is not None:
            text = profile.get("note", "")
        elif is_neuropixels(self.geometry):
            text = "Recording channels follow the active channel map / IMRO selected after import."
        elif self.mapping.contact_to_channel:
            text = self.geometry.metadata.get(
                "channel_map_note", "Using the supplied channel map; verify it against your actual connection.")
        elif profiles:
            text = "Wiring unassigned. Choose your connection above; otherwise only physical Site IDs are available."
        else:
            text = ("Recording-channel wiring is not supported for this model / connection. "
                    "Geometry remains available with physical Site IDs.")
            reason = self.geometry.metadata.get("wiring_unavailable_reason", "")
            if reason:
                text += " " + reason
        self.wiring_status.setText(text)
        self.wiring_status.setVisible(bool(text))
        reference = profile or (profiles[0] if profiles else {})
        sources = [("Probe map", reference.get("source_url")),
                   ("Headstage pinout", reference.get("headstage_source_url")),
                   ("Adapter map", reference.get("adapter_source_url"))]
        if not profiles and self.geometry.metadata.get("manufacturer") == "Cambridge NeuroTech":
            sources = [("Manufacturer maps", "https://www.cambridgeneurotech.com/neural-probes/probe-maps")]
        if not profiles and self.geometry.metadata.get("manufacturer") == "NeuroNexus":
            count = len(self.geometry.contacts)
            sources = [("Manufacturer maps", f"https://www.neuronexus.com/product_documentation/{count}-channel-package/")]
        links = [f'<a href="{escape(url, quote=True)}">{label}</a>'
                 for label, url in sources if isinstance(url, str) and url.startswith("https://")]
        self.wiring_sources.setText(" · ".join(links))
        self.wiring_sources.setVisible(bool(links))

    def showEvent(self, event):
        super().showEvent(event)
        self.preview.fit()


class CoordinateDialog(QDialog):
    def __init__(self, title, explanation, labels, values=None, probe=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(480, 260)
        self.values = None
        layout = QFormLayout(self)
        text = QLabel(explanation)
        text.setWordWrap(True)
        layout.addRow(text)
        self.fields = []
        for index, label in enumerate(labels):
            edit = QLineEdit("" if values is None else str(values[index]))
            edit.setPlaceholderText("Required, in µm")
            layout.addRow(label, edit)
            self.fields.append(edit)
        self.direction = QCheckBox("Local +y points toward the probe base")
        self.direction.setChecked(True)
        if probe:
            layout.addRow(self.direction)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def validate(self):
        try:
            values = tuple(float(field.text()) for field in self.fields)
            if not np.isfinite(values).all():
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Coordinates required", "Enter three finite coordinates in µm.")
            return
        self.values = values
        self.accept()
