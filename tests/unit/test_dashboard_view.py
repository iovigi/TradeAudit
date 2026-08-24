"""
Unit tests for DashboardView and filter widget UI components using pytest-qt.
"""

from datetime import datetime, timedelta
import pytest
from PySide6.QtCore import Qt

from tradeaudit.domain.models import Trade, MT5AccountInfo
from tradeaudit.ui.widgets.filter_bar import FilterBarWidget
from tradeaudit.ui.widgets.kpi_card import KPICardGridWidget
from tradeaudit.ui.views.dashboard_view import DashboardView


@pytest.fixture
def sample_trades():
    now = datetime(2026, 8, 25, 12, 0, 0)
    return [
        Trade(
            id=1,
            symbol="EURUSD",
            direction="BUY",
            open_time=now - timedelta(days=1),
            close_time=now - timedelta(days=1),
            profit=150.0,
            status="CLOSED",
            realized_r=1.5,
            risk_percentage=1.0
        ),
        Trade(
            id=2,
            symbol="GBPUSD",
            direction="SELL",
            open_time=now - timedelta(days=2),
            close_time=now - timedelta(days=2),
            profit=-100.0,
            status="CLOSED",
            realized_r=-1.0,
            risk_percentage=1.0
        )
    ]


def test_filter_bar_widget_instantiation(qtbot):
    widget = FilterBarWidget()
    qtbot.addWidget(widget)
    assert widget is not None

    widget.set_available_symbols(["EURUSD", "GBPUSD", "XAUUSD"])
    filter_obj = widget.get_filter()
    assert filter_obj is not None


def test_kpi_card_grid_instantiation(qtbot):
    grid = KPICardGridWidget()
    qtbot.addWidget(grid)
    assert grid.card_trades is not None
    assert grid.card_winrate is not None
    assert grid.card_net_profit is not None


def test_dashboard_view_set_trades(qtbot, sample_trades):
    view = DashboardView()
    qtbot.addWidget(view)

    account = MT5AccountInfo(login=123456, name="Demo Trader", balance=10000.0)
    view.set_trades(sample_trades, account_info=account)

    assert view._raw_trades == sample_trades
    assert view.kpi_grid.card_trades.lbl_value.text() == "2"
    assert view.kpi_grid.card_winrate.lbl_value.text() == "50.0%"
