"""Clipboard manager handling internal serialized canvas items and native Windows clipboard interoperability."""

import json
import os
import uuid
from typing import Optional, Sequence
from PySide6.QtCore import QPointF, QRectF, QMimeData, QByteArray, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QClipboard, QImage, QPainter, QColor
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

from vait.constants import CUSTOM_MIME_TYPE
from vait.items import BaseCanvasItem, ImageItem, TextItem, item_from_dict
from vait.commands.undo_commands import AddItemsCommand, DeleteItemsCommand

class ClipboardManager:
    """Manages copying and pasting between canvas and Windows system clipboard."""

    def __init__(self, scene: QGraphicsScene, undo_stack):
        self.scene = scene
        self.undo_stack = undo_stack

    def copy_selection(self) -> bool:
        """Copy selected canvas items to system clipboard in internal format + image/text fallbacks."""
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, BaseCanvasItem)]
        if not selected_items:
            return False

        # 1. Internal JSON serialization
        items_data = [item.to_dict() for item in selected_items]
        json_bytes = json.dumps(items_data).encode("utf-8")

        mime_data = QMimeData()
        mime_data.setData(CUSTOM_MIME_TYPE, QByteArray(json_bytes))

        # 2. External Text fallback
        text_parts = [item.get_plain_text() for item in selected_items if isinstance(item, TextItem)]
        if text_parts:
            mime_data.setText("\n\n".join(text_parts))

        # 3. External Image fallback (render selected items)
        rendered_image = self._render_items_to_image(selected_items)
        if rendered_image and not rendered_image.isNull():
            mime_data.setImageData(rendered_image)

        # Apply to native Windows clipboard
        clipboard = QGuiApplication.clipboard()
        clipboard.setMimeData(mime_data, QClipboard.Mode.Clipboard)
        return True

    def cut_selection(self) -> bool:
        """Copy selected items then delete them with undo support."""
        if self.copy_selection():
            selected = [item for item in self.scene.selectedItems() if isinstance(item, BaseCanvasItem)]
            if selected:
                cmd = DeleteItemsCommand(self.scene, selected, "Cut Items")
                self.undo_stack.push(cmd)
            return True
        return False

    def paste_from_clipboard(self, target_pos: Optional[QPointF] = None) -> list[BaseCanvasItem]:
        """Paste items from clipboard (internal canvas items or external image/text)."""
        clipboard = QGuiApplication.clipboard()
        mime_data = clipboard.mimeData()
        if not mime_data:
            return []

        pasted_items: list[BaseCanvasItem] = []

        # Case 1: Internal serialized canvas items
        if mime_data.hasFormat(CUSTOM_MIME_TYPE):
            raw_bytes = bytes(mime_data.data(CUSTOM_MIME_TYPE).data())
            try:
                items_data = json.loads(raw_bytes.decode("utf-8"))
                pasted_items = self._deserialize_and_position(items_data, target_pos)
            except Exception as e:
                print(f"Error parsing internal clipboard data: {e}")

        # Case 2: External image from browser/Paint/Explorer
        elif mime_data.hasImage():
            qimage = clipboard.image()
            if not qimage.isNull():
                pos = target_pos if target_pos is not None else QPointF(100, 100)
                img_item = ImageItem.from_qimage(qimage, x=pos.x(), y=pos.y())
                pasted_items = [img_item]

        # Case 3: Image files copied from Windows File Explorer
        elif mime_data.hasUrls():
            pos = target_pos if target_pos is not None else QPointF(100, 100)
            offset = 0
            for url in mime_data.urls():
                local_path = url.toLocalFile()
                if os.path.exists(local_path):
                    ext = os.path.splitext(local_path)[1].lower()
                    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"):
                        try:
                            img_item = ImageItem.from_file(local_path, x=pos.x() + offset, y=pos.y() + offset)
                            pasted_items.append(img_item)
                            offset += 30
                        except Exception as e:
                            print(f"Failed to load image file {local_path}: {e}")

        # Case 4: External text from browser/notepad/code editor
        elif mime_data.hasText():
            text = mime_data.text()
            if text.strip():
                pos = target_pos if target_pos is not None else QPointF(100, 100)
                txt_item = TextItem(text=text, x=pos.x(), y=pos.y(), width=260)
                pasted_items = [txt_item]

        if pasted_items:
            cmd = AddItemsCommand(self.scene, pasted_items, "Paste Items")
            self.undo_stack.push(cmd)

        return pasted_items

    def duplicate_selection(self, offset: QPointF = QPointF(25, 25)) -> list[BaseCanvasItem]:
        """Duplicate currently selected items, slightly offset, with fresh IDs."""
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, BaseCanvasItem)]
        if not selected_items:
            return []

        items_data = [item.to_dict() for item in selected_items]
        new_items = []
        for d in items_data:
            d["id"] = str(uuid.uuid4())
            d["x"] = d.get("x", 0) + offset.x()
            d["y"] = d.get("y", 0) + offset.y()
            item = item_from_dict(d)
            if item:
                new_items.append(item)

        if new_items:
            cmd = AddItemsCommand(self.scene, new_items, "Duplicate Selection")
            self.undo_stack.push(cmd)

        return new_items

    def _deserialize_and_position(self, items_data: list[dict], target_pos: Optional[QPointF]) -> list[BaseCanvasItem]:
        """Instantiate items from dict, re-centering them around target_pos or offsetting."""
        if not items_data:
            return []

        # Find center of copied items
        min_x = min(d.get("x", 0) for d in items_data)
        min_y = min(d.get("y", 0) for d in items_data)
        max_x = max(d.get("x", 0) + d.get("width", 50) for d in items_data)
        max_y = max(d.get("y", 0) + d.get("height", 50) for d in items_data)
        orig_center = QPointF((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)

        if target_pos is not None:
            delta = target_pos - orig_center
        else:
            delta = QPointF(25, 25)

        new_items = []
        for d in items_data:
            d["id"] = str(uuid.uuid4())  # Fresh unique ID
            d["x"] = d.get("x", 0) + delta.x()
            d["y"] = d.get("y", 0) + delta.y()
            item = item_from_dict(d)
            if item:
                new_items.append(item)

        return new_items

    def _render_items_to_image(self, items: list[BaseCanvasItem]) -> Optional[QImage]:
        """Render a collection of canvas items to a high-res QImage."""
        if not items:
            return None

        # Calculate bounding rect of all items in scene coordinates
        total_rect = QRectF()
        for item in items:
            total_rect = total_rect.united(item.sceneBoundingRect())

        if total_rect.isEmpty() or total_rect.width() <= 0 or total_rect.height() <= 0:
            return None

        # Add modest padding
        pad = 10.0
        render_rect = total_rect.adjusted(-pad, -pad, pad, pad)
        w = int(max(1, render_rect.width()))
        h = int(max(1, render_rect.height()))

        # Guard against absurd sizes
        if w > 8000 or h > 8000:
            scale = 8000.0 / max(w, h)
            w = int(w * scale)
            h = int(h * scale)

        image = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Clear selection temporarily so handles don't render into exported clipboard image
        selected_states = {item: item.isSelected() for item in items}
        for item in items:
            item.setSelected(False)

        self.scene.render(painter, target=QRectF(0, 0, w, h), source=render_rect)

        # Restore selection
        for item, state in selected_states.items():
            item.setSelected(state)

        painter.end()
        return image
