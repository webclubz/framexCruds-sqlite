#!/usr/bin/env python3
"""
pyCruds - A modular CRUD application builder
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QFile
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Set palette for better window controls visibility
    from PyQt6.QtGui import QPalette, QColor
    palette = app.palette()

    # Make window frame and title bar elements darker for contrast
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    app.setPalette(palette)

    # Load central stylesheet (minimal design)
    try:
        with open('styles/app.qss', 'r') as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Stylesheet load failed: {e}")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
