"""Image exporter for canvas contents (all items, selection, or visible viewport)."""

import os
from typing import Optional, Literal
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from vait.items.base_item import BaseCanvasItem

class CanvasExporter:
    """Exports canvas areas or items into PNG/JPEG images."""

    @staticmethod
    def export_to_image(
        scene: QGraphicsScene,
        filepath: str,
        view: Optional[QGraphicsView] = None,
        scope: Literal["all", "selected", "viewport"] = "all",
        transparent_bg: bool = False,
        scale_factor: float = 2.0  # Crisp 2x retina/high-res rendering by default
    ) -> bool:
        """Render target area to image file."""
        if scope == "selected":
            items = [item for item in scene.selectedItems() if isinstance(item, BaseCanvasItem)]
            if not items:
                return False
            rect = QRectF()
            for it in items:
                rect = rect.united(it.sceneBoundingRect())
            rect = rect.adjusted(-15, -15, 15, 15)
        elif scope == "viewport" and view is not None:
            rect = view.mapToScene(view.viewport().rect()).boundingRect()
        else:  # "all"
            rect = scene.itemsBoundingRect()
            if rect.isEmpty() or rect.width() <= 0 or rect.height() <= 0:
                rect = QRectF(-200, -200, 400, 400)
            else:
                rect = rect.adjusted(-30, -30, 30, 30)

        w = int(rect.width() * scale_factor)
        h = int(rect.height() * scale_factor)

        # Cap dimensions to prevent out-of-memory errors
        max_dim = 12000
        if w > max_dim or h > max_dim:
            ratio = max_dim / max(w, h)
            w = int(w * ratio)
            h = int(h * ratio)

        w = max(10, w)
        h = max(10, h)

        image = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        if transparent_bg:
            image.fill(Qt.GlobalColor.transparent)
        else:
            image.fill(QColor("#ffffff"))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Hide selection handles during export
        selected_items = list(scene.selectedItems())
        for it in selected_items:
            it.setSelected(False)

        scene.render(painter, target=QRectF(0, 0, w, h), source=rect)

        # Restore selection
        for it in selected_items:
            it.setSelected(True)

        painter.end()

        # Save to file
        ext = os.path.splitext(filepath)[1].lower()
        fmt = "PNG" if ext == ".png" else "JPEG"
        return image.save(filepath, fmt, quality=95)
