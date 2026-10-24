"""Application entry point for Vait Infinite Canvas Whiteboard."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from vait.constants import APP_NAME, APP_VERSION
from vait.ui.theme import DARK_THEME_QSS
from vait.ui.main_window import MainWindow

def main():
    # Set application details
    QApplication.setApplicationName(APP_NAME)
    QApplication.setApplicationVersion(APP_VERSION)
    QApplication.setOrganizationName("Vait")

    app = QApplication(sys.argv)

    # Set default modern system font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Apply modern stylesheet
    app.setStyleSheet(DARK_THEME_QSS)

    # Launch main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
