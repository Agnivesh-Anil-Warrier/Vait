"""Programmatic vector icon generation using QPainter for crisp high-DPI rendering."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QBrush, QColor, QPolygonF, QPainterPath

def _render_icon_pixmap(name: str, color: str, size: int) -> QPixmap:
    scale_factor = 2  # 2x supersampling for high-DPI crispness
    pix = QPixmap(size * scale_factor, size * scale_factor)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(scale_factor, scale_factor)

    pen = QPen(QColor(color), 2.0, Qt.PenStyle.SolidLine)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if name == "select":
        # Solid sleek cursor arrow
        path = QPainterPath()
        path.moveTo(5, 3)
        path.lineTo(12, 20)
        path.lineTo(14.5, 14.5)
        path.lineTo(20, 13.5)
        path.closeSubpath()
        painter.setBrush(QBrush(QColor(color)))
        painter.drawPath(path)

    elif name == "pan":
        # Hand with open fingers
        path = QPainterPath()
        path.moveTo(8.5, 13)
        path.lineTo(8.5, 7.5)
        path.quadTo(9.5, 5.5, 11, 7.5)
        path.lineTo(11, 13)
        path.lineTo(11, 6)
        path.quadTo(12, 4.5, 13.5, 6)
        path.lineTo(13.5, 13)
        path.lineTo(13.5, 7.5)
        path.quadTo(14.5, 6, 16, 7.5)
        path.lineTo(16, 13.5)
        path.quadTo(16, 19, 12, 19.5)
        path.quadTo(7, 19.5, 7, 14.5)
        path.lineTo(7, 11)
        path.quadTo(7, 9.5, 8.5, 11)
        path.closeSubpath()
        painter.drawPath(path)

    elif name == "pen":
        # Pencil angled
        path = QPainterPath()
        path.moveTo(16, 4)
        path.lineTo(20, 8)
        path.lineTo(9, 19)
        path.lineTo(5, 19)
        path.lineTo(5, 15)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(13, 7, 17, 11)

    elif name == "eraser":
        # Eraser angled with band
        path = QPainterPath()
        path.moveTo(7, 17)
        path.lineTo(15, 9)
        path.lineTo(19, 13)
        path.lineTo(11, 21)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(11, 13, 15, 17)

    elif name == "text":
        # Large clear T
        pen.setWidthF(2.2)
        painter.setPen(pen)
        painter.drawLine(4, 5, 20, 5)
        painter.drawLine(12, 5, 12, 19)
        painter.drawLine(8, 19, 16, 19)

    elif name == "rectangle":
        painter.drawRect(QRectF(4, 5, 16, 14))

    elif name == "rounded_rect":
        painter.drawRoundedRect(QRectF(4, 5, 16, 14), 4, 4)

    elif name == "ellipse":
        painter.drawEllipse(QRectF(4, 5, 16, 14))

    elif name == "line":
        painter.drawLine(QPointF(4, 20), QPointF(20, 4))

    elif name == "arrow":
        painter.drawLine(QPointF(4, 20), QPointF(19, 5))
        path = QPainterPath()
        path.moveTo(12, 5)
        path.lineTo(19, 5)
        path.lineTo(19, 12)
        painter.drawPath(path)

    elif name == "triangle":
        poly = QPolygonF([QPointF(12, 4), QPointF(20, 19), QPointF(4, 19)])
        painter.drawPolygon(poly)

    elif name == "diamond":
        poly = QPolygonF([QPointF(12, 4), QPointF(20, 12), QPointF(12, 20), QPointF(4, 12)])
        painter.drawPolygon(poly)

    elif name == "image":
        painter.drawRect(QRectF(3, 4, 18, 16))
        painter.drawEllipse(QPointF(8, 9), 2, 2)
        path = QPainterPath()
        path.moveTo(3, 17)
        path.lineTo(8, 12)
        path.lineTo(13, 16)
        path.lineTo(16, 13)
        path.lineTo(21, 17)
        painter.drawPath(path)

    elif name == "undo":
        path = QPainterPath()
        path.moveTo(8, 6)
        path.lineTo(4, 10)
        path.lineTo(8, 14)
        painter.drawPath(path)
        painter.drawArc(QRectF(4, 10, 15, 10), 0 * 16, 180 * 16)

    elif name == "redo":
        path = QPainterPath()
        path.moveTo(16, 6)
        path.lineTo(20, 10)
        path.lineTo(16, 14)
        painter.drawPath(path)
        painter.drawArc(QRectF(5, 10, 15, 10), 0 * 16, 180 * 16)

    elif name == "zoom_in":
        painter.drawEllipse(QRectF(4, 4, 12, 12))
        painter.drawLine(13, 13, 19, 19)
        painter.drawLine(7, 10, 13, 10)
        painter.drawLine(10, 7, 10, 13)

    elif name == "zoom_out":
        painter.drawEllipse(QRectF(4, 4, 12, 12))
        painter.drawLine(13, 13, 19, 19)
        painter.drawLine(7, 10, 13, 10)

    elif name == "fit":
        painter.drawPolyline([QPointF(4, 9), QPointF(4, 4), QPointF(9, 4)])
        painter.drawPolyline([QPointF(15, 4), QPointF(20, 4), QPointF(20, 9)])
        painter.drawPolyline([QPointF(20, 15), QPointF(20, 20), QPointF(15, 20)])
        painter.drawPolyline([QPointF(9, 20), QPointF(4, 20), QPointF(4, 15)])

    elif name == "save":
        painter.drawRect(QRectF(4, 4, 16, 16))
        painter.drawRect(QRectF(7, 4, 10, 6))
        painter.drawRect(QRectF(7, 13, 10, 7))

    elif name == "open":
        path = QPainterPath()
        path.moveTo(3, 7)
        path.lineTo(8, 7)
        path.lineTo(10, 9)
        path.lineTo(21, 9)
        path.lineTo(21, 19)
        path.lineTo(3, 19)
        path.closeSubpath()
        painter.drawPath(path)

    elif name == "new":
        path = QPainterPath()
        path.moveTo(4, 3)
        path.lineTo(14, 3)
        path.lineTo(20, 9)
        path.lineTo(20, 21)
        path.lineTo(4, 21)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(12, 11, 12, 17)
        painter.drawLine(9, 14, 15, 14)

    elif name == "export":
        painter.drawPolyline([QPointF(8, 10), QPointF(4, 10), QPointF(4, 20), QPointF(20, 20), QPointF(20, 10), QPointF(16, 10)])
        painter.drawLine(12, 15, 12, 4)
        painter.drawLine(8, 8, 12, 4)
        painter.drawLine(16, 8, 12, 4)

    elif name == "grid":
        dots = [
            QPointF(6, 6), QPointF(12, 6), QPointF(18, 6),
            QPointF(6, 12), QPointF(12, 12), QPointF(18, 12),
            QPointF(6, 18), QPointF(12, 18), QPointF(18, 18),
        ]
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        for d in dots:
            painter.drawEllipse(d, 1.8, 1.8)

    painter.end()
    return pix

def create_icon(name: str, color: str = "#f1f5f9", size: int = 24) -> QIcon:
    """Generate high-DPI QIcon with bright normal, active, and dimmed disabled states."""
    icon = QIcon()
    # Normal state (crisp light off-white)
    normal_pix = _render_icon_pixmap(name, color, size)
    icon.addPixmap(normal_pix, QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(_render_icon_pixmap(name, "#ffffff", size), QIcon.Mode.Normal, QIcon.State.On)

    # Active / Hover state (pure bright white)
    hover_pix = _render_icon_pixmap(name, "#ffffff", size)
    icon.addPixmap(hover_pix, QIcon.Mode.Active, QIcon.State.Off)
    icon.addPixmap(hover_pix, QIcon.Mode.Active, QIcon.State.On)

    # Disabled state (dimmed slate so it looks inactive, not invisible)
    disabled_pix = _render_icon_pixmap(name, "#475569", size)
    icon.addPixmap(disabled_pix, QIcon.Mode.Disabled, QIcon.State.Off)
    icon.addPixmap(disabled_pix, QIcon.Mode.Disabled, QIcon.State.On)

    return icon
