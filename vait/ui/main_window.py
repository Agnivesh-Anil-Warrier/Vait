"""Main window assembling top toolbar, tool palette, properties panel, infinite canvas, and status bar."""

import os
from typing import Optional
from PySide6.QtCore import Qt, QSettings, QPointF, QSize
from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QToolButton,
    QButtonGroup,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QWidget,
    QMenu
)
from PySide6.QtGui import (
    QAction,
    QKeySequence,
    QUndoStack,
    QIcon
)

from vait.constants import (
    APP_NAME,
    PROJECT_FILE_FILTER,
    EXPORT_IMAGE_FILTER,
    PROJECT_FILE_EXTENSION,
    ToolMode,
    ShapeType,
    GridStyle
)
from vait.canvas.canvas_scene import InfiniteCanvasScene
from vait.canvas.canvas_view import InfiniteCanvasView
from vait.clipboard.clipboard_manager import ClipboardManager
from vait.storage.project_file import ProjectFileManager
from vait.storage.exporter import CanvasExporter
from vait.items import BaseCanvasItem, ShapeItem, ImageItem
from vait.commands.undo_commands import ChangePropertyCommand
from vait.ui.icons import create_icon
from vait.ui.properties_panel import PropertiesPanel
from vait.ui.status_bar import CanvasStatusBar

