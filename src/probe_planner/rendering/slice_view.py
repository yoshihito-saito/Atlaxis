"""Native atlas slices in one 3D scene, plus the local import preview."""

from collections import OrderedDict

import numpy as np
import pyvista as pv
from scipy.ndimage import binary_erosion
from PySide6.QtCore import QEvent, Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QFont, QImage, QShortcut, QKeySequence, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QToolTip,
    QGridLayout, QLabel, QSlider, QPushButton,
)
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingCore import vtkCellPicker, vtkPropAssembly

from probe_planner.atlas.sections import section_at, shank_tip_atlas_position
from .scene import Scene
from .navigation import NavigationInteractor


def anatomical_views(orientation):
    """Camera-side normals and upright directions in BrainGlobe atlas axes."""
    anterior = np.array([1 if c == "p" else -1 if c == "a" else 0 for c in orientation])
    right = np.array([1 if c == "l" else -1 if c == "r" else 0 for c in orientation])
    dorsal = np.array([1 if c == "i" else -1 if c == "s" else 0 for c in orientation])
    return {"Front": (anterior, dorsal), "Back": (-anterior, dorsal),
            "Right": (right, dorsal), "Left": (-right, dorsal),
            "Top": (dorsal, anterior), "Bottom": (-dorsal, anterior),
            "Oblique": (anterior + right + 0.7 * dorsal, dorsal)}


def section_rgba(section, mask_colors=None, mask_opacity=0.25):
    reference = np.asarray(section.reference, dtype=float)
    foreground = reference[reference > 0]
    low, high = np.percentile(foreground, [1, 99]) if foreground.size else (0, 1)
    gray = np.clip((reference - low) / max(high - low, 1), 0, 1)
    gray = (gray * 200).astype(np.uint8)
    rgba = np.empty((*gray.shape, 4), dtype=np.uint8)
    rgba[:, :, :3] = gray[:, :, None]
    labels = section.annotation
    mask = labels != 0
    rgba[:, :, 3] = np.where(mask, 255, 0)
    edges = np.zeros(mask.shape, dtype=bool)
    edges[1:] |= labels[1:] != labels[:-1]
    edges[:, 1:] |= labels[:, 1:] != labels[:, :-1]
    rgba[edges & mask, :3] = (103, 123, 145)
    rgba[mask & ~binary_erosion(mask), :3] = (163, 188, 224)
    if mask_colors and mask_opacity:
        # One lookup per pixel keeps the all-region overlay responsive without
        # rescanning the whole section separately for every region.
        region_ids, inverse = np.unique(labels, return_inverse=True)
        inverse = inverse.reshape(labels.shape)
        colors = np.array([mask_colors.get(int(region_id), (0, 0, 0))
                           for region_id in region_ids], dtype=np.uint8)
        known = np.array([int(region_id) in mask_colors for region_id in region_ids])
        selected = known[inverse] & mask
        rgba[selected, :3] = np.rint((1 - mask_opacity) * rgba[selected, :3]
                                     + mask_opacity * colors[inverse[selected]]).astype(np.uint8)
    return rgba


def section_mesh(section, resolution_um):
    """Map image columns/rows into atlas axes; distances are micrometers."""
    height, width = section.reference.shape
    points = np.zeros((4, 3))
    points[:, section.normal] = section.index * resolution_um[section.normal]
    points[:, section.horizontal] = np.array([0, width, width, 0]) * section.pixel_um[0]
    points[:, section.vertical] = np.array([0, 0, height, height]) * section.pixel_um[1]
    mesh = pv.PolyData(points, [4, 0, 1, 2, 3])
    # PyVista's numpy texture conversion flips image rows into VTK's bottom-up
    # texture convention. v=1 therefore represents row zero, not the last row.
    mesh.active_texture_coordinates = np.array([[0, 1], [1, 1], [1, 0], [0, 0]], dtype=float)
    return mesh


