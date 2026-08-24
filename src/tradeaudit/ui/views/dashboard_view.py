"""
Dashboard View component for TradeAudit.
Combines account banner, interactive filter bar, performance KPI cards, and QtCharts visualizations.
"""

import logging
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QFrame
)

from tradeaudit.domain.models import Trade, MT5AccountInfo
from tradeaudit.domain.filters import AnalysisFilter, FilterEvaluator
from tradeaudit.app.services.performance_analyzer import PerformanceAnalyzer
from tradeaudit.ui.widgets.account_info_card import AccountInfoCard
from tradeaudit.ui.widgets.filter_bar import FilterBarWidget
from tradeaudit.ui.widgets.kpi_card import KPICardGridWidget
from tradeaudit.ui.widgets.charts_widget import DashboardChartsWidget

logger = logging.getLogger("tradeaudit.ui.views.dashboard_view")


class DashboardView(QWidget):
    """Primary Dashboard tab view for TradeAudit."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._raw_trades: List[Trade] = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scrollable container for dashboard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #161b22;
            }
            QScrollBar:vertical {
                background: #121820;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #2a3444;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0078d7;
            }
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 1. Account Info Header Banner
        self.account_card = AccountInfoCard()
        layout.addWidget(self.account_card)

        # 2. Interactive Filter Bar
        self.filter_bar = FilterBarWidget()
        self.filter_bar.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.filter_bar)

        # 3. KPI Grid
        self.kpi_grid = KPICardGridWidget()
        layout.addWidget(self.kpi_grid)

        # 4. Charts Visualizations Grid
        self.charts_widget = DashboardChartsWidget()
        layout.addWidget(self.charts_widget, stretch=1)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def set_account_info(self, account_info: Optional[MT5AccountInfo]):
        """Update account info header card."""
        self.account_card.update_account_info(account_info)

    def set_trades(self, trades: List[Trade], account_info: Optional[MT5AccountInfo] = None):
        """Populate dataset, update symbol filters, and calculate dashboard metrics."""
        self._raw_trades = trades
        if account_info:
            self.set_account_info(account_info)

        # Update symbol filter dropdown with unique symbols from trade history
        symbols = list({t.symbol for t in trades if t.symbol})
        self.filter_bar.set_available_symbols(symbols)

        # Recalculate KPIs and charts
        self._recalculate_dashboard()

    def _on_filter_changed(self, filter_obj: AnalysisFilter):
        """Handle filter change signal emitted from FilterBarWidget."""
        self._recalculate_dashboard(filter_obj)

    def _recalculate_dashboard(self, filter_obj: Optional[AnalysisFilter] = None):
        """Evaluate active filter, compute performance metrics, and refresh UI components."""
        active_filter = filter_obj or self.filter_bar.get_filter()
        filtered_trades = FilterEvaluator.apply(self._raw_trades, active_filter)

        logger.debug(
            "Recalculating dashboard metrics for %d filtered trades out of %d total.",
            len(filtered_trades),
            len(self._raw_trades)
        )

        metrics = PerformanceAnalyzer.analyze(filtered_trades)
        by_symbol = PerformanceAnalyzer.analyze_by_symbol(filtered_trades)
        by_direction = PerformanceAnalyzer.analyze_by_direction(filtered_trades)

        self.kpi_grid.update_metrics(metrics)
        self.charts_widget.update_charts(metrics, by_symbol, by_direction)
