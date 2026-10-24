"""Shape graphics items: Rectangle, Rounded Rect, Ellipse, Line, Arrow, Triangle, Diamond."""

import math
from typing import Optional, Any
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget, QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QPainterPath

from vait.constants import (
    ShapeType,
    Z_SHAPE,
    DEFAULT_STROKE_COLOR,
    DEFAULT_FILL_COLOR,
    DEFAULT_STROKE_WIDTH
)
from vait.items.base_item import BaseCanvasItem
from vait.items.handles import (
    HandleId,
    draw_handles,
    get_handle_at_pos,
    HANDLE_SIZE,
    HANDLE_HOVER_EXTRA
)

class ShapeItem(BaseCanvasItem):
    """Canvas item representing geometric shapes with customizable strokes and fills."""

    def __init__(
        self,
        shape_type: ShapeType = ShapeType.RECTANGLE,
        x: float = 0,
        y: float = 0,
        width: float = 120,
        height: float = 80,
        parent=None
    ):
        super().__init__(x, y, width, height, parent)
        self.item_type = "shape"
        self.shape_type: ShapeType = shape_type
        self.setZValue(Z_SHAPE)

        # Style attributes
        self.stroke_color: str = DEFAULT_STROKE_COLOR
        self.stroke_width: float = DEFAULT_STROKE_WIDTH
        self.fill_color: str = DEFAULT_FILL_COLOR
        self.fill_transparent: bool = True
        self.corner_radius: float = 12.0

        # Linear shape support (Line, Arrow)
        self.is_linear_item = self.shape_type in (ShapeType.LINE, ShapeType.ARROW)
        self.include_rotate_handle = not self.is_linear_item

        # Local endpoints for linear shapes
        self.p1: QPointF = QPointF(0, 0)
        self.p2: QPointF = QPointF(width, height)

    def paint_content(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self.stroke_width <= 0:
            painter.setPen(Qt.PenStyle.NoPen)
        else:
            pen = QPen(QColor(self.stroke_color), self.stroke_width, Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

        if self.fill_transparent or self.is_linear_item:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        else:
            painter.setBrush(QBrush(QColor(self.fill_color)))

        rect = self._rect

        if self.shape_type == ShapeType.RECTANGLE:
            painter.drawRect(rect)
        elif self.shape_type == ShapeType.ROUNDED_RECT:
            painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
        elif self.shape_type == ShapeType.ELLIPSE:
            painter.drawEllipse(rect)
        elif self.shape_type == ShapeType.TRIANGLE:
            top = QPointF(rect.x() + rect.width() / 2, rect.y())
            bottom_right = QPointF(rect.x() + rect.width(), rect.y() + rect.height())
            bottom_left = QPointF(rect.x(), rect.y() + rect.height())
            poly = QPolygonF([top, bottom_right, bottom_left])
            painter.drawPolygon(poly)
        elif self.shape_type == ShapeType.DIAMOND:
            top = QPointF(rect.x() + rect.width() / 2, rect.y())
            right = QPointF(rect.x() + rect.width(), rect.y() + rect.height() / 2)
            bottom = QPointF(rect.x() + rect.width() / 2, rect.y() + rect.height())
            left = QPointF(rect.x(), rect.y() + rect.height() / 2)
            poly = QPolygonF([top, right, bottom, left])
            painter.drawPolygon(poly)
        elif self.shape_type == ShapeType.LINE:
            painter.drawLine(self.p1, self.p2)
        elif self.shape_type == ShapeType.ARROW:
            self._draw_arrow(painter, self.p1, self.p2)

        painter.restore()

    def _draw_arrow(self, painter: QPainter, start: QPointF, end: QPointF):
        """Draw a line with a crisp arrow head at `end`."""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.hypot(dx, dy)
        if length < 1.0:
            return

        angle = math.atan2(dy, dx)
        # Cap arrow size relative to line length and stroke width
        arrow_size = max(8.0, min(length * 0.45, self.stroke_width * 3.0 + 10.0))

        # Arrow head points
        arrow_p1 = QPointF(
            end.x() - arrow_size * math.cos(angle - math.pi / 6),
            end.y() - arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = QPointF(
            end.x() - arrow_size * math.cos(angle + math.pi / 6),
            end.y() - arrow_size * math.sin(angle + math.pi / 6)
        )

        # Draw main line stopping slightly before end tip so rounded stroke cap does not poke out
        line_stop_dist = min(arrow_size * 0.4, length * 0.3)
        line_end = QPointF(
            end.x() - line_stop_dist * math.cos(angle),
            end.y() - line_stop_dist * math.sin(angle)
        )
        painter.drawLine(start, line_end)

        # Draw arrowhead with solid fill and 1px crisp outline matching stroke color
        painter.save()
        arrow_pen = QPen(QColor(self.stroke_color), 1.0, Qt.PenStyle.SolidLine)
        arrow_pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(arrow_pen)
        painter.setBrush(QBrush(QColor(self.stroke_color)))
        arrow_head = QPolygonF([end, arrow_p1, arrow_p2])
        painter.drawPolygon(arrow_head)
        painter.restore()

    def boundingRect(self) -> QRectF:
        if self.is_linear_item:
            scale = self.get_view_scale()
            inv_scale = 1.0 / max(scale, 0.0001)
            handle_pad = (HANDLE_SIZE + 16.0) * inv_scale
            stroke_pad = (self.stroke_width / 2.0) + 4.0
            arrow_pad = (self.stroke_width * 3.5 + 16.0) if self.shape_type == ShapeType.ARROW else 0.0
            pad = max(handle_pad, stroke_pad + arrow_pad)
            min_x = min(self.p1.x(), self.p2.x())
            min_y = min(self.p1.y(), self.p2.y())
            max_x = max(self.p1.x(), self.p2.x())
            max_y = max(self.p1.y(), self.p2.y())
            return QRectF(min_x, min_y, max(1.0, max_x - min_x), max(1.0, max_y - min_y)).adjusted(-pad, -pad, pad, pad)
        return super().boundingRect()

    def shape(self) -> QPainterPath:
        """Accurate hit test path."""
        if self.is_linear_item:
            from PySide6.QtGui import QPainterPathStroker
            path = QPainterPath()
            path.moveTo(self.p1)
            path.lineTo(self.p2)
            stroker = QPainterPathStroker()
            scale = self.get_view_scale()
            inv_scale = 1.0 / max(scale, 0.0001)
            stroker.setWidth(max(24.0 * inv_scale, self.stroke_width * 2.0))
            stroke_path = stroker.createStroke(path)

            if self.isSelected():
                handle_r = (HANDLE_SIZE / 2.0 + HANDLE_HOVER_EXTRA + 4.0) * inv_scale
                handles_path = QPainterPath()
                handles_path.addEllipse(self.p1, handle_r, handle_r)
                handles_path.addEllipse(self.p2, handle_r, handle_r)
                return stroke_path.united(handles_path)
            return stroke_path

        return super().shape()

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "shape_type": self.shape_type.value,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "fill_color": self.fill_color,
            "fill_transparent": self.fill_transparent,
            "corner_radius": self.corner_radius,
            "p1": (self.p1.x(), self.p1.y()),
            "p2": (self.p2.x(), self.p2.y()),
        })
        return d

    def from_dict(self, data: dict[str, Any]):
        super().from_dict(data)
        st_val = data.get("shape_type", ShapeType.RECTANGLE.value)
        try:
            self.shape_type = ShapeType(st_val)
        except ValueError:
            self.shape_type = ShapeType.RECTANGLE

        self.is_linear_item = self.shape_type in (ShapeType.LINE, ShapeType.ARROW)
        self.include_rotate_handle = not self.is_linear_item

        self.stroke_color = data.get("stroke_color", DEFAULT_STROKE_COLOR)
        self.stroke_width = data.get("stroke_width", DEFAULT_STROKE_WIDTH)
        self.fill_color = data.get("fill_color", DEFAULT_FILL_COLOR)
        self.fill_transparent = data.get("fill_transparent", True)
        self.corner_radius = data.get("corner_radius", 12.0)

        if "p1" in data and "p2" in data:
            self.p1 = QPointF(data["p1"][0], data["p1"][1])
            self.p2 = QPointF(data["p2"][0], data["p2"][1])
        else:
            self.p1 = QPointF(0, 0)
            self.p2 = QPointF(self._rect.width(), self._rect.height())

        self.update()
