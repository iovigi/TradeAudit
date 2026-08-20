"""
Main window PySide6 GUI component for TradeAudit.
"""

import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QFrame
)

from tradeaudit.app.config import Settings
from tradeaudit.infrastructure.database.connection import DatabaseManager

logger = logging.getLogger("tradeaudit.ui.main_window")


class MainWindow(QMainWindow):
    """Primary application window for TradeAudit."""

    def __init__(self, settings: Settings, db_manager: DatabaseManager):
        super().__init__()
        self.settings = settings
        self.db_manager = db_manager

        self.setWindowTitle(f"{self.settings.app_name} v{self.settings.app_version}")
        self.resize(1100, 700)
        self.setMinimumSize(900, 550)

        self._apply_dark_theme()
        self._init_ui()
        self._init_status_bar()

        logger.info("MainWindow initialized successfully.")

    def _apply_dark_theme(self) -> None:
        """Apply a sleek, modern dark color palette."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(18, 22, 28))
        palette.setColor(QPalette.WindowText, QColor(230, 235, 240))
        palette.setColor(QPalette.Base, QColor(25, 30, 38))
        palette.setColor(QPalette.AlternateBase, QColor(32, 38, 48))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(230, 235, 240))
        palette.setColor(QPalette.Button, QColor(32, 40, 52))
        palette.setColor(QPalette.ButtonText, QColor(230, 235, 240))
        palette.setColor(QPalette.BrightText, QColor(255, 68, 68))
        palette.setColor(QPalette.Link, QColor(0, 162, 232))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

    def _init_ui(self) -> None:
        """Construct central widget layout."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        header_layout = QVBoxLayout(header_card)

        title_label = QLabel(f"⚡ {self.settings.app_name}")
        title_font = QFont("Segoe UI", 20, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")

        subtitle_label = QLabel("MetaTrader 5 Performance Audit, Risk & Execution Intelligence Engine")
        sub_font = QFont("Segoe UI", 10)
        subtitle_label.setFont(sub_font)
        subtitle_label.setStyleSheet("color: #8b9bb4;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        # Body Container
        body_card = QFrame()
        body_card.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px dashed #2d3748;
                border-radius: 8px;
                padding: 32px;
            }
        """)
        body_layout = QVBoxLayout(body_card)
        body_layout.setAlignment(Qt.AlignCenter)

        welcome_title = QLabel("Phase 0 — Foundation Ready")
        welcome_title.setFont(QFont("Segoe UI", 14, QFont.DemiBold))
        welcome_title.setStyleSheet("color: #00e676;")

        welcome_desc = QLabel(
            "Project foundation, logging, configuration, SQLite database, "
            "and PySide6 GUI shell initialized successfully."
        )
        welcome_desc.setFont(QFont("Segoe UI", 10))
        welcome_desc.setStyleSheet("color: #a0aec0;")
        welcome_desc.setWordWrap(True)
        welcome_desc.setAlignment(Qt.AlignCenter)

        body_layout.addWidget(welcome_title, alignment=Qt.AlignCenter)
        body_layout.addSpacing(8)
        body_layout.addWidget(welcome_desc, alignment=Qt.AlignCenter)

        layout.addWidget(header_card)
        layout.addWidget(body_card, stretch=1)

    def _init_status_bar(self) -> None:
        """Configure system status bar."""
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        # DB Connection Status Indicator
        db_healthy = self.db_manager.check_connection()
        db_status_text = "🟢 DB Connected" if db_healthy else "🔴 DB Connection Error"
        
        self.db_label = QLabel(db_status_text)
        self.db_label.setStyleSheet("padding: 0 8px; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.db_label)

        # Version Indicator
        self.version_label = QLabel(f"Version: {self.settings.app_version}")
        self.version_label.setStyleSheet("padding: 0 8px; color: #718096;")
        self.status_bar.addPermanentWidget(self.version_label)

        self.status_bar.showMessage("TradeAudit Phase 0 ready.", 5000)
