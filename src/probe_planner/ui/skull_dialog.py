"""Skull registration and dorsal craniotomy drawing controls."""

import base64
from copy import copy
from uuid import uuid4

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap, QPolygonF, QTransform
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel, QLineEdit,
    QAbstractItemView, QGraphicsItem, QHeaderView, QTableWidget, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from probe_planner.implant.skull import Craniotomy, Skull


def number(value=0, minimum=-10000, maximum=10000, suffix=" mm"):
    spin = QDoubleSpinBox()
    spin.setDecimals(3)
    spin.setRange(minimum, maximum)
    spin.setSingleStep(0.1)
    spin.setSuffix(suffix)
    spin.setValue(value)
    spin.setKeyboardTracking(False)
    return spin


class SkullDialog(QDialog):
    def __init__(self, skull, preview, parent=None, *, reference_skull=None):
        super().__init__(parent)
        self.setWindowTitle("Skull")
        self.skull = self.result_skull = skull
        self.preview = preview
        self.reference_skull = reference_skull
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.units = QComboBox()
        self.units.addItems(["mm", "µm"])
        row.addWidget(QLabel("File units"))
        row.addWidget(self.units)
        button = QPushButton("Import skull…")
        button.clicked.connect(self.import_mesh)
        row.addWidget(button)
        layout.addLayout(row)
        if reference_skull is not None:
            button = QPushButton("Use atlas reference")
            button.clicked.connect(self.use_reference)
            layout.addWidget(button)
        self.source = QLabel()
        self.source.setWordWrap(True)
        layout.addWidget(self.source)
        hint = QLabel("AP + anterior · ML + right · DV + ventral.\n"
                      "Importing a custom mesh replaces existing openings.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.controls = QWidget()
        form = QFormLayout(self.controls)
        self.size = number(100, 0.01, 10000, " %")
        self.size_label = QLabel("Skull scale")
        self.size.setToolTip("Scales the skull only about its origin; brain and probe coordinates are unchanged.")
        form.addRow(self.size_label, self.size)
        self.axes = []
        for native in "XYZ":
            combo = QComboBox()
            for label, axis in (("AP +", 1), ("AP −", -1), ("ML +", 2),
                                ("ML −", -2), ("DV +", 3), ("DV −", -3)):
                combo.addItem(label, axis)
            self.axes.append(combo)
            form.addRow(f"Native {native} points toward", combo)
        self.translation, self.rotation = [], []
        for axis in ("AP", "ML", "DV"):
            spin = number()
            self.translation.append(spin)
            form.addRow(f"{axis} translation", spin)
        for axis in ("AP", "ML", "DV"):
            spin = number(minimum=-180, maximum=180, suffix=" °")
            self.rotation.append(spin)
            form.addRow(f"Rotate about {axis}", spin)
        self.visible = QCheckBox("Show skull")
        form.addRow(self.visible)
        self.opacity = number(100, 0, 100, " %")
        form.addRow("Opacity", self.opacity)
        layout.addWidget(self.controls)
        actions = QHBoxLayout()
        button = QPushButton("Preview in 3D")
        button.clicked.connect(self.show_preview)
        actions.addWidget(button)
        button = QPushButton("Remove skull")
        button.clicked.connect(self.remove)
        actions.addWidget(button)
        layout.addLayout(actions)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.populate()

    def populate(self):
        self.controls.setEnabled(self.skull is not None)
        self.source.setText((self.skull.source_name +
                             (" · Approximate alignment / scale." if self.skull.reference_info else
                              " · Approximate shape for placement planning." if self.skull.approximate else ""))
                            if self.skull else "No skull loaded")
        if self.skull is None:
            return
        distance = self.skull.base_landmark_distance
        self.size_label.setText("Bregma–Lambda" if distance else "Skull scale")
        self.size.setSuffix(" mm" if distance else " %")
        self.size.setValue(self.skull.scale * (distance if distance else 100))
        for control, value in zip(self.axes, self.skull.axes):
            control.setCurrentIndex(control.findData(value))
        for controls, values in ((self.translation, self.skull.translation_mm),
                                 (self.rotation, self.skull.rotation_deg)):
            for control, value in zip(controls, values):
                control.setValue(value)
        self.visible.setChecked(self.skull.visible)
        self.opacity.setValue(self.skull.opacity * 100)

    def candidate(self):
        if self.skull is None:
            return None
        candidate = copy(self.skull)
        candidate.scale = self.size.value() / (self.skull.base_landmark_distance or 100)
        candidate.axes = tuple(control.currentData() for control in self.axes)
        candidate.translation_mm = tuple(control.value() for control in self.translation)
        candidate.rotation_deg = tuple(control.value() for control in self.rotation)
        candidate.visible = self.visible.isChecked()
        candidate.opacity = self.opacity.value() / 100
        candidate.validate_settings()
        return candidate

    def use_reference(self):
        self.skull = copy(self.reference_skull)
        self.skull.openings = []
        self.skull.visible = True
        self.skull.scale = 1.0
        self.skull.axes = (1, 2, 3)
        self.skull.rotation_deg = self.skull.translation_mm = (0.0, 0.0, 0.0)
        self.populate()

    def import_mesh(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import skull", "", "Skull surface (*.stl *.obj *.vtp)")
        if path:
            try:
                self.skull = Skull.read(path, self.units.currentText())
                self.populate()
            except Exception as error:
                QMessageBox.warning(self, "Cannot import skull", str(error))

    def show_preview(self):
        try:
            self.preview(self.candidate())
        except Exception as error:
            QMessageBox.warning(self, "Cannot preview skull", str(error))

    def accept(self):
        try:
            self.result_skull = self.candidate()
            self.preview(self.result_skull)
        except Exception as error:
            QMessageBox.warning(self, "Cannot place skull", str(error))
            return
        super().accept()

    def remove(self):
        self.result_skull = None
        super().accept()


def outline_path(shape, points, ml_sign=-1):
    path = QPainterPath()
    if not points:
        return path
    p = [QPointF(ml_sign * ml, -ap) for ap, ml in points]
    if shape == "Rectangle" and len(p) == 2:
        path.addRect(QRectF(p[0], p[1]).normalized())
    elif shape == "Circle" and len(p) == 2:
        radius = np.linalg.norm(np.asarray(points[1]) - points[0])
        path.addEllipse(p[0], radius, radius)
    else:
        path.moveTo(p[0])
        for point in p[1:]:
            path.lineTo(point)
        if len(p) >= 3:
            path.closeSubpath()
    return path


class OpeningView(QGraphicsView):
    edited = Signal()

    def __init__(self, skull, ml_sign):
        super().__init__()
        self.ml_sign = ml_sign
        self.setScene(QGraphicsScene(self))
        self.setMinimumSize(440, 330)
        self.setBackgroundBrush(QColor("#101216"))
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip("Left: draw · Right: move ROI · Middle: pan · Double-click: fit\n"
                        "Polygon: click first vertex or press Enter to finish. ML positive = left.")
        self.shape, self.points = "Rectangle", []
        self.anchor = self.pan = self.gesture = None
        self.polygon_finished = False
        self.navigated = False
        self.before_press = ([], False)
        self.other_items = []
        pen = QPen(QColor("#00eee2"), 2)
        pen.setCosmetic(True)
        self.path_item = self.scene().addPath(QPainterPath(), pen, QColor(0, 238, 226, 35))
        self.path_item.setZValue(2)
        self.set_surface(skull)

    def set_surface(self, skull):
        from probe_planner.rendering.skull_projection import dorsal_projection

        projection = skull.reference_info.get("dorsal_projection")
        # A cached projection is valid under uniform size/translation. For a
        # newly rotated custom placement, shade its actually placed triangles.
        if projection and tuple(skull.axes) == (1, 2, 3) and not any(skull.rotation_deg):
            image = QImage.fromData(base64.b64decode(projection["png_base64"]), "PNG")
            low = np.array(projection["bounds_mm"][:2]) * skull.scale
            high = np.array(projection["bounds_mm"][2:]) * skull.scale
            low += [skull.translation_mm[1], -skull.translation_mm[0]]
            high += [skull.translation_mm[1], -skull.translation_mm[0]]
        else:
            image, bounds = dorsal_projection(skull.source_mesh(display=True), pixels=900)
            low, high = np.array(bounds[:2]), np.array(bounds[2:])
        item = self.scene().addPixmap(QPixmap.fromImage(image))
        item.setTransform(QTransform(self.ml_sign * (high[0] - low[0]) / max(1, image.width() - 1),
                                     0, 0, (high[1] - low[1]) / max(1, image.height() - 1),
                                     self.ml_sign * low[0], low[1]))
        item.setOpacity(.72)
        item.setZValue(-1)
        bounds = item.sceneBoundingRect().adjusted(-.8, -.8, .8, .8)
        self.setSceneRect(bounds)
        for name, color in (("Bregma", "#ff7865"), ("Lambda", "#68bfff")):
            point = skull.landmark_points().get(name)
            if point is None:
                if name != "Bregma":
                    continue
                point = np.zeros(3)
            x, y = self.ml_sign * point[1], -point[0]
            marker = self.scene().addEllipse(-.075, -.075, .15, .15, QPen(QColor(color)), QColor(color))
            marker.setPos(x, y)
            marker.setZValue(4)
            label = self.scene().addSimpleText(name)
            label.setBrush(QColor(color))
            label.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            label.setPos(x + .18, y)
            label.setZValue(4)
        for text, x, y in (("A", bounds.center().x(), bounds.top()),
                           ("P", bounds.center().x(), bounds.bottom() - .3)):
            label = self.scene().addSimpleText(text)
            label.setBrush(QColor("#91a2b8"))
            label.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            label.setPos(x, y)

    def reset_view(self):
        self.navigated = False
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.centerOn(self.sceneRect().center())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.navigated:
            self.reset_view()

    def set_opening(self, shape, points, finished=True):
        self.shape, self.points = shape, [list(p) for p in points]
        self.polygon_finished = finished and len(points) >= 3
        self.anchor = self.gesture = None
        self.redraw()

    def redraw(self):
        self.path_item.setPath(outline_path(self.shape, self.points, self.ml_sign))

    def show_others(self, drafts, selected):
        for item in self.other_items:
            self.scene().removeItem(item)
        pen = QPen(QColor("#e7ac52"), 1)
        pen.setCosmetic(True)
        self.other_items = [self.scene().addPath(outline_path(d["shape"], d["points"], self.ml_sign), pen)
                            for i, d in enumerate(drafts) if i != selected]

    def coordinates(self, event):
        point = self.mapToScene(event.position().toPoint())
        return np.array([-point.y(), self.ml_sign * point.x()])

    def mousePressEvent(self, event):
        self.setFocus()
        self.before_press = ([p[:] for p in self.points], self.polygon_finished)
        if event.button() == Qt.MiddleButton:
            self.pan = event.position()
            event.accept()
            return
        point = self.coordinates(event)
        if event.button() == Qt.RightButton:
            if self.points:
                self.anchor, self.original = point, np.array(self.points)
                self.gesture = "move"
        elif event.button() == Qt.LeftButton:
            if self.shape == "Polygon":
                if self.polygon_finished:
                    self.points = []
                    self.polygon_finished = False
                first = (self.mapFromScene(QPointF(self.ml_sign * self.points[0][1], -self.points[0][0]))
                         if self.points else None)
                if len(self.points) >= 3 and (first - event.position().toPoint()).manhattanLength() <= 10:
                    self.polygon_finished = True
                else:
                    self.points.append(point.tolist())
            else:
                self.anchor, self.gesture = point, "draw"
                self.points = [point.tolist(), point.tolist()]
        else:
            return super().mousePressEvent(event)
        self.redraw()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.pan is not None:
            delta = event.position() - self.pan
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            self.pan = event.position()
            self.navigated = True
        elif self.anchor is not None:
            point = self.coordinates(event)
            self.points = ((self.original + point - self.anchor).tolist() if self.gesture == "move"
                           else [self.anchor.tolist(), point.tolist()])
            self.redraw()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.pan = None
        elif event.button() in (Qt.LeftButton, Qt.RightButton):
            self.anchor = self.gesture = None
            self.edited.emit()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.points, self.polygon_finished = self.before_press
        self.anchor = self.gesture = self.pan = None
        self.redraw()
        self.edited.emit()
        self.reset_view()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.shape == "Polygon":
            if len(self.points) >= 3:
                self.polygon_finished = True
                self.edited.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        factor = 1.06 ** (event.angleDelta().y() / 120)
        self.scale(factor, factor)
        self.navigated = True
        event.accept()


class CraniotomyDialog(QDialog):
    def __init__(self, skull, apply, parent=None, *, ml_sign=-1):
        super().__init__(parent)
        self.setWindowTitle("Make craniotomy")
        self.resize(960, 760)
        self.skull = skull
        self.apply_callback = apply
        self.current = -1
        self.loading = False
        self.drafts = [dict(id=o.id, name=o.name, shape=o.shape,
                            points=[list(p) for p in o.points_mm], finished=True) for o in skull.openings]
        root = QVBoxLayout(self)
        self.view = OpeningView(skull, ml_sign)
        self.view.edited.connect(self.geometry_edited)
        root.addWidget(self.view, 1)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Name", "Shape", "AP (mm)", "ML (mm)",
                                              "AP size (mm)", "ML size (mm)", "Diameter (mm)", ""])
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setMinimumHeight(135)
        self.table.setMaximumHeight(220)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 35)
        self.table.cellClicked.connect(lambda row, column: self.select(row))
        root.addWidget(self.table)
        actions = QHBoxLayout()
        add = QPushButton("+")
        add.setAutoDefault(False)
        add.setFixedWidth(36)
        add.setToolTip("Add craniotomy")
        add.clicked.connect(self.add)
        actions.addWidget(add)
        actions.addStretch()
        apply_button = QPushButton("Apply craniotomy")
        apply_button.setAutoDefault(False)
        apply_button.clicked.connect(self.apply)
        actions.addWidget(apply_button)
        root.addLayout(actions)
        self.rebuild_table()
        if self.drafts:
            self.select(0)
        else:
            self.add()
        QTimer.singleShot(0, self.view.reset_view)

    def rebuild_table(self):
        self.loading = True
        self.table.setRowCount(len(self.drafts))
        self.widgets = []
        for row, draft in enumerate(self.drafts):
            name = QLineEdit(draft["name"])
            name.textEdited.connect(lambda value, row=row: self.rename(row, value))
            shape = QComboBox()
            shape.addItems(["Rectangle", "Circle", "Polygon"])
            shape.setCurrentText(draft["shape"])
            shape.currentTextChanged.connect(lambda value, row=row: self.change_shape(row, value))
            widgets = [name, shape]
            for column in range(2, 7):
                spin = number(minimum=-10000 if column < 4 else .001, suffix="")
                spin.setToolTip("ML positive = anatomical left" if column == 3 else "Millimeters")
                spin.valueChanged.connect(lambda value, row=row, column=column: self.edit_geometry(row, column, value))
                widgets.append(spin)
            delete = QPushButton("×")
            delete.setAutoDefault(False)
            delete.setToolTip("Delete craniotomy")
            delete.clicked.connect(lambda checked=False, row=row: self.delete(row))
            widgets.append(delete)
            self.widgets.append(widgets)
            for column, widget in enumerate(widgets):
                self.table.setCellWidget(row, column, widget)
            self.sync_row(row)
        self.loading = False

    def sync_row(self, row):
        draft = self.drafts[row]
        points = np.asarray(draft["points"], dtype=float)
        center, sizes, diameter = np.zeros(2), np.ones(2), 1.
        if len(points):
            center = points[0].copy() if draft["shape"] == "Circle" else (points.min(axis=0) + points.max(axis=0)) / 2
            sizes = np.ptp(points, axis=0)
            if draft["shape"] == "Circle" and len(points) == 2:
                diameter = 2 * np.linalg.norm(points[1] - points[0])
        values = [center[0], -center[1], *sizes, diameter]
        for column, value in enumerate(values, 2):
            control = self.widgets[row][column]
            control.blockSignals(True)
            control.setValue(float(value))
            control.blockSignals(False)
            editable = (column < 4 or (draft["shape"] == "Circle" if column == 6 else draft["shape"] == "Rectangle"))
            control.setEnabled(editable and (draft["shape"] != "Polygon" or len(points) >= 3))

    def select(self, row):
        if self.loading or not 0 <= row < len(self.drafts):
            return
        self.current = row
        self.table.selectRow(row)
        draft = self.drafts[row]
        self.view.set_opening(draft["shape"], draft["points"], draft["finished"])
        self.view.show_others(self.drafts, row)

    def geometry_edited(self):
        if self.current < 0:
            return
        draft = self.drafts[self.current]
        draft["points"] = [p[:] for p in self.view.points]
        draft["finished"] = self.view.polygon_finished
        self.sync_row(self.current)

    def rename(self, row, value):
        self.drafts[row]["name"] = value

    def change_shape(self, row, shape):
        if self.loading:
            return
        self.drafts[row]["shape"] = shape
        self.drafts[row]["points"] = ([] if shape == "Polygon" else
                                         [[0., 0.], [0.5, 0.]] if shape == "Circle" else
                                         [[-.5, -.5], [.5, .5]])
        self.drafts[row]["finished"] = False
        self.sync_row(row)
        self.select(row)

    def edit_geometry(self, row, column, value):
        if self.loading:
            return
        draft = self.drafts[row]
        points = np.asarray(draft["points"], dtype=float)
        if not len(points):
            return
        shape = draft["shape"]
        if column < 4:
            axis = column - 2
            center = points[0] if shape == "Circle" else (points.min(axis=0) + points.max(axis=0)) / 2
            points[:, axis] += (value if axis == 0 else -value) - center[axis]
        elif shape == "Rectangle":
            axis = column - 4
            center = points[:, axis].mean()
            points[0, axis], points[1, axis] = center - value / 2, center + value / 2
        elif shape == "Circle":
            direction = points[1] - points[0]
            length = np.linalg.norm(direction)
            points[1] = points[0] + (direction / length if length else np.array([1., 0.])) * value / 2
        draft["points"] = points.tolist()
        self.sync_row(row)
        self.select(row)

    def add(self):
        number = 1
        names = {d["name"] for d in self.drafts}
        while f"Craniotomy {number}" in names:
            number += 1
        self.drafts.append(dict(id=uuid4().hex, name=f"Craniotomy {number}", shape="Rectangle",
                                points=[[-.5, -.5], [.5, .5]], finished=True))
        self.rebuild_table()
        self.select(len(self.drafts) - 1)

    def delete(self, row):
        del self.drafts[row]
        self.rebuild_table()
        if self.drafts:
            self.select(min(row, len(self.drafts) - 1))
        else:
            self.current = -1
            self.view.set_opening("Rectangle", [])
            self.view.show_others([], -1)

    def apply(self):
        try:
            openings = []
            for row, draft in enumerate(self.drafts):
                if draft["shape"] == "Polygon" and not draft["finished"]:
                    self.select(row)
                    raise ValueError(f"{draft['name']}: click the first vertex or press Enter to finish.")
                openings.append(Craniotomy(draft["id"], draft["name"], draft["shape"],
                                            [p[:] for p in draft["points"]]))
            candidate = copy(self.skull)
            candidate.openings = openings
            candidate.visible = True
            self.apply_callback(candidate)
            self.skull = candidate
            self.accept()
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Cannot apply craniotomy", str(error))
