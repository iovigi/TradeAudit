"""
Unit tests for TradeChartView, TradeChartDialog, and CandlestickChartWidget Qt components.
"""

from datetime import datetime, timezone
import pytest
from PySide6.QtCore import Qt

from tradeaudit.domain.models import Trade, ComplianceStatus, EmotionTag
from tradeaudit.domain.candles import Candle, TimeFrame, TradeExecutionOverlay
from tradeaudit.app.services.trade_chart_service import TradeChartService
from tradeaudit.ui.widgets.candlestick_chart_widget import CandlestickChartWidget
from tradeaudit.ui.dialogs.trade_chart_dialog import TradeChartDialog
from tradeaudit.ui.views.trade_chart_view import TradeChartView


@pytest.fixture
def sample_trades():
    t1 = Trade(
        position_id=101,
        account_id=123456,
        symbol="EURUSD",
        direction="BUY",
        volume=1.0,
        open_time=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        open_price=1.0850,
        close_time=datetime(2026, 3, 1, 11, 30, tzinfo=timezone.utc),
        close_price=1.0900,
        initial_sl=1.0820,
        initial_tp=1.0920,
        profit=500.0,
        realized_r=1.67,
        planned_rr=2.33,
        compliance_status=ComplianceStatus.COMPLIANT,
        emotion_tag=EmotionTag.CALM
    )
    t2 = Trade(
        position_id=102,
        account_id=123456,
        symbol="GBPUSD",
        direction="SELL",
        volume=0.5,
        open_time=datetime(2026, 3, 2, 14, 0, tzinfo=timezone.utc),
        open_price=1.2700,
        close_time=datetime(2026, 3, 2, 15, 0, tzinfo=timezone.utc),
        close_price=1.2730,
        initial_sl=1.2740,
        initial_tp=1.2620,
        profit=-150.0,
        realized_r=-0.75,
        planned_rr=2.0,
        compliance_status=ComplianceStatus.DEVIATION,
        emotion_tag=EmotionTag.FOMO
    )
    return [t1, t2]


def test_candlestick_chart_widget_render(qtbot):
    widget = CandlestickChartWidget()
    qtbot.addWidget(widget)

    candles = [
        Candle(datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc), 1.0800, 1.0850, 1.0790, 1.0840, 100),
        Candle(datetime(2026, 1, 1, 10, 15, tzinfo=timezone.utc), 1.0840, 1.0860, 1.0810, 1.0820, 120),
    ]
    overlay = TradeExecutionOverlay(
        ticket=101,
        symbol="EURUSD",
        direction="BUY",
        entry_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        entry_price=1.0800,
        volume=1.0,
        initial_sl=1.0750,
        initial_tp=1.0900
    )

    widget.set_data(candles, overlay)
    assert len(widget._visible_candles) == 2

    # Test replay index
    widget.set_replay_index(1)
    assert len(widget._visible_candles) == 1

    widget.set_replay_index(None)
    assert len(widget._visible_candles) == 2


def test_trade_chart_dialog(qtbot, sample_trades):
    dialog = TradeChartDialog(trades=sample_trades, initial_trade_index=0)
    qtbot.addWidget(dialog)

    assert dialog.current_trade_index == 0
    assert "EURUSD" in dialog.trade_title_label.text()
    assert dialog.nav_next_btn.isEnabled() is True
    assert dialog.nav_prev_btn.isEnabled() is False

    # Next trade
    dialog._on_next_trade()
    assert dialog.current_trade_index == 1
    assert "GBPUSD" in dialog.trade_title_label.text()
    assert dialog.nav_next_btn.isEnabled() is False
    assert dialog.nav_prev_btn.isEnabled() is True

    # Timeframe selection
    dialog._on_timeframe_changed(TimeFrame.H1)
    assert dialog.current_timeframe == TimeFrame.H1


def test_trade_chart_view_tab(qtbot, sample_trades):
    view = TradeChartView()
    qtbot.addWidget(view)

    view.set_trades(sample_trades)
    assert view.trade_selector_combo.count() == 2
    assert "101" in view.title_label.text()

    # Show by ticket
    view.show_trade_by_ticket(102)
    assert view._current_trade_index == 1
    assert "102" in view.title_label.text()

    # Replay controls
    view._toggle_replay()
    assert view.btn_play.text() == "⏸ Pause"
    view._toggle_replay()
    assert view.btn_play.text() == "▶ Play"
