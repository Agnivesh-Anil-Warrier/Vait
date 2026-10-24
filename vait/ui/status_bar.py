"""Bottom status bar showing zoom level, selection state, coordinates, and shortcuts."""

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import (
    QStatusBar,
    QLabel,
    QHBoxLayout,
    QWidget,
    QToolButton,
    QMenu
)

class CanvasStatusBar(QStatusBar):
    """Custom status bar displaying canvas context and navigation controls."""

    def __init__(self, view, parent=None):
        super().__init__(parent)
        self.view = view

        # Permanent status widgets on right
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-weight: 500;")

        self.lbl_coords = QLabel("X: 0, Y: 0")
        self.lbl_coords.setStyleSheet("color: #64748b; font-family: monospace; min-width: 140px;")

        self.btn_zoom = QToolButton()
        self.btn_zoom.setText("100%")
        self.btn_zoom.setStyleSheet("font-weight: 600; min-width: 50px;")
        self.btn_zoom.setToolTip("Click to choose zoom level")

        # Zoom popup menu
        self.zoom_menu = QMenu(self)
        for pct in (25, 50, 75, 100, 150, 200, 300, 400):
            action = self.zoom_menu.addAction(f"{pct}%")
            action.triggered.connect(lambda checked=False, p=pct: self.view.set_zoom_level(p / 100.0))
        self.zoom_menu.addSeparator()
        self.zoom_menu.addAction("Reset Zoom (100%)", self.view.reset_zoom)
        self.zoom_menu.addAction("Fit All Content", self.view.fit_content)
        self.btn_zoom.setMenu(self.zoom_menu)
        self.btn_zoom.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.lbl_hint = QLabel("Space + Drag or Middle-Click to pan  •  Scroll to zoom")
        self.lbl_hint.setStyleSheet("color: #475569; font-style: italic;")

        # Assemble
        self.addWidget(self.lbl_status, 1)
        self.addPermanentWidget(self.lbl_hint)
        self.addPermanentWidget(self.lbl_coords)
        self.addPermanentWidget(self.btn_zoom)

        # Connect signals
        self.view.zoom_changed.connect(self.update_zoom)
        self.view.cursor_scene_pos_changed.connect(self.update_coords)

    def update_zoom(self, zoom: float):
        pct = int(round(zoom * 100))
        self.btn_zoom.setText(f"{pct}%")

    def update_coords(self, pt: QPointF):
        self.lbl_coords.setText(f"X: {int(pt.x())}, Y: {int(pt.y())}")

    def update_selection_info(self, items: list):
        if not items:
            self.lbl_status.setText("Ready")
        elif len(items) == 1:
            itype = getattr(items[0], "item_type", "Item").capitalize()
            self.lbl_status.setText(f"Selected: {itype}")
        else:
            self.lbl_status.setText(f"{len(items)} items selected")
