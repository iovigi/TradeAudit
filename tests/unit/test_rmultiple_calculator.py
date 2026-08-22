"""
Unit tests for RMultipleCalculator service.
"""

from tradeaudit.app.services.rmultiple_calculator import RMultipleCalculator


def test_planned_rr_calculation():
    rr = RMultipleCalculator.calculate_planned_rr(price_risk=5.0, planned_reward=15.0)
    assert rr == 3.0


def test_planned_rr_missing_risk():
    rr = RMultipleCalculator.calculate_planned_rr(price_risk=None, planned_reward=15.0)
    assert rr is None


def test_realized_r_win():
    realized_r = RMultipleCalculator.calculate_realized_r(net_profit=300.0, monetary_risk=100.0)
    assert realized_r == 3.0


def test_realized_r_loss():
    realized_r = RMultipleCalculator.calculate_realized_r(net_profit=-100.0, monetary_risk=100.0)
    assert realized_r == -1.0


def test_realized_r_missing_sl_returns_none():
    realized_r = RMultipleCalculator.calculate_realized_r(net_profit=250.0, monetary_risk=None)
    assert realized_r is None
