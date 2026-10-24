"""Unit tests for canvas items: shapes, text, strokes, and images."""

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPixmap, QColor
from vait.constants import ShapeType
from vait.items import ShapeItem, TextItem, StrokeItem, ImageItem, item_from_dict

def test_shape_item_lifecycle(qapp):
    shape = ShapeItem(shape_type=ShapeType.RECTANGLE, x=50, y=100, width=200, height=150)
    shape.stroke_color = "#ff0000"
    shape.stroke_width = 4.0
    shape.fill_color = "#00ff00"
    shape.fill_transparent = False

    data = shape.to_dict()
    assert data["type"] == "shape"
    assert data["shape_type"] == "rectangle"
    assert data["stroke_color"] == "#ff0000"
    assert data["stroke_width"] == 4.0
    assert data["fill_color"] == "#00ff00"
    assert data["fill_transparent"] is False
    assert data["x"] == 50
    assert data["y"] == 100

    restored = item_from_dict(data)
    assert isinstance(restored, ShapeItem)
    assert restored.shape_type == ShapeType.RECTANGLE
    assert restored.pos() == QPointF(50, 100)
    assert restored.rect.width() == 200
    assert restored.rect.height() == 150
    assert restored.stroke_color == "#ff0000"

def test_linear_shapes(qapp):
    arrow = ShapeItem(shape_type=ShapeType.ARROW, x=10, y=20, width=100, height=80)
    assert arrow.is_linear_item is True
    assert arrow.include_rotate_handle is False

    data = arrow.to_dict()
    restored = item_from_dict(data)
    assert isinstance(restored, ShapeItem)
    assert restored.shape_type == ShapeType.ARROW
    assert restored.is_linear_item is True

def test_text_item_lifecycle(qapp):
    text_item = TextItem("Hello Whiteboard", x=30, y=40, width=250)
    text_item.font_size = 24
    text_item.font_bold = True
    text_item.text_color = "#2563eb"

    data = text_item.to_dict()
    assert data["type"] == "text"
    assert data["text"] == "Hello Whiteboard"
    assert data["font_size"] == 24
    assert data["font_bold"] is True

    restored = item_from_dict(data)
    assert isinstance(restored, TextItem)
    assert restored.get_plain_text() == "Hello Whiteboard"
    assert restored.font_size == 24
    assert restored.font_bold is True

def test_stroke_item_lifecycle(qapp):
    points = [QPointF(10, 10), QPointF(20, 25), QPointF(40, 50)]
    stroke = StrokeItem(points=points, color="#10b981", width=5.0)
    stroke.finish_stroke()

    assert len(stroke.points) == 3
    assert stroke.color == "#10b981"
    assert stroke.stroke_width == 5.0

    data = stroke.to_dict()
    assert data["type"] == "stroke"
    assert data["color"] == "#10b981"
    assert len(data["points"]) == 3

    restored = item_from_dict(data)
    assert isinstance(restored, StrokeItem)
    assert restored.color == "#10b981"
    assert len(restored.points) == 3

def test_image_item_lifecycle(qapp):
    pix = QPixmap(100, 80)
    pix.fill(QColor("blue"))
    img = ImageItem(pixmap=pix, x=15, y=25)

    assert img.lock_aspect_ratio is True
    assert img.rect.width() == 100
    assert img.rect.height() == 80
    assert img.raw_bytes is not None

    data = img.to_dict()
    assert data["type"] == "image"
    assert data["x"] == 15
    assert data["y"] == 25

    restored = item_from_dict(data)
    assert isinstance(restored, ImageItem)
    assert restored.pos() == QPointF(15, 25)
    assert not restored.pixmap.isNull()

def test_create_app_icon(qapp):
    from vait.ui.icons import create_app_icon, render_app_icon_pixmap
    icon = create_app_icon()
    assert not icon.isNull()
    pix = render_app_icon_pixmap(64)
    assert not pix.isNull()
    assert pix.width() == 64
    assert pix.height() == 64

