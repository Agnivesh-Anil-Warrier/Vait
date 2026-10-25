"""Contextual properties toolbar adapting to the active selection or active drawing tool."""

from typing import Optional, Sequence
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QFontComboBox,
    QColorDialog,
    QFrame,
    QButtonGroup
)
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QPen, QBrush

from vait.constants import (
    ToolMode,
    ShapeType,
    DEFAULT_STROKE_COLOR,
    DEFAULT_FILL_COLOR,
    DEFAULT_PEN_COLOR
)
from vait.items import (
    BaseCanvasItem,
    ShapeItem,
    TextItem,
    StrokeItem,
    ImageItem
)
from vait.commands.undo_commands import ChangePropertyCommand
from vait.ui.icons import create_icon

def make_color_icon(color_hex: str, size: int = 20) -> QIcon:
    """Generate high-DPI rounded color swatch with a contrasting border for visibility on dark backgrounds."""
    scale = 2
    pix = QPixmap(size * scale, size * scale)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(scale, scale)

    rect = QRectF(1.0, 1.0, size - 2.0, size - 2.0)
    col = QColor(color_hex)
    painter.setBrush(QBrush(col))

    # Border contrast: if color is dark (like #000000), use bright border; otherwise slate
    luminance = 0.299 * col.red() + 0.587 * col.green() + 0.114 * col.blue()
    border_color = QColor("#e2e8f0") if luminance < 120 else QColor("#334155")
    painter.setPen(QPen(border_color, 1.5))
    painter.drawRoundedRect(rect, 4, 4)
    painter.end()
    return QIcon(pix)

