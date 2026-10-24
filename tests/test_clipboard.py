"""Unit tests for internal and external clipboard operations."""

from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QGraphicsScene

from vait.constants import ShapeType
from vait.items import ShapeItem, TextItem
from vait.clipboard.clipboard_manager import ClipboardManager

def test_copy_and_paste_internal(qapp):
    scene = QGraphicsScene()
    stack = QUndoStack()
    clip_mgr = ClipboardManager(scene, stack)

    shape = ShapeItem(shape_type=ShapeType.ELLIPSE, x=50, y=50, width=120, height=80)
    scene.addItem(shape)
    shape.setSelected(True)

    # Copy
    copied = clip_mgr.copy_selection()
    assert copied is True

    # Paste at target pos
    target_pos = QPointF(200, 200)
    pasted = clip_mgr.paste_from_clipboard(target_pos=target_pos)
    assert len(pasted) == 1
    assert pasted[0].item_id != shape.item_id  # Unique fresh ID
    assert pasted[0].shape_type == ShapeType.ELLIPSE

    # Verify added to scene and undoable
    assert pasted[0] in scene.items()
    stack.undo()
    assert pasted[0] not in scene.items()

def test_duplicate_selection(qapp):
    scene = QGraphicsScene()
    stack = QUndoStack()
    clip_mgr = ClipboardManager(scene, stack)

    txt = TextItem("Duplicate me", x=100, y=100)
    scene.addItem(txt)
    txt.setSelected(True)

    dupes = clip_mgr.duplicate_selection(offset=QPointF(30, 30))
    assert len(dupes) == 1
    assert dupes[0].item_id != txt.item_id
    assert dupes[0].pos() == QPointF(130, 130)
    assert dupes[0].get_plain_text() == "Duplicate me"
