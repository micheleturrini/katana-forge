#!/usr/bin/env python3
"""
Launcher script for Katana Modern FX FloorBoard Editor.
"""

import sys
import os

# Add current workspace directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from katana_modern.ui.main_window import KatanaMainWindow


def main():
    # High DPI scaling configuration
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Katana Forge")
    app.setApplicationDisplayName("Katana Forge — MkII Tone Studio")
    app.setOrganizationName("KatanaForge")

    from PyQt6.QtGui import QIcon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "katana_modern", "resources", "app_logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = KatanaMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
