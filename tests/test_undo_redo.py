"""Unit tests for undo/redo commands."""

from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QGraphicsScene
from vait.constants import ShapeType
from vait.items import ShapeItem, TextItem
from vait.commands.undo_commands import (
    AddItemsCommand,
    DeleteItemsCommand,
    MoveItemsCommand,
    TransformItemCommand,
    ChangePropertyCommand,
    EditTextCommand
)

def test_add_and_delete_commands(qapp):
    scene = QGraphicsScene()
    stack = QUndoStack()

    item1 = ShapeItem(shape_type=ShapeType.RECTANGLE, x=10, y=10)
    item2 = TextItem("Test Text", x=50, y=50)

    # 1. Add command
    cmd_add = AddItemsCommand(scene, [item1, item2])
    stack.push(cmd_add)

    assert len(scene.items()) == 3  # item1, item2, plus item2's inner editor child
    assert item1 in scene.items()

    # 2. Undo Add
    stack.undo()
    assert item1 not in scene.items()
    assert item2 not in scene.items()

    # 3. Redo Add
    stack.redo()
    assert item1 in scene.items()
    assert item2 in scene.items()

    # 4. Delete command
    cmd_del = DeleteItemsCommand(scene, [item1])
    stack.push(cmd_del)
    assert item1 not in scene.items()

    # 5. Undo Delete
    stack.undo()
    assert item1 in scene.items()

def test_move_command(qapp):
    scene = QGraphicsScene()
    stack = QUndoStack()

    item = ShapeItem(x=100, y=100)
    scene.addItem(item)

    old_pos = [QPointF(100, 100)]
    new_pos = [QPointF(250, 300)]

    cmd_move = MoveItemsCommand([item], old_pos, new_pos)
    stack.push(cmd_move)
    assert item.pos() == QPointF(250, 300)

    stack.undo()
    assert item.pos() == QPointF(100, 100)

    stack.redo()
    assert item.pos() == QPointF(250, 300)

def test_change_property_command(qapp):
    stack = QUndoStack()
    item = ShapeItem()
    item.stroke_color = "#000000"

    cmd = ChangePropertyCommand([item], "stroke_color", ["#000000"], ["#ff5500"])
    stack.push(cmd)
    assert item.stroke_color == "#ff5500"

    stack.undo()
    assert item.stroke_color == "#000000"

    stack.redo()
    assert item.stroke_color == "#ff5500"

def test_edit_text_command(qapp):
    stack = QUndoStack()
    txt = TextItem("Original")

    cmd = EditTextCommand(txt, "Original", "Modified")
    stack.push(cmd)
    assert txt.get_plain_text() == "Modified"

    stack.undo()
    assert txt.get_plain_text() == "Original"

    stack.redo()
    assert txt.get_plain_text() == "Modified"
