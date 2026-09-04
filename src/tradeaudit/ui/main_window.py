"""
Main window PySide6 GUI component for TradeAudit.
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QPalette, QColor, QIcon, QDesktopServices
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

from tradeaudit.app.config import Settings, get_resource_path
from tradeaudit.domain.models import MT5Settings
from tradeaudit.infrastructure.database.connection import DatabaseManager
from tradeaudit.infrastructure.security.credential_store import CredentialStore
from tradeaudit.infrastructure.repositories.settings_repository import SettingsRepository
from tradeaudit.infrastructure.repositories.trade_repository import TradeRepository
from tradeaudit.infrastructure.repositories.strategy_repository import StrategyRepository
from tradeaudit.infrastructure.repositories.trade_event_repository import TradeEventRepository
from tradeaudit.app.services.sync_service import SyncService
from tradeaudit.app.services.strategy_service import StrategyService
from tradeaudit.app.services.live_position_watcher import LivePositionWatcherService
from tradeaudit.app.services.backup_service import BackupService
from tradeaudit.app.services.trade_chart_service import TradeChartService
from tradeaudit.infrastructure.mt5.candle_reader import MT5CandleReader
from tradeaudit.infrastructure.mt5.connection_service import MT5ConnectionService, ConnectionState
from tradeaudit.ui.widgets.connection_status_badge import ConnectionStatusBadge
from tradeaudit.ui.views.settings_view import SettingsView
from tradeaudit.ui.views.trades_view import TradesView
from tradeaudit.ui.views.dashboard_view import DashboardView
from tradeaudit.ui.views.strategy_view import StrategyView
from tradeaudit.ui.views.strategy_vs_trader_view import StrategyVsTraderView
from tradeaudit.ui.views.breakdown_view import BreakdownView
from tradeaudit.ui.views.live_journal_view import LiveJournalView
from tradeaudit.ui.views.report_view import ReportView
from tradeaudit.ui.views.quant_research_view import QuantResearchView
from tradeaudit.ui.views.trade_chart_view import TradeChartView
from tradeaudit.ui.dialogs.trade_chart_dialog import TradeChartDialog
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
        settings_repo: Optional[SettingsRepository] = None,
        trade_repo: Optional[TradeRepository] = None,
        strategy_repo: Optional[StrategyRepository] = None,
        trade_event_repo: Optional[TradeEventRepository] = None,
        strategy_service: Optional[StrategyService] = None,
        sync_service: Optional[SyncService] = None,
        live_watcher_service: Optional[LivePositionWatcherService] = None
    ):
        super().__init__()
        self.settings = settings
        self.db_manager = db_manager

        # Initialize Infrastructure Services
        self.mt5_service = mt5_service or MT5ConnectionService()
        self.credential_store = credential_store or CredentialStore()
        self.settings_repo = settings_repo or SettingsRepository(self.db_manager)
        self.trade_repo = trade_repo or TradeRepository(self.db_manager)
        self.strategy_repo = strategy_repo or StrategyRepository(self.db_manager)
        self.trade_event_repo = trade_event_repo or TradeEventRepository(self.db_manager)
        self.strategy_service = strategy_service or StrategyService(self.strategy_repo, self.trade_repo)
        self.sync_service = sync_service or SyncService(trade_repo=self.trade_repo)
        self.live_watcher_service = live_watcher_service or LivePositionWatcherService(
            event_repository=self.trade_event_repo,
            sync_service=self.sync_service
        )
        self.backup_service = BackupService(settings=self.settings, db_manager=self.db_manager)
        self.candle_reader = MT5CandleReader(connection_service=self.mt5_service)
        self.trade_chart_service = TradeChartService(
            candle_reader=self.candle_reader,
            trade_event_repository=self.trade_event_repo
        )

        self.setWindowTitle(f"{self.settings.app_name} v{self.settings.app_version}")
        self.resize(1100, 750)
        self.setMinimumSize(950, 600)

        # Set Window Icon
        icon_path = get_resource_path("resources/icons/tradeaudit.ico")
        if not icon_path.exists():
            icon_path = get_resource_path("resources/icons/tradeaudit.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._apply_dark_theme()
        self._init_ui()
        self._init_status_bar()
        self._load_saved_configuration()
        self._refresh_trades()

        logger.info("MainWindow initialized with MT5, Settings, Trade Sync, Strategy & Live Journal services.")



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
        self.dashboard_view = DashboardView()

        # Tab 2: Trades View
        self.trades_view = TradesView()
        self.trades_view.sync_requested.connect(self._on_sync_requested)
        self.trades_view.chart_requested.connect(self._open_trade_chart)

        # Tab 3: Strategy Management View
        self.strategy_view = StrategyView(strategy_service=self.strategy_service)
        self.strategy_view.strategy_changed.connect(self._on_strategy_changed)

        # Tab 4: Strategy vs Trader View
        self.strategy_vs_trader_view = StrategyVsTraderView()

        # Tab 5: Breakdown Analytics View
        self.breakdown_view = BreakdownView()

        # Tab 6: Live Trade Journal
        self.live_journal_view = LiveJournalView()
        self.live_journal_view.poll_requested.connect(self._poll_live_positions)

        # Tab 7: AI-Ready & Markdown Reports View
        self.report_view = ReportView()

        # Tab 8: Quantitative Risk & Statistical Research View
        self.quant_view = QuantResearchView()

        # Tab 9: Interactive Candlestick Trade Chart & Replay View
        self.trade_chart_view = TradeChartView(chart_service=self.trade_chart_service)

        # Tab 10: Settings View
        self.settings_view = SettingsView()
        self.settings_view.settings_saved.connect(self._on_settings_saved)
        self.settings_view.connect_requested.connect(self._on_connect_requested)
        self.settings_view.disconnect_requested.connect(self._on_disconnect_requested)
        self.settings_view.backup_requested.connect(self._on_backup_requested)
        self.settings_view.open_data_folder_requested.connect(self._on_open_data_folder_requested)

        self.tab_widget.addTab(self.dashboard_view, "📈 Dashboard")
        self.tab_widget.addTab(self.trades_view, "📊 Trades")
        self.tab_widget.addTab(self.strategy_view, "🎯 Strategies")
        self.tab_widget.addTab(self.strategy_vs_trader_view, "⚖️ Strategy vs Trader")
        self.tab_widget.addTab(self.breakdown_view, "🔍 Breakdowns")
        self.tab_widget.addTab(self.live_journal_view, "📝 Live Journal")
        self.tab_widget.addTab(self.report_view, "📄 AI Reports")
        self.tab_widget.addTab(self.quant_view, "🔬 Quant & Risk")
        self.tab_widget.addTab(self.trade_chart_view, "🕯️ Trade Chart")
        self.tab_widget.addTab(self.settings_view, "⚙️ MT5 Settings")


        layout.addWidget(header_card)
        layout.addWidget(self.tab_widget, stretch=1)

    def _poll_live_positions(self) -> None:
        """Poll active MT5 positions and update LiveJournalView."""
        saved_settings = self.settings_repo.load_mt5_settings()
        account_id = saved_settings.login if saved_settings else 0
        if not account_id:
            self.live_journal_view.set_status("Configure MT5 settings first")
            return

        if self.mt5_service.is_connected():
            positions = self.live_watcher_service.poll_positions(account_id)
            events = self.trade_event_repo.get_all_events(limit=100)
            self.live_journal_view.update_positions(positions)
            self.live_journal_view.update_events(events)
            self.live_journal_view.set_status(f"Active ({len(positions)} open position(s))")
        else:
            self.live_journal_view.set_status("MT5 Disconnected")

    def _on_strategy_changed(self) -> None:
        """Handle strategy creation/update/deletion events."""
        saved_settings = self.settings_repo.load_mt5_settings()
        if saved_settings and saved_settings.login:
            self.strategy_service.reevaluate_account_compliance(saved_settings.login)
            self._refresh_trades()




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
        self.settings_view.set_storage_info(str(self.settings.data_dir), self.settings.database_url)

    def _on_backup_requested(self) -> None:
        """Create an on-demand database backup."""
        try:
            backup_path = self.backup_service.create_backup(tag="manual")
            self.settings_view.show_feedback(f"✅ Backup created successfully:\n{backup_path.name}")
            self.status_bar.showMessage(f"✅ Database backup saved: {backup_path.name}", 6000)
        except Exception as e:
            logger.error("Failed to create database backup: %s", e)
            self.settings_view.show_feedback(f"❌ Backup failed: {e}", is_error=True)
            self.status_bar.showMessage("❌ Database backup failed.", 6000)

    def _on_open_data_folder_requested(self) -> None:
        """Open the application data folder in the system file explorer."""
        folder = self.settings.data_dir
        folder.mkdir(parents=True, exist_ok=True)
        url = QUrl.fromLocalFile(str(folder))
        QDesktopServices.openUrl(url)
        self.status_bar.showMessage(f"Opened data folder: {folder}", 4000)

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
            self.dashboard_view.set_account_info(account_info)
            self.settings_view.show_feedback(
                f"✅ Connected to MT5! Account: {account_info.login} ({account_info.name}) | Balance: {account_info.balance:.2f} {account_info.currency}"
            )
            self._refresh_trades()
            self.status_bar.showMessage(f"🟢 Connected to MT5 Account {account_info.login}.", 5000)

        except MT5Error as e:
            self.status_badge.set_status(ConnectionState.ERROR)
            self.dashboard_view.set_account_info(None)
            self.settings_view.show_feedback(f"❌ Connection failed: {e.message}", is_error=True)
            self.status_bar.showMessage(f"🔴 MT5 Connection Error: {e.message}", 6000)
        except Exception as e:
            self.status_badge.set_status(ConnectionState.ERROR)
            self.dashboard_view.set_account_info(None)
            self.settings_view.show_feedback(f"❌ Unexpected error: {e}", is_error=True)
            self.status_bar.showMessage("🔴 Unexpected MT5 connection error.", 6000)

    def _on_disconnect_requested(self) -> None:
        """Handle disconnect request from SettingsView."""
        self.mt5_service.disconnect()
        self.status_badge.set_status(ConnectionState.DISCONNECTED)
        self.dashboard_view.set_account_info(None)
        self.settings_view.show_feedback("🔌 Disconnected from MT5 terminal.")
        self.status_bar.showMessage("MT5 disconnected.", 4000)

    def _refresh_trades(self) -> None:
        """Fetch stored trades from DB and update TradesView, DashboardView, StrategyVsTraderView, BreakdownView, and ReportView."""
        saved_settings = self.settings_repo.load_mt5_settings()
        if saved_settings and saved_settings.login:
            trades = self.trade_repo.get_trades(saved_settings.login)
            last_sync = self.trade_repo.get_last_sync_time(saved_settings.login)
            strategies = self.strategy_repo.get_all_strategies()
            account_info = None
            if self.mt5_service.is_connected():
                try:
                    account_info = self.mt5_service.get_account_info()
                except Exception:
                    pass

            self.trades_view.set_trades(trades, last_sync=last_sync)
            self.dashboard_view.set_trades(trades)
            self.strategy_vs_trader_view.set_trades(trades)
            self.breakdown_view.set_trades(trades)
            self.report_view.set_strategies(strategies)
            self.report_view.set_trades(trades, account_info=account_info)
            self.quant_view.set_trades(trades)
            self.trade_chart_view.set_trades(trades)

    def _open_trade_chart(self, trade) -> None:
        """Open TradeChartDialog popup and update the TradeChart tab."""
        saved_settings = self.settings_repo.load_mt5_settings()
        all_trades = self.trade_repo.get_trades(saved_settings.login) if saved_settings and saved_settings.login else [trade]
        
        idx = 0
        for i, t in enumerate(all_trades):
            if t.position_id == trade.position_id:
                idx = i
                break

        self.trade_chart_view.show_trade_by_position_id(trade.position_id)
        
        # Open modal inspection dialog
        dialog = TradeChartDialog(
            trades=all_trades,
            initial_trade_index=idx,
            chart_service=self.trade_chart_service,
            parent=self
        )
        dialog.exec()


    def _on_sync_requested(self) -> None:
        """Handle sync history action from TradesView toolbar."""
        saved_settings = self.settings_repo.load_mt5_settings()
        if not saved_settings or not saved_settings.login:
            self.status_bar.showMessage("⚠️ Please configure MT5 account settings first.", 5000)
            return

        account_info = None
        if self.mt5_service.is_connected():
            try:
                account_info = self.mt5_service.get_account_info()
            except Exception:
                pass

        self.status_bar.showMessage(f"Syncing MT5 history for account {saved_settings.login}...", 0)
        res = self.sync_service.sync_account_history(account_id=saved_settings.login, account_info=account_info)

        self._refresh_trades()

        if res.success:
            self.status_bar.showMessage(f"✅ {res.message}", 6000)
        else:
            self.status_bar.showMessage(f"❌ Sync failed: {res.message}", 7000)

