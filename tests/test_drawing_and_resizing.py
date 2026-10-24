"""Specific tests verifying freehand drawing, stroke non-selection, and handle-based resizing."""

from PySide6.QtCore import QPointF, QPoint, Qt, QRectF
from PySide6.QtGui import QUndoStack, QMouseEvent, QCursor, QPixmap, QColor, QPainter
from PySide6.QtWidgets import (
    QGraphicsSceneMouseEvent,
    QGraphicsItem,
    QStyleOptionGraphicsItem
)

from vait.constants import ToolMode, ShapeType
from vait.canvas.canvas_scene import InfiniteCanvasScene
from vait.canvas.canvas_view import InfiniteCanvasView
from vait.items import ShapeItem, StrokeItem, ImageItem, TextItem
from vait.items.handles import HandleId, get_handle_positions, get_handle_at_pos

def test_freehand_pen_drawing_not_selected(qapp):
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)

    scene.set_tool(ToolMode.PEN)
    assert scene.current_tool == ToolMode.PEN

    # Simulate mouse press at (100, 100)
    press_event = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_event.setScenePos(QPointF(100, 100))
    press_event.setButton(Qt.MouseButton.LeftButton)
    scene.mousePressEvent(press_event)

    assert scene._current_stroke is not None

    # Simulate mouse moves
    for y in range(110, 200, 20):
        move_event = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
        move_event.setScenePos(QPointF(100, y))
        scene.mouseMoveEvent(move_event)

    assert len(scene._current_stroke.points) > 2
    # Verify boundingRect is non-empty and encompasses the drawn path
    br = scene._current_stroke.boundingRect()
    assert br.height() >= 80

    # Simulate mouse release
    rel_event = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_event.setScenePos(QPointF(100, 200))
    rel_event.setButton(Qt.MouseButton.LeftButton)
    scene.mouseReleaseEvent(rel_event)

    strokes = [it for it in scene.items() if isinstance(it, StrokeItem)]
    assert len(strokes) == 1
    # Stroke must NOT be selected on creation
    assert strokes[0].isSelected() is False

def test_pen_drawing_in_front_of_image(qapp):
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)

    # 1. Add image to scene
    pix = QPixmap(200, 200)
    pix.fill(QColor("white"))
    image = ImageItem(pixmap=pix, x=50, y=50)
    scene.addItem(image)

    # 2. Switch to Pen and draw over the image
    scene.set_tool(ToolMode.PEN)
    press_event = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_event.setScenePos(QPointF(100, 100))
    press_event.setButton(Qt.MouseButton.LeftButton)
    scene.mousePressEvent(press_event)

    rel_event = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_event.setScenePos(QPointF(150, 150))
    rel_event.setButton(Qt.MouseButton.LeftButton)
    scene.mouseReleaseEvent(rel_event)

    strokes = [it for it in scene.items() if isinstance(it, StrokeItem)]
    assert len(strokes) == 1
    # Drawing stroke z-value must be strictly higher than image z-value
    assert strokes[0].zValue() > image.zValue()

def test_shape_handle_hit_test_and_resize(qapp):
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)

    scene.set_tool(ToolMode.SELECT)
    shape = ShapeItem(shape_type=ShapeType.RECTANGLE, x=100, y=100, width=120, height=80)
    scene.addItem(shape)
    shape.setSelected(True)

    # 1. Verify shape() includes selection handles when selected
    br = shape.boundingRect()
    item_shape = shape.shape()
    assert item_shape.boundingRect().contains(br.center())

    # 2. Get bottom-right handle position
    handles = get_handle_positions(shape.rect, scale=1.0)
    se_pt = handles[HandleId.BOTTOM_RIGHT]
    assert get_handle_at_pos(se_pt, shape.rect, scale=1.0) == HandleId.BOTTOM_RIGHT

    # 3. Simulate mouse press on bottom-right handle
    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    press_ev.setPos(se_pt)
    press_ev.setScenePos(shape.mapToScene(se_pt))
    shape.mousePressEvent(press_ev)

    assert shape._active_handle == HandleId.BOTTOM_RIGHT

    # 4. Simulate dragging handle by (+50, +30)
    move_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    move_ev.setScenePos(shape.mapToScene(se_pt) + QPointF(50, 30))
    shape.mouseMoveEvent(move_ev)

    assert shape.rect.width() == 170  # 120 + 50
    assert shape.rect.height() == 110  # 80 + 30

    # 5. Release handle
    rel_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_ev.setButton(Qt.MouseButton.LeftButton)
    shape.mouseReleaseEvent(rel_ev)

    assert shape._active_handle == HandleId.NONE
    assert shape.rect.width() == 170

