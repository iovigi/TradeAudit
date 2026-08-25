"""
Unit tests for StrategyComplianceEngine.
"""

import pytest
from datetime import datetime, timezone
from tradeaudit.domain.models import Trade, Strategy, ComplianceStatus
from tradeaudit.app.services.strategy_compliance_engine import StrategyComplianceEngine


@pytest.fixture
def engine():
    return StrategyComplianceEngine()


def test_compliant_trade(engine):
    strategy = Strategy(
        min_rr=1.5,
        max_risk_pct=2.0,
        requires_sl=True,
        requires_tp=True,
        allowed_direction="BUY",
        allowed_symbols=["EURUSD"],
        allowed_sessions=["LONDON"]
    )

    trade = Trade(
        symbol="EURUSD",
        direction="BUY",
        open_time=datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc),  # 10:00 UTC = London
        initial_sl=1.0900,
        initial_tp=1.1200,
        planned_rr=2.0,
        risk_percentage=1.0
    )

    result = engine.evaluate(trade, strategy)
    assert result.status == ComplianceStatus.COMPLIANT
    assert len(result.violations) == 0
    assert len(result.passed_rules) == 7


def test_min_rr_violation(engine):
    strategy = Strategy(min_rr=2.0)
    trade = Trade(planned_rr=1.2)

    result = engine.evaluate(trade, strategy)
    assert result.status == ComplianceStatus.DEVIATION
    assert any(v.rule_name == "MIN_RR" for v in result.violations)


def test_max_risk_percent_violation(engine):
    strategy = Strategy(max_risk_pct=1.0)
    trade = Trade(risk_percentage=2.5)

    result = engine.evaluate(trade, strategy)
    assert result.status == ComplianceStatus.DEVIATION
    assert any(v.rule_name == "MAX_RISK_PERCENT" for v in result.violations)


def test_missing_sl_tp_violations(engine):
    strategy = Strategy(requires_sl=True, requires_tp=True)
    trade = Trade(initial_sl=None, initial_tp=None)

    result = engine.evaluate(trade, strategy)
    assert result.status == ComplianceStatus.DEVIATION
    violation_rules = [v.rule_name for v in result.violations]
    assert "REQUIRES_STOP_LOSS" in violation_rules
    assert "REQUIRES_TAKE_PROFIT" in violation_rules


def test_allowed_direction_and_symbol_violations(engine):
    strategy = Strategy(allowed_direction="SELL", allowed_symbols=["GBPUSD"])
    trade = Trade(symbol="EURUSD", direction="BUY")

    result = engine.evaluate(trade, strategy)
    assert result.status == ComplianceStatus.DEVIATION
    violation_rules = [v.rule_name for v in result.violations]
    assert "ALLOWED_DIRECTION" in violation_rules
    assert "ALLOWED_SYMBOL" in violation_rules


def test_allowed_session_violation(engine):
    strategy = Strategy(allowed_sessions=["LONDON"])  # 08:00 - 16:00 UTC
    trade = Trade(open_time=datetime(2026, 8, 25, 20, 0, tzinfo=timezone.utc))  # 20:00 UTC (New York evening)

    result = engine.evaluate(trade, strategy)
    assert result.status == ComplianceStatus.DEVIATION
    assert any(v.rule_name == "ALLOWED_SESSION" for v in result.violations)


def test_max_trades_per_day_violation(engine):
    strategy = Strategy(id=1, max_trades_per_day=2)

    open_dt = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
    t1 = Trade(id=101, strategy_id=1, open_time=open_dt)
    t2 = Trade(id=102, strategy_id=1, open_time=open_dt)
    t3 = Trade(id=103, strategy_id=1, open_time=open_dt)

    all_trades = [t1, t2, t3]

    result = engine.evaluate(t3, strategy, all_trades=all_trades)
    assert result.status == ComplianceStatus.DEVIATION
    assert any(v.rule_name == "MAX_TRADES_PER_DAY" for v in result.violations)
