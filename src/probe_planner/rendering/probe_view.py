"""Zoomable physical probe drawing shared by Geometry and the oblique section."""

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPen, QPolygonF, QImage, QPixmap
from PySide6.QtWidgets import QToolTip, QGraphicsView

from probe_planner.probes.neuropixels import active_site_ids
from .slice_view import SectionView


ACTIVE_COLOR = "#ff19ef"
REFERENCE_COLOR = "#00fff0"


class ProbeView(SectionView):
    sitesSelected = Signal(object, object)
    selectionStarted = Signal()

    def __init__(self, *, labels=True):
        super().__init__()
        self.navigation_speed = 1.0
        self.probe = None
        self.rows = {}
        self.active_sites = set()
        self.uv = np.empty((0, 2))
        self.shank_centers = {}
        self.bounds = QRectF()
        self.image_bounds = None
        self.labels = labels
        self.draw_selection = False
        self.selection_start = self.selection_rect = None
        self.roi_rects = []
        self.face_z = None
        self.setMinimumWidth(180)
        self.setToolTip("Scroll to zoom · Drag to pan · Double-click to fit")
        # Hover is handled here, so Qt's cached AnchorUnderMouse position is stale.
        self.setTransformationAnchor(QGraphicsView.NoAnchor)

    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.pixelDelta().y()
        factor = 1.15 ** (delta / 120 * self.navigation_speed)
        if not 1e-5 <= self.transform().m11() * factor <= 10:
            event.accept()
            return
        position = event.position()
        anchor = self.viewportTransform().inverted()[0].map(position)
        # Leave room around the content so scene-edge scrollbar clamping cannot
        # move the anchor when zooming out or near a corner of the image.
        visible = self.mapToScene(self.viewport().rect()).boundingRect()
        margin = max(visible.width(), visible.height()) / min(factor, 1.0)
        self.setSceneRect(self.sceneRect().united(visible.adjusted(-margin, -margin, margin, margin)))
        self.scale(factor, factor)
        shifted = self.viewportTransform().inverted()[0].map(position)
        self.translate(shifted.x() - anchor.x(), shifted.y() - anchor.y())
        event.accept()

    def set_probe(self, probe, rows, *, fit=False):
        changed = self.probe is None or probe is None or self.probe.id != probe.id or self.probe.geometry is not probe.geometry
        self.probe = probe
        self.rows = {row["contact_id"]: row for row in rows}
        self.active_sites = active_site_ids(probe.geometry, probe.channel_map) if probe else set()
        if probe is None:
            self.uv = np.empty((0, 2))
            self.bounds = QRectF()
        else:
            geometry = probe.geometry
            self.uv = geometry.points[:, :2] * (1, -geometry.y_to_base)
            self.shank_centers = {}
            for shank in {c.shank_id for c in geometry.contacts}:
                xs = self.uv[[c.shank_id == shank for c in geometry.contacts], 0]
                self.shank_centers[shank] = (xs.min() + xs.max()) / 2
            vertices = [self.uv] + [np.asarray(body.outline_um)[:, :2] * (1, -geometry.y_to_base)
                                     for body in geometry.display_bodies]
            points = np.concatenate(vertices)
            low, high = points.min(axis=0), points.max(axis=0)
            self.bounds = QRectF(QPointF(*low), QPointF(*high)).adjusted(-200, -100, 200, 100)
        self.scene().setSceneRect(self.bounds.united(self.image_bounds or QRectF()))
        if fit or changed:
            self.fit()
        self.viewport().update()

    def set_section_image(self, section, rgba, atlas):
        self.scene().clear()
        self.section, self.atlas = section, atlas
        self.image_bounds = None
        self.face_z = None
        if section is not None:
            height, width = rgba.shape[:2]
            image = QImage(rgba.data, width, height, rgba.strides[0], QImage.Format_RGBA8888).copy()
            item = self.scene().addPixmap(QPixmap.fromImage(image))
            item.setScale(section.pixel_um[0])
            item.setPos(*section.origin_uv)
            self.image_bounds = item.sceneBoundingRect()
            self.face_z = section.face_z_um
        self.scene().setSceneRect(self.bounds.united(self.image_bounds or QRectF()))
        self.viewport().update()

    def fit(self):
        bounds = self.image_bounds or self.bounds
        if not bounds.isEmpty():
            self.setSceneRect(bounds.adjusted(-bounds.width(), -bounds.height(), bounds.width(), bounds.height()))
            self.fitInView(bounds, Qt.KeepAspectRatio)

    def drawForeground(self, painter, rect):
        if self.probe is None:
            return
        geometry = self.probe.geometry
        zoom = max(self.transform().m11(), 1e-8)
        for body in geometry.display_bodies:
            polygon = QPolygonF([QPointF(x, -geometry.y_to_base * y) for x, y, _ in body.outline_um])
            selected = body.shank_id == self.probe.selected_shank_id
            pen = QPen(QColor(REFERENCE_COLOR if selected else "#85919e"))
            pen.setWidthF(1.0 if selected else 0.7)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(112, 128, 144, 25 if self.section is not None else 90))
            painter.drawPolygon(polygon)
        visible = ((self.uv[:, 0] >= rect.left() - 200) & (self.uv[:, 0] <= rect.right() + 200)
                   & (self.uv[:, 1] >= rect.top()) & (self.uv[:, 1] <= rect.bottom()))
        labels = []
        for index in np.flatnonzero(visible):
            contact = geometry.contacts[index]
            row = self.rows.get(contact.contact_id, {})
            channel = self.probe.channel_map.contact_to_channel.get(contact.contact_id)
            active = contact.contact_id in self.active_sites
            point = QPointF(*self.uv[index])
            radius = max(3.5 if active else 5.0, (1.6 if active else 1.2) / zoom)
            painter.setPen(Qt.NoPen)
            color = QColor(ACTIVE_COLOR if active else "#78818f")
            if active:
                color.setAlphaF(0.5)
            painter.setBrush(color)
            painter.drawEllipse(point, radius, radius)
            category = self.probe.channel_map.blueprint.get(contact.contact_id)
            if not self.labels and category and category != "Low":
                color = QColor("#ffd166" if category != "Excluded" else "#8a8a8a")
                color.setAlphaF(0.5)
                pen = QPen(color)
                pen.setCosmetic(True)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(QRectF(point.x() - radius, point.y() - radius, 2 * radius, 2 * radius))
            if self.labels and (active or not self.probe.channel_map.contact_to_channel):
                region = row.get("region_acronym", "—")
                label = (f"ch {channel} · {region}" if channel is not None
                         else f"{contact.contact_id} · {region}")
                labels.append((point, label, active, contact.shank_id, contact.x_um))
        for bounds, registered, selected in self.roi_rects:
            pen = QPen(QColor("#00fff0" if registered else "#ffd166"), 0,
                       Qt.SolidLine if registered else Qt.DashLine)
            pen.setCosmetic(True)
            pen.setWidthF(1.3 if selected else 0.7)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(bounds)
        if self.selection_rect is not None:
            pen = QPen(QColor("#ffd166"), 0, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(QColor(255, 209, 102, 25))
            painter.drawRect(self.selection_rect)
        # Fixed-size labels, culled on overlap. Zoom reveals all nearby channels;
        # a low-zoom full-shaft view is not overwhelmed by thousands of strings.
        transform = painter.worldTransform()
        painter.save()
        painter.resetTransform()
        painter.setFont(QFont("Helvetica Neue", 9))
        metrics = painter.fontMetrics()
        occupied = []
        for point, label, active, shank, x in labels:
            position = transform.map(point)
            width = metrics.horizontalAdvance(label)
            left = x < self.shank_centers[shank]
            label_rect = QRectF(position.x() - width - 9 if left else position.x() + 9,
                                position.y() - metrics.height() / 2, width, metrics.height())
            if any(label_rect.intersects(other) for other in occupied):
                continue
            occupied.append(label_rect.adjusted(-3, -2, 3, 2))
            color = QColor(ACTIVE_COLOR if active else "#abb4c2")
            if active:
                color.setAlphaF(0.5)
            painter.setPen(color)
            painter.drawText(label_rect, Qt.AlignVCenter, label)
        painter.restore()

    def mouseDoubleClickEvent(self, event):
        self.fit()
        event.accept()

    def mousePressEvent(self, event):
        if self.draw_selection and event.button() == Qt.LeftButton:
            self.selectionStarted.emit()
            self.selection_start = self.mapToScene(event.position().toPoint())
            self.selection_rect = QRectF(self.selection_start, self.selection_start)
            event.accept()
        elif event.button() == Qt.RightButton:
            self.pan_position = event.position()
            self.pan_scroll = [float(self.horizontalScrollBar().value()), float(self.verticalScrollBar().value())]
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.selection_start is not None and event.button() == Qt.LeftButton:
            rectangle = QRectF(self.selection_start, self.mapToScene(event.position().toPoint())).normalized()
            sites = [contact.contact_id for contact, uv in zip(self.probe.geometry.contacts, self.uv)
                     if rectangle.contains(QPointF(*uv))] if self.probe else []
            self.selection_start = self.selection_rect = None
            self.sitesSelected.emit(sites, [rectangle.left(), rectangle.top(), rectangle.right(), rectangle.bottom()])
            self.viewport().update()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.pan_position = None
            self.unsetCursor()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        point = self.mapToScene(event.position().toPoint())
        if self.selection_start is not None:
            self.selection_rect = QRectF(self.selection_start, point).normalized()
            self.viewport().update()
            return
        if self.pan_position is not None:
            super().mouseMoveEvent(event)
            return
        if self.probe and len(self.uv):
            distances = np.sum((self.uv - (point.x(), point.y())) ** 2, axis=1)
            index = int(np.argmin(distances))
            if distances[index] <= (10 / max(self.transform().m11(), 1e-8)) ** 2:
                contact = self.probe.geometry.contacts[index]
                row = self.rows.get(contact.contact_id, {})
                channel = self.probe.channel_map.contact_to_channel.get(contact.contact_id)
                active = contact.contact_id in self.active_sites
                text = (f"{contact.contact_id} · Shank {contact.shank_id}\n"
                        f"{'Active' if active else 'Inactive'} · Channel {channel if channel is not None else '—'}\n"
                        f"{row.get('region_acronym', '—')} · {row.get('region_name', 'Atlas not loaded')}")
                if self.face_z is not None:
                    text += f"\nDistance from displayed plane: {abs(contact.z_um - self.face_z):.2f} µm"
                category = self.probe.channel_map.blueprint.get(contact.contact_id, "Low")
                QToolTip.showText(event.globalPosition().toPoint(), text + f"\nSelection: {category}", self)
                return
        if self.section is not None:
            x, y = np.floor((np.array([point.x(), point.y()]) - self.section.origin_uv) / self.section.pixel_um).astype(int)
            if 0 <= y < self.section.annotation.shape[0] and 0 <= x < self.section.annotation.shape[1]:
                region = self.atlas.structures.get(int(self.section.annotation[y, x]), {})
                QToolTip.showText(event.globalPosition().toPoint(),
                    f"{region.get('acronym', '—')} · {region.get('name', 'Unannotated')}", self)
                return
        QToolTip.hideText()