def test_shape_top_left_resize_shifts_position(qapp):
    shape = ShapeItem(shape_type=ShapeType.RECTANGLE, x=100, y=100, width=100, height=100)
    shape.setSelected(True)

    handles = get_handle_positions(shape.rect, scale=1.0)
    nw_pt = handles[HandleId.TOP_LEFT]

    # Press on NW handle
    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    press_ev.setPos(nw_pt)
    press_ev.setScenePos(shape.mapToScene(nw_pt))
    shape.mousePressEvent(press_ev)

    assert shape._active_handle == HandleId.TOP_LEFT

    # Drag NW handle by (-20, -30) in scene (enlarging shape to top-left)
    move_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    move_ev.setScenePos(shape.mapToScene(nw_pt) + QPointF(-20, -30))
    shape.mouseMoveEvent(move_ev)

    assert shape.rect.width() == 120  # 100 - (-20)
    assert shape.rect.height() == 130  # 100 - (-30)
    assert shape.pos() == QPointF(80, 70)  # Top-left moved to (80, 70)

def test_image_resize_preserves_aspect_ratio(qapp):
    pix = QPixmap(200, 100)  # 2:1 aspect ratio
    pix.fill(QColor("red"))
    img = ImageItem(pixmap=pix, x=50, y=50)
    img.setSelected(True)
    assert img.lock_aspect_ratio is True

    handles = get_handle_positions(img.rect, scale=1.0)
    se_pt = handles[HandleId.BOTTOM_RIGHT]

    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    press_ev.setPos(se_pt)
    press_ev.setScenePos(img.mapToScene(se_pt))
    img.mousePressEvent(press_ev)

    # Drag bottom-right handle
    move_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    move_ev.setScenePos(img.mapToScene(se_pt) + QPointF(100, 100))
    img.mouseMoveEvent(move_ev)

    # Aspect ratio 2:1 preserved
    assert img.rect.width() == 300
    assert img.rect.height() == 150

def test_shape_creation_auto_shifts_to_select_mode(qapp):
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)

    scene.set_tool(ToolMode.SHAPE)
    scene.current_shape_type = ShapeType.RECTANGLE
    assert scene.current_tool == ToolMode.SHAPE

    # Mouse press to start shape
    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    press_ev.setScenePos(QPointF(50, 50))
    scene.mousePressEvent(press_ev)

    # Mouse move to expand shape
    move_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    move_ev.setScenePos(QPointF(200, 150))
    scene.mouseMoveEvent(move_ev)

    # Mouse release to finalize shape
    rel_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_ev.setButton(Qt.MouseButton.LeftButton)
    rel_ev.setScenePos(QPointF(200, 150))
    scene.mouseReleaseEvent(rel_ev)

    # 1. Shape created and selected
    shapes = [it for it in scene.items() if isinstance(it, ShapeItem)]
    assert len(shapes) == 1
    assert shapes[0].isSelected() is True

    # 2. Tool automatically shifted to SELECT mode
    assert scene.current_tool == ToolMode.SELECT

