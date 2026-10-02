"""Software dorsal shading of actual CT triangles; no inferred suture curves."""

import base64

import numpy as np
from PySide6.QtCore import QBuffer, QIODevice, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPolygonF


def dorsal_projection(mesh, pixels=1200):
    """Rasterize AP-up / ML-right in mm with depth-ordered surface shading.

    The image preserves source surface relief, including sutures when resolved
    by the CT segmentation. It does not identify or reconstruct missing sutures.
    """
    points = np.asarray(mesh.points)
    low = np.array([points[:, 1].min(), -points[:, 0].max()])
    high = np.array([points[:, 1].max(), -points[:, 0].min()])
    scale = (pixels - 1) / max(high - low)
    shape = np.ceil((high - low) * scale).astype(int) + 1
    image = QImage(int(shape[0]), int(shape[1]), QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    faces = mesh.faces.reshape(-1, 4)[:, 1:]
    triangles = points[faces]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    normals /= np.maximum(lengths[:, None], np.finfo(float).tiny)
    light = np.array([0.25, -0.35, -0.9])
    light /= np.linalg.norm(light)
    shade = .35 + .65 * np.maximum(0, normals @ light)
    colors = np.clip(shade[:, None] * np.array([222, 214, 190]), 0, 255).astype(int)
    projected = np.column_stack((points[:, 1], -points[:, 0]))
    projected = (projected - low) * scale
    painter = QPainter(image)
    painter.setPen(Qt.NoPen)
    try:
        # Far to near along ventral+; opaque faces avoid accumulating opacity
        # across internal bone surfaces. The final pixmap controls translucency.
        for index in np.argsort(triangles[:, :, 2].mean(axis=1))[::-1]:
            painter.setBrush(QColor(*colors[index].tolist()))
            painter.drawPolygon(QPolygonF([QPointF(*p) for p in projected[faces[index]]]))
    finally:
        painter.end()
    # Store the pixel-grid extent, including rounding of the shorter image axis.
    return image, [*low, *(low + (shape - 1) / scale)]


def encoded_projection(mesh):
    image, bounds = dorsal_projection(mesh)
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("Could not encode the CT dorsal image.")
    return {"png_base64": base64.b64encode(bytes(buffer.data())).decode("ascii"),
            "bounds_mm": bounds, "source": "Original CT surface relief; no inferred sutures"}