class PropertiesPanel(QFrame):
    """Contextual toolbar displaying controls relevant to active selection or drawing tool."""

    property_changed = Signal(str, object)

    def __init__(self, scene, undo_stack, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.undo_stack = undo_stack
        self._current_items: list[BaseCanvasItem] = []

        self.setFixedHeight(46)
        self.setStyleSheet("""
            PropertiesPanel {
                background-color: #1e293b;
                border-bottom: 1px solid #334155;
                padding: 2px 10px;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
                margin-right: 4px;
            }
            QToolButton#colorButton {
                background-color: #0f172a;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 3px 6px;
                min-width: 32px;
                min-height: 24px;
            }
            QToolButton#colorButton:hover {
                border-color: #94a3b8;
                background-color: #334155;
            }
            QSpinBox {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 3px 6px;
                font-weight: 600;
                min-height: 22px;
                min-width: 68px;
            }
            QSpinBox:hover {
                border-color: #94a3b8;
            }
            QCheckBox {
                color: #e2e8f0;
                font-weight: 600;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #475569;
                border-radius: 4px;
                background-color: #0f172a;
            }
            QCheckBox::indicator:hover {
                border-color: #94a3b8;
            }
            QCheckBox::indicator:checked {
                background-color: #2563eb;
                border-color: #3b82f6;
            }
            QToolButton.panelBtn {
                background-color: #0f172a;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 5px;
                padding: 3px 8px;
                font-weight: 600;
                min-height: 22px;
            }
            QToolButton.panelBtn:hover {
                background-color: #334155;
                border-color: #94a3b8;
            }
            QToolButton.panelBtn:checked {
                background-color: #2563eb;
                border-color: #60a5fa;
                color: #ffffff;
            }
        """)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 2, 10, 2)
        self.main_layout.setSpacing(10)

        # 0. Shape Type Selector
        self.lbl_shape_type = QLabel("Shape:")
        self.combo_shape_type = QComboBox()
        self.combo_shape_type.setToolTip("Active Shape Type")
        shapes_data = [
            ("Rectangle", ShapeType.RECTANGLE, "rectangle"),
            ("Rounded Rect", ShapeType.ROUNDED_RECT, "rounded_rect"),
            ("Ellipse / Circle", ShapeType.ELLIPSE, "ellipse"),
            ("Line", ShapeType.LINE, "line"),
            ("Arrow", ShapeType.ARROW, "arrow"),
            ("Triangle", ShapeType.TRIANGLE, "triangle"),
            ("Diamond", ShapeType.DIAMOND, "diamond"),
        ]
        for label, st, icon_name in shapes_data:
            self.combo_shape_type.addItem(create_icon(icon_name), label, st)
        self.combo_shape_type.currentIndexChanged.connect(self._on_shape_type_changed)

        # 1. Stroke / Pen Color
        self.lbl_stroke = QLabel("Stroke:")
        self.btn_stroke_color = QToolButton()
        self.btn_stroke_color.setObjectName("colorButton")
        self.btn_stroke_color.setToolTip("Stroke / Outline Color")
        self.btn_stroke_color.clicked.connect(self._choose_stroke_color)

        # 2. Stroke Width
        self.spin_stroke_width = QSpinBox()
        self.spin_stroke_width.setRange(0, 5000)
        self.spin_stroke_width.setValue(2)
        self.spin_stroke_width.setSuffix(" px")
        self.spin_stroke_width.setToolTip("Stroke Width (0 for borderless)")
        self.spin_stroke_width.valueChanged.connect(self._on_stroke_width_changed)

        # 3. Fill Color
        self.lbl_fill = QLabel("Fill:")
        self.btn_fill_color = QToolButton()
        self.btn_fill_color.setObjectName("colorButton")
        self.btn_fill_color.setToolTip("Shape Fill Color")
        self.btn_fill_color.clicked.connect(self._choose_fill_color)

        self.chk_fill_transparent = QCheckBox("None")
        self.chk_fill_transparent.setToolTip("Transparent Fill")
        self.chk_fill_transparent.toggled.connect(self._on_fill_transparent_toggled)

        # 4. Text Controls
        self.font_combo = QFontComboBox()
        self.font_combo.setToolTip("Font Family")
        self.font_combo.currentFontChanged.connect(self._on_font_family_changed)

        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 96)
        self.spin_font_size.setValue(16)
        self.spin_font_size.setSuffix(" pt")
        self.spin_font_size.setToolTip("Font Size")
        self.spin_font_size.valueChanged.connect(self._on_font_size_changed)

        self.btn_bold = QToolButton()
        self.btn_bold.setText("B")
        self.btn_bold.setProperty("class", "panelBtn")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setStyleSheet("font-weight: bold; min-width: 26px;")
        self.btn_bold.toggled.connect(self._on_bold_toggled)

        self.btn_italic = QToolButton()
        self.btn_italic.setText("I")
        self.btn_italic.setProperty("class", "panelBtn")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setStyleSheet("font-style: italic; min-width: 26px;")
        self.btn_italic.toggled.connect(self._on_italic_toggled)

        self.align_group = QButtonGroup(self)
        self.btn_align_left = QToolButton()
        self.btn_align_left.setText("L")
        self.btn_align_left.setProperty("class", "panelBtn")
        self.btn_align_left.setCheckable(True)
        self.btn_align_left.setChecked(True)
        self.align_group.addButton(self.btn_align_left)

        self.btn_align_center = QToolButton()
        self.btn_align_center.setText("C")
        self.btn_align_center.setProperty("class", "panelBtn")
        self.btn_align_center.setCheckable(True)
        self.align_group.addButton(self.btn_align_center)

        self.btn_align_right = QToolButton()
        self.btn_align_right.setText("R")
        self.btn_align_right.setProperty("class", "panelBtn")
        self.btn_align_right.setCheckable(True)
        self.align_group.addButton(self.btn_align_right)

        self.btn_align_left.clicked.connect(lambda: self._on_align_changed(Qt.AlignmentFlag.AlignLeft))
        self.btn_align_center.clicked.connect(lambda: self._on_align_changed(Qt.AlignmentFlag.AlignCenter))
        self.btn_align_right.clicked.connect(lambda: self._on_align_changed(Qt.AlignmentFlag.AlignRight))

        # 5. Image Controls
        self.chk_lock_aspect = QCheckBox("Lock Aspect")
        self.chk_lock_aspect.setChecked(True)
        self.chk_lock_aspect.toggled.connect(self._on_lock_aspect_toggled)

        # 6. Layer Arrangement
        self.btn_bring_front = QToolButton()
        self.btn_bring_front.setText("Bring to Front")
        self.btn_bring_front.setProperty("class", "panelBtn")
        self.btn_bring_front.clicked.connect(self._bring_to_front)

        self.btn_send_back = QToolButton()
        self.btn_send_back.setText("Send to Back")
        self.btn_send_back.setProperty("class", "panelBtn")
        self.btn_send_back.clicked.connect(self._send_to_back)

        # Build initial layout
        self._build_layout()
        self.update_for_selection([])

    def _build_layout(self):
        l = self.main_layout
        # Shape Type group
        l.addWidget(self.lbl_shape_type)
        l.addWidget(self.combo_shape_type)
        l.addSpacing(6)

        # Stroke group
        l.addWidget(self.lbl_stroke)
        l.addWidget(self.btn_stroke_color)
        l.addWidget(self.spin_stroke_width)

        l.addSpacing(8)
        # Fill group
        l.addWidget(self.lbl_fill)
        l.addWidget(self.btn_fill_color)
        l.addWidget(self.chk_fill_transparent)

        l.addSpacing(8)
        # Text group
        l.addWidget(self.font_combo)
        l.addWidget(self.spin_font_size)
        l.addWidget(self.btn_bold)
        l.addWidget(self.btn_italic)
        l.addWidget(self.btn_align_left)
        l.addWidget(self.btn_align_center)
        l.addWidget(self.btn_align_right)

        l.addSpacing(8)
        # Image group
        l.addWidget(self.chk_lock_aspect)

        l.addSpacing(8)
        # Arrange group
        l.addWidget(self.btn_bring_front)
        l.addWidget(self.btn_send_back)

        l.addStretch()

    def update_for_selection(self, selected_items: list[BaseCanvasItem]):
        """Update property panel visibility and values based on selected items."""
        self._current_items = selected_items

        if not selected_items:
            # Show default tool settings (e.g. Pen or Shape)
            self._show_tool_defaults()
            return

        has_shape = any(isinstance(it, ShapeItem) for it in selected_items)
        has_text = any(isinstance(it, TextItem) for it in selected_items)
        has_stroke = any(isinstance(it, StrokeItem) for it in selected_items)
        has_image = any(isinstance(it, ImageItem) for it in selected_items)

        # Visibility
        self.lbl_shape_type.setVisible(has_shape)
        self.combo_shape_type.setVisible(has_shape)
        if has_shape:
            for it in selected_items:
                if isinstance(it, ShapeItem):
                    idx = self.combo_shape_type.findData(it.shape_type)
                    if idx >= 0:
                        self.combo_shape_type.blockSignals(True)
                        self.combo_shape_type.setCurrentIndex(idx)
                        self.combo_shape_type.blockSignals(False)
                    break

        # Visibility
        self.lbl_stroke.setVisible(has_shape or has_stroke or has_text)
        if has_text and not (has_shape or has_stroke):
            self.lbl_stroke.setText("Text Color:")
        elif has_stroke and not (has_shape or has_text):
            self.lbl_stroke.setText("Pen:")
        else:
            self.lbl_stroke.setText("Outline:")

        self.btn_stroke_color.setVisible(has_shape or has_stroke or has_text)
        self.spin_stroke_width.setVisible(has_shape or has_stroke)

        self.lbl_fill.setVisible(has_shape)
        self.btn_fill_color.setVisible(has_shape)
        self.chk_fill_transparent.setVisible(has_shape)

        self.font_combo.setVisible(has_text)
        self.spin_font_size.setVisible(has_text)
        self.btn_bold.setVisible(has_text)
        self.btn_italic.setVisible(has_text)
        self.btn_align_left.setVisible(has_text)
        self.btn_align_center.setVisible(has_text)
        self.btn_align_right.setVisible(has_text)

        self.chk_lock_aspect.setVisible(has_image or has_shape)
        self.btn_bring_front.setVisible(True)
        self.btn_send_back.setVisible(True)

        # Populate current values from primary selected item
        primary = selected_items[0]
        if isinstance(primary, ShapeItem):
            # Synchronize active defaults with selected item so subsequent shapes inherit it
            self.scene.shape_stroke_color = primary.stroke_color
            self.scene.shape_stroke_width = primary.stroke_width
            self.scene.shape_fill_color = primary.fill_color
            self.scene.shape_fill_transparent = primary.fill_transparent

            self.btn_stroke_color.setIcon(make_color_icon(primary.stroke_color))
            self.spin_stroke_width.blockSignals(True)
            self.spin_stroke_width.setValue(int(primary.stroke_width))
            self.spin_stroke_width.blockSignals(False)

            self.btn_fill_color.setIcon(make_color_icon(primary.fill_color))
            self.chk_fill_transparent.blockSignals(True)
            self.chk_fill_transparent.setChecked(primary.fill_transparent)
            self.chk_fill_transparent.blockSignals(False)
        elif isinstance(primary, StrokeItem):
            self.scene.pen_color = primary.color
            screen_w = getattr(primary, "screen_brush_width", None)
            if screen_w is None:
                zoom = self.scene.get_current_zoom_scale()
                screen_w = max(1.0, round(primary.stroke_width * zoom))
            self.scene.pen_width = float(screen_w)

            self.btn_stroke_color.setIcon(make_color_icon(primary.color))
            self.spin_stroke_width.blockSignals(True)
            self.spin_stroke_width.setValue(int(screen_w))
            self.spin_stroke_width.blockSignals(False)
        elif isinstance(primary, TextItem):
            self.btn_stroke_color.setIcon(make_color_icon(primary.text_color))

            self.font_combo.blockSignals(True)
            self.font_combo.setCurrentFont(QFont(primary.font_family))
            self.font_combo.blockSignals(False)

            self.spin_font_size.blockSignals(True)
            self.spin_font_size.setValue(primary.font_size)
            self.spin_font_size.blockSignals(False)

            self.btn_bold.blockSignals(True)
            self.btn_bold.setChecked(primary.font_bold)
            self.btn_bold.blockSignals(False)

            self.btn_italic.blockSignals(True)
            self.btn_italic.setChecked(primary.font_italic)
            self.btn_italic.blockSignals(False)
        elif isinstance(primary, ImageItem):
            self.chk_lock_aspect.blockSignals(True)
            self.chk_lock_aspect.setChecked(primary.lock_aspect_ratio)
            self.chk_lock_aspect.blockSignals(False)

    def _show_tool_defaults(self):
        """Show default controls when no item is selected."""
        tool = getattr(self.scene, "current_tool", ToolMode.SELECT)

        is_shape_tool = (tool == ToolMode.SHAPE)
        self.lbl_shape_type.setVisible(is_shape_tool)
        self.combo_shape_type.setVisible(is_shape_tool)
        if is_shape_tool:
            idx = self.combo_shape_type.findData(self.scene.current_shape_type)
            if idx >= 0:
                self.combo_shape_type.blockSignals(True)
                self.combo_shape_type.setCurrentIndex(idx)
                self.combo_shape_type.blockSignals(False)

        if tool == ToolMode.PEN:
            self.lbl_stroke.setVisible(True)
            self.lbl_stroke.setText("Pen:")
            self.btn_stroke_color.setVisible(True)
            self.btn_stroke_color.setIcon(make_color_icon(self.scene.pen_color))
            self.spin_stroke_width.setVisible(True)
            self.spin_stroke_width.setValue(int(self.scene.pen_width))

            self.lbl_fill.setVisible(False)
            self.btn_fill_color.setVisible(False)
            self.chk_fill_transparent.setVisible(False)
        else:
            # For SHAPE, SELECT, or any default canvas state:
            # Keep active outline and fill color controls visible and synced!
            self.lbl_stroke.setVisible(True)
            self.lbl_stroke.setText("Outline:")
            self.btn_stroke_color.setVisible(True)
            self.btn_stroke_color.setIcon(make_color_icon(self.scene.shape_stroke_color))
            self.spin_stroke_width.setVisible(True)
            self.spin_stroke_width.setValue(int(self.scene.shape_stroke_width))

            self.lbl_fill.setVisible(True)
            self.btn_fill_color.setVisible(True)
            self.btn_fill_color.setIcon(make_color_icon(self.scene.shape_fill_color))
            self.chk_fill_transparent.setVisible(True)
            self.chk_fill_transparent.setChecked(self.scene.shape_fill_transparent)

        self.font_combo.setVisible(False)
        self.spin_font_size.setVisible(False)
        self.btn_bold.setVisible(False)
        self.btn_italic.setVisible(False)
        self.btn_align_left.setVisible(False)
        self.btn_align_center.setVisible(False)
        self.btn_align_right.setVisible(False)
        self.chk_lock_aspect.setVisible(False)
        self.btn_bring_front.setVisible(False)
        self.btn_send_back.setVisible(False)

    def _on_shape_type_changed(self, idx: int):
        st = self.combo_shape_type.itemData(idx)
        if not st:
            return
        self.scene.current_shape_type = st

        # Sync main window button icon
        win = self.window()
        if hasattr(win, "btn_tool_shape"):
            icon_map = {
                ShapeType.RECTANGLE: "rectangle",
                ShapeType.ROUNDED_RECT: "rounded_rect",
                ShapeType.ELLIPSE: "ellipse",
                ShapeType.LINE: "line",
                ShapeType.ARROW: "arrow",
                ShapeType.TRIANGLE: "triangle",
                ShapeType.DIAMOND: "diamond",
            }
            win.btn_tool_shape.setIcon(create_icon(icon_map.get(st, "rectangle")))

        # If any shape is selected on canvas, update it!
        if self._current_items:
            targets = [it for it in self._current_items if isinstance(it, ShapeItem)]
            if targets:
                old_types = [it.shape_type for it in targets]
                cmd = ChangePropertyCommand(targets, "shape_type", old_types, [st] * len(targets))
                self.undo_stack.push(cmd)
                for it in targets:
                    it.is_linear_item = it.shape_type in (ShapeType.LINE, ShapeType.ARROW)
                    it.include_rotate_handle = not it.is_linear_item
                    it.update()

    def _choose_stroke_color(self):
        curr_hex = self.scene.shape_stroke_color
        if self._current_items:
            for it in self._current_items:
                if isinstance(it, ShapeItem):
                    curr_hex = it.stroke_color
                    break
                elif isinstance(it, StrokeItem):
                    curr_hex = it.color
                    break
                elif isinstance(it, TextItem):
                    curr_hex = it.text_color
                    break

        col = QColorDialog.getColor(QColor(curr_hex), self, "Choose Color")
        if col.isValid():
            hex_str = col.name()
            self.btn_stroke_color.setIcon(make_color_icon(hex_str))
            # Always remember chosen color for subsequent shapes and pen strokes
            self.scene.shape_stroke_color = hex_str
            self.scene.pen_color = hex_str

            if self._current_items:
                shape_targets = [it for it in self._current_items if isinstance(it, ShapeItem)]
                if shape_targets:
                    old_vals = [it.stroke_color for it in shape_targets]
                    cmd = ChangePropertyCommand(shape_targets, "stroke_color", old_vals, [hex_str] * len(shape_targets))
                    self.undo_stack.push(cmd)

                stroke_targets = [it for it in self._current_items if isinstance(it, StrokeItem)]
                if stroke_targets:
                    old_vals = [it.color for it in stroke_targets]
                    cmd = ChangePropertyCommand(stroke_targets, "color", old_vals, [hex_str] * len(stroke_targets))
                    self.undo_stack.push(cmd)

                text_targets = [it for it in self._current_items if isinstance(it, TextItem)]
                if text_targets:
                    old_vals = [it.text_color for it in text_targets]
                    cmd = ChangePropertyCommand(text_targets, "text_color", old_vals, [hex_str] * len(text_targets))
                    self.undo_stack.push(cmd)

    def _choose_fill_color(self):
        curr_hex = self.scene.shape_fill_color
        if self._current_items:
            for it in self._current_items:
                if isinstance(it, ShapeItem):
                    curr_hex = it.fill_color
                    break

        col = QColorDialog.getColor(QColor(curr_hex), self, "Choose Fill Color")
        if col.isValid():
            hex_str = col.name()
            self.btn_fill_color.setIcon(make_color_icon(hex_str))
            # Always remember chosen fill color for subsequent shapes
            self.scene.shape_fill_color = hex_str
            self.scene.shape_fill_transparent = False
            self.chk_fill_transparent.blockSignals(True)
            self.chk_fill_transparent.setChecked(False)
            self.chk_fill_transparent.blockSignals(False)

            if self._current_items:
                targets = [it for it in self._current_items if isinstance(it, ShapeItem)]
                if targets:
                    old_vals = [it.fill_color for it in targets]
                    cmd = ChangePropertyCommand(targets, "fill_color", old_vals, [hex_str] * len(targets))
                    self.undo_stack.push(cmd)

                    # Also disable transparent fill so the chosen color is visible
                    trans_targets = [it for it in targets if it.fill_transparent]
                    if trans_targets:
                        old_trans = [it.fill_transparent for it in trans_targets]
                        cmd_trans = ChangePropertyCommand(trans_targets, "fill_transparent", old_trans, [False] * len(trans_targets))
                        self.undo_stack.push(cmd_trans)

    def _on_stroke_width_changed(self, val: int):
        self.scene.pen_width = float(val)
        self.scene.shape_stroke_width = float(val)

        if self._current_items:
            # 1. Shape items (scene stroke width)
            shape_targets = [it for it in self._current_items if isinstance(it, ShapeItem)]
            if shape_targets:
                old_vals = [it.stroke_width for it in shape_targets]
                cmd = ChangePropertyCommand(shape_targets, "stroke_width", old_vals, [float(val)] * len(shape_targets))
                self.undo_stack.push(cmd)

            # 2. Stroke items (zoom-adjusted scene width)
            stroke_targets = [it for it in self._current_items if isinstance(it, StrokeItem)]
            if stroke_targets:
                zoom = self.scene.get_current_zoom_scale()
                new_scene_w = float(val) / max(zoom, 0.0001)
                old_vals = [it.stroke_width for it in stroke_targets]
                for it in stroke_targets:
                    it.screen_brush_width = float(val)
                cmd = ChangePropertyCommand(stroke_targets, "stroke_width", old_vals, [new_scene_w] * len(stroke_targets))
                self.undo_stack.push(cmd)

    def _on_fill_transparent_toggled(self, checked: bool):
        self.scene.shape_fill_transparent = checked

        if self._current_items:
            targets = [it for it in self._current_items if isinstance(it, ShapeItem)]
            if targets:
                old_vals = [it.fill_transparent for it in targets]
                cmd = ChangePropertyCommand(targets, "fill_transparent", old_vals, [checked] * len(targets))
                self.undo_stack.push(cmd)

    def _on_font_family_changed(self, font: QFont):
        targets = [it for it in self._current_items if isinstance(it, TextItem)]
        if targets:
            old_vals = [it.font_family for it in targets]
            cmd = ChangePropertyCommand(targets, "font_family", old_vals, [font.family()] * len(targets))
            self.undo_stack.push(cmd)

    def _on_font_size_changed(self, size: int):
        targets = [it for it in self._current_items if isinstance(it, TextItem)]
        if targets:
            old_vals = [it.font_size for it in targets]
            cmd = ChangePropertyCommand(targets, "font_size", old_vals, [size] * len(targets))
            self.undo_stack.push(cmd)

    def _on_bold_toggled(self, checked: bool):
        targets = [it for it in self._current_items if isinstance(it, TextItem)]
        if targets:
            old_vals = [it.font_bold for it in targets]
            cmd = ChangePropertyCommand(targets, "font_bold", old_vals, [checked] * len(targets))
            self.undo_stack.push(cmd)

    def _on_italic_toggled(self, checked: bool):
        targets = [it for it in self._current_items if isinstance(it, TextItem)]
        if targets:
            old_vals = [it.font_italic for it in targets]
            cmd = ChangePropertyCommand(targets, "font_italic", old_vals, [checked] * len(targets))
            self.undo_stack.push(cmd)

    def _on_align_changed(self, align: Qt.AlignmentFlag):
        targets = [it for it in self._current_items if isinstance(it, TextItem)]
        if targets:
            old_vals = [it.text_alignment for it in targets]
            cmd = ChangePropertyCommand(targets, "text_alignment", old_vals, [align] * len(targets))
            self.undo_stack.push(cmd)

    def _on_lock_aspect_toggled(self, checked: bool):
        for it in self._current_items:
            it.lock_aspect_ratio = checked

    def _bring_to_front(self):
        if not self._current_items:
            return
        max_z = max((it.zValue() for it in self.scene.items()), default=0.0)
        for it in self._current_items:
            it.setZValue(max_z + 1.0)

    def _send_to_back(self):
        if not self._current_items:
            return
        min_z = min((it.zValue() for it in self.scene.items()), default=0.0)
        for it in self._current_items:
            it.setZValue(min_z - 1.0)