def test_color_persistence_across_objects(qapp):
    from vait.ui.properties_panel import PropertiesPanel
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    panel = PropertiesPanel(scene, stack)

    # 1. Create a shape and select it
    shape1 = ShapeItem(shape_type=ShapeType.RECTANGLE, x=10, y=10)
    scene.addItem(shape1)
    shape1.setSelected(True)
    panel.update_for_selection([shape1])

    # 2. Change stroke color to orange and fill color to green
    panel.scene.shape_stroke_color = "#f97316"
    panel.scene.shape_fill_color = "#22c55e"
    panel.scene.shape_fill_transparent = False

    # 3. Create a second shape
    scene.set_tool(ToolMode.SHAPE)
    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    press_ev.setScenePos(QPointF(100, 100))
    scene.mousePressEvent(press_ev)

    move_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    move_ev.setScenePos(QPointF(200, 200))
    scene.mouseMoveEvent(move_ev)

    rel_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_ev.setButton(Qt.MouseButton.LeftButton)
    rel_ev.setScenePos(QPointF(200, 200))
    scene.mouseReleaseEvent(rel_ev)

    shapes = [it for it in scene.items() if isinstance(it, ShapeItem) and it != shape1]
    assert len(shapes) == 1
    shape2 = shapes[0]

    # Verify shape2 kept the chosen colors instead of reverting to black/blue
    assert shape2.stroke_color == "#f97316"
    assert shape2.fill_color == "#22c55e"
    assert shape2.fill_transparent is False

    # 4. Deselect shape2 and verify outline/fill controls stay visible in SELECT mode
    scene.clearSelection()
    panel.update_for_selection([])
    assert not panel.btn_stroke_color.isHidden()
    assert not panel.btn_fill_color.isHidden()
    assert scene.shape_stroke_color == "#f97316"
    assert scene.shape_fill_color == "#22c55e"

    # 5. Select shape1 with different colors and verify active tool colors sync to shape1
    shape1.stroke_color = "#e11d48"
    shape1.fill_color = "#a855f7"
    panel.update_for_selection([shape1])
    assert scene.shape_stroke_color == "#e11d48"
    assert scene.shape_fill_color == "#a855f7"

def test_shape_type_switching_and_morphing(qapp):
    from vait.ui.main_window import MainWindow
    win = MainWindow()

    # 1. Default shape is RECTANGLE
    assert win.scene.current_shape_type == ShapeType.RECTANGLE

    # 2. Switch shape to ELLIPSE via _set_active_shape
    win._set_active_shape(ShapeType.ELLIPSE, "ellipse")
    assert win.scene.current_shape_type == ShapeType.ELLIPSE
    assert win.scene.current_tool == ToolMode.SHAPE

    # 3. Create an ellipse on the canvas
    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    press_ev.setScenePos(QPointF(50, 50))
    win.scene.mousePressEvent(press_ev)

    move_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    move_ev.setScenePos(QPointF(150, 150))
    win.scene.mouseMoveEvent(move_ev)

    rel_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_ev.setButton(Qt.MouseButton.LeftButton)
    rel_ev.setScenePos(QPointF(150, 150))
    win.scene.mouseReleaseEvent(rel_ev)

    shapes = [it for it in win.scene.items() if isinstance(it, ShapeItem)]
    assert len(shapes) == 1
    shape = shapes[0]
    assert shape.shape_type == ShapeType.ELLIPSE

    # 4. Shape is selected on canvas; switch shape type to DIAMOND via properties panel
    win.properties_panel.update_for_selection([shape])
    idx = win.properties_panel.combo_shape_type.findData(ShapeType.DIAMOND)
    assert idx >= 0
    win.properties_panel.combo_shape_type.setCurrentIndex(idx)

    # Shape should now be a DIAMOND!
    assert shape.shape_type == ShapeType.DIAMOND

    # 5. Undo restores to ELLIPSE
    win.undo_stack.undo()
    assert shape.shape_type == ShapeType.ELLIPSE

    # 6. Redo switches back to DIAMOND
    win.undo_stack.redo()
    assert shape.shape_type == ShapeType.DIAMOND

def test_stroke_width_any_value(qapp):
    from vait.ui.main_window import MainWindow
    win = MainWindow()

    shape = ShapeItem(shape_type=ShapeType.RECTANGLE, width=100, height=100)
    win.scene.addItem(shape)
    shape.setSelected(True)
    win.properties_panel.update_for_selection([shape])

    # Spinbox accepts values greater than 48px (e.g. 120px, 350px)
    win.properties_panel.spin_stroke_width.setValue(120)
    assert shape.stroke_width == 120.0
    assert win.scene.shape_stroke_width == 120.0

    win.properties_panel.spin_stroke_width.setValue(500)
    assert shape.stroke_width == 500.0

    # Bounding rect expands appropriately without clipping
    br = shape.boundingRect()
    assert br.width() > 100 + 400

