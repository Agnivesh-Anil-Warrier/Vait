"""Unit tests for self-contained ZIP project saving, loading, and export."""

import os
import tempfile
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QGraphicsScene

from vait.constants import ShapeType
from vait.items import ShapeItem, TextItem, StrokeItem, ImageItem
from vait.storage.project_file import ProjectFileManager
from vait.storage.exporter import CanvasExporter

def test_save_and_load_project(qapp):
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_whiteboard.canvas")

        # Create diverse set of canvas items
        shape = ShapeItem(shape_type=ShapeType.DIAMOND, x=100, y=100, width=80, height=80)
        shape.stroke_color = "#3b82f6"

        text = TextItem("Test Persistent Text", x=200, y=200)
        text.font_size = 20

        stroke = StrokeItem(points=[QPointF(0, 0), QPointF(50, 50), QPointF(100, 30)])
        stroke.finish_stroke()

        pix = QPixmap(50, 50)
        pix.fill(QColor("purple"))
        image = ImageItem(pixmap=pix, x=300, y=300)

        items = [shape, text, stroke, image]
        view_state = {"zoom": 1.25, "center_x": 150.0, "center_y": 150.0}

        # Save project
        success = ProjectFileManager.save_project(filepath, items, view_state)
        assert success is True
        assert os.path.exists(filepath)

        # Load project
        loaded_items, loaded_view = ProjectFileManager.load_project(filepath)
        assert len(loaded_items) == 4
        assert loaded_view["zoom"] == 1.25

        types = [it.item_type for it in loaded_items]
        assert "shape" in types
        assert "text" in types
        assert "stroke" in types
        assert "image" in types

        # Verify image bytes and pixmap survived
        loaded_image = next(it for it in loaded_items if isinstance(it, ImageItem))
        assert not loaded_image.pixmap.isNull()
        assert loaded_image.pos() == QPointF(300, 300)

def test_export_to_image(qapp):
    scene = QGraphicsScene()
    shape = ShapeItem(shape_type=ShapeType.RECTANGLE, x=0, y=0, width=100, height=100)
    shape.fill_color = "#22c55e"
    shape.fill_transparent = False
    scene.addItem(shape)

    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = os.path.join(tmpdir, "exported.png")
        ok = CanvasExporter.export_to_image(scene, export_path, scope="all")
        assert ok is True
        assert os.path.exists(export_path)
        assert os.path.getsize(export_path) > 0
