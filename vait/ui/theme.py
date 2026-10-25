"""Modern Windows desktop theme stylesheet and palette for Vait."""

DARK_THEME_QSS = """
/* Global Window & Fonts */
QMainWindow, QDialog {
    background-color: #0f172a;
    color: #f1f5f9;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
}

/* Toolbars */
QToolBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 4px;
    spacing: 5px;
    margin: 4px;
}

QToolBar::separator:horizontal {
    width: 1px;
    height: 18px;
    margin: 4px 6px;
    background-color: #334155;
}

QToolBar::separator:vertical {
    height: 1px;
    width: 24px;
    margin: 6px 4px;
    background-color: #334155;
}

/* Tool Buttons */
QToolButton {
    background-color: transparent;
    color: #f1f5f9;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px;
    min-width: 26px;
    min-height: 26px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #334155;
    border: 1px solid #475569;
    color: #ffffff;
}

QToolButton:pressed {
    background-color: #0f172a;
    border: 1px solid #334155;
}

QToolButton:checked {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #60a5fa;
}

QToolButton:checked:hover {
    background-color: #1d4ed8;
    border: 1px solid #93c5fd;
}

QToolButton:disabled {
    color: #475569;
}

QToolButton::menu-button {
    border: none;
    border-left: 1px solid rgba(255, 255, 255, 0.2);
    width: 14px;
    padding: 1px;
}

QToolButton::menu-button:hover {
    background-color: rgba(255, 255, 255, 0.15);
}

QToolButton::menu-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid #f1f5f9;
    margin-right: 2px;
}

QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #334155;
    border: 1px solid #475569;
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton#primaryButton {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #1d4ed8;
}

/* Menu Bar & Menus */
QMenuBar {
    background-color: #0f172a;
    color: #cbd5e1;
    border-bottom: 1px solid #1e293b;
    padding: 2px 6px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 8px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #1e293b;
    color: #ffffff;
}

QMenu {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px 0px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #334155;
    margin: 4px 8px;
}

/* Status Bar */
QStatusBar {
    background-color: #0f172a;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
    padding: 3px 10px;
    font-size: 12px;
}

/* SpinBox, ComboBox, LineEdit */
QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 20px;
}

QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, QLineEdit:hover {
    border-color: #475569;
}

QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {
    border-color: #3b82f6;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}

QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8;
    margin-right: 6px;
}

QComboBox::down-arrow:hover {
    border-top-color: #f8fafc;
}

/* ComboBox Dropdown View */
QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: #f8fafc;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    color: #f8fafc;
    min-height: 26px;
    padding: 4px 8px;
    border-radius: 4px;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #334155;
    color: #ffffff;
}

/* Item Views generally */
QListView, QTreeView, QTableView, QAbstractItemView {
    background-color: #1e293b;
    color: #f8fafc;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    border: 1px solid #334155;
    border-radius: 6px;
    outline: none;
}

QListView::item, QTreeView::item, QTableView::item {
    color: #f8fafc;
    padding: 4px 8px;
}

QListView::item:selected, QTreeView::item:selected, QTableView::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QListView::item:hover, QTreeView::item:hover, QTableView::item:hover {
    background-color: #334155;
    color: #ffffff;
}

/* Tooltip */
QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
}

/* Color Picker Button */
QPushButton.color-pill {
    min-width: 20px;
    min-height: 20px;
    max-width: 20px;
    max-height: 20px;
    border-radius: 10px;
    border: 2px solid #ffffff;
    margin: 2px;
}

/* Dock & Properties Panel */
QDockWidget {
    color: #f8fafc;
    font-weight: 600;
}

QDockWidget::title {
    background-color: #1e293b;
    padding: 6px 10px;
    border-bottom: 1px solid #334155;
}

QLabel {
    color: #cbd5e1;
}

/* Rubber Band Marquee Selection */
QRubberBand {
    border: 1.5px solid #3b82f6;
    background-color: rgba(59, 130, 246, 0.22);
}
"""

from PySide6.QtGui import QPalette, QColor

def get_dark_palette() -> QPalette:
    """Return a unified dark mode QPalette for the application."""
    palette = QPalette()
    bg_dark = QColor("#0f172a")
    card_dark = QColor("#1e293b")
    border_dark = QColor("#334155")
    text_primary = QColor("#f8fafc")
    disabled_text = QColor("#64748b")
    accent_blue = QColor("#2563eb")

    palette.setColor(QPalette.ColorRole.Window, bg_dark)
    palette.setColor(QPalette.ColorRole.WindowText, text_primary)
    palette.setColor(QPalette.ColorRole.Base, card_dark)
    palette.setColor(QPalette.ColorRole.AlternateBase, bg_dark)
    palette.setColor(QPalette.ColorRole.ToolTipBase, bg_dark)
    palette.setColor(QPalette.ColorRole.ToolTipText, text_primary)
    palette.setColor(QPalette.ColorRole.Text, text_primary)
    palette.setColor(QPalette.ColorRole.Button, card_dark)
    palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, accent_blue)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#3b82f6"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, disabled_text)

    # Disabled colors
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, border_dark)

    return palette