def test_linear_shapes_drawing_and_handle_resizing(qapp):
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)

    # 1. Select LINE tool
    scene.set_tool(ToolMode.SHAPE)
    scene.current_shape_type = ShapeType.LINE

    # Mouse press at (100, 100)
    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    press_ev.setScenePos(QPointF(100, 100))
    scene.mousePressEvent(press_ev)

    # Drag to (200, 150)
    move_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    move_ev.setScenePos(QPointF(200, 150))
    scene.mouseMoveEvent(move_ev)

    # Release at (200, 150)
    rel_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_ev.setButton(Qt.MouseButton.LeftButton)
    rel_ev.setScenePos(QPointF(200, 150))
    scene.mouseReleaseEvent(rel_ev)

    # Line should be created and selected, scene returns to SELECT mode
    assert scene.current_tool == ToolMode.SELECT
    lines = [it for it in scene.items() if isinstance(it, ShapeItem) and it.shape_type == ShapeType.LINE]
    assert len(lines) == 1
    line = lines[0]
    assert line.isSelected() is True
    assert line.is_linear_item is True
    assert line.pos() == QPointF(100, 100)
    assert line.p1 == QPointF(0, 0)
    assert line.p2 == QPointF(100, 50)

    # Verify boundingRect calculates without error and includes handles & stroke padding
    br = line.boundingRect()
    assert br.isValid()
    assert br.width() >= 100
    assert br.height() >= 50

    # 2. Test handle detection on line
    handles = get_handle_positions(line.rect, scale=1.0, is_linear=True, p1=line.p1, p2=line.p2)
    assert HandleId.START_POINT in handles
    assert HandleId.END_POINT in handles
    assert handles[HandleId.START_POINT] == QPointF(0, 0)
    assert handles[HandleId.END_POINT] == QPointF(100, 50)

    h_end = get_handle_at_pos(QPointF(100, 50), line.rect, scale=1.0, is_linear=True, p1=line.p1, p2=line.p2)
    assert h_end == HandleId.END_POINT

    # 3. Drag END_POINT to (160, 90) in local coordinates
    press_handle = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_handle.setButton(Qt.MouseButton.LeftButton)
    press_handle.setPos(QPointF(100, 50))
    press_handle.setScenePos(line.mapToScene(QPointF(100, 50)))
    line.mousePressEvent(press_handle)

    assert line._active_handle == HandleId.END_POINT

    drag_handle = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    drag_handle.setPos(QPointF(160, 90))
    drag_handle.setScenePos(line.mapToScene(QPointF(160, 90)))
    line.mouseMoveEvent(drag_handle)

    assert line.p2 == QPointF(160, 90)

    release_handle = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    release_handle.setButton(Qt.MouseButton.LeftButton)
    release_handle.setPos(QPointF(160, 90))
    release_handle.setScenePos(line.mapToScene(QPointF(160, 90)))
    line.mouseReleaseEvent(release_handle)

    assert line._active_handle == HandleId.NONE
    assert line.p2 == QPointF(160, 90)

    # 4. Undo restores p2 to (100, 50)
    stack.undo()
    assert line.p2 == QPointF(100, 50)

    # Redo restores p2 to (160, 90)
    stack.redo()
    assert line.p2 == QPointF(160, 90)

    # 5. Draw ARROW interactively
    scene.set_tool(ToolMode.SHAPE)
    scene.current_shape_type = ShapeType.ARROW

    press_arr = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_arr.setButton(Qt.MouseButton.LeftButton)
    press_arr.setScenePos(QPointF(300, 300))
    scene.mousePressEvent(press_arr)

    move_arr = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
    move_arr.setScenePos(QPointF(450, 300))  # Horizontal arrow
    scene.mouseMoveEvent(move_arr)

    rel_arr = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_arr.setButton(Qt.MouseButton.LeftButton)
    rel_arr.setScenePos(QPointF(450, 300))
    scene.mouseReleaseEvent(rel_arr)

    arrows = [it for it in scene.items() if isinstance(it, ShapeItem) and it.shape_type == ShapeType.ARROW]
    assert len(arrows) == 1
    arrow = arrows[0]
    assert arrow.p1 == QPointF(0, 0)
    assert arrow.p2 == QPointF(150, 0)

    # Paint into a pixmap to test _draw_arrow execution
    pix = QPixmap(200, 200)
    painter = QPainter(pix)
    opt = QStyleOptionGraphicsItem()
    arrow.paint(painter, opt)
    painter.end()

