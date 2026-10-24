"""Graphics items package and item factory."""

from typing import Optional, Any
from vait.items.base_item import BaseCanvasItem
from vait.items.shape_item import ShapeItem
from vait.items.text_item import TextItem
from vait.items.image_item import ImageItem
from vait.items.stroke_item import StrokeItem

def item_from_dict(data: dict[str, Any]) -> Optional[BaseCanvasItem]:
    """Factory creating canvas item from serialized dictionary."""
    itype = data.get("type", "")
    item: Optional[BaseCanvasItem] = None

    if itype == "shape":
        item = ShapeItem()
    elif itype == "text":
        item = TextItem()
    elif itype == "image":
        item = ImageItem()
    elif itype == "stroke":
        item = StrokeItem()

    if item is not None:
        item.from_dict(data)

    return item

__all__ = [
    "BaseCanvasItem",
    "ShapeItem",
    "TextItem",
    "ImageItem",
    "StrokeItem",
    "item_from_dict",
]
