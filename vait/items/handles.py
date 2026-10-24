"""Interactive handles for canvas item selection, resizing, and rotation."""

from enum import Enum, auto
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush

class HandleId(Enum):
    NONE = auto()
    TOP_LEFT = auto()
    TOP_MID = auto()
    TOP_RIGHT = auto()
    MID_RIGHT = auto()
    BOTTOM_RIGHT = auto()
    BOTTOM_MID = auto()
    BOTTOM_LEFT = auto()
    MID_LEFT = auto()
    ROTATE = auto()
    START_POINT = auto()
    END_POINT = auto()

HANDLE_SIZE = 8.0  # Size in screen pixels
HANDLE_HOVER_EXTRA = 8.0
ROTATE_OFFSET = 24.0  # Pixels above the top edge

HANDLE_CURSORS = {
    HandleId.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
    HandleId.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
    HandleId.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
    HandleId.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
    HandleId.TOP_MID: Qt.CursorShape.SizeVerCursor,
    HandleId.BOTTOM_MID: Qt.CursorShape.SizeVerCursor,
    HandleId.MID_LEFT: Qt.CursorShape.SizeHorCursor,
    HandleId.MID_RIGHT: Qt.CursorShape.SizeHorCursor,
    HandleId.ROTATE: Qt.CursorShape.PointingHandCursor,
    HandleId.START_POINT: Qt.CursorShape.CrossCursor,
    HandleId.END_POINT: Qt.CursorShape.CrossCursor,
}

def get_handle_positions(rect: QRectF, scale: float = 1.0, is_linear: bool = False, p1: QPointF = None, p2: QPointF = None) -> dict[HandleId, QPointF]:
    """Return local coordinates for each handle."""
    if is_linear and p1 is not None and p2 is not None:
        return {
            HandleId.START_POINT: p1,
            HandleId.END_POINT: p2,
        }

    w = rect.width()
    h = rect.height()
    x = rect.x()
    y = rect.y()

    # Offset rotate handle in local coordinates (adjusted for zoom)
    rot_dist = ROTATE_OFFSET / max(scale, 0.0001)

    return {
        HandleId.TOP_LEFT: QPointF(x, y),
        HandleId.TOP_MID: QPointF(x + w / 2, y),
        HandleId.TOP_RIGHT: QPointF(x + w, y),
        HandleId.MID_RIGHT: QPointF(x + w, y + h / 2),
        HandleId.BOTTOM_RIGHT: QPointF(x + w, y + h),
        HandleId.BOTTOM_MID: QPointF(x + w / 2, y + h),
        HandleId.BOTTOM_LEFT: QPointF(x, y + h),
        HandleId.MID_LEFT: QPointF(x, y + h / 2),
        HandleId.ROTATE: QPointF(x + w / 2, y - rot_dist),
    }

def get_handle_at_pos(
    pos: QPointF,
    rect: QRectF,
    scale: float = 1.0,
    is_linear: bool = False,
    p1: QPointF = None,
    p2: QPointF = None,
    include_rotate: bool = True
) -> HandleId:
    """Check if pos is over any handle, accounting for view scale."""
    handles = get_handle_positions(rect, scale, is_linear, p1, p2)
    # Radius in local coordinates
    r = (HANDLE_SIZE / 2.0 + HANDLE_HOVER_EXTRA) / max(scale, 0.0001)

    for h_id, pt in handles.items():
        if not include_rotate and h_id == HandleId.ROTATE:
            continue
        dx = pos.x() - pt.x()
        dy = pos.y() - pt.y()
        if (dx * dx + dy * dy) <= (r * r):
            return h_id
    return HandleId.NONE

def draw_handles(
    painter: QPainter,
    rect: QRectF,
    scale: float = 1.0,
    is_linear: bool = False,
    p1: QPointF = None,
    p2: QPointF = None,
    include_rotate: bool = True,
    accent_color: QColor = QColor("#3b82f6")
):
    """Draw selection outline and handles scaled inversely with zoom so they remain crisp."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    inv_scale = 1.0 / max(scale, 0.0001)
    handle_radius = (HANDLE_SIZE / 2.0) * inv_scale
    line_width = 1.2 * inv_scale

    # 1. Selection bounding outline (only for 2D shapes, not linear items)
    if not is_linear:
        outline_pen = QPen(accent_color, line_width, Qt.PenStyle.SolidLine)
        outline_pen.setCosmetic(False)
        painter.setPen(outline_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

    # 2. Rotate stem
    if include_rotate and not is_linear:
        top_mid = QPointF(rect.x() + rect.width() / 2, rect.y())
        rot_pos = QPointF(top_mid.x(), top_mid.y() - ROTATE_OFFSET * inv_scale)
        stem_pen = QPen(accent_color, line_width, Qt.PenStyle.DotLine)
        painter.setPen(stem_pen)
        painter.drawLine(top_mid, rot_pos)

    # 3. Handle boxes/circles
    handles = get_handle_positions(rect, scale, is_linear, p1, p2)
    handle_brush = QBrush(QColor("#ffffff"))
    handle_pen = QPen(accent_color, line_width)

    for h_id, pt in handles.items():
        if not include_rotate and h_id == HandleId.ROTATE:
            continue

        painter.setPen(handle_pen)
        painter.setBrush(handle_brush)

        if h_id == HandleId.ROTATE:
            # Draw circle for rotation
            painter.setBrush(QBrush(accent_color))
            painter.drawEllipse(pt, handle_radius, handle_radius)
        elif is_linear:
            # Circular endpoints for lines/arrows
            painter.drawEllipse(pt, handle_radius * 1.2, handle_radius * 1.2)
        else:
            # Square resize handle
            handle_rect = QRectF(
                pt.x() - handle_radius,
                pt.y() - handle_radius,
                handle_radius * 2,
                handle_radius * 2
            )
            painter.drawRect(handle_rect)

    painter.restore()
