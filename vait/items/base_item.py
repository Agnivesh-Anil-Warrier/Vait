"""Base graphics item for all whiteboard elements."""

import math
import uuid
from typing import Optional, Any
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtWidgets import (
    QGraphicsObject,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
    QStyleOptionGraphicsItem,
    QWidget
)
from PySide6.QtGui import QPainter, QCursor, QPainterPath

from vait.constants import ToolMode
from vait.items.handles import (
    HandleId,
    get_handle_at_pos,
    draw_handles,
    HANDLE_CURSORS,
    ROTATE_OFFSET,
    HANDLE_SIZE
)

class BaseCanvasItem(QGraphicsObject):
    """
    Abstract base canvas item providing selection handles, interactive resizing,
    rotation, serialization, and undo tracking signals.
    """

    # Signals for undo/redo tracking
    geometry_change_committed = Signal(object, dict, dict)  # item, old_state, new_state
    property_change_committed = Signal(object, str, object, object)  # item, prop, old, new

    def __init__(self, x: float = 0, y: float = 0, width: float = 100, height: float = 100, parent=None):
        super().__init__(parent)
        self.item_id: str = str(uuid.uuid4())
        self.item_type: str = "base"
        self._rect = QRectF(0, 0, max(10.0, width), max(10.0, height))
        self.setPos(x, y)

        self.lock_aspect_ratio: bool = False
        self.is_linear_item: bool = False  # True for Line and Arrow
        self.include_rotate_handle: bool = True

        # Interactive manipulation state
        self._active_handle: HandleId = HandleId.NONE
        self._drag_start_scene_pos: QPointF = QPointF()
        self._drag_start_pos: QPointF = QPointF()
        self._drag_start_rect: QRectF = QRectF()
        self._drag_start_rotation: float = 0.0
        self._drag_start_p1: QPointF = QPointF()
        self._drag_start_p2: QPointF = QPointF()
        self._is_dragging_item: bool = False
        self._initial_mouse_pos_on_item: QPointF = QPointF()

        # Flags
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self._update_transform_origin()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change in (
            QGraphicsItem.GraphicsItemChange.ItemSelectedChange,
            QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged,
        ):
            self.prepareGeometryChange()
            self.update()
            scene = self.scene()
            if scene:
                scene.update()
        return super().itemChange(change, value)

    @property
    def rect(self) -> QRectF:
        return self._rect

    @rect.setter
    def rect(self, r: QRectF):
        self.prepareGeometryChange()
        min_dim = 1.0 if self.is_linear_item else 10.0
        self._rect = QRectF(r.x(), r.y(), max(min_dim, r.width()), max(min_dim, r.height()))
        self._update_transform_origin()
        self.update()

    def set_size(self, width: float, height: float):
        self.prepareGeometryChange()
        min_dim = 1.0 if self.is_linear_item else 10.0
        self._rect = QRectF(self._rect.x(), self._rect.y(), max(min_dim, width), max(min_dim, height))
        self._update_transform_origin()
        self.update()

    def _update_transform_origin(self):
        """Set rotation origin to center of item."""
        if not self.is_linear_item:
            self.setTransformOriginPoint(self._rect.center())

    def get_view_scale(self) -> float:
        """Calculate approximate scale of the view currently rendering this item."""
        views = self.scene().views() if self.scene() else []
        if views:
            # Get m11 from view transform
            return views[0].transform().m11()
        return 1.0

    def boundingRect(self) -> QRectF:
        """Bounding rect including room for selection handles, rotation stem, and stroke width."""
        scale = self.get_view_scale()
        inv_scale = 1.0 / max(scale, 0.0001)
        stroke_pad = (getattr(self, "stroke_width", 0) / 2.0) + 2.0
        pad = max(stroke_pad, (HANDLE_SIZE + 10.0) * inv_scale)
        rot_pad = (ROTATE_OFFSET + HANDLE_SIZE + 15.0) * inv_scale if self.include_rotate_handle else pad
        rot_pad = max(rot_pad, stroke_pad)

        return self._rect.adjusted(-pad, -rot_pad, pad, pad)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint item content (subclasses override paint_content) and selection handles."""
        self.paint_content(painter, option, widget)

        if self.isSelected():
            scale = option.levelOfDetailFromTransform(painter.worldTransform())
            p1 = getattr(self, "p1", None)
            p2 = getattr(self, "p2", None)
            draw_handles(
                painter,
                self._rect,
                scale=scale,
                is_linear=self.is_linear_item,
                p1=p1,
                p2=p2,
                include_rotate=self.include_rotate_handle
            )

    def paint_content(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Subclasses implement specific rendering here."""
        pass

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        scene = self.scene()
        if scene and getattr(scene, "current_tool", ToolMode.SELECT) != ToolMode.SELECT:
            self.unsetCursor()
            return
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        """Update cursor based on hovered handle when selected."""
        scene = self.scene()
        if scene and getattr(scene, "current_tool", ToolMode.SELECT) != ToolMode.SELECT:
            self.unsetCursor()
            return

        if self.isSelected():
            scale = self.get_view_scale()
            p1 = getattr(self, "p1", None)
            p2 = getattr(self, "p2", None)
            handle = get_handle_at_pos(
                event.pos(),
                self._rect,
                scale=scale,
                is_linear=self.is_linear_item,
                p1=p1,
                p2=p2,
                include_rotate=self.include_rotate_handle
            )
            if handle in HANDLE_CURSORS:
                self.setCursor(QCursor(HANDLE_CURSORS[handle]))
                event.accept()
                return

        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor if self.isSelected() else Qt.CursorShape.ArrowCursor))
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            scale = self.get_view_scale()
            p1 = getattr(self, "p1", None)
            p2 = getattr(self, "p2", None)
            check_handles = self.isSelected()

            # If not selected yet but clicked directly on a linear endpoint, auto-select and start handle drag
            if not check_handles and self.is_linear_item and p1 is not None and p2 is not None:
                h_check = get_handle_at_pos(
                    event.pos(),
                    self._rect,
                    scale=scale,
                    is_linear=True,
                    p1=p1,
                    p2=p2,
                    include_rotate=False
                )
                if h_check in (HandleId.START_POINT, HandleId.END_POINT):
                    self.setSelected(True)
                    check_handles = True

            if check_handles:
                handle = get_handle_at_pos(
                    event.pos(),
                    self._rect,
                    scale=scale,
                    is_linear=self.is_linear_item,
                    p1=p1,
                    p2=p2,
                    include_rotate=self.include_rotate_handle
                )

                if handle != HandleId.NONE:
                    self._active_handle = handle
                    self._drag_start_scene_pos = event.scenePos()
                    self._drag_start_pos = self.pos()
                    self._drag_start_rect = QRectF(self._rect)
                    self._drag_start_rotation = self.rotation()
                    if self.is_linear_item and p1 is not None and p2 is not None:
                        self._drag_start_p1 = QPointF(p1)
                        self._drag_start_p2 = QPointF(p2)
                    event.accept()
                    return

        # Regular item move
        self._active_handle = HandleId.NONE
        self._is_dragging_item = True
        self._drag_start_pos = self.pos()
        self._drag_start_scene_pos = event.scenePos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self._active_handle != HandleId.NONE:
            # Handle resizing or rotation
            self._handle_resize_or_rotate(event)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._active_handle != HandleId.NONE:
            # Finished handle drag
            self._active_handle = HandleId.NONE
            old_state = {
                "pos": (self._drag_start_pos.x(), self._drag_start_pos.y()),
                "rect": (self._drag_start_rect.x(), self._drag_start_rect.y(), self._drag_start_rect.width(), self._drag_start_rect.height()),
                "rotation": self._drag_start_rotation
            }
            new_state = {
                "pos": (self.pos().x(), self.pos().y()),
                "rect": (self._rect.x(), self._rect.y(), self._rect.width(), self._rect.height()),
                "rotation": self.rotation()
            }
            if self.is_linear_item and hasattr(self, "p1") and hasattr(self, "p2") and hasattr(self, "_drag_start_p1"):
                old_state["p1"] = (self._drag_start_p1.x(), self._drag_start_p1.y())
                old_state["p2"] = (self._drag_start_p2.x(), self._drag_start_p2.y())
                new_state["p1"] = (self.p1.x(), self.p1.y())
                new_state["p2"] = (self.p2.x(), self.p2.y())

            if old_state != new_state:
                self.geometry_change_committed.emit(self, old_state, new_state)
            event.accept()
            return

        if self._is_dragging_item:
            self._is_dragging_item = False

        super().mouseReleaseEvent(event)

    def shape(self) -> QPainterPath:
        """Accurate hit-testing path including handles when selected."""
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRect(self._rect)
        if self.isSelected():
            from vait.items.handles import get_handle_positions, HANDLE_SIZE, HANDLE_HOVER_EXTRA, HandleId
            scale = self.get_view_scale()
            inv_scale = 1.0 / max(scale, 0.0001)
            p1 = getattr(self, "p1", None)
            p2 = getattr(self, "p2", None)
            handles = get_handle_positions(self._rect, scale=scale, is_linear=self.is_linear_item, p1=p1, p2=p2)
            r = (HANDLE_SIZE / 2.0 + HANDLE_HOVER_EXTRA) * inv_scale
            for h_id, pt in handles.items():
                if not self.include_rotate_handle and h_id == HandleId.ROTATE:
                    continue
                path.addRect(pt.x() - r, pt.y() - r, r * 2, r * 2)
        return path

    def _handle_resize_or_rotate(self, event: QGraphicsSceneMouseEvent):
        """Execute resize or rotation logic based on active handle."""
        if self.is_linear_item and self._active_handle in (HandleId.START_POINT, HandleId.END_POINT):
            pos = event.pos()
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Snap angle relative to the other stationary endpoint to 45 degree increments
                anchor = self.p2 if self._active_handle == HandleId.START_POINT else self.p1
                delta = pos - anchor
                length = math.hypot(delta.x(), delta.y())
                if length > 0.001:
                    angle = math.atan2(delta.y(), delta.x())
                    snap_angle = round(angle / (math.pi / 4.0)) * (math.pi / 4.0)
                    pos = anchor + QPointF(length * math.cos(snap_angle), length * math.sin(snap_angle))

            self.prepareGeometryChange()
            if self._active_handle == HandleId.START_POINT:
                self.p1 = pos
            else:
                self.p2 = pos

            min_x = min(self.p1.x(), self.p2.x())
            min_y = min(self.p1.y(), self.p2.y())
            max_x = max(self.p1.x(), self.p2.x())
            max_y = max(self.p1.y(), self.p2.y())
            self._rect = QRectF(min_x, min_y, max(1.0, max_x - min_x), max(1.0, max_y - min_y))
            self.update()
            return

        if self._active_handle == HandleId.ROTATE:
            # Calculate angle between item center (in scene coordinates) and current mouse scene position
            center_scene = self.mapToScene(self._rect.center())
            curr_pos = event.scenePos()
            delta = curr_pos - center_scene
            # Angle in degrees (0 is straight right, 90 is straight down)
            angle_rad = math.atan2(delta.y(), delta.x())
            angle_deg = math.degrees(angle_rad) + 90.0  # Align stem pointing upwards (0 deg is up)

            # Snap to 15-degree increments if Shift is pressed
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                angle_deg = round(angle_deg / 15.0) * 15.0

            self.setRotation(angle_deg)
            return

        # Resizing using stable coordinate projection from initial drag state
        delta_scene = event.scenePos() - self._drag_start_scene_pos
        rot_rad = math.radians(self._drag_start_rotation)
        cos_r = math.cos(rot_rad)
        sin_r = math.sin(rot_rad)

        # Rotate scene delta into item local axes (inverse rotation)
        dx = delta_scene.x() * cos_r + delta_scene.y() * sin_r
        dy = -delta_scene.x() * sin_r + delta_scene.y() * cos_r

        start_w = self._drag_start_rect.width()
        start_h = self._drag_start_rect.height()
        keep_aspect = self.lock_aspect_ratio or bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        aspect = start_h / max(1.0, start_w)
        min_dim = 15.0

        h = self._active_handle
        local_offset = QPointF(0, 0)
        new_w = start_w
        new_h = start_h

        if h == HandleId.BOTTOM_RIGHT:
            new_w = max(min_dim, start_w + dx)
            new_h = max(min_dim, start_h + dy)
            if keep_aspect:
                new_h = new_w * aspect
        elif h == HandleId.MID_RIGHT:
            new_w = max(min_dim, start_w + dx)
            if keep_aspect:
                new_h = new_w * aspect
        elif h == HandleId.BOTTOM_MID:
            new_h = max(min_dim, start_h + dy)
            if keep_aspect:
                new_w = new_h / max(0.001, aspect)
        elif h == HandleId.TOP_LEFT:
            new_w = max(min_dim, start_w - dx)
            new_h = max(min_dim, start_h - dy)
            if keep_aspect:
                new_h = new_w * aspect
                new_w = new_h / max(0.001, aspect)
            local_offset = QPointF(start_w - new_w, start_h - new_h)
        elif h == HandleId.TOP_MID:
            new_h = max(min_dim, start_h - dy)
            if keep_aspect:
                new_w = new_h / max(0.001, aspect)
            local_offset = QPointF(0, start_h - new_h)
        elif h == HandleId.TOP_RIGHT:
            new_w = max(min_dim, start_w + dx)
            new_h = max(min_dim, start_h - dy)
            if keep_aspect:
                new_h = new_w * aspect
            local_offset = QPointF(0, start_h - new_h)
        elif h == HandleId.MID_LEFT:
            new_w = max(min_dim, start_w - dx)
            if keep_aspect:
                new_h = new_w * aspect
            local_offset = QPointF(start_w - new_w, 0)
        elif h == HandleId.BOTTOM_LEFT:
            new_w = max(min_dim, start_w - dx)
            new_h = max(min_dim, start_h + dy)
            if keep_aspect:
                new_h = new_w * aspect
            local_offset = QPointF(start_w - new_w, 0)

        # Apply new top-left position in scene space
        scene_dx = local_offset.x() * cos_r - local_offset.y() * sin_r
        scene_dy = local_offset.x() * sin_r + local_offset.y() * cos_r
        self.setPos(self._drag_start_pos + QPointF(scene_dx, scene_dy))
        self.set_size(new_w, new_h)

    def to_dict(self) -> dict[str, Any]:
        """Serialize item properties into a dictionary."""
        return {
            "id": self.item_id,
            "type": self.item_type,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "width": self._rect.width(),
            "height": self._rect.height(),
            "rotation": self.rotation(),
            "z_value": self.zValue(),
            "lock_aspect_ratio": self.lock_aspect_ratio,
        }

    def from_dict(self, data: dict[str, Any]):
        """Load item properties from dictionary."""
        self.item_id = data.get("id", str(uuid.uuid4()))
        self.setPos(data.get("x", 0.0), data.get("y", 0.0))
        w = data.get("width", 100.0)
        h = data.get("height", 100.0)
        self.set_size(w, h)
        self.setRotation(data.get("rotation", 0.0))
        self.setZValue(data.get("z_value", 0.0))
        self.lock_aspect_ratio = data.get("lock_aspect_ratio", False)

    def get_geometry_state(self) -> dict:
        """Capture current geometry for undo/redo."""
        state = {
            "pos": (self.pos().x(), self.pos().y()),
            "rect": (self._rect.x(), self._rect.y(), self._rect.width(), self._rect.height()),
            "rotation": self.rotation()
        }
        if self.is_linear_item and hasattr(self, "p1") and hasattr(self, "p2"):
            state["p1"] = (self.p1.x(), self.p1.y())
            state["p2"] = (self.p2.x(), self.p2.y())
        return state

    def apply_geometry_state(self, state: dict):
        """Restore geometry from state dict."""
        self.prepareGeometryChange()
        if "pos" in state:
            self.setPos(state["pos"][0], state["pos"][1])
        if "rect" in state:
            rx, ry, rw, rh = state["rect"]
            self._rect = QRectF(rx, ry, rw, rh)
            self._update_transform_origin()
        if "rotation" in state:
            self.setRotation(state["rotation"])
        if "p1" in state and hasattr(self, "p1"):
            self.p1 = QPointF(state["p1"][0], state["p1"][1])
        if "p2" in state and hasattr(self, "p2"):
            self.p2 = QPointF(state["p2"][0], state["p2"][1])
        self.update()
