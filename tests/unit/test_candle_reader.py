"""
Unit tests for MT5CandleReader infrastructure service.
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest

from tradeaudit.domain.candles import TimeFrame
from tradeaudit.infrastructure.mt5.candle_reader import MT5CandleReader


def test_candle_reader_synthetic_generation():
    reader = MT5CandleReader()
    start_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc)

    candles = reader.generate_synthetic_candles(
        symbol="EURUSD",
        timeframe=TimeFrame.M15,
        date_from=start_time,
        date_to=end_time,
        anchor_price=1.1000,
        target_price=1.1050
    )

    assert len(candles) > 0
    # For a 4-hour range at M15, we expect around 17 candles
    assert len(candles) == 17
    assert candles[0].timestamp == start_time
    assert all(c.high >= c.low for c in candles)
    assert all(c.high >= c.open and c.high >= c.close for c in candles)
    assert all(c.low <= c.open and c.low <= c.close for c in candles)


def test_fetch_rates_around_trade():
    reader = MT5CandleReader()
    entry_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    exit_time = datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)

    candles = reader.fetch_rates_around_trade(
        symbol="GBPUSD",
        timeframe=TimeFrame.M5,
        entry_time=entry_time,
        exit_time=exit_time,
        entry_price=1.2500,
        exit_price=1.2550,
        bars_before=10,
        bars_after=10
    )

    assert len(candles) > 20
    assert candles[0].timestamp < entry_time
    assert candles[-1].timestamp > exit_time


def test_is_connected_with_mock_service():
    mock_conn = MagicMock()
    mock_conn.is_connected = True
    reader = MT5CandleReader(connection_service=mock_conn)
    assert reader.is_connected() is True

    mock_conn.is_connected = False
    assert reader.is_connected() is False
