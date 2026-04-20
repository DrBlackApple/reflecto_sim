"""Entry point for reflecto_sim — Reflectometry Simulator."""

from __future__ import annotations

import sys
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication


def _asset_path(relative: str) -> Path:
    """Resolve an asset path for both dev and PyInstaller contexts."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / relative

from reflecto_sim.materials import MaterialLibrary
from reflecto_sim.ui.app import ReflectoApp
from reflecto_sim.ui.palette import BG_DARK, BTN_BG, ENTRY_BG, LABEL_COL, SPINE_COL


def _apply_dark_palette(app: QApplication) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,           QColor(BG_DARK))
    pal.setColor(QPalette.ColorRole.WindowText,       QColor(LABEL_COL))
    pal.setColor(QPalette.ColorRole.Base,             QColor(ENTRY_BG))
    pal.setColor(QPalette.ColorRole.AlternateBase,    QColor(BG_DARK))
    pal.setColor(QPalette.ColorRole.ToolTipBase,      QColor(BG_DARK))
    pal.setColor(QPalette.ColorRole.ToolTipText,      QColor(LABEL_COL))
    pal.setColor(QPalette.ColorRole.Text,             QColor(LABEL_COL))
    pal.setColor(QPalette.ColorRole.Button,           QColor(BTN_BG))
    pal.setColor(QPalette.ColorRole.ButtonText,       QColor(LABEL_COL))
    pal.setColor(QPalette.ColorRole.BrightText,       QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.Link,             QColor("#00BFFF"))
    pal.setColor(QPalette.ColorRole.Highlight,        QColor(SPINE_COL))
    pal.setColor(QPalette.ColorRole.HighlightedText,  QColor(LABEL_COL))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       QColor("#555577"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#555577"))
    app.setPalette(pal)

    # Additional stylesheet tweaks for QFrame separators and labels
    app.setStyleSheet("""
        QFrame[frameShape="4"],
        QFrame[frameShape="5"] {
            color: #3a3a5a;
            background: #3a3a5a;
        }
        QLabel {
            color: #ccccee;
        }
        QCheckBox {
            color: #ccccee;
        }
        QRadioButton {
            color: #ccccee;
        }
        QLineEdit {
            background: #1a1a2e;
            color: #ccccee;
            border: 1px solid #3a3a5a;
            border-radius: 3px;
            padding: 2px 4px;
        }
        QComboBox {
            background: #1a1a2e;
            color: #ccccee;
            border: 1px solid #3a3a5a;
            border-radius: 3px;
            padding: 2px 4px;
        }
        QComboBox QAbstractItemView {
            background: #1a1a2e;
            color: #ccccee;
            selection-background-color: #3a3a5a;
        }
        QScrollArea {
            border: 1px solid #3a3a5a;
        }
        QScrollBar:vertical {
            background: #0d0d1a;
            width: 8px;
        }
        QScrollBar::handle:vertical {
            background: #3a3a5a;
            border-radius: 4px;
        }
        QPushButton {
            background: #1e1e3a;
            color: #ccccee;
            border: 1px solid #3a3a5a;
            border-radius: 3px;
            padding: 3px 8px;
        }
        QPushButton:hover {
            background: #2a2a5a;
        }
        QPushButton:pressed {
            background: #3a3a7a;
        }
        QPushButton#btn_compute {
            background: #1a3a1a;
            color: #98FB98;
            font-weight: bold;
            padding: 5px 8px;
        }
        QPushButton#btn_compute:hover {
            background: #2a5a2a;
        }
        QListWidget {
            background: #12122a;
            color: #ccccee;
            border: 1px solid #3a3a5a;
        }
        QSpinBox {
            background: #1a1a2e;
            color: #ccccee;
            border: 1px solid #3a3a5a;
            border-radius: 3px;
            padding: 2px 4px;
        }
        QSlider::groove:horizontal {
            background: #3a3a5a;
            height: 4px;
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: #00BFFF;
            width: 12px;
            height: 12px;
            margin: -4px 0;
            border-radius: 6px;
        }
        QMenuBar {
            background: #0d0d1a;
            color: #ccccee;
        }
        QMenuBar::item:selected {
            background: #3a3a5a;
        }
        QMenu {
            background: #0d0d1a;
            color: #ccccee;
            border: 1px solid #3a3a5a;
        }
        QMenu::item:selected {
            background: #3a3a5a;
        }
        QStatusBar {
            background: #0d0d1a;
            color: #aaaacc;
        }
        QToolTip {
            background: #1a1a2e;
            color: #ccccee;
            border: 1px solid #3a3a5a;
        }
    """)


def main() -> None:
    # Configure pyqtgraph before creating QApplication
    pg.setConfigOption("background", BG_DARK)
    pg.setConfigOption("foreground", LABEL_COL)
    pg.setConfigOption("antialias", True)

    app = QApplication(sys.argv)
    app.setApplicationName("reflecto_sim")
    icon_path = _asset_path("assets/icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    _apply_dark_palette(app)

    lib = MaterialLibrary()
    mat_dir = Path(__file__).parent / "materials"
    if mat_dir.exists():
        loaded = lib.load_directory(mat_dir)
        print(f"Loaded materials: {loaded}")
    else:
        print(f"Warning: materials directory not found at {mat_dir}")

    window = ReflectoApp(lib)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
