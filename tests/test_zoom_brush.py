"""Unit and integration tests for zoom-aware brush size, cursor preview, and coordinate system."""

import math
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QUndoStack, QMouseEvent, QCursor
from PySide6.QtWidgets import QGraphicsSceneMouseEvent

from vait.constants import ToolMode, ShapeType, DEFAULT_PEN_WIDTH, DEFAULT_PEN_COLOR
from vait.canvas.canvas_scene import InfiniteCanvasScene
from vait.canvas.canvas_view import InfiniteCanvasView
from vait.items import StrokeItem, ShapeItem
from vait.ui.icons import create_brush_cursor


def test_brush_cursor_properties(qapp):
    """Verify circular brush cursor creation, diameter, hotspot, and visual consistency."""
    # Test multiple configured screen-space brush sizes
    for brush_size in [2, 4, 8, 14, 20]:
        cursor = create_brush_cursor(diameter=brush_size, color="#2563eb", dpr=1.0)
        assert isinstance(cursor, QCursor)
        pix = cursor.pixmap()
        assert not pix.isNull()

        # Hotspot must be at exact geometric center
        hotspot = cursor.hotSpot()
        expected_center = pix.width() // 2
        assert hotspot.x() == expected_center
        assert hotspot.y() == expected_center

        # Pixmap must be large enough to contain the circle and padding
        assert pix.width() >= brush_size


def test_constant_screen_space_brush_stroke_creation(qapp):
    """Test that newly drawn strokes compute scene_brush_width = screen_brush_width / zoom_scale
    at 100%, 50%, 43%, and 200% zoom, maintaining constant apparent screen thickness."""
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)
    view.resize(800, 600)
    view.show()

    scene.set_tool(ToolMode.PEN)
    configured_brush_size = 4.0  # 4 px on screen
    scene.pen_width = configured_brush_size

    test_zooms = [1.0, 0.5, 0.43, 2.0]
    expected_scene_widths = {
        1.0: 4.0,
        0.5: 8.0,
        0.43: 4.0 / 0.43,   # ~9.3023
        2.0: 2.0,
    }

    for zoom in test_zooms:
        view.set_zoom_level(zoom)
        actual_zoom = view.transform().m11()
        assert abs(actual_zoom - zoom) < 1e-4

        # Simulate drawing a stroke
        start_scene = view.mapToScene(QPoint(150, 150))
        end_scene = view.mapToScene(QPoint(150, 250))

        press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
        press_ev.setScenePos(start_scene)
        press_ev.setButton(Qt.MouseButton.LeftButton)
        scene.mousePressEvent(press_ev)

        assert scene._current_stroke is not None
        stroke = scene._current_stroke

        # Verify stroke width in canvas/scene coordinates
        expected_w = expected_scene_widths[zoom]
        assert abs(stroke.stroke_width - expected_w) < 1e-3, (
            f"At zoom {zoom*100}%, expected scene width {expected_w}, got {stroke.stroke_width}"
        )

        # Apparent screen thickness must be constant (~4 px)
        apparent_screen_thickness = stroke.stroke_width * actual_zoom
        assert abs(apparent_screen_thickness - configured_brush_size) < 1e-3

        # Add point and release
        move_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseMove)
        move_ev.setScenePos(end_scene)
        scene.mouseMoveEvent(move_ev)

        rel_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
        rel_ev.setScenePos(end_scene)
        rel_ev.setButton(Qt.MouseButton.LeftButton)
        scene.mouseReleaseEvent(rel_ev)


def test_existing_strokes_scale_naturally_with_canvas(qapp):
    """When the user zooms after drawing, existing strokes must remain attached to
    their canvas coordinates and scale naturally, without resizing their scene coordinates."""
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)
    view.resize(800, 600)
    view.show()

    scene.set_tool(ToolMode.PEN)
    scene.pen_width = 4.0

    # Draw at 43% zoom
    view.set_zoom_level(0.43)
    p1 = QPointF(100, 100)
    p2 = QPointF(100, 200)

    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setScenePos(p1)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    scene.mousePressEvent(press_ev)

    rel_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMouseRelease)
    rel_ev.setScenePos(p2)
    rel_ev.setButton(Qt.MouseButton.LeftButton)
    scene.mouseReleaseEvent(rel_ev)

    strokes = [it for it in scene.items() if isinstance(it, StrokeItem)]
    assert len(strokes) == 1
    drawn_stroke = strokes[0]
    initial_scene_width = drawn_stroke.stroke_width
    assert abs(initial_scene_width - (4.0 / 0.43)) < 1e-3

    # Now zoom to 100%, 200%, 50%
    for new_zoom in [1.0, 2.0, 0.5]:
        view.set_zoom_level(new_zoom)
        # The existing stroke's canvas scene stroke_width must remain unchanged
        assert drawn_stroke.stroke_width == initial_scene_width, (
            "Existing stroke's scene stroke_width must not be mutated on zoom"
        )


