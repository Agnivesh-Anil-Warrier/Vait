"""Integration tests verifying MainWindow interactions, UI controls, and project workflow."""

import os
import tempfile
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QApplication
from vait.ui.main_window import MainWindow
from vait.constants import ToolMode, ShapeType
from vait.items import ShapeItem, TextItem, StrokeItem

def test_mainwindow_full_workflow(qapp):
    win = MainWindow()
    win.show()

    # 1. Test initial state
    assert win.scene is not None
    assert win.view is not None
    assert win.view.zoom_level == 1.0

    # 2. Add shapes and text to canvas
    shape = ShapeItem(shape_type=ShapeType.RECTANGLE, x=100, y=150, width=150, height=100)
    win.scene.addItem(shape)
    shape.setSelected(True)

    # Check properties panel reacts to selection
    assert len(win.properties_panel._current_items) == 1
    assert win.properties_panel.lbl_stroke.isVisible() is True

    # 3. Test changing color through properties
    win.properties_panel.spin_stroke_width.setValue(6)
    assert shape.stroke_width == 6.0

    # 4. Test Text item inline editing
    text_item = TextItem(text="Integration Test", x=300, y=150)
    win.scene.addItem(text_item)
    text_item.set_plain_text("Updated Text")
    assert text_item.get_plain_text() == "Updated Text"

    # 5. Test Zoom actions
    win.act_zoom_in.trigger()
    assert win.view.zoom_level > 1.0
    win.act_reset_zoom.trigger()
    assert win.view.zoom_level == 1.0

    # 6. Test Save and Load roundtrip via MainWindow methods
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "integration_canvas.canvas")
        saved = win._do_save(save_path)
        assert saved is True
        assert os.path.exists(save_path)

        # Clear canvas
        win.scene.clear()
        assert len(win.scene.items()) == 0

        # Open project
        win.open_project_file(save_path)
        # Should restore shape + text items (and inner editor child)
        items = [it for it in win.scene.items() if hasattr(it, "item_type")]
        assert len(items) == 2

    win.close()