class MainWindow(QMainWindow):
    """Primary application window for Vait Infinite Canvas Whiteboard."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Untitled[*] — {APP_NAME}")
        self.resize(1280, 800)

        # Settings for recent files and window state
        self.settings = QSettings("VaitApp", "Whiteboard")
        self.current_project_path: Optional[str] = None

        # Core undo stack
        self.undo_stack = QUndoStack(self)
        self.undo_stack.cleanChanged.connect(self._on_clean_changed)

        # Core canvas scene and view
        self.scene = InfiniteCanvasScene(self.undo_stack, self)
        self.view = InfiniteCanvasView(self.scene, self)

        # Clipboard manager
        self.clipboard_manager = ClipboardManager(self.scene, self.undo_stack)

        # Properties panel and status bar
        self.properties_panel = PropertiesPanel(self.scene, self.undo_stack, self)
        self.status_bar = CanvasStatusBar(self.view, self)
        self.setStatusBar(self.status_bar)

        # Central layout
        central_container = QWidget()
        layout = QVBoxLayout(central_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.properties_panel)
        layout.addWidget(self.view, 1)
        self.setCentralWidget(central_container)

        # Connect signals
        self.scene.selection_state_changed.connect(self._on_selection_changed)
        self.scene.tool_changed.connect(self._on_scene_tool_changed)
        self.view.image_dropped.connect(self._on_image_dropped)
        self.view.project_dropped.connect(self.open_project_file)

        # Setup menus, toolbars, actions
        self._setup_actions()
        self._setup_menus()
        self._setup_top_toolbar()
        self._setup_left_tool_palette()

        self._update_window_title()

    # --- Setup UI Elements ---

    def _setup_actions(self):
        # File Actions
        self.act_new = QAction(create_icon("new"), "&New Canvas", self)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)
        self.act_new.setStatusTip("Create a new blank canvas")
        self.act_new.triggered.connect(self.new_project)

        self.act_open = QAction(create_icon("open"), "&Open...", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.setStatusTip("Open an existing .canvas project")
        self.act_open.triggered.connect(self.open_project_dialog)

        self.act_save = QAction(create_icon("save"), "&Save", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.setStatusTip("Save current canvas project")
        self.act_save.triggered.connect(self.save_project)

        self.act_save_as = QAction("Save &As...", self)
        self.act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.act_save_as.setStatusTip("Save project with a new filename")
        self.act_save_as.triggered.connect(self.save_project_as)

        self.act_export = QAction(create_icon("export"), "&Export Image...", self)
        self.act_export.setShortcut(QKeySequence("Ctrl+E"))
        self.act_export.setStatusTip("Export canvas to PNG/JPG image")
        self.act_export.triggered.connect(self.export_image_dialog)

        # Edit Actions
        self.act_undo = self.undo_stack.createUndoAction(self, "&Undo")
        self.act_undo.setIcon(create_icon("undo"))
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)

        self.act_redo = self.undo_stack.createRedoAction(self, "&Redo")
        self.act_redo.setIcon(create_icon("redo"))
        self.act_redo.setShortcuts([QKeySequence.StandardKey.Redo, QKeySequence("Ctrl+Y")])

        self.act_cut = QAction("&Cut", self)
        self.act_cut.setShortcut(QKeySequence.StandardKey.Cut)
        self.act_cut.triggered.connect(self.clipboard_manager.cut_selection)

        self.act_copy = QAction("&Copy", self)
        self.act_copy.setShortcut(QKeySequence.StandardKey.Copy)
        self.act_copy.triggered.connect(self.clipboard_manager.copy_selection)

        self.act_paste = QAction("&Paste", self)
        self.act_paste.setShortcut(QKeySequence.StandardKey.Paste)
        self.act_paste.triggered.connect(lambda: self.clipboard_manager.paste_from_clipboard(
            target_pos=self.view.mapToScene(self.view.viewport().rect().center())
        ))

        self.act_duplicate = QAction("&Duplicate", self)
        self.act_duplicate.setShortcut(QKeySequence("Ctrl+D"))
        self.act_duplicate.triggered.connect(self.clipboard_manager.duplicate_selection)

        self.act_delete = QAction("&Delete", self)
        self.act_delete.setShortcuts([QKeySequence.StandardKey.Delete, QKeySequence("Backspace")])
        self.act_delete.triggered.connect(self.scene.delete_selection)
        self.addAction(self.act_delete)

        self.act_select_all = QAction("Select &All", self)
        self.act_select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.act_select_all.triggered.connect(self.scene.select_all)

        self.act_escape = QAction("Cancel / Deselect", self)
        self.act_escape.setShortcut(QKeySequence("Escape"))
        self.act_escape.triggered.connect(self._on_escape_pressed)
        self.addAction(self.act_escape)

        # View Actions
        self.act_zoom_in = QAction(create_icon("zoom_in"), "Zoom &In", self)
        self.act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.act_zoom_in.triggered.connect(self.view.zoom_in)

        self.act_zoom_out = QAction(create_icon("zoom_out"), "Zoom &Out", self)
        self.act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.act_zoom_out.triggered.connect(self.view.zoom_out)

        self.act_reset_zoom = QAction("Reset Zoom (100%)", self)
        self.act_reset_zoom.setShortcut(QKeySequence("Ctrl+0"))
        self.act_reset_zoom.triggered.connect(self.view.reset_zoom)

        self.act_fit_all = QAction(create_icon("fit"), "&Fit All Content", self)
        self.act_fit_all.setShortcut(QKeySequence("Shift+1"))
        self.act_fit_all.triggered.connect(self.view.fit_content)

        self.act_grid_toggle = QAction(create_icon("grid"), "Toggle Grid Style", self)
        self.act_grid_toggle.setToolTip("Toggle between Dots, Lines, and Blank grid")
        self.act_grid_toggle.triggered.connect(self._toggle_grid_style)

    def _setup_menus(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.act_new)
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_export)
        file_menu.addSeparator()
        self.recent_menu = file_menu.addMenu("Recent Projects")
        self._update_recent_menu()
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_cut)
        edit_menu.addAction(self.act_copy)
        edit_menu.addAction(self.act_paste)
        edit_menu.addAction(self.act_duplicate)
        edit_menu.addAction(self.act_delete)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_select_all)

        # View Menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.act_zoom_in)
        view_menu.addAction(self.act_zoom_out)
        view_menu.addAction(self.act_reset_zoom)
        view_menu.addAction(self.act_fit_all)
        view_menu.addSeparator()
        view_menu.addAction(self.act_grid_toggle)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About Vait", self._show_about_dialog)
        help_menu.addAction("&Shortcuts Cheatsheet", self._show_shortcuts_dialog)

    def _setup_top_toolbar(self):
        tb = QToolBar("Main Controls", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        tb.addAction(self.act_new)
        tb.addAction(self.act_open)
        tb.addAction(self.act_save)
        tb.addAction(self.act_export)
        tb.addSeparator()
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)
        tb.addSeparator()
        tb.addAction(self.act_zoom_in)
        tb.addAction(self.act_zoom_out)
        tb.addAction(self.act_fit_all)
        tb.addAction(self.act_grid_toggle)

    def _setup_left_tool_palette(self):
        palette = QToolBar("Tools", self)
        palette.setMovable(False)
        palette.setOrientation(Qt.Orientation.Vertical)
        palette.setIconSize(QSize(24, 24))
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, palette)

        self.tool_button_group = QButtonGroup(self)
        self.tool_button_group.setExclusive(True)

        def add_tool_btn(tool_mode: ToolMode, icon_name: str, tooltip: str, shortcut_str: str = ""):
            btn = QToolButton(palette)
            btn.setIcon(create_icon(icon_name))
            btn.setCheckable(True)
            tip = f"{tooltip} ({shortcut_str})" if shortcut_str else tooltip
            btn.setToolTip(tip)
            if shortcut_str:
                act = QAction(self)
                act.setShortcut(QKeySequence(shortcut_str))
                act.triggered.connect(lambda: self._select_tool(tool_mode, btn))
                self.addAction(act)
            btn.clicked.connect(lambda: self._select_tool(tool_mode, btn))
            palette.addWidget(btn)
            self.tool_button_group.addButton(btn)
            return btn

        # 1. Select
        self.btn_tool_select = add_tool_btn(ToolMode.SELECT, "select", "Select & Manipulate", "V")
        self.btn_tool_select.setChecked(True)

        # 2. Pan / Hand
        self.btn_tool_pan = add_tool_btn(ToolMode.PAN, "pan", "Hand Tool (Pan)", "H")

        palette.addSeparator()

        # 3. Pen
        self.btn_tool_pen = add_tool_btn(ToolMode.PEN, "pen", "Freehand Pen", "P")

        # 4. Eraser
        self.btn_tool_eraser = add_tool_btn(ToolMode.ERASER, "eraser", "Stroke Eraser", "E")

        palette.addSeparator()

        # 5. Text
        self.btn_tool_text = add_tool_btn(ToolMode.TEXT, "text", "Text Box", "T")

        # 6. Shapes with dropdown popup
        self.btn_tool_shape = QToolButton(palette)
        self.btn_tool_shape.setIcon(create_icon("rectangle"))
        self.btn_tool_shape.setCheckable(True)
        self.btn_tool_shape.setToolTip("Shapes (Rectangle, Ellipse, Line, Arrow, Triangle, Diamond)")
        self.tool_button_group.addButton(self.btn_tool_shape)

        # Shape choices popup menu
        shape_menu = QMenu(self.btn_tool_shape)
        shapes_info = [
            (ShapeType.RECTANGLE, "rectangle", "Rectangle", "R"),
            (ShapeType.ROUNDED_RECT, "rounded_rect", "Rounded Rectangle", ""),
            (ShapeType.ELLIPSE, "ellipse", "Ellipse / Circle", "O"),
            (ShapeType.LINE, "line", "Line", "L"),
            (ShapeType.ARROW, "arrow", "Arrow", "A"),
            (ShapeType.TRIANGLE, "triangle", "Triangle", ""),
            (ShapeType.DIAMOND, "diamond", "Diamond", ""),
        ]

        for st, icon_name, label, sc in shapes_info:
            act = shape_menu.addAction(create_icon(icon_name), f"{label} ({sc})" if sc else label)
            act.triggered.connect(lambda checked=False, s=st, ic=icon_name: self._set_active_shape(s, ic))
            if sc:
                key_act = QAction(self)
                key_act.setShortcut(QKeySequence(sc))
                key_act.triggered.connect(lambda s=st, ic=icon_name: self._set_active_shape(s, ic))
                self.addAction(key_act)

        self.btn_tool_shape.setMenu(shape_menu)
        self.btn_tool_shape.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btn_tool_shape.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_tool_shape.customContextMenuRequested.connect(
            lambda pos: shape_menu.exec(self.btn_tool_shape.mapToGlobal(pos))
        )

        def _on_shape_btn_clicked():
            if self.scene.current_tool == ToolMode.SHAPE:
                # If already in shape tool, clicking again pops up the shape choices menu
                self.btn_tool_shape.showMenu()
            else:
                self._select_tool(ToolMode.SHAPE, self.btn_tool_shape)

        self.btn_tool_shape.clicked.connect(_on_shape_btn_clicked)
        palette.addWidget(self.btn_tool_shape)

        palette.addSeparator()

        # 7. Image
        self.btn_tool_image = QToolButton(palette)
        self.btn_tool_image.setIcon(create_icon("image"))
        self.btn_tool_image.setToolTip("Insert Image File (I)")
        self.btn_tool_image.clicked.connect(self.insert_image_dialog)
        palette.addWidget(self.btn_tool_image)

        act_img = QAction(self)
        act_img.setShortcut(QKeySequence("I"))
        act_img.triggered.connect(self.insert_image_dialog)
        self.addAction(act_img)

    def _select_tool(self, tool_mode: ToolMode, button: QToolButton):
        button.setChecked(True)
        self.scene.set_tool(tool_mode)

    def _on_scene_tool_changed(self, tool_mode: ToolMode):
        """Keep tool palette buttons in sync when active tool changes programmatically."""
        if tool_mode == ToolMode.SELECT:
            self.btn_tool_select.setChecked(True)
        elif tool_mode == ToolMode.PAN:
            self.btn_tool_pan.setChecked(True)
        elif tool_mode == ToolMode.PEN:
            self.btn_tool_pen.setChecked(True)
        elif tool_mode == ToolMode.ERASER:
            self.btn_tool_eraser.setChecked(True)
        elif tool_mode == ToolMode.TEXT:
            self.btn_tool_text.setChecked(True)
        elif tool_mode == ToolMode.SHAPE:
            self.btn_tool_shape.setChecked(True)
        selected = [it for it in self.scene.selectedItems() if isinstance(it, BaseCanvasItem)]
        self.properties_panel.update_for_selection(selected)

    def _set_active_shape(self, shape_type: ShapeType, icon_name: str):
        self.scene.current_shape_type = shape_type
        self.btn_tool_shape.setIcon(create_icon(icon_name))
        display_name = shape_type.value.capitalize().replace("_", " ")
        self.btn_tool_shape.setToolTip(f"Shape: {display_name}")
        self._select_tool(ToolMode.SHAPE, self.btn_tool_shape)

        # Synchronize properties panel dropdown if present
        if hasattr(self, "properties_panel") and hasattr(self.properties_panel, "combo_shape_type"):
            idx = self.properties_panel.combo_shape_type.findData(shape_type)
            if idx >= 0:
                self.properties_panel.combo_shape_type.blockSignals(True)
                self.properties_panel.combo_shape_type.setCurrentIndex(idx)
                self.properties_panel.combo_shape_type.blockSignals(False)

        # If any shape is currently selected on the canvas, change its shape type!
        selected_shapes = [it for it in self.scene.selectedItems() if isinstance(it, ShapeItem)]
        if selected_shapes:
            old_types = [it.shape_type for it in selected_shapes]
            cmd = ChangePropertyCommand(selected_shapes, "shape_type", old_types, [shape_type] * len(selected_shapes))
            self.undo_stack.push(cmd)
            for it in selected_shapes:
                it.is_linear_item = it.shape_type in (ShapeType.LINE, ShapeType.ARROW)
                it.include_rotate_handle = not it.is_linear_item
                it.update()

    def _toggle_grid_style(self):
        styles = [GridStyle.DOTS, GridStyle.LINES, GridStyle.NONE]
        curr_idx = styles.index(self.scene.grid_style)
        next_style = styles[(curr_idx + 1) % len(styles)]
        self.scene.grid_style = next_style
        self.scene.update()
        name = next_style.value.capitalize()
        self.statusBar().showMessage(f"Grid: {name}", 2000)

    def _on_selection_changed(self, selected_items: list):
        self.properties_panel.update_for_selection(selected_items)
        self.status_bar.update_selection_info(selected_items)

    def _on_clean_changed(self, is_clean: bool):
        self.setWindowModified(not is_clean)
        self._update_window_title()

    def _on_escape_pressed(self):
        if self.scene.selectedItems():
            self.scene.clearSelection()
        elif self.scene.current_tool != ToolMode.SELECT:
            self._select_tool(ToolMode.SELECT, self.btn_tool_select)

    def _update_window_title(self):
        name = os.path.basename(self.current_project_path) if self.current_project_path else "Untitled"
        self.setWindowTitle(f"{name}[*] — {APP_NAME}")

    # --- Project Persistence ---

    def new_project(self):
        if not self._maybe_save():
            return
        self.scene.clear()
        self.undo_stack.clear()
        self.current_project_path = None
        self.view.reset_zoom()
        self._update_window_title()
        self.statusBar().showMessage("New canvas ready", 2000)

    def open_project_dialog(self):
        if not self._maybe_save():
            return
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Canvas Project", "", PROJECT_FILE_FILTER)
        if filepath:
            self.open_project_file(filepath)

    def open_project_file(self, filepath: str):
        if not os.path.exists(filepath):
            QMessageBox.critical(self, "File Not Found", f"Cannot find file:\n{filepath}")
            return

        try:
            items, view_state = ProjectFileManager.load_project(filepath)
            self.scene.clear()
            self.undo_stack.clear()

            for item in items:
                self.scene.addItem(item)

            if view_state:
                self.view.restore_view_state(view_state)

            self.current_project_path = filepath
            self.undo_stack.setClean()
            self._update_window_title()
            self._add_to_recent(filepath)
            self.statusBar().showMessage(f"Opened {os.path.basename(filepath)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Failed to Open Project", f"Could not open project:\n{str(e)}")

    def save_project(self) -> bool:
        if not self.current_project_path:
            return self.save_project_as()
        return self._do_save(self.current_project_path)

    def save_project_as(self) -> bool:
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Canvas As", "", PROJECT_FILE_FILTER)
        if not filepath:
            return False
        if not filepath.lower().endswith(PROJECT_FILE_EXTENSION):
            filepath += PROJECT_FILE_EXTENSION
        if self._do_save(filepath):
            self.current_project_path = filepath
            self._add_to_recent(filepath)
            return True
        return False

    def _do_save(self, filepath: str) -> bool:
        try:
            view_state = self.view.get_view_state()
            items = [it for it in self.scene.items() if hasattr(it, "to_dict")]
            ProjectFileManager.save_project(filepath, items, view_state)
            self.undo_stack.setClean()
            self._update_window_title()
            self.statusBar().showMessage(f"Saved to {os.path.basename(filepath)}", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save project:\n{str(e)}")
            return False

    def _maybe_save(self) -> bool:
        if not self.isWindowModified():
            return True
        res = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "The document has been modified.\nDo you want to save your changes?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        if res == QMessageBox.StandardButton.Save:
            return self.save_project()
        elif res == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def closeEvent(self, event):
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()

    # --- Image Insertion and Drag & Drop ---

    def insert_image_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Insert Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*.*)"
        )
        if filepath:
            center_scene = self.view.mapToScene(self.view.viewport().rect().center())
            self._insert_image(filepath, center_scene)

    def _on_image_dropped(self, filepath: str, scene_pos: QPointF):
        self._insert_image(filepath, scene_pos)

    def _insert_image(self, filepath: str, scene_pos: QPointF):
        try:
            img_item = ImageItem.from_file(filepath, x=scene_pos.x(), y=scene_pos.y())
            from vait.commands.undo_commands import AddItemsCommand
            cmd = AddItemsCommand(self.scene, [img_item], f"Insert {os.path.basename(filepath)}")
            self.undo_stack.push(cmd)
            self._select_tool(ToolMode.SELECT, self.btn_tool_select)
        except Exception as e:
            QMessageBox.critical(self, "Image Error", f"Could not load image:\n{str(e)}")

    # --- Export ---

    def export_image_dialog(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Canvas Image", "canvas_export.png", EXPORT_IMAGE_FILTER)
        if not filepath:
            return

        has_selection = bool(self.scene.selectedItems())
        scope = "all"
        if has_selection:
            res = QMessageBox.question(
                self,
                "Export Scope",
                "Do you want to export only the selected items?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if res == QMessageBox.StandardButton.Cancel:
                return
            scope = "selected" if res == QMessageBox.StandardButton.Yes else "all"

        try:
            success = CanvasExporter.export_to_image(
                self.scene,
                filepath,
                view=self.view,
                scope=scope,
                scale_factor=2.0
            )
            if success:
                self.statusBar().showMessage(f"Successfully exported to {os.path.basename(filepath)}", 3000)
            else:
                QMessageBox.warning(self, "Export Failed", "Canvas export could not be completed.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export image:\n{str(e)}")

    # --- Recent Projects ---

    def _add_to_recent(self, filepath: str):
        recents = self.settings.value("recent_projects", [])
        if not isinstance(recents, list):
            recents = []
        if filepath in recents:
            recents.remove(filepath)
        recents.insert(0, filepath)
        recents = recents[:8]
        self.settings.setValue("recent_projects", recents)
        self._update_recent_menu()

    def _update_recent_menu(self):
        self.recent_menu.clear()
        recents = self.settings.value("recent_projects", [])
        if not isinstance(recents, list) or not recents:
            act = self.recent_menu.addAction("No Recent Files")
            act.setEnabled(False)
            return

        for p in recents:
            if os.path.exists(p):
                act = self.recent_menu.addAction(os.path.basename(p))
                act.triggered.connect(lambda checked=False, path=p: self.open_project_file(path))

    # --- Help Dialogs ---

    def _show_about_dialog(self):
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME} v1.0</h3>"
            "<p>A personal infinite canvas desktop application for organizing images, text, drawings, and shapes.</p>"
            "<p>Built with PySide6 (Qt for Python).</p>"
        )

    def _show_shortcuts_dialog(self):
        msg = """
<b>Canvas Navigation:</b><br>
• Space + Left Drag or Middle Mouse Button: Pan canvas<br>
• Mouse Wheel: Zoom in/out anchored to mouse<br>
• Ctrl+0: Reset zoom to 100%<br>
• Shift+1: Fit all content in view<br><br>

<b>Tools:</b><br>
• V: Select & Move<br>
• H: Hand / Pan<br>
• P: Freehand Pen<br>
• E: Eraser<br>
• T: Text Box<br>
• R: Rectangle | O: Ellipse | L: Line | A: Arrow<br>
• I: Insert Image<br><br>

<b>Editing & Selection:</b><br>
• Click & Drag: Move or marquee select<br>
• Shift + Drag Shape: Constrain square/circle<br>
• Ctrl+C / Ctrl+V: Copy & Paste<br>
• Ctrl+X: Cut<br>
• Ctrl+D: Duplicate<br>
• Ctrl+Z / Ctrl+Y: Undo & Redo<br>
• Delete / Backspace: Remove selected objects<br>
• Double-click text: Edit text inline
"""
        QMessageBox.information(self, "Keyboard Shortcuts & Gestures", msg)