def test_marquee_drag_selection_and_multi_delete_move(qapp):
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)
    view.resize(800, 600)
    view.show()

    # 1. Add a stroke and a rectangle
    stroke = StrokeItem([QPointF(50, 50), QPointF(100, 100), QPointF(120, 120)], color="#ff0000", width=4)
    scene.addItem(stroke)

    rect_shape = ShapeItem(shape_type=ShapeType.RECTANGLE, x=200, y=200, width=80, height=80)
    scene.addItem(rect_shape)

    assert not stroke.isSelected()
    assert not rect_shape.isSelected()

    # Ensure in SELECT mode
    scene.set_tool(ToolMode.SELECT)

    # 2. Simulate mouse press in empty space (scene: 10, 10) mapped to view
    p_start = view.mapFromScene(QPointF(10, 10))
    p_end = view.mapFromScene(QPointF(320, 320))

    press_ev = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        p_start,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    view.mousePressEvent(press_ev)

    assert view._is_rubber_banding is True
    assert view._rubber_band.isVisible() is True

    # 3. Simulate dragging to p_end, covering both the stroke and the rect
    move_ev = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        p_end,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    view.mouseMoveEvent(move_ev)

    # Both items should now be dynamically selected in the marquee
    assert stroke.isSelected() is True
    assert rect_shape.isSelected() is True
    assert len(scene.selectedItems()) == 2

    # 4. Simulate mouse release to commit marquee selection
    release_ev = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        p_end,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier
    )
    view.mouseReleaseEvent(release_ev)

    assert view._is_rubber_banding is False
    assert view._rubber_band.isVisible() is False
    assert stroke.isSelected() is True
    assert rect_shape.isSelected() is True

    # 5. Test multi-item delete (Delete button / shortcut)
    scene.delete_selection()
    assert stroke not in scene.items()
    assert rect_shape not in scene.items()
    assert len(scene.items()) == 0

    # Undo multi-delete restores both items
    stack.undo()
    assert stroke in scene.items()
    assert rect_shape in scene.items()
    assert stroke.isSelected() is True
    assert rect_shape.isSelected() is True

    # Redo multi-delete removes both items again
    stack.redo()
    assert stroke not in scene.items()
    assert rect_shape not in scene.items()

    # Undo to restore items for multi-move test
    stack.undo()
    assert stroke in scene.items()
    assert rect_shape in scene.items()

    # 6. Test multi-item move with MoveItemsCommand
    from vait.commands.undo_commands import MoveItemsCommand
    orig_stroke_pos = stroke.pos()
    orig_rect_pos = rect_shape.pos()
    new_stroke_pos = orig_stroke_pos + QPointF(50, 60)
    new_rect_pos = orig_rect_pos + QPointF(50, 60)

    move_cmd = MoveItemsCommand([stroke, rect_shape], [orig_stroke_pos, orig_rect_pos], [new_stroke_pos, new_rect_pos])
    stack.push(move_cmd)

    assert stroke.pos() == new_stroke_pos
    assert rect_shape.pos() == new_rect_pos

    # Undo multi-move
    stack.undo()
    assert stroke.pos() == orig_stroke_pos
    assert rect_shape.pos() == orig_rect_pos

    # Redo multi-move
    stack.redo()
    assert stroke.pos() == new_stroke_pos
    assert rect_shape.pos() == new_rect_pos

    # 7. Test Shift-marquee preserves initial selection
    scene.clearSelection()
    rect_shape.setSelected(True)
    assert rect_shape.isSelected() is True
    assert stroke.isSelected() is False

    # Shift-drag marquee covering only the stroke (scene: 40, 40 to 140, 140)
    p_shift_start = view.mapFromScene(QPointF(40, 40))
    p_shift_end = view.mapFromScene(QPointF(140, 140))

    shift_press = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        p_shift_start,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ShiftModifier
    )
    view.mousePressEvent(shift_press)
    assert view._is_rubber_banding is True

    shift_move = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        p_shift_end,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ShiftModifier
    )
    view.mouseMoveEvent(shift_move)

    # Both rect_shape (initially selected) and stroke (in marquee) must now be selected!
    assert stroke.isSelected() is True
    assert rect_shape.isSelected() is True

    shift_rel = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        p_shift_end,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.ShiftModifier
    )
    view.mouseReleaseEvent(shift_rel)

    assert view._is_rubber_banding is False
    assert stroke.isSelected() is True
    assert rect_shape.isSelected() is True



