"""Infinite Canvas Scene with background grid, tool event dispatching, and item lifecycle management."""

from typing import Optional
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent
from PySide6.QtGui import QPainter, QPen, QColor, QBrush

from vait.constants import (
    SCENE_EXTENT,
    GRID_BASE_SIZE,
    GRID_DOT_RADIUS,
    GRID_COLOR_LIGHT,
    CANVAS_BG_LIGHT,
    ToolMode,
    ShapeType,
    GridStyle,
    DEFAULT_PEN_COLOR,
    DEFAULT_PEN_WIDTH,
    DEFAULT_STROKE_COLOR,
    DEFAULT_STROKE_WIDTH,
    DEFAULT_FILL_COLOR,
    Z_STROKE
)
from vait.items import (
    BaseCanvasItem,
    ShapeItem,
    TextItem,
    StrokeItem,
    ImageItem
)
from vait.commands.undo_commands import (
    AddItemsCommand,
    DeleteItemsCommand,
    MoveItemsCommand,
    TransformItemCommand,
    ChangePropertyCommand
)

class InfiniteCanvasScene(QGraphicsScene):
    """QGraphicsScene supporting infinite grid drawing, tool routing, and undo management."""

    status_message = Signal(str)
    selection_state_changed = Signal(list)  # List of selected BaseCanvasItems
    tool_changed = Signal(object)  # Emits ToolMode when active tool changes

    def __init__(self, undo_stack, parent=None):
        half_ext = SCENE_EXTENT / 2.0
        super().__init__(-half_ext, -half_ext, SCENE_EXTENT, SCENE_EXTENT, parent)
        self.undo_stack = undo_stack

        self.grid_style: GridStyle = GridStyle.DOTS
        self.grid_base_size: int = GRID_BASE_SIZE
        self.bg_color: QColor = QColor(CANVAS_BG_LIGHT)
        self.grid_color: QColor = QColor(GRID_COLOR_LIGHT)

        # Active tool state
        self.current_tool: ToolMode = ToolMode.SELECT
        self.current_shape_type: ShapeType = ShapeType.RECTANGLE

        # Tool properties for new objects
        self.pen_color: str = DEFAULT_PEN_COLOR
        self.pen_width: float = DEFAULT_PEN_WIDTH
        self.shape_stroke_color: str = DEFAULT_STROKE_COLOR
        self.shape_stroke_width: float = DEFAULT_STROKE_WIDTH
        self.shape_fill_color: str = DEFAULT_FILL_COLOR
        self.shape_fill_transparent: bool = True

        # Interactive drawing state
        self._current_stroke: Optional[StrokeItem] = None
        self._preview_shape: Optional[ShapeItem] = None
        self._shape_start_pos: QPointF = QPointF()

        # Multi-move tracking
        self._moving_items: list[BaseCanvasItem] = []
        self._start_item_positions: list[QPointF] = []
        self._is_moving_selection: bool = False
        self.selectionChanged.connect(self._on_selection_changed)

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, BaseCanvasItem):
            if not getattr(item, "_geometry_committed_connected", False):
                item.geometry_change_committed.connect(self._on_item_geometry_committed)
                item._geometry_committed_connected = True

    def _on_item_geometry_committed(self, item, old_state, new_state):
        cmd = TransformItemCommand(item, old_state, new_state)
        self.undo_stack.push(cmd)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Draw infinite dot-grid or line-grid dynamically adapting to zoom level."""
        # 1. Background fill
        painter.fillRect(rect, self.bg_color)

        if self.grid_style == GridStyle.NONE:
            return

        # Adaptive grid spacing based on zoom/LOD
        scale = painter.worldTransform().m11()
        step = self.grid_base_size

        # If zoomed out far, scale up step so dots don't become dense noise
        if scale < 0.2:
            step *= 8
        elif scale < 0.5:
            step *= 4
        elif scale < 0.8:
            step *= 2

        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)
        right = int(rect.right()) + step
        bottom = int(rect.bottom()) + step

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        if self.grid_style == GridStyle.DOTS:
            dot_color = self.grid_color
            painter.setPen(QPen(dot_color, GRID_DOT_RADIUS))
            # Draw dots
            points = []
            x = left
            while x <= right:
                y = top
                while y <= bottom:
                    points.append(QPointF(x, y))
                    y += step
                x += step
            painter.drawPoints(points)

        elif self.grid_style == GridStyle.LINES:
            line_pen = QPen(self.grid_color, 1.0)
            line_pen.setCosmetic(True)
            painter.setPen(line_pen)

            # Vertical lines
            x = left
            while x <= right:
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                x += step

            # Horizontal lines
            y = top
            while y <= bottom:
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
                y += step

        painter.restore()

    def set_tool(self, tool: ToolMode):
        """Change active tool and update interaction flags."""
        self.current_tool = tool
        # Clear preview or in-progress items if switching
        if self._preview_shape and self._preview_shape.scene() == self:
            self.removeItem(self._preview_shape)
            self._preview_shape = None

        if tool != ToolMode.SELECT:
            self.clearSelection()

        # Lock/unlock items depending on tool mode so drawing doesn't grab existing items
        is_select_mode = (tool == ToolMode.SELECT)
        for item in self.items():
            if isinstance(item, BaseCanvasItem):
                item.setFlag(BaseCanvasItem.GraphicsItemFlag.ItemIsMovable, is_select_mode)
                item.setFlag(BaseCanvasItem.GraphicsItemFlag.ItemIsSelectable, is_select_mode)

        self.update()
        self.tool_changed.emit(tool)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.scenePos()

        # Tool: PEN
        if self.current_tool == ToolMode.PEN:
            top_z = max([it.zValue() for it in self.items()] + [Z_STROKE])
            self._current_stroke = StrokeItem(
                points=[pos],
                color=self.pen_color,
                width=self.pen_width
            )
            self._current_stroke.setZValue(top_z + 0.1)
            self.addItem(self._current_stroke)
            event.accept()
            return

        # Tool: ERASER
        if self.current_tool == ToolMode.ERASER:
            self._erase_at_point(pos)
            event.accept()
            return

        # Tool: SHAPE
        if self.current_tool == ToolMode.SHAPE:
            self._shape_start_pos = pos
            self._preview_shape = ShapeItem(
                shape_type=self.current_shape_type,
                x=pos.x(),
                y=pos.y(),
                width=10,
                height=10
            )
            self._preview_shape.stroke_color = self.shape_stroke_color
            self._preview_shape.stroke_width = self.shape_stroke_width
            self._preview_shape.fill_color = self.shape_fill_color
            self._preview_shape.fill_transparent = self.shape_fill_transparent
            if self.current_shape_type in (ShapeType.LINE, ShapeType.ARROW):
                self._preview_shape.p1 = QPointF(0, 0)
                self._preview_shape.p2 = QPointF(0, 0)
                self._preview_shape._rect = QRectF(0, 0, 1, 1)
            self.addItem(self._preview_shape)
            event.accept()
            return

        # Tool: TEXT
        if self.current_tool == ToolMode.TEXT:
            txt_item = TextItem(text="Type here...", x=pos.x(), y=pos.y(), width=200)
            cmd = AddItemsCommand(self, [txt_item], "Create Text")
            self.undo_stack.push(cmd)
            self.clearSelection()
            txt_item.setSelected(True)
            txt_item.start_editing()
            # Switch back to select tool
            self.set_tool(ToolMode.SELECT)
            event.accept()
            return

        # Tool: SELECT (track start positions for multi-move undo)
        if self.current_tool == ToolMode.SELECT:
            clicked_item = self.itemAt(pos, self.views()[0].transform() if self.views() else self.transform())
            selected = [it for it in self.selectedItems() if isinstance(it, BaseCanvasItem)]

            if clicked_item and isinstance(clicked_item, BaseCanvasItem):
                self._moving_items = selected if clicked_item in selected else [clicked_item]
                self._start_item_positions = [it.pos() for it in self._moving_items]
                self._is_moving_selection = True
            else:
                self._moving_items = []
                self._start_item_positions = []
                self._is_moving_selection = False

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        pos = event.scenePos()

        # Tool: PEN
        if self.current_tool == ToolMode.PEN and self._current_stroke:
            self._current_stroke.add_point(pos)
            self._current_stroke.update()
            event.accept()
            return

        # Tool: ERASER
        if self.current_tool == ToolMode.ERASER and (event.buttons() & Qt.MouseButton.LeftButton):
            self._erase_at_point(pos)
            event.accept()
            return

        # Tool: SHAPE preview
        if self.current_tool == ToolMode.SHAPE and self._preview_shape:
            start = self._shape_start_pos
            curr = pos
            keep_square = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

            if self.current_shape_type in (ShapeType.LINE, ShapeType.ARROW):
                delta = curr - start
                if keep_square:
                    import math
                    length = math.hypot(delta.x(), delta.y())
                    if length > 0.001:
                        angle = math.atan2(delta.y(), delta.x())
                        snap_angle = round(angle / (math.pi / 4.0)) * (math.pi / 4.0)
                        delta = QPointF(length * math.cos(snap_angle), length * math.sin(snap_angle))

                self._preview_shape.prepareGeometryChange()
                self._preview_shape.p1 = QPointF(0, 0)
                self._preview_shape.p2 = delta
                self._preview_shape.setPos(start)
                min_x = min(0.0, delta.x())
                min_y = min(0.0, delta.y())
                max_x = max(0.0, delta.x())
                max_y = max(0.0, delta.y())
                self._preview_shape._rect = QRectF(min_x, min_y, max(1.0, max_x - min_x), max(1.0, max_y - min_y))
                self._preview_shape.update()
            else:
                x = min(start.x(), curr.x())
                y = min(start.y(), curr.y())
                w = abs(curr.x() - start.x())
                h = abs(curr.y() - start.y())

                if keep_square:
                    side = max(w, h)
                    w = side
                    h = side
                    if curr.x() < start.x():
                        x = start.x() - side
                    if curr.y() < start.y():
                        y = start.y() - side

                self._preview_shape.setPos(x, y)
                self._preview_shape.set_size(max(10.0, w), max(10.0, h))

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        # Tool: PEN
        if self.current_tool == ToolMode.PEN and self._current_stroke:
            stroke = self._current_stroke
            self._current_stroke = None
            stroke.finish_stroke()
            # Register undo command without selecting stroke
            cmd = AddItemsCommand(self, [stroke], "Draw Stroke", select_items=False)
            self.undo_stack.push(cmd)
            event.accept()
            return

        # Tool: SHAPE
        if self.current_tool == ToolMode.SHAPE and self._preview_shape:
            shape = self._preview_shape
            self._preview_shape = None
            is_valid = False
            if shape.is_linear_item:
                is_valid = (shape.p2 - shape.p1).manhattanLength() > 4.0
            else:
                is_valid = shape.rect.width() > 5 or shape.rect.height() > 5

            if is_valid:
                cmd = AddItemsCommand(self, [shape], f"Create {shape.shape_type.value.capitalize()}")
                self.undo_stack.push(cmd)
                self.clearSelection()
                shape.setSelected(True)
                # Automatically shift to select mode after creating a shape
                self.set_tool(ToolMode.SELECT)
            else:
                self.removeItem(shape)
            event.accept()
            return

        # Multi-move undo commit
        if self._is_moving_selection and self._moving_items:
            self._is_moving_selection = False
            curr_positions = [it.pos() for it in self._moving_items]
            changed = any(
                (p1 - p2).manhattanLength() > 1.0
                for p1, p2 in zip(self._start_item_positions, curr_positions)
            )
            if changed:
                cmd = MoveItemsCommand(self._moving_items, self._start_item_positions, curr_positions)
                self.undo_stack.push(cmd)
            self._moving_items = []
            self._start_item_positions = []

        super().mouseReleaseEvent(event)

    def _erase_at_point(self, pos: QPointF):
        """Find strokes or items under eraser cursor and remove them with undo support."""
        erased = []
        for it in self.items():
            if isinstance(it, StrokeItem):
                if it.intersects_segment(pos, pos, tolerance=12.0):
                    erased.append(it)

        if erased:
            cmd = DeleteItemsCommand(self, erased, "Erase Strokes")
            self.undo_stack.push(cmd)

    def _on_selection_changed(self):
        selected = [it for it in self.selectedItems() if isinstance(it, BaseCanvasItem)]
        self.selection_state_changed.emit(selected)

    def select_all(self):
        """Select all canvas items."""
        for it in self.items():
            if isinstance(it, BaseCanvasItem):
                it.setSelected(True)

    def delete_selection(self):
        """Delete currently selected items with undo."""
        selected = [it for it in self.selectedItems() if isinstance(it, BaseCanvasItem)]
        if selected:
            cmd = DeleteItemsCommand(self, selected, "Delete Items")
            self.undo_stack.push(cmd)
