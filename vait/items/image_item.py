"""Image graphics item supporting aspect ratio lock, smooth scaling, and self-contained persistence."""

import base64
import os
from typing import Optional, Any
from PySide6.QtCore import QPointF, QRectF, Qt, QByteArray, QBuffer, QIODevice
from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PySide6.QtGui import QPainter, QPixmap, QImage, QColor

from vait.constants import Z_IMAGE
from vait.items.base_item import BaseCanvasItem

class ImageItem(BaseCanvasItem):
    """Canvas item representing an imported or pasted image."""

    def __init__(
        self,
        pixmap: Optional[QPixmap] = None,
        raw_bytes: Optional[bytes] = None,
        x: float = 0,
        y: float = 0,
        max_initial_width: float = 400,
        parent=None
    ):
        super().__init__(x, y, 100, 100, parent)
        self.item_type = "image"
        self.setZValue(Z_IMAGE)
        self.lock_aspect_ratio = True  # Preserved by default for images

        self.pixmap: QPixmap = QPixmap()
        self.raw_bytes: Optional[bytes] = raw_bytes
        self.asset_id: Optional[str] = None
        self.original_filename: str = ""

        if pixmap and not pixmap.isNull():
            self.set_pixmap(pixmap, max_initial_width=max_initial_width)
        elif raw_bytes:
            self.set_image_bytes(raw_bytes, max_initial_width=max_initial_width)

    def set_pixmap(self, pixmap: QPixmap, max_initial_width: float = 400):
        """Set item pixmap and auto-calculate dimensions maintaining original aspect ratio."""
        self.pixmap = pixmap
        orig_w = pixmap.width()
        orig_h = pixmap.height()

        if orig_w > 0 and orig_h > 0:
            scale = min(1.0, max_initial_width / orig_w)
            target_w = orig_w * scale
            target_h = orig_h * scale
            self.set_size(target_w, target_h)

        # Cache bytes if not already provided
        if not self.raw_bytes:
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            self.pixmap.save(buf, "PNG")
            self.raw_bytes = bytes(ba.data())

    def set_image_bytes(self, data: bytes, max_initial_width: float = 400):
        """Load image from raw bytes."""
        self.raw_bytes = data
        pix = QPixmap()
        if pix.loadFromData(data):
            self.set_pixmap(pix, max_initial_width=max_initial_width)
        else:
            # Fallback error placeholder
            self.pixmap = QPixmap(100, 100)
            self.pixmap.fill(QColor("#fca5a5"))
            self.set_size(100, 100)

    @classmethod
    def from_file(cls, filepath: str, x: float = 0, y: float = 0) -> "ImageItem":
        """Factory method to load image from file path."""
        with open(filepath, "rb") as f:
            data = f.read()
        item = cls(raw_bytes=data, x=x, y=y)
        item.original_filename = os.path.basename(filepath)
        return item

    @classmethod
    def from_qimage(cls, qimage: QImage, x: float = 0, y: float = 0) -> "ImageItem":
        """Factory method from QImage (e.g. from clipboard)."""
        pix = QPixmap.fromImage(qimage)
        return cls(pixmap=pix, x=x, y=y)

    def paint_content(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        if not self.pixmap.isNull():
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(self._rect.toRect(), self.pixmap)
            painter.restore()
        else:
            # Placeholder for broken image
            painter.save()
            painter.setPen(QColor("#ef4444"))
            painter.drawRect(self._rect)
            painter.drawText(self._rect, Qt.AlignmentFlag.AlignCenter, "Image Unavailable")
            painter.restore()

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        b64_str = base64.b64encode(self.raw_bytes).decode("ascii") if self.raw_bytes else ""
        d.update({
            "asset_id": self.asset_id or self.item_id,
            "original_filename": self.original_filename,
            "raw_bytes_b64": b64_str,
        })
        return d

    def from_dict(self, data: dict[str, Any]):
        super().from_dict(data)
        self.asset_id = data.get("asset_id", self.item_id)
        self.original_filename = data.get("original_filename", "")
        b64_str = data.get("raw_bytes_b64", "")
        if b64_str:
            try:
                self.raw_bytes = base64.b64decode(b64_str.encode("ascii"))
                pix = QPixmap()
                if pix.loadFromData(self.raw_bytes):
                    self.pixmap = pix
            except Exception:
                pass
        self.update()
