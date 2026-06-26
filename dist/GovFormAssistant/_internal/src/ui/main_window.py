import os
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import settings
from src.ui.tabs.batch_tab import BatchTab
from src.ui.tabs.converter_tab import ConverterTab
from src.ui.tabs.file_size_tab import FileSizeTab
from src.ui.tabs.image_resizer_tab import ImageResizerTab
from src.ui.tabs.pdf_tools_tab import PDFToolsTab
from src.ui.tabs.presets_tab import PresetsTab
from src.ui.tabs.signature_tab import SignatureTab


_STYLE_DIR = Path(__file__).parent.parent.parent / "assets" / "styles"


def _load_qss(name: str) -> str:
    path = _STYLE_DIR / f"{name}.qss"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Government Form Assistant")
        self.setMinimumSize(1050, 720)
        self.resize(
            settings.get("window_width", 1100),
            settings.get("window_height", 750),
        )

        self._build_ui()
        self._apply_theme()

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_tabs())

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "Government Form Assistant v1.0  |  100% Offline  |  No data sent anywhere"
        )

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("appHeader")
        header.setFixedHeight(58)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("Government Form Assistant")
        title.setObjectName("headerTitle")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addStretch()

        badge = QLabel("100% Offline  |  Privacy First")
        badge.setObjectName("headerBadge")
        layout.addWidget(badge)

        layout.addSpacing(20)

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("themeToggleBtn")
        self.theme_btn.setFixedSize(110, 32)
        self.theme_btn.clicked.connect(self._toggle_theme)
        self._update_theme_btn_label()
        layout.addWidget(self.theme_btn)

        return header

    def _build_tabs(self) -> QTabWidget:
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setIconSize(QSize(18, 18))
        self.tabs.setDocumentMode(False)

        tab_defs = [
            ("Image Resizer", ImageResizerTab()),
            ("File Size", FileSizeTab()),
            ("Signature", SignatureTab()),
            ("PDF Tools", PDFToolsTab()),
            ("Converters", ConverterTab()),
            ("Exam Presets", PresetsTab()),
            ("Batch Process", BatchTab()),
        ]
        for label, widget in tab_defs:
            self.tabs.addTab(widget, label)

        return self.tabs

    # ------------------------------------------------------------------ #
    # Theme
    # ------------------------------------------------------------------ #

    def _toggle_theme(self) -> None:
        new_theme = "light" if settings.theme == "dark" else "dark"
        settings.theme = new_theme
        self._update_theme_btn_label()
        self._apply_theme()

    def _update_theme_btn_label(self) -> None:
        self.theme_btn.setText(
            "Light Mode" if settings.theme == "dark" else "Dark Mode"
        )

    def _apply_theme(self) -> None:
        qss = _load_qss(settings.theme)
        self.setStyleSheet(qss)

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def closeEvent(self, event) -> None:
        settings.set("window_width", self.width())
        settings.set("window_height", self.height())
        event.accept()

    def show_status(self, message: str, timeout: int = 5000) -> None:
        self.status_bar.showMessage(message, timeout)
