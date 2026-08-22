"""
Unit tests for RiskCalculator service.
"""

from tradeaudit.domain.models import Trade
from tradeaudit.app.services.risk_calculator import RiskCalculator


def test_calculate_price_risk_buy():
    risk = RiskCalculator.calculate_price_risk("BUY", open_price=100.0, initial_sl=95.0)
    assert risk == 5.0


def test_calculate_price_risk_sell():
    risk = RiskCalculator.calculate_price_risk("SELL", open_price=100.0, initial_sl=105.0)
    assert risk == 5.0


def test_calculate_price_risk_missing_sl():
    risk = RiskCalculator.calculate_price_risk("BUY", open_price=100.0, initial_sl=None)
    assert risk is None


def test_calculate_planned_reward():
    reward = RiskCalculator.calculate_planned_reward("BUY", open_price=100.0, initial_tp=115.0)
    assert reward == 15.0


def test_calculate_monetary_risk_with_closed_trade_deal_results():
    trade = Trade(
        position_id=1,
        direction="BUY",
        open_price=1.1000,
        close_price=1.1050,
        initial_sl=1.0950,
        volume=1.0,
        profit=500.0  # $500 profit for 50 pips = $10 per pip
    )
    monetary_risk = RiskCalculator.calculate_monetary_risk(trade)
    # Price risk = 50 pips (0.0050). Value per price unit = 500 / 0.0050 = 100,000. Risk = 0.0050 * 100,000 = $500
    assert monetary_risk == 500.0


def test_calculate_risk_percentage():
    pct = RiskCalculator.calculate_risk_percentage(monetary_risk=200.0, account_balance=10000.0)
    assert pct == 2.0