class SectionView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setBackgroundBrush(QColor("#101216"))
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.navigation_speed = 0.35
        self.pan_position = None
        self.pan_scroll = None
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.section = self.atlas = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if not delta:
            delta = event.pixelDelta().y()
        factor = 1.15 ** (delta / 120 * self.navigation_speed)
        zoom = self.transform().m11()
        if 1e-5 <= zoom * factor <= 10:
            self.scale(factor, factor)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pan_position = event.position()
            self.pan_scroll = [float(self.horizontalScrollBar().value()), float(self.verticalScrollBar().value())]
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pan_position = None
            self.unsetCursor()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.pan_position is not None:
            delta = event.position() - self.pan_position
            self.pan_position = event.position()
            for axis, (bar, distance) in enumerate(zip(
                    (self.horizontalScrollBar(), self.verticalScrollBar()), (delta.x(), delta.y()))):
                self.pan_scroll[axis] = min(bar.maximum(), max(bar.minimum(),
                    self.pan_scroll[axis] - distance * self.navigation_speed))
                bar.setValue(round(self.pan_scroll[axis]))
            QToolTip.hideText()
            event.accept()
            return
        super().mouseMoveEvent(event)
        item = self.itemAt(event.position().toPoint())
        if item is not None and item.toolTip():
            QToolTip.showText(event.globalPosition().toPoint(), item.toolTip(), self)
            return
        if self.section is None:
            return
        point = self.mapToScene(event.position().toPoint())
        x = int(np.floor(point.x() / self.section.pixel_um[0]))
        y = int(np.floor(point.y() / self.section.pixel_um[1]))
        if 0 <= y < self.section.annotation.shape[0] and 0 <= x < self.section.annotation.shape[1]:
            region_id = int(self.section.annotation[y, x])
            region = self.atlas.structures.get(region_id, {})
            QToolTip.showText(event.globalPosition().toPoint(),
                             f"{region.get('acronym', '—')} · {region.get('name', 'Unannotated')}", self)

    def fit(self):
        bounds = self.scene().itemsBoundingRect()
        if not bounds.isEmpty():
            margin = max(bounds.width(), bounds.height()) * 0.04
            bounds = bounds.adjusted(-margin, -margin, margin, margin)
            self.scene().setSceneRect(bounds)
            self.fitInView(bounds, Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene() is not None:
            self.fit()

    def drawForeground(self, painter, rect):
        # Import preview coordinates are micrometers. Keep the scale overlay
        # in viewport pixels so it never changes the scene bounds or fitting.
        scale = np.hypot(self.transform().m11(), self.transform().m12())
        if scale <= 0 or self.viewport().width() < 80:
            return
        target_um = min(120.0, self.viewport().width() / 3) / scale
        decade = 10.0 ** np.floor(np.log10(target_um))
        length_um = max(step for step in (1, 2, 5) if step <= target_um / decade) * decade
        length_px = length_um * scale
        label = f"{length_um / 1000:g} mm" if length_um >= 1000 else f"{length_um:g} µm"
        painter.save()
        painter.resetTransform()
        font = QFont(self.font())
        font.setPointSizeF(9)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        x, y = 18.0, float(self.viewport().height() - 18)
        width = max(length_px, painter.fontMetrics().horizontalAdvance(label))
        painter.fillRect(QRectF(x - 6, y - 30, width + 12, 40), QColor(16, 18, 22, 210))
        painter.setPen(QPen(QColor("#dce4ee"), 2))
        painter.drawText(QRectF(x, y - 28, width + 1, 20), Qt.AlignLeft | Qt.AlignVCenter, label)
        painter.drawLine(QPointF(x, y), QPointF(x + length_px, y))
        for end in (x, x + length_px):
            painter.drawLine(QPointF(end, y - 4), QPointF(end, y + 4))
        painter.restore()


class SliceWorkspace(QWidget):
    """One camera for region surfaces, orthogonal atlas planes and probes."""

    def __init__(self):
        super().__init__()
        self.cache = OrderedDict()
        self.atlas = None
        self.frame = None
        self.section_center = None
        self.selected_reference = None
        self.has_reference_tip = False
        self.section_indices = {}
        self.sections = {}
        self.section_actors = {}
        self.displayed_keys = {}
        self.mask_ids = set()
        self.mask_enabled = False
        self.mask_opacity = 0.25
        self.mask_colors = {}
        self.cube_widget = None
        self.cube_faces = {}
        self.cube_picker = vtkCellPicker()
        self.cube_picker.SetTolerance(0.001)
        self.visible_views = {name: True for name in ("Brain outline", "3D regions", "Coronal", "Sagittal")}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plotter = NavigationInteractor(self, auto_update=False)
        self.plotter.pick_orientation = self.pick_orientation
        self.plotter.home_view = lambda: self.set_view("Oblique")
        self.plotter.setFocusPolicy(Qt.StrongFocus)
        self.plotter.installEventFilter(self)
        layout.addWidget(self.plotter.interactor, 1)
        self.outline = Scene(self.plotter)
        self.plotter.enable_depth_peeling()
        self.section_timer = QTimer(self)
        self.section_timer.setSingleShot(True)
        self.section_timer.setInterval(30)
        self.section_timer.timeout.connect(self._refresh_sections)
        section_controls = QGridLayout()
        section_controls.setContentsMargins(4, 4, 4, 4)
        section_controls.setVerticalSpacing(4)
        self.section_sliders = {}
        self.section_labels = {}
        for row, name in enumerate(("Coronal", "Sagittal")):
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 0)
            slider.setEnabled(False)
            slider.valueChanged.connect(lambda index, name=name: self.set_section_index(name, index))
            label = QLabel("—")
            label.setMinimumWidth(90)
            section_controls.addWidget(QLabel(name), row, 0)
            section_controls.addWidget(slider, row, 1)
            section_controls.addWidget(label, row, 2)
            self.section_sliders[name] = slider
            self.section_labels[name] = label
        self.follow_tip_button = QPushButton("Follow tip")
        self.follow_tip_button.setEnabled(False)
        self.follow_tip_button.setToolTip("Return both sections to automatic following of the selected shank tip")
        self.follow_tip_button.clicked.connect(self.follow_tip)
        section_controls.addWidget(self.follow_tip_button, 0, 3, 2, 1)
        section_controls.setColumnStretch(1, 1)
        layout.addLayout(section_controls)
        self.section_shortcuts = []
        for key, name, step in ((Qt.Key_Left, "Sagittal", -1), (Qt.Key_Right, "Sagittal", 1),
                                (Qt.Key_Up, "Coronal", 1), (Qt.Key_Down, "Coronal", -1)):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            shortcut.activated.connect(lambda name=name, step=step: self.step_section(name, step))
            self.section_shortcuts.append(shortcut)

    def set_view_visible(self, name, visible):
        self.visible_views[name] = visible
        if name == "Brain outline":
            actor = self.outline.brain_outline_actor
        elif name == "3D regions":
            actor = self.outline.region_actor
        else:
            actor = self.section_actors.get(name)
        if actor is not None:
            actor.visibility = visible
        # Toggle a layer without hiding the shared canvas or moving the camera.
        self.plotter.render()

    def set_navigation_speed(self, speed):
        self.plotter.navigation_speed = speed
        style = self.plotter.iren.get_interactor_style()
        style.SetMotionFactor(10 * speed)
        style.SetMouseWheelMotionFactor(speed)

    def set_mask(self, region_ids, enabled, opacity, *, expand=True):
        self.mask_ids = set(region_ids)
        self.mask_enabled = enabled
        self.mask_opacity = opacity
        self.mask_colors = {}
        if self.atlas is not None and enabled:
            for region_id, region in self.atlas.structures.items():
                path = region.get("structure_id_path", [region_id])
                if region_id in self.mask_ids or (expand and self.mask_ids.intersection(path)):
                    self.mask_colors[region_id] = region.get("rgb_triplet", (229, 200, 136))
        self.cache.clear()
        self.displayed_keys.clear()

    def set_brain_outline(self, mesh):
        self.outline.set_brain_outline(mesh)
        self.outline.brain_outline_actor.visibility = self.visible_views["Brain outline"]

    def set_region_meshes(self, meshes, structures):
        self.outline.set_region_meshes(meshes, structures)
        if self.outline.region_actor is not None:
            self.outline.region_actor.visibility = self.visible_views["3D regions"]

    def fit_views(self):
        self.plotter.reset_camera()

    def show_probes(self, atlas, frame, probes, selected, fit=False):
        new_atlas = atlas is not self.atlas
        if new_atlas:
            self.cache.clear()
            self.displayed_keys.clear()
            self.atlas = atlas
            self.set_mask(set(), False, self.mask_opacity)
            if atlas is not None:
                self.set_orientation_markers(atlas.orientation)
            fit = True
        reference = (id(selected), selected.selected_shank_id) if selected is not None else None
        if new_atlas or reference != self.selected_reference:
            self.section_indices.clear()
        self.selected_reference = reference
        self.frame = frame
        self.has_reference_tip = selected is not None and frame is not None and atlas is not None
        self.section_center = None
        if atlas is not None:
            if self.has_reference_tip:
                self.section_center = shank_tip_atlas_position(selected, frame)
            else:
                self.section_center = np.asarray(atlas.annotation.shape) * np.asarray(atlas.resolution_um) / 2
        self._refresh_sections(render=False)
        # Atlas and probe positions share the same physical axes; no flattened
        # projected copies of the probe are added to the section planes.
        placed_probes = probes if atlas is not None and frame is not None else []
        if new_atlas and atlas is not None:
            self.orient_camera(atlas)
        self.outline.show_probes(placed_probes, selected, frame, fit)

    def set_section_index(self, name, index):
        if self.atlas is None:
            return
        self.section_indices[name] = index
        self.follow_tip_button.setEnabled(self.has_reference_tip)
        if not self.section_timer.isActive():
            self.section_timer.start()

    def step_section(self, name, direction):
        section = self.sections.get(name)
        if section is None:
            return
        # Atlas origin letters determine the sign of anatomical AP/ML travel.
        sign = 1 if self.atlas.orientation[section.normal] in "pl" else -1
        slider = self.section_sliders[name]
        slider.setValue(slider.value() + direction * sign)

    def follow_tip(self, checked=False):
        self.section_indices.clear()
        self._refresh_sections()

    def _refresh_sections(self, render=True):
        """Update only slice actors; manual browsing never remaps or moves probes."""
        self.section_timer.stop()
        atlas, frame, center = self.atlas, self.frame, self.section_center
        self.sections.clear()
        for name in ("Coronal", "Sagittal"):
            slider = self.section_sliders[name]
            slider.setEnabled(center is not None)
            if center is None:
                actor = self.section_actors.pop(name, None)
                if actor is not None:
                    self.plotter.remove_actor(actor, render=False)
                self.displayed_keys.pop(name, None)
                self.section_labels[name].setText("—")
                continue
            section = section_at(atlas, frame, center, name, slice_index=self.section_indices.get(name))
            self.sections[name] = section
            slider.blockSignals(True)
            slider.setRange(0, atlas.annotation.shape[section.normal] - 1)
            slider.setPageStep(max(1, slider.maximum() // 100))
            slider.setInvertedAppearance(atlas.orientation[section.normal] in "ar")
            slider.setInvertedControls(atlas.orientation[section.normal] in "ar")
            slider.setValue(section.index)
            slider.blockSignals(False)
            mode = "Manual slice" if name in self.section_indices else "Following tip" if self.has_reference_tip else "Atlas center"
            slider.setToolTip(f"{section.caption}\n{mode} · 1 step = {atlas.resolution_um[section.normal]:g} µm")
            self.section_labels[name].setText(section.caption.split(" · ")[1])
            key = (name, section.index)
            if key != self.displayed_keys.get(name):
                if key not in self.cache:
                    texture = pv.Texture(section_rgba(section, self.mask_colors, self.mask_opacity))
                    texture.interpolate = True
                    texture.repeat = False
                    self.cache[key] = texture
                    if len(self.cache) > 8:
                        self.cache.popitem(last=False)
                self.cache.move_to_end(key)
                mesh = section_mesh(section, atlas.resolution_um)
                if name not in self.section_actors:
                    self.section_actors[name] = self.plotter.add_mesh(
                        mesh, texture=self.cache[key], lighting=False, opacity=0.9,
                        reset_camera=False, render=False)
                else:
                    actor = self.section_actors[name]
                    actor.mapper.dataset = mesh
                    actor.SetTexture(self.cache[key])
                self.displayed_keys[name] = key
            self.section_actors[name].visibility = self.visible_views[name]
        self.plotter.interactor.setToolTip("\n".join(
            section.caption + " · " + section.axis_labels for section in self.sections.values())
            + "\nDouble-click: home · right-drag: pan · swipe / wheel / pinch: zoom at cursor"
            + "\nLeft / Right: sagittal · Up / Down: coronal")
        self.follow_tip_button.setEnabled(self.has_reference_tip and bool(self.section_indices))
        if render:
            self.plotter.reset_camera_clipping_range()
            self.plotter.render()

    def orient_camera(self, atlas):
        self.set_view("Oblique")

    def set_view(self, name):
        if self.atlas is None:
            return
        atlas = self.atlas
        direction, up = anatomical_views(atlas.orientation)[name]
        self.set_view_direction(direction, up)

    def set_view_direction(self, direction, up=None):
        if self.atlas is None:
            return
        atlas = self.atlas
        direction = np.asarray(direction, dtype=float)
        direction /= np.linalg.norm(direction)
        if up is None:
            views = anatomical_views(atlas.orientation)
            dorsal = views["Top"][0]
            up = views["Front"][0] if abs(np.dot(direction, dorsal)) > 0.999 else dorsal
        center = np.asarray(atlas.annotation.shape) * np.asarray(atlas.resolution_um) / 2
        extent = max(np.asarray(atlas.annotation.shape) * np.asarray(atlas.resolution_um))
        self.plotter.camera_position = (center + direction * extent, center, up)
        self.plotter.enable_parallel_projection()
        self.plotter.reset_camera()

    def set_orientation_markers(self, orientation):
        if self.cube_widget is not None:
            self.cube_widget.SetEnabled(False)
        cube = vtkPropAssembly()
        self.cube_faces = {}
        for name, (normal, up) in anatomical_views(orientation).items():
            if name == "Oblique":
                continue
            # Each label's x/y axes match its camera preset, including opposite
            # faces. This keeps the text upright and never mirrored head-on.
            basis = np.column_stack((np.cross(up, normal), up, normal))
            corners = np.array([[-0.5, -0.5, 0.5], [0.5, -0.5, 0.5],
                                [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]])
            face = pv.PolyData(corners @ basis.T, [4, 0, 1, 2, 3])
            actor = pv.Actor(mapper=pv.DataSetMapper(dataset=face))
            actor.prop.color = "#b3c4e0"
            actor.prop.lighting = False
            actor.prop.show_edges = True
            actor.prop.edge_color = "#53647d"
            cube.AddPart(actor)
            self.cube_faces[name] = actor
            # Texture text gives the cube a real bold sans-serif font instead
            # of VTK vector glyphs, while retaining an upright face-local basis.
            bitmap = QImage(320, 112, QImage.Format_RGBA8888)
            bitmap.fill(Qt.transparent)
            painter = QPainter(bitmap)
            painter.setRenderHint(QPainter.TextAntialiasing)
            font = QFont("Arial")
            font.setPixelSize(64)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#19212e"))
            painter.drawText(bitmap.rect(), Qt.AlignCenter, name.upper())
            painter.end()
            pixels = np.frombuffer(bitmap.bits(), dtype=np.uint8).reshape(112, 320, 4).copy()
            text_corners = np.array([[-0.45, -0.18, 0.501], [0.45, -0.18, 0.501],
                                     [0.45, 0.18, 0.501], [-0.45, 0.18, 0.501]])
            text = pv.PolyData(text_corners @ basis.T, [4, 0, 1, 2, 3])
            text.active_texture_coordinates = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
            label = pv.Actor(mapper=pv.DataSetMapper(dataset=text))
            texture = pv.Texture(pixels)
            texture.interpolate = True
            label.SetTexture(texture)
            label.prop.lighting = False
            label.pickable = False
            cube.AddPart(label)
        self.cube_widget = vtkOrientationMarkerWidget()
        self.cube_widget.SetOrientationMarker(cube)
        self.cube_widget.SetInteractor(self.plotter.iren.interactor)
        self.cube_widget.SetCurrentRenderer(self.plotter.renderer)
        self.resize_orientation_cube()
        self.cube_widget.SetEnabled(True)
        self.cube_widget.SetInteractive(False)

    def resize_orientation_cube(self, size=None):
        if self.cube_widget is None:
            return
        size = size or self.plotter.size()
        width, height = max(1, size.width()), max(1, size.height())
        side = min(144 * 0.8, width, height)
        self.cube_widget.SetViewport(1 - side / width, 1 - side / height, 1, 1)

    def eventFilter(self, watched, event):
        if watched is self.plotter:
            if event.type() == QEvent.Resize:
                self.resize_orientation_cube(event.size())
            elif event.type() == QEvent.MouseButtonPress:
                self.plotter.setFocus(Qt.MouseFocusReason)
        return super().eventFilter(watched, event)

    def pick_orientation(self, point):
        if self.cube_widget is None or not self.cube_widget.GetEnabled():
            return False
        # Qt uses logical top-left coordinates; VTK uses physical bottom-left.
        scale = self.plotter.devicePixelRatioF()
        x = round(point.x() * scale)
        y = round((self.plotter.height() - point.y() - 1) * scale)
        renderer = self.cube_widget.GetRenderer()
        if not renderer.IsInViewport(x, y) or not self.cube_picker.Pick(x, y, 0, renderer):
            return False
        path = self.cube_picker.GetPath()
        picked = path.GetLastNode().GetViewProp() if path else None
        for name, actor in self.cube_faces.items():
            if picked == actor:
                # Near an edge/corner, combine the corresponding atlas axes.
                # The middle 60% of each face keeps its cardinal view.
                hit = np.asarray(self.cube_picker.GetPickPosition())
                direction = np.where(np.abs(hit) >= 0.30, np.sign(hit), 0.0)
                self.set_view_direction(direction)
                return True
        return False
