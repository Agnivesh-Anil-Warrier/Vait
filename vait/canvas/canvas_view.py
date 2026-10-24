"""Infinite Canvas View with smooth panning, zooming under mouse, drag-and-drop, and marquee selection."""

import os
from typing import Optional
from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal, QMimeData
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QRubberBand
)
from PySide6.QtGui import (
    QPainter,
    QMouseEvent,
    QWheelEvent,
    QKeyEvent,
    QDragEnterEvent,
    QDropEvent,
    QCursor,
    QTransform
)

from vait.constants import (
    MIN_ZOOM,
    MAX_ZOOM,
    DEFAULT_ZOOM,
    ToolMode
)
from vait.items import ImageItem, BaseCanvasItem
from vait.items.handles import HandleId, get_handle_at_pos

class InfiniteCanvasView(QGraphicsView):
    """Modern infinite canvas viewport with hardware-accelerated rendering and natural gestures."""

    zoom_changed = Signal(float)  # Emits current zoom level (e.g. 1.0 = 100%)
    cursor_scene_pos_changed = Signal(QPointF)
    image_dropped = Signal(str, QPointF)
    project_dropped = Signal(str)

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # Anchor zoom under mouse pointer
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # Hide scrollbars for true infinite canvas feel
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

        # Full viewport update prevents dirty-rect ghosting/trails with custom handles and antialiasing
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Enable mouse tracking for coordinates readout
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        # Pan state
        self._is_panning: bool = False
        self._pan_start_mouse_pos: QPoint = QPoint()
        self._space_pressed: bool = False

        # Marquee / Rubber band selection state parented directly to viewport
        self._rubber_band: QRubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self.viewport())
        self._rubber_band_origin: QPoint = QPoint()
        self._is_rubber_banding: bool = False
        self._initial_selection: set = set()

        # Current zoom multiplier
        self._zoom: float = DEFAULT_ZOOM

    @property
    def zoom_level(self) -> float:
        return self._zoom

    def set_zoom_level(self, zoom: float, anchor_pos: Optional[QPoint] = None):
        """Set absolute zoom level clamped between bounds."""
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        factor = new_zoom / self._zoom
        self._zoom = new_zoom

        self.scale(factor, factor)
        self.zoom_changed.emit(self._zoom)

    def zoom_in(self):
        """Zoom in by 15%."""
        self.set_zoom_level(self._zoom * 1.15)

    def zoom_out(self):
        """Zoom out by 15%."""
        self.set_zoom_level(self._zoom / 1.15)

    def reset_zoom(self):
        """Reset view to 100% zoom."""
        factor = 1.0 / self._zoom
        self._zoom = 1.0
        self.scale(factor, factor)
        self.zoom_changed.emit(1.0)

    def fit_content(self):
        """Fit all canvas items in view with generous margin."""
        rect = self.scene().itemsBoundingRect()
        if not rect.isEmpty() and rect.width() > 0 and rect.height() > 0:
            padded_rect = rect.adjusted(-50, -50, 50, 50)
            self.fitInView(padded_rect, Qt.AspectRatioMode.KeepAspectRatio)
            # Update internal zoom tracking
            self._zoom = self.transform().m11()
            self.zoom_changed.emit(self._zoom)

    def get_view_state(self) -> dict:
        """Capture current viewport center and zoom for project saving."""
        center_scene = self.mapToScene(self.viewport().rect().center())
        return {
            "zoom": self._zoom,
            "center_x": center_scene.x(),
            "center_y": center_scene.y(),
        }

    def restore_view_state(self, state: dict):
        """Restore viewport center and zoom level from saved project."""
        target_zoom = state.get("zoom", 1.0)
        cx = state.get("center_x", 0.0)
        cy = state.get("center_y", 0.0)

        # Set zoom
        self.reset_zoom()
        self.set_zoom_level(target_zoom)

        # Center on target
        self.centerOn(QPointF(cx, cy))

    # --- Mouse and Wheel Events ---

    def wheelEvent(self, event: QWheelEvent):
        """Zoom in/out anchored around current mouse position."""
        angle = event.angleDelta().y()
        if angle != 0:
            factor = 1.15 if angle > 0 else (1.0 / 1.15)
            new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, self._zoom * factor))
            actual_factor = new_zoom / self._zoom
            self._zoom = new_zoom

            self.scale(actual_factor, actual_factor)
            self.zoom_changed.emit(self._zoom)
            event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        # 1. Middle Mouse Button Pan OR Space + Left Click Pan OR Pan Tool Active
        is_middle_click = (event.button() == Qt.MouseButton.MiddleButton)
        is_space_drag = (event.button() == Qt.MouseButton.LeftButton and self._space_pressed)
        canvas_scene = self.scene()
        is_pan_tool = hasattr(canvas_scene, "current_tool") and canvas_scene.current_tool == ToolMode.PAN and event.button() == Qt.MouseButton.LeftButton

        mouse_pt = event.position().toPoint()

        if is_middle_click or is_space_drag or is_pan_tool:
            self._is_panning = True
            self._pan_start_mouse_pos = mouse_pt
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return

        # 2. Check for Marquee selection when in SELECT mode and clicking empty space
        if (
            hasattr(canvas_scene, "current_tool")
            and canvas_scene.current_tool == ToolMode.SELECT
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene_pos = self.mapToScene(mouse_pt)
            item = canvas_scene.itemAt(scene_pos, self.transform())

            # Check if clicked on a handle of an already selected item
            clicked_on_handle = False
            if item is not None and item.isSelected() and isinstance(item, BaseCanvasItem):
                scale = item.get_view_scale()
                p1 = getattr(item, "p1", None)
                p2 = getattr(item, "p2", None)
                h = get_handle_at_pos(
                    item.mapFromScene(scene_pos),
                    item._rect,
                    scale=scale,
                    is_linear=item.is_linear_item,
                    p1=p1,
                    p2=p2,
                    include_rotate=item.include_rotate_handle
                )
                if h != HandleId.NONE:
                    clicked_on_handle = True

            # If not clicking on a handle, and no item under cursor (empty space):
            if not clicked_on_handle and item is None:
                self._is_rubber_banding = True
                self._rubber_band_origin = mouse_pt
                self._rubber_band.setGeometry(QRect(mouse_pt, QSize(1, 1)))
                self._rubber_band.show()
                self._rubber_band.raise_()
                is_shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                self._initial_selection = set(canvas_scene.selectedItems()) if is_shift else set()
                if not is_shift:
                    canvas_scene.clearSelection()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        mouse_pt = event.position().toPoint()
        # Emit coordinates for status bar
        scene_pos = self.mapToScene(mouse_pt)
        self.cursor_scene_pos_changed.emit(scene_pos)

        # Handle viewport pan
        if self._is_panning:
            delta = mouse_pt - self._pan_start_mouse_pos
            self._pan_start_mouse_pos = mouse_pt

            # Adjust view center
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        # Handle rubber band marquee selection
        if self._is_rubber_banding:
            x1 = min(self._rubber_band_origin.x(), mouse_pt.x())
            y1 = min(self._rubber_band_origin.y(), mouse_pt.y())
            w = abs(mouse_pt.x() - self._rubber_band_origin.x())
            h = abs(mouse_pt.y() - self._rubber_band_origin.y())
            rect = QRect(x1, y1, max(1, w), max(1, h))
            self._rubber_band.setGeometry(rect)

            # Update selection for items intersecting marquee in scene coordinates
            scene_poly = self.mapToScene(rect)
            scene_rect = scene_poly.boundingRect()

            canvas_scene = self.scene()
            for it in canvas_scene.items():
                if isinstance(it, BaseCanvasItem):
                    in_marquee = scene_rect.intersects(it.sceneBoundingRect())
                    if in_marquee:
                        it.setSelected(True)
                    else:
                        it.setSelected(it in self._initial_selection)

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            if self._space_pressed:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.unsetCursor()
            event.accept()
            return

        if self._is_rubber_banding:
            self._is_rubber_banding = False
            self._rubber_band.hide()
            canvas_scene = self.scene()
            if hasattr(canvas_scene, "_on_selection_changed"):
                canvas_scene._on_selection_changed()
            self.viewport().update()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    # --- Keyboard Pan Modifiers ---

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = True
            if not self._is_panning:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = False
            if not self._is_panning:
                self.unsetCursor()
            event.accept()
            return
        super().keyReleaseEvent(event)

    # --- Drag and Drop from Windows Explorer ---

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            scene_pos = self.mapToScene(event.position().toPoint())
            offset = 0

            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if os.path.exists(local_path):
                    ext = os.path.splitext(local_path)[1].lower()
                    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"):
                        drop_pt = QPointF(scene_pos.x() + offset, scene_pos.y() + offset)
                        self.image_dropped.emit(local_path, drop_pt)
                        offset += 30
                    elif ext == ".canvas":
                        self.project_dropped.emit(local_path)

            event.acceptProposedAction()
        else:
            super().dropEvent(event)