def test_panning_does_not_affect_brush_size(qapp):
    """Verify that panning the viewport does not alter zoom scale or scene brush width."""
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)
    view.resize(800, 600)
    view.show()

    scene.set_tool(ToolMode.PEN)
    scene.pen_width = 6.0
    view.set_zoom_level(1.0)

    # Pan by moving scrollbars
    view.horizontalScrollBar().setValue(250)
    view.verticalScrollBar().setValue(350)

    # Zoom scale must still be 1.0
    assert abs(view.transform().m11() - 1.0) < 1e-5
    assert abs(scene.get_current_zoom_scale() - 1.0) < 1e-5

    # Stroke drawn while panned must still have width = 6.0
    p1 = view.mapToScene(QPoint(100, 100))
    press_ev = QGraphicsSceneMouseEvent(QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress)
    press_ev.setScenePos(p1)
    press_ev.setButton(Qt.MouseButton.LeftButton)
    scene.mousePressEvent(press_ev)

    stroke = scene._current_stroke
    assert stroke is not None
    assert abs(stroke.stroke_width - 6.0) < 1e-4
    scene.mouseReleaseEvent(press_ev)


def test_cursor_active_only_when_drawing_tool_is_active(qapp):
    """Verify custom circular brush cursor is displayed when PEN tool is active,
    and hidden/replaced when another tool is selected."""
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)
    view.resize(800, 600)
    view.show()

    # Default tool is SELECT
    assert scene.current_tool == ToolMode.SELECT
    assert view.viewport().cursor().shape() != Qt.CursorShape.BitmapCursor

    # Switch to PEN
    scene.set_tool(ToolMode.PEN)
    # Viewport cursor should be custom BitmapCursor representing circular brush
    assert view.viewport().cursor().shape() == Qt.CursorShape.BitmapCursor

    # Switch to PAN
    scene.set_tool(ToolMode.PAN)
    assert view.viewport().cursor().shape() == Qt.CursorShape.OpenHandCursor

    # Switch to ERASER
    scene.set_tool(ToolMode.ERASER)
    assert view.viewport().cursor().shape() == Qt.CursorShape.CrossCursor

    # Switch to TEXT
    scene.set_tool(ToolMode.TEXT)
    assert view.viewport().cursor().shape() == Qt.CursorShape.IBeamCursor

    # Switch back to PEN
    scene.set_tool(ToolMode.PEN)
    assert view.viewport().cursor().shape() == Qt.CursorShape.BitmapCursor


def test_brush_size_change_updates_cursor(qapp):
    """Verify that updating scene.pen_width updates the cursor diameter."""
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)
    view.resize(800, 600)
    view.show()

    scene.set_tool(ToolMode.PEN)
    scene.pen_width = 4.0
    cur4 = view.viewport().cursor()
    pix4 = cur4.pixmap()

    scene.pen_width = 16.0
    cur16 = view.viewport().cursor()
    pix16 = cur16.pixmap()

    # Pixmap of 16px brush cursor must be strictly larger than 4px
    assert pix16.width() > pix4.width()


def test_canvas_item_hover_does_not_override_brush_cursor(qapp):
    """When PEN tool is active, moving the mouse over items on the canvas
    must not revert the cursor back to ArrowCursor or SizeAllCursor."""
    stack = QUndoStack()
    scene = InfiniteCanvasScene(stack)
    view = InfiniteCanvasView(scene)
    view.resize(800, 600)
    view.show()

    # Add a shape item
    shape = ShapeItem(shape_type=ShapeType.RECTANGLE, x=50, y=50, width=150, height=150)
    scene.addItem(shape)

    # Set tool to PEN
    scene.set_tool(ToolMode.PEN)

    # Trigger hover on the shape
    from PySide6.QtWidgets import QGraphicsSceneHoverEvent
    hover_ev = QGraphicsSceneHoverEvent(QGraphicsSceneHoverEvent.Type.GraphicsSceneHoverMove)
    hover_ev.setPos(QPointF(20, 20))
    hover_ev.setScenePos(QPointF(70, 70))
    shape.hoverMoveEvent(hover_ev)

    # The shape should NOT have set a cursor on itself
    assert shape.hasCursor() is False
