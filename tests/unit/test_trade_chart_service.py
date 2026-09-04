"""
Unit tests for TradeChartService.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from tradeaudit.domain.models import Trade, SLHistoryRecord, TPHistoryRecord, ComplianceStatus, EmotionTag
from tradeaudit.domain.candles import TimeFrame
from tradeaudit.app.services.trade_chart_service import TradeChartService


def test_build_overlay_with_sl_tp_history():
    trade = Trade(
        position_id=555,
        account_id=123456,
        symbol="XAUUSD",
        direction="BUY",
        volume=0.5,
        open_time=datetime(2026, 2, 1, 14, 0, tzinfo=timezone.utc),
        open_price=2000.0,
        close_time=datetime(2026, 2, 1, 15, 30, tzinfo=timezone.utc),
        close_price=2020.0,
        initial_sl=1990.0,
        initial_tp=2030.0,
        profit=1000.0,
        realized_r=2.0,
        planned_rr=3.0,
        compliance_status=ComplianceStatus.COMPLIANT,
        emotion_tag=EmotionTag.CALM
    )

    mock_event_repo = MagicMock()
    mock_event_repo.get_sl_history_for_position.return_value = [
        SLHistoryRecord(
            trade_id=555,
            position_id=555,
            old_sl=1990.0,
            new_sl=2000.0,
            timestamp=datetime(2026, 2, 1, 14, 45, tzinfo=timezone.utc)
        )
    ]
    mock_event_repo.get_tp_history_for_position.return_value = [
        TPHistoryRecord(
            trade_id=555,
            position_id=555,
            old_tp=2030.0,
            new_tp=2025.0,
            timestamp=datetime(2026, 2, 1, 15, 0, tzinfo=timezone.utc)
        )
    ]

    service = TradeChartService(trade_event_repository=mock_event_repo)
    overlay = service.build_overlay(trade)

    assert overlay.ticket == 555
    assert overlay.symbol == "XAUUSD"
    assert overlay.direction == "BUY"
    assert overlay.initial_sl == 1990.0
    assert len(overlay.sl_modifications) == 1
    assert overlay.sl_modifications[0][1] == 2000.0
    assert len(overlay.tp_modifications) == 1
    assert overlay.tp_modifications[0][1] == 2025.0
    assert overlay.compliance_status == "COMPLIANT"
    assert overlay.emotion_tag == "CALM"


def test_get_candles_caching():
    trade = Trade(
        position_id=777,
        account_id=123456,
        symbol="EURUSD",
        direction="SELL",
        volume=1.0,
        open_time=datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc),
        open_price=1.0900,
        close_time=datetime(2026, 2, 1, 11, 0, tzinfo=timezone.utc),
        close_price=1.0850,
        initial_sl=1.0950,
        initial_tp=1.0800,
        profit=500.0,
        realized_r=1.0
    )

    service = TradeChartService()
    candles1 = service.get_candles_for_trade(trade, timeframe=TimeFrame.M15)
    candles2 = service.get_candles_for_trade(trade, timeframe=TimeFrame.M15)

    assert len(candles1) > 0
    # Should return cached identical list
    assert candles1 is candles2

    service.clear_cache()
    candles3 = service.get_candles_for_trade(trade, timeframe=TimeFrame.M15)
    assert candles3 is not candles1
