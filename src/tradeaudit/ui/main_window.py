"""
Main window PySide6 GUI component for TradeAudit.
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QFrame,
    QTabWidget
)

from tradeaudit.app.config import Settings
from tradeaudit.domain.models import MT5Settings
from tradeaudit.infrastructure.database.connection import DatabaseManager
from tradeaudit.infrastructure.security.credential_store import CredentialStore
from tradeaudit.infrastructure.repositories.settings_repository import SettingsRepository
from tradeaudit.infrastructure.mt5.connection_service import MT5ConnectionService, ConnectionState
from tradeaudit.ui.widgets.connection_status_badge import ConnectionStatusBadge
from tradeaudit.ui.widgets.account_info_card import AccountInfoCard
from tradeaudit.ui.views.settings_view import SettingsView
from tradeaudit.app.exceptions import MT5Error, CredentialStoreError

logger = logging.getLogger("tradeaudit.ui.main_window")


class MainWindow(QMainWindow):
    """Primary application window for TradeAudit."""

    def __init__(
        self,
        settings: Settings,
        db_manager: DatabaseManager,
        mt5_service: Optional[MT5ConnectionService] = None,
        credential_store: Optional[CredentialStore] = None,
        settings_repo: Optional[SettingsRepository] = None
    ):
        super().__init__()
        self.settings = settings
        self.db_manager = db_manager

        # Initialize Infrastructure Services
        self.mt5_service = mt5_service or MT5ConnectionService()
        self.credential_store = credential_store or CredentialStore()
        self.settings_repo = settings_repo or SettingsRepository(self.db_manager)

        self.setWindowTitle(f"{self.settings.app_name} v{self.settings.app_version}")
        self.resize(1100, 750)
        self.setMinimumSize(950, 600)

        self._apply_dark_theme()
        self._init_ui()
        self._init_status_bar()
        self._load_saved_configuration()

        logger.info("MainWindow initialized with MT5 & Settings services.")

    def _apply_dark_theme(self) -> None:
        """Apply modern dark color palette."""
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
        """Construct central widget layout with header and tab container."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                padding: 14px 20px;
            }
        """)
        header_layout = QHBoxLayout(header_card)

        title_vbox = QVBoxLayout()
        title_label = QLabel(f"⚡ {self.settings.app_name}")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff;")

        subtitle_label = QLabel("MetaTrader 5 Performance Audit, Risk & Execution Intelligence Engine")
        subtitle_label.setFont(QFont("Segoe UI", 9))
        subtitle_label.setStyleSheet("color: #8b9bb4;")

        title_vbox.addWidget(title_label)
        title_vbox.addWidget(subtitle_label)

        self.status_badge = ConnectionStatusBadge()

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        header_layout.addWidget(self.status_badge)

        # Main Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2a3444;
                background-color: #161b22;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #121820;
                color: #8b9bb4;
                padding: 10px 20px;
                font-weight: bold;
                border: 1px solid #232d3d;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1a222d;
                color: #00a2e8;
                border-top: 2px solid #00a2e8;
            }
            QTabBar::tab:hover:!selected {
                background-color: #1a222d;
                color: #e2e8f0;
            }
        """)

        # Tab 1: Dashboard View
        self.dashboard_tab = QWidget()
        dash_layout = QVBoxLayout(self.dashboard_tab)
        dash_layout.setContentsMargins(16, 16, 16, 16)
        dash_layout.setSpacing(16)

        self.account_card = AccountInfoCard()
        dash_layout.addWidget(self.account_card)
        dash_layout.addStretch()

        # Tab 2: Settings View
        self.settings_view = SettingsView()
        self.settings_view.settings_saved.connect(self._on_settings_saved)
        self.settings_view.connect_requested.connect(self._on_connect_requested)
        self.settings_view.disconnect_requested.connect(self._on_disconnect_requested)

        self.tab_widget.addTab(self.dashboard_tab, "📈 Dashboard")
        self.tab_widget.addTab(self.settings_view, "⚙️ MT5 Settings")

        layout.addWidget(header_card)
        layout.addWidget(self.tab_widget, stretch=1)

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

        self.status_bar.showMessage("TradeAudit Phase 1 Ready.", 5000)

    def _load_saved_configuration(self) -> None:
        """Load persisted settings and password on app launch."""
        saved_settings = self.settings_repo.load_mt5_settings()
        password = ""
        if saved_settings and saved_settings.login:
            try:
                password = self.credential_store.get_password(saved_settings.login) or ""
            except CredentialStoreError as e:
                logger.warning("Could not retrieve password for account %s: %s", saved_settings.login, e)

        self.settings_view.populate_settings(saved_settings, password)

    def _on_settings_saved(self, settings: MT5Settings) -> None:
        """Handle save settings request from SettingsView."""
        try:
            self.settings_repo.save_mt5_settings(settings)
            password = self.settings_view.get_password()
            if settings.login and password:
                self.credential_store.save_password(settings.login, password)

            self.settings_view.show_feedback("✅ Settings and credentials saved successfully.")
            self.status_bar.showMessage("MT5 settings saved.", 4000)
        except Exception as e:
            logger.error("Failed to save settings: %s", e)
            self.settings_view.show_feedback(f"❌ Failed to save settings: {e}", is_error=True)

    def _on_connect_requested(self, settings: MT5Settings, password: str) -> None:
        """Handle connect request from SettingsView."""
        self.settings_view.clear_feedback()
        self.status_badge.set_status(ConnectionState.CONNECTING)
        self.status_bar.showMessage(f"Connecting to MT5 server {settings.server}...", 0)

        # First save current settings
        self._on_settings_saved(settings)

        if not password and settings.login:
            try:
                password = self.credential_store.get_password(settings.login) or ""
            except CredentialStoreError:
                pass

        try:
            account_info = self.mt5_service.connect(
                mt5_path=settings.mt5_path,
                login=settings.login,
                password=password,
                server=settings.server,
                timeout_ms=settings.timeout_ms
            )
            self.status_badge.set_status(ConnectionState.CONNECTED, server=settings.server, login=settings.login)
            self.account_card.update_account_info(account_info)
            self.settings_view.show_feedback(
                f"✅ Connected to MT5! Account: {account_info.login} ({account_info.name}) | Balance: {account_info.balance:.2f} {account_info.currency}"
            )
            self.status_bar.showMessage(f"🟢 Connected to MT5 Account {account_info.login}.", 5000)
        except MT5Error as e:
            self.status_badge.set_status(ConnectionState.ERROR)
            self.account_card.update_account_info(None)
            self.settings_view.show_feedback(f"❌ Connection failed: {e.message}", is_error=True)
            self.status_bar.showMessage(f"🔴 MT5 Connection Error: {e.message}", 6000)
        except Exception as e:
            self.status_badge.set_status(ConnectionState.ERROR)
            self.account_card.update_account_info(None)
            self.settings_view.show_feedback(f"❌ Unexpected error: {e}", is_error=True)
            self.status_bar.showMessage("🔴 Unexpected MT5 connection error.", 6000)

    def _on_disconnect_requested(self) -> None:
        """Handle disconnect request from SettingsView."""
        self.mt5_service.disconnect()
        self.status_badge.set_status(ConnectionState.DISCONNECTED)
        self.account_card.update_account_info(None)
        self.settings_view.show_feedback("🔌 Disconnected from MT5 terminal.")
        self.status_bar.showMessage("MT5 disconnected.", 4000)
