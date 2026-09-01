"""
Unit tests for QuantResearchView PySide6 GUI component (Phase 13).
"""

from datetime import datetime, timezone
import pytest

from PySide6.QtCore import Qt
from tradeaudit.domain.models import Trade
from tradeaudit.ui.views.quant_research_view import QuantResearchView


def _make_sample_trade(ticket: int, profit: float, realized_r: float) -> Trade:
    return Trade(
        id=ticket,
        position_id=ticket,
        account_id=12345,
        symbol="EURUSD",
        direction="BUY",
        volume=0.1,
        open_time=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
        close_time=datetime(2026, 8, 1, 11, 0, tzinfo=timezone.utc),
        open_price=1.1000,
        close_price=1.1050,
        initial_sl=1.0950,
        initial_tp=1.1100,
        profit=profit,
        commission=0.0,
        swap=0.0,
        fee=0.0,
        status="CLOSED",
        price_risk=0.0050,
        monetary_risk=50.0,
        planned_rr=2.0,
        realized_r=realized_r
    )


def test_quant_research_view_instantiation(qtbot):
    view = QuantResearchView()
    qtbot.addWidget(view)
    assert view is not None
    assert view.combo_sims.currentText() == "1000"
    assert view.spin_horizon.value() == 50
    assert view.table_details.columnCount() == 4


def test_quant_research_view_set_trades_and_render(qtbot):
    view = QuantResearchView()
    qtbot.addWidget(view)

    trades = [
        _make_sample_trade(ticket=100 + i, profit=100.0 if i % 2 == 0 else -50.0, realized_r=2.0 if i % 2 == 0 else -1.0)
        for i in range(1, 21)
    ]

    view.set_trades(trades)

    # Check that Monte Carlo chart has series attached
    assert len(view.chart_mc.series()) == 5
    assert view.table_details.rowCount() > 0

    # Trigger window change
    view.combo_window.setCurrentText("50")

    # Trigger simulation click
    qtbot.mouseClick(view.btn_run, Qt.LeftButton)
    assert view._current_result is not None


def test_quant_research_view_empty_trades(qtbot):
    view = QuantResearchView()
    qtbot.addWidget(view)

    view.set_trades([])
    assert view.table_details.rowCount() == 0
    assert len(view.chart_mc.series()) == 0
