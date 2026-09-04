"""
Unit tests for domain Candle and TradeExecutionOverlay models.
"""

from datetime import datetime, timezone
import pytest

from tradeaudit.domain.candles import Candle, TimeFrame, TradeExecutionOverlay


def test_timeframe_properties():
    assert TimeFrame.M1.minutes == 1
    assert TimeFrame.M5.minutes == 5
    assert TimeFrame.M15.minutes == 15
    assert TimeFrame.M30.minutes == 30
    assert TimeFrame.H1.minutes == 60
    assert TimeFrame.H4.minutes == 240
    assert TimeFrame.D1.minutes == 1440
    assert TimeFrame.W1.minutes == 10080


def test_candle_bullish_bearish():
    bull_candle = Candle(
        timestamp=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        open=1.0800,
        high=1.0850,
        low=1.0790,
        close=1.0840,
        volume=250
    )
    assert bull_candle.is_bullish is True
    assert pytest.approx(bull_candle.body_size) == 0.0040
    assert pytest.approx(bull_candle.total_range) == 0.0060

    bear_candle = Candle(
        timestamp=datetime(2026, 1, 1, 10, 15, tzinfo=timezone.utc),
        open=1.0840,
        high=1.0860,
        low=1.0770,
        close=1.0780,
        volume=320
    )
    assert bear_candle.is_bullish is False
    assert pytest.approx(bear_candle.body_size) == 0.0060
    assert pytest.approx(bear_candle.total_range) == 0.0090


def test_trade_execution_overlay_defaults():
    overlay = TradeExecutionOverlay(
        ticket=1001,
        symbol="EURUSD",
        direction="BUY",
        entry_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        entry_price=1.0800,
        volume=1.0,
        initial_sl=1.0750,
        initial_tp=1.0900,
        exit_time=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        exit_price=1.0900,
        net_profit=1000.0,
        realized_r=2.0,
        planned_rr=2.0
    )
    assert overlay.ticket == 1001
    assert overlay.direction == "BUY"
    assert len(overlay.sl_modifications) == 0
    assert len(overlay.tp_modifications) == 0
