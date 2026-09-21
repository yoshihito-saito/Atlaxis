"""Camera navigation for mouse and macOS trackpad input."""

import numpy as np
from PySide6.QtCore import QEvent, Qt
from pyvistaqt import QtInteractor


class NavigationInteractor(QtInteractor):
    def __init__(self, *args, **kwargs):
        self.navigation_speed = 1.0
        self.pan_position = None
        self.pick_orientation = None
        self.home_view = None
        self.orientation_pressed = False
        super().__init__(*args, **kwargs)

    def pan_pixels(self, dx, dy):
        """Translate camera and focus equally on the current focal plane."""
        camera = self.camera
        renderer = self.renderer
        renderer.SetWorldPoint(*camera.focal_point, 1)
        renderer.WorldToDisplay()
        x, y, depth = renderer.GetDisplayPoint()
        scale = self.devicePixelRatioF() * self.navigation_speed
        renderer.SetDisplayPoint(x - dx * scale, y + dy * scale, depth)
        renderer.DisplayToWorld()
        point = np.asarray(renderer.GetWorldPoint())
        shift = point[:3] / point[3] - np.asarray(camera.focal_point)
        camera.position = np.asarray(camera.position) + shift
        camera.focal_point = np.asarray(camera.focal_point) + shift
        self.reset_camera_clipping_range()
        self.render()

    def cursor_world(self, position):
        renderer = self.renderer
        renderer.SetWorldPoint(*self.camera.focal_point, 1)
        renderer.WorldToDisplay()
        depth = renderer.GetDisplayPoint()[2]
        scale = self.devicePixelRatioF()
        renderer.SetDisplayPoint(position.x() * scale,
                                 (self.height() - position.y() - 1) * scale, depth)
        renderer.DisplayToWorld()
        point = np.asarray(renderer.GetWorldPoint())
        return point[:3] / point[3]

    def zoom_by(self, steps, position=None):
        anchor = self.cursor_world(position) if position is not None else None
        self.camera.zoom(1.2 ** (steps * self.navigation_speed))
        if anchor is not None:
            shift = anchor - self.cursor_world(position)
            self.camera.position = np.asarray(self.camera.position) + shift
            self.camera.focal_point = np.asarray(self.camera.focal_point) + shift
        self.reset_camera_clipping_range()
        self.render()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.home_view:
            self.home_view()
            self.orientation_pressed = True
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.pick_orientation and self.pick_orientation(event.position()):
            self.orientation_pressed = True
            event.accept()
        elif event.button() == Qt.RightButton:
            self.pan_position = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.orientation_pressed:
            event.accept()
        elif self.pan_position is not None:
            delta = event.position() - self.pan_position
            self.pan_position = event.position()
            self.pan_pixels(delta.x(), delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.orientation_pressed:
            self.orientation_pressed = False
            event.accept()
        elif event.button() == Qt.RightButton:
            self.pan_position = None
            self.unsetCursor()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        pixels = event.pixelDelta()
        delta = pixels.y() if not pixels.isNull() else event.angleDelta().y()
        if delta:
            self.zoom_by(delta / 120, event.position())
        event.accept()

    def event(self, event):
        if event.type() == QEvent.NativeGesture and event.gestureType() == Qt.ZoomNativeGesture:
            self.zoom_by(event.value() * 5, event.position())
            event.accept()
            return True
        return super().event(event)
