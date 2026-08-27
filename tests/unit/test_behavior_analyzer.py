"""
Unit tests for BehaviorAnalyzer service.
"""

from datetime import datetime, timezone, timedelta
import pytest

from tradeaudit.domain.models import (
    Trade,
    TradeDeal,
    Strategy,
    BehaviorFlagType,
    ConfidenceLevel,
    UserBehaviorAction
)
from tradeaudit.app.services.behavior_analyzer import BehaviorAnalyzer


@pytest.fixture
def analyzer():
    return BehaviorAnalyzer()


def test_revenge_trading_detection(analyzer):
    base_time = datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc)

    losing_trade = Trade(
        id=1,
        symbol="EURUSD",
        direction="BUY",
        volume=1.0,
        open_time=base_time,
        close_time=base_time + timedelta(minutes=15),
        profit=-100.0,
        status="CLOSED",
        monetary_risk=100.0
    )

    # Opened 10 min after losing trade close, with volume 2.0 (increased risk)
    revenge_trade = Trade(
        id=2,
        symbol="EURUSD",
        direction="BUY",
        volume=2.0,
        open_time=base_time + timedelta(minutes=25),
        profit=0.0,
        status="OPEN",
        monetary_risk=200.0
    )

    flags = analyzer.analyze_trade(revenge_trade, [losing_trade])

    assert len(flags) > 0
    revenge_flag = next((f for f in flags if f.flag_type == BehaviorFlagType.POSSIBLE_REVENGE_TRADE), None)
    assert revenge_flag is not None
    assert revenge_flag.confidence == ConfidenceLevel.HIGH
    assert "increased risk/volume" in revenge_flag.reason


def test_revenge_trading_not_flagged_after_win(analyzer):
    base_time = datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc)

    winning_trade = Trade(
        id=1,
        symbol="EURUSD",
        direction="BUY",
        volume=1.0,
        open_time=base_time,
        close_time=base_time + timedelta(minutes=15),
        profit=150.0,
        status="CLOSED"
    )

    next_trade = Trade(
        id=2,
        symbol="EURUSD",
        direction="BUY",
        volume=1.0,
        open_time=base_time + timedelta(minutes=20),
        status="OPEN"
    )

    flags = analyzer.analyze_trade(next_trade, [winning_trade])
    revenge_flag = next((f for f in flags if f.flag_type == BehaviorFlagType.POSSIBLE_REVENGE_TRADE), None)
    assert revenge_flag is None


def test_overtrading_detection(analyzer):
    base_time = datetime(2026, 8, 27, 8, 0, 0, tzinfo=timezone.utc)
    strategy = Strategy(max_trades_per_day=3)

    prior_trades = [
        Trade(id=i, symbol="EURUSD", open_time=base_time + timedelta(hours=i), status="CLOSED")
        for i in range(3)
    ]

    fourth_trade = Trade(
        id=4,
        symbol="EURUSD",
        open_time=base_time + timedelta(hours=4),
        status="OPEN"
    )

    flags = analyzer.analyze_trade(fourth_trade, prior_trades, strategy)
    overtrading_flag = next((f for f in flags if f.flag_type == BehaviorFlagType.OVERTRADING), None)

    assert overtrading_flag is not None
    assert overtrading_flag.metrics["trades_today"] == 4
    assert overtrading_flag.metrics["max_allowed"] == 3


def test_risk_escalation_detection(analyzer):
    base_time = datetime(2026, 8, 27, 8, 0, 0, tzinfo=timezone.utc)

    # Baseline historical trades with avg risk = $100
    prior_trades = [
        Trade(id=i, open_time=base_time + timedelta(hours=i), monetary_risk=100.0)
        for i in range(5)
    ]

    escalated_trade = Trade(
        id=6,
        open_time=base_time + timedelta(hours=6),
        monetary_risk=250.0  # 2.5x higher risk
    )

    flags = analyzer.analyze_trade(escalated_trade, prior_trades)
    risk_flag = next((f for f in flags if f.flag_type == BehaviorFlagType.RISK_ESCALATION), None)

    assert risk_flag is not None
    assert risk_flag.confidence == ConfidenceLevel.HIGH
    assert risk_flag.metrics["escalation_ratio"] == 2.5


def test_sl_moved_away_buy(analyzer):
    base_time = datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc)

    deal_in = TradeDeal(ticket=1, account_id=1, entry="IN", time=base_time, sl=1.0850, price=1.0900)
    deal_mod = TradeDeal(ticket=2, account_id=1, entry="INOUT", time=base_time + timedelta(minutes=5), sl=1.0800, price=1.0890)

    trade = Trade(
        id=1,
        direction="BUY",
        initial_sl=1.0850,
        open_time=base_time,
        deals=[deal_in, deal_mod]
    )

    flags = analyzer.analyze_trade(trade, [])
    sl_flag = next((f for f in flags if f.flag_type == BehaviorFlagType.SL_MOVED_AWAY), None)

    assert sl_flag is not None
    assert sl_flag.confidence == ConfidenceLevel.HIGH
    assert "widened down" in sl_flag.reason


def test_sl_moved_away_sell(analyzer):
    base_time = datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc)

    deal_in = TradeDeal(ticket=1, account_id=1, entry="IN", time=base_time, sl=1.0950, price=1.0900)
    deal_mod = TradeDeal(ticket=2, account_id=1, entry="INOUT", time=base_time + timedelta(minutes=5), sl=1.1000, price=1.0910)

    trade = Trade(
        id=1,
        direction="SELL",
        initial_sl=1.0950,
        open_time=base_time,
        deals=[deal_in, deal_mod]
    )

    flags = analyzer.analyze_trade(trade, [])
    sl_flag = next((f for f in flags if f.flag_type == BehaviorFlagType.SL_MOVED_AWAY), None)

    assert sl_flag is not None
    assert sl_flag.confidence == ConfidenceLevel.HIGH
    assert "widened up" in sl_flag.reason


def test_fomo_detection(analyzer):
    base_time = datetime(2026, 8, 27, 10, 0, 0, tzinfo=timezone.utc)

    trade1 = Trade(id=1, open_time=base_time)
    trade2 = Trade(
        id=2,
        open_time=base_time + timedelta(seconds=90),
        initial_sl=None  # No SL
    )

    flags = analyzer.analyze_trade(trade2, [trade1])
    fomo_flag = next((f for f in flags if f.flag_type == BehaviorFlagType.POSSIBLE_FOMO), None)

    assert fomo_flag is not None
    assert fomo_flag.confidence == ConfidenceLevel.MEDIUM
