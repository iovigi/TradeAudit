"""
Unit tests for TradesView and TradesTableModel PySide6 UI components.
"""

from datetime import datetime, timezone
import pytest
from PySide6.QtCore import Qt

from tradeaudit.domain.models import Trade, TradeDeal
from tradeaudit.ui.views.trades_view import TradesView, TradesTableModel


def test_trades_table_model(qtbot):
    t_open = datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
    t_close = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)

    deals = [
        TradeDeal(ticket=1, account_id=100, position_id=50, symbol="EURUSD", type="BUY", entry="IN", time=t_open, volume=1.0, price=1.0800),
        TradeDeal(ticket=2, account_id=100, position_id=50, symbol="EURUSD", type="SELL", entry="OUT", time=t_close, volume=1.0, price=1.0850, profit=500.0)
    ]

    trade = Trade(
        position_id=50,
        symbol="EURUSD",
        direction="BUY",
        volume=1.0,
        open_time=t_open,
        close_time=t_close,
        open_price=1.0800,
        close_price=1.0850,
        profit=500.0,
        status="CLOSED",
        deals=deals
    )

    model = TradesTableModel([trade])
    assert model.rowCount() == 1
    assert model.columnCount() == 17

    # Column 0: Position ID
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "50"
    # Column 1: Symbol
    assert model.data(model.index(0, 1), Qt.DisplayRole) == "EURUSD"
    # Column 2: Type
    assert model.data(model.index(0, 2), Qt.DisplayRole) == "BUY"
    # Column 12: Realized R (None -> UNKNOWN)
    assert model.data(model.index(0, 12), Qt.DisplayRole) == "UNKNOWN"
    # Column 13: Net Profit
    assert model.data(model.index(0, 13), Qt.DisplayRole) == "+500.00"
    # Column 14: Emotion
    assert model.data(model.index(0, 14), Qt.DisplayRole) == "—"
    # Column 15: Behavior Flags
    assert model.data(model.index(0, 15), Qt.DisplayRole) == "—"
    # Column 16: Status
    assert model.data(model.index(0, 16), Qt.DisplayRole) == "CLOSED"


def test_trades_view_instantiation_and_filtering(qtbot):
    view = TradesView()
    qtbot.addWidget(view)

    t_open = datetime.now(timezone.utc)
    t1 = Trade(position_id=1, symbol="EURUSD", direction="BUY", volume=1.0, open_time=t_open, open_price=1.08, status="CLOSED", profit=100.0)
    t2 = Trade(position_id=2, symbol="GBPUSD", direction="SELL", volume=0.5, open_time=t_open, open_price=1.25, status="OPEN", profit=-50.0)

    view.set_trades([t1, t2])
    assert view.model.rowCount() == 2

    # Filter symbol
    view.txt_filter_symbol.setText("GBP")
    assert view.model.rowCount() == 1
    assert view.model.get_trade(0).symbol == "GBPUSD"

    # Reset symbol filter and filter status
    view.txt_filter_symbol.setText("")
    view.cmb_filter_status.setCurrentText("CLOSED")
    assert view.model.rowCount() == 1
    assert view.model.get_trade(0).position_id == 1
