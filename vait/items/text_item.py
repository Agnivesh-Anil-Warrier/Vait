"""Text box graphics item supporting multiline rich text, wrapping, inline editing, and styling."""

from typing import Optional, Any
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtWidgets import (
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
    QGraphicsItem
)
from PySide6.QtGui import (
    QPainter,
    QFont,
    QColor,
    QTextCursor,
    QTextCharFormat,
    QTextBlockFormat,
    QTextOption
)

from vait.constants import (
    Z_TEXT,
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    DEFAULT_TEXT_COLOR
)
from vait.items.base_item import BaseCanvasItem

class _InnerEditor(QGraphicsTextItem):
    """Child text item handling direct keyboard input and cursor focus."""

    def __init__(self, parent: "TextItem"):
        super().__init__(parent)
        self.parent_item = parent
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.parent_item.finish_editing()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
            event.accept()
            return
        super().keyPressEvent(event)

class TextItem(BaseCanvasItem):
    """Canvas item representing an editable multiline text box."""

    editing_finished = Signal(object, str, str)  # item, old_text, new_text

    def __init__(
        self,
        text: str = "Double click to edit",
        x: float = 0,
        y: float = 0,
        width: float = 200,
        parent=None
    ):
        super().__init__(x, y, width, 50, parent)
        self.item_type = "text"
        self.setZValue(Z_TEXT)

        self.padding = 6.0
        self.font_family: str = DEFAULT_FONT_FAMILY
        self.font_size: int = DEFAULT_FONT_SIZE
        self.font_bold: bool = False
        self.font_italic: bool = False
        self.text_color: str = DEFAULT_TEXT_COLOR
        self.text_alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft
        self.bg_color: Optional[str] = None  # Transparent by default, or card color e.g. "#fef08a" for sticky note

        self._old_text_before_edit: str = text
        self._is_editing: bool = False

        # Setup inner editor
        self._editor = _InnerEditor(self)
        self._editor.setPos(self.padding, self.padding)
        self._editor.setPlainText(text)
        self._apply_styling()
        self._update_text_layout()

    def _apply_styling(self):
        """Apply font, color, and alignment to inner editor."""
        font = QFont(self.font_family, self.font_size)
        font.setBold(self.font_bold)
        font.setItalic(self.font_italic)
        self._editor.setFont(font)
        self._editor.setDefaultTextColor(QColor(self.text_color))

        # Set alignment across the document
        doc = self._editor.document()
        opt = QTextOption()
        opt.setAlignment(self.text_alignment)
        opt.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        doc.setDefaultTextOption(opt)

        # Update block alignment
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.SelectionType.Document)
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(self.text_alignment)
        cursor.mergeBlockFormat(block_fmt)

    def _update_text_layout(self):
        """Update editor width and adjust parent height to fit text."""
        inner_w = max(40.0, self._rect.width() - self.padding * 2)
        self._editor.setTextWidth(inner_w)
        doc_h = self._editor.document().size().height()
        new_h = max(30.0, doc_h + self.padding * 2)

        if abs(new_h - self._rect.height()) > 1.0:
            self.prepareGeometryChange()
            self._rect = QRectF(self._rect.x(), self._rect.y(), self._rect.width(), new_h)
            self._update_transform_origin()
            self.update()

    def set_size(self, width: float, height: float):
        self.prepareGeometryChange()
        self._rect = QRectF(self._rect.x(), self._rect.y(), max(40.0, width), max(30.0, height))
        self._update_transform_origin()
        self._update_text_layout()

    def get_plain_text(self) -> str:
        return self._editor.toPlainText()

    def set_plain_text(self, text: str):
        self._editor.setPlainText(text)
        self._apply_styling()
        self._update_text_layout()

    def get_html(self) -> str:
        return self._editor.toHtml()

    def set_html(self, html: str):
        self._editor.setHtml(html)
        self._apply_styling()
        self._update_text_layout()

    def start_editing(self):
        """Enter inline editing mode."""
        if self._is_editing:
            return
        self._is_editing = True
        self._old_text_before_edit = self._editor.toPlainText()
        self._editor.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self._editor.setFocus()
        cursor = self._editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self._editor.setTextCursor(cursor)

    def finish_editing(self):
        """Exit inline editing mode and commit changes."""
        if not self._is_editing:
            return
        self._is_editing = False
        new_text = self._editor.toPlainText()
        self._update_text_layout()
        if new_text != self._old_text_before_edit:
            self.editing_finished.emit(self, self._old_text_before_edit, new_text)
            self.property_change_committed.emit(self, "text", self._old_text_before_edit, new_text)

    def mouseDoubleClickEvent(self, event):
        """Double click opens inline text editor."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_editing()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def paint_content(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        if self.bg_color:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(self.bg_color))
            painter.drawRoundedRect(self._rect, 6.0, 6.0)
            painter.restore()

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        align_str = "left"
        if self.text_alignment == Qt.AlignmentFlag.AlignCenter:
            align_str = "center"
        elif self.text_alignment == Qt.AlignmentFlag.AlignRight:
            align_str = "right"

        d.update({
            "text": self.get_plain_text(),
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_bold": self.font_bold,
            "font_italic": self.font_italic,
            "text_color": self.text_color,
            "alignment": align_str,
            "bg_color": self.bg_color,
        })
        return d

    def from_dict(self, data: dict[str, Any]):
        super().from_dict(data)
        self.font_family = data.get("font_family", DEFAULT_FONT_FAMILY)
        self.font_size = data.get("font_size", DEFAULT_FONT_SIZE)
        self.font_bold = data.get("font_bold", False)
        self.font_italic = data.get("font_italic", False)
        self.text_color = data.get("text_color", DEFAULT_TEXT_COLOR)
        self.bg_color = data.get("bg_color", None)

        align_str = data.get("alignment", "left")
        if align_str == "center":
            self.text_alignment = Qt.AlignmentFlag.AlignCenter
        elif align_str == "right":
            self.text_alignment = Qt.AlignmentFlag.AlignRight
        else:
            self.text_alignment = Qt.AlignmentFlag.AlignLeft

        self.set_plain_text(data.get("text", ""))
