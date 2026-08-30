"""UI Views package."""
from tradeaudit.ui.views.settings_view import SettingsView
from tradeaudit.ui.views.trades_view import TradesView
from tradeaudit.ui.views.dashboard_view import DashboardView
from tradeaudit.ui.views.strategy_view import StrategyView, StrategyFormDialog
from tradeaudit.ui.views.strategy_vs_trader_view import StrategyVsTraderView
from tradeaudit.ui.views.breakdown_view import BreakdownView
from tradeaudit.ui.views.live_journal_view import LiveJournalView
from tradeaudit.ui.views.report_view import ReportView

__all__ = [
    "SettingsView",
    "TradesView",
    "DashboardView",
    "StrategyView",
    "StrategyFormDialog",
    "StrategyVsTraderView",
    "BreakdownView",
    "LiveJournalView",
    "ReportView",
]






