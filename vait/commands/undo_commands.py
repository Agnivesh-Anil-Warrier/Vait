"""Undo and redo commands using QUndoCommand."""

from typing import Any, Sequence
from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

from vait.items.base_item import BaseCanvasItem
from vait.items.text_item import TextItem
from vait.constants import ShapeType

class AddItemsCommand(QUndoCommand):
    """Command for adding one or multiple items to the canvas."""

    def __init__(
        self,
        scene: QGraphicsScene,
        items: Sequence[QGraphicsItem],
        text: str = "Add Item",
        select_items: bool = True
    ):
        super().__init__(text)
        self.scene = scene
        self.items = list(items)
        self.select_items = select_items

    def undo(self):
        for item in self.items:
            if item.scene() == self.scene:
                self.scene.removeItem(item)

    def redo(self):
        for item in self.items:
            if item.scene() != self.scene:
                self.scene.addItem(item)
        if self.select_items:
            self.scene.clearSelection()
            for item in self.items:
                item.setSelected(True)
        else:
            for item in self.items:
                item.setSelected(False)

class DeleteItemsCommand(QUndoCommand):
    """Command for deleting one or multiple items from the canvas."""

    def __init__(self, scene: QGraphicsScene, items: Sequence[QGraphicsItem], text: str = "Delete Item"):
        super().__init__(text)
        self.scene = scene
        self.items = list(items)

    def undo(self):
        for item in self.items:
            if item.scene() != self.scene:
                self.scene.addItem(item)
        self.scene.clearSelection()
        for item in self.items:
            item.setSelected(True)

    def redo(self):
        for item in self.items:
            if item.scene() == self.scene:
                self.scene.removeItem(item)

class MoveItemsCommand(QUndoCommand):
    """Command for moving items across the canvas."""

    def __init__(
        self,
        items: Sequence[BaseCanvasItem],
        old_positions: Sequence[QPointF],
        new_positions: Sequence[QPointF],
        text: str = "Move"
    ):
        super().__init__(text)
        self.items = list(items)
        self.old_positions = [QPointF(p) for p in old_positions]
        self.new_positions = [QPointF(p) for p in new_positions]

    def undo(self):
        for item, pos in zip(self.items, self.old_positions):
            item.setPos(pos)

    def redo(self):
        for item, pos in zip(self.items, self.new_positions):
            item.setPos(pos)

class TransformItemCommand(QUndoCommand):
    """Command for resizing or rotating an item."""

    def __init__(
        self,
        item: BaseCanvasItem,
        old_state: dict,
        new_state: dict,
        text: str = "Transform"
    ):
        super().__init__(text)
        self.item = item
        self.old_state = old_state
        self.new_state = new_state

    def undo(self):
        self.item.apply_geometry_state(self.old_state)

    def redo(self):
        self.item.apply_geometry_state(self.new_state)

class ChangePropertyCommand(QUndoCommand):
    """Command for updating styling properties (color, stroke width, fill, font)."""

    def __init__(
        self,
        items: Sequence[BaseCanvasItem],
        prop_name: str,
        old_values: Sequence[Any],
        new_values: Sequence[Any],
        text: str = "Change Property"
    ):
        super().__init__(text)
        self.items = list(items)
        self.prop_name = prop_name
        self.old_values = list(old_values)
        self.new_values = list(new_values)

    def undo(self):
        for item, val in zip(self.items, self.old_values):
            setattr(item, self.prop_name, val)
            if self.prop_name == "shape_type" and hasattr(item, "is_linear_item"):
                item.is_linear_item = val in (ShapeType.LINE, ShapeType.ARROW)
                item.include_rotate_handle = not item.is_linear_item
            if hasattr(item, "_apply_styling"):
                item._apply_styling()
            item.update()

    def redo(self):
        for item, val in zip(self.items, self.new_values):
            setattr(item, self.prop_name, val)
            if self.prop_name == "shape_type" and hasattr(item, "is_linear_item"):
                item.is_linear_item = val in (ShapeType.LINE, ShapeType.ARROW)
                item.include_rotate_handle = not item.is_linear_item
            if hasattr(item, "_apply_styling"):
                item._apply_styling()
            item.update()

class EditTextCommand(QUndoCommand):
    """Command for text content edits."""

    def __init__(self, item: TextItem, old_text: str, new_text: str, text: str = "Edit Text"):
        super().__init__(text)
        self.item = item
        self.old_text = old_text
        self.new_text = new_text

    def undo(self):
        self.item.set_plain_text(self.old_text)

    def redo(self):
        self.item.set_plain_text(self.new_text)
