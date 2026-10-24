"""Freehand drawing stroke item supporting smooth bezier curves, eraser hit-testing, and styling."""

from typing import Optional, Any
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget, QGraphicsItem
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QPainterPath,
    QPainterPathStroker
)

from vait.constants import Z_STROKE, DEFAULT_PEN_COLOR, DEFAULT_PEN_WIDTH
from vait.items.base_item import BaseCanvasItem

class StrokeItem(BaseCanvasItem):
    """Canvas item representing a freehand pen stroke with smooth curves."""

    def __init__(
        self,
        points: Optional[list[QPointF]] = None,
        color: str = DEFAULT_PEN_COLOR,
        width: float = DEFAULT_PEN_WIDTH,
        parent=None
    ):
        super().__init__(0, 0, 10, 10, parent)
        self.item_type = "stroke"
        self.setZValue(Z_STROKE)
        self.include_rotate_handle = False  # Keep strokes simple with corner/bounding box resize

        self.color: str = color
        self.stroke_width: float = width
        self.points: list[QPointF] = []
        self._path: QPainterPath = QPainterPath()

        if points:
            for pt in points:
                self.points.append(QPointF(pt))
            self._rebuild_path()

    def add_point(self, pt: QPointF):
        """Append a point and update smooth path with immediate geometry notification."""
        self.prepareGeometryChange()
        self.points.append(pt)
        self._rebuild_path()
        self.update()

    def _rebuild_path(self):
        """Build smooth quadratic bezier path through points."""
        path = QPainterPath()
        pts = self.points
        if not pts:
            self._path = path
            return

        if len(pts) == 1:
            path.moveTo(pts[0])
            path.lineTo(pts[0].x() + 0.1, pts[0].y() + 0.1)
        elif len(pts) == 2:
            path.moveTo(pts[0])
            path.lineTo(pts[1])
        else:
            path.moveTo(pts[0])
            for i in range(1, len(pts) - 1):
                p0 = pts[i]
                p1 = pts[i + 1]
                mid = QPointF((p0.x() + p1.x()) / 2.0, (p0.y() + p1.y()) / 2.0)
                path.quadTo(p0, mid)
            path.lineTo(pts[-1])

        self._path = path
        if not path.isEmpty():
            br = path.boundingRect()
            self._rect = QRectF(br.x(), br.y(), max(5.0, br.width()), max(5.0, br.height()))

    def boundingRect(self) -> QRectF:
        """Dynamic bounding rect encompassing stroke path without clipping during drawing or selection."""
        if self._path.isEmpty():
            return self._rect
        scale = self.get_view_scale()
        inv_scale = 1.0 / max(scale, 0.0001)
        pad = max(16.0, self.stroke_width * 2, 25.0 * inv_scale)
        rect = self._path.boundingRect()
        if not self._rect.isNull():
            rect = rect.united(self._rect)
        return rect.adjusted(-pad, -pad, pad, pad)

    def finish_stroke(self):
        """Finalize stroke geometry and normalize coordinates relative to item pos."""
        if not self.points:
            return
        self._recalculate_bounds()

    def _recalculate_bounds(self):
        """Normalize stroke points so item position is top-left, and local coordinates are relative."""
        if not self.points:
            return

        min_x = min(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_x = max(p.x() for p in self.points)
        max_y = max(p.y() for p in self.points)

        w = max(5.0, max_x - min_x)
        h = max(5.0, max_y - min_y)

        self.prepareGeometryChange()
        curr_pos = self.pos()
        if curr_pos == QPointF(0, 0):
            self.setPos(min_x, min_y)
            self.points = [QPointF(p.x() - min_x, p.y() - min_y) for p in self.points]
        self._rect = QRectF(0, 0, w, h)
        self._rebuild_path()
        self._update_transform_origin()
        self.update()

    def shape(self) -> QPainterPath:
        """Accurate stroker path for hit detection."""
        stroker = QPainterPathStroker()
        scale = self.get_view_scale()
        inv_scale = 1.0 / max(scale, 0.0001)
        stroker.setWidth(max(16.0 * inv_scale, self.stroke_width * 2))
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(self._path)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint stroke content and a clean selection outline when selected."""
        self.paint_content(painter, option, widget)

        if self.isSelected():
            scale = option.levelOfDetailFromTransform(painter.worldTransform())
            inv_scale = 1.0 / max(scale, 0.0001)
            line_width = 1.5 * inv_scale
            pad = 6.0 * inv_scale
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pen = QPen(QColor("#3b82f6"), line_width, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            box = self._rect.adjusted(-pad, -pad, pad, pad)
            painter.drawRoundedRect(box, 4.0 * inv_scale, 4.0 * inv_scale)
            painter.restore()

    def paint_content(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        if self._path.isEmpty():
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor(self.color), self.stroke_width, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self._path)
        painter.restore()

    def intersects_segment(self, p1: QPointF, p2: QPointF, tolerance: float = 10.0) -> bool:
        """Check if a line segment (e.g. from eraser stroke) intersects this stroke."""
        eraser_path = QPainterPath()
        eraser_path.moveTo(self.mapFromScene(p1))
        eraser_path.lineTo(self.mapFromScene(p2))

        stroker = QPainterPathStroker()
        stroker.setWidth(tolerance * 2)
        eraser_stroke = stroker.createStroke(eraser_path)

        return self.shape().intersects(eraser_stroke)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "color": self.color,
            "stroke_width": self.stroke_width,
            "points": [(p.x(), p.y()) for p in self.points]
        })
        return d

    def from_dict(self, data: dict[str, Any]):
        super().from_dict(data)
        self.color = data.get("color", DEFAULT_PEN_COLOR)
        self.stroke_width = data.get("stroke_width", DEFAULT_PEN_WIDTH)
        pts_data = data.get("points", [])
        self.points = [QPointF(x, y) for x, y in pts_data]
        self._rebuild_path()
        self.update()
