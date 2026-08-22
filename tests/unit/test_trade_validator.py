"""
Unit tests for TradeValidator service.
"""

from tradeaudit.domain.models import Trade
from tradeaudit.app.services.trade_validator import TradeValidator


def test_valid_buy_setup():
    is_valid, error = TradeValidator.validate_setup(
        direction="BUY",
        open_price=1.1000,
        initial_sl=1.0950,
        initial_tp=1.1100
    )
    assert is_valid is True
    assert error is None


def test_invalid_buy_sl_above_entry():
    is_valid, error = TradeValidator.validate_setup(
        direction="BUY",
        open_price=1.1000,
        initial_sl=1.1050
    )
    assert is_valid is False
    assert "Stop Loss" in error


def test_invalid_buy_tp_below_entry():
    is_valid, error = TradeValidator.validate_setup(
        direction="BUY",
        open_price=1.1000,
        initial_sl=1.0950,
        initial_tp=1.0900
    )
    assert is_valid is False
    assert "Take Profit" in error


def test_valid_sell_setup():
    is_valid, error = TradeValidator.validate_setup(
        direction="SELL",
        open_price=1.1000,
        initial_sl=1.1050,
        initial_tp=1.0900
    )
    assert is_valid is True
    assert error is None


def test_invalid_sell_sl_below_entry():
    is_valid, error = TradeValidator.validate_setup(
        direction="SELL",
        open_price=1.1000,
        initial_sl=1.0950
    )
    assert is_valid is False
    assert "Stop Loss" in error


def test_trade_instance_validation():
    trade = Trade(
        position_id=101,
        symbol="EURUSD",
        direction="BUY",
        open_price=1.1000,
        initial_sl=1.1050  # Invalid for BUY
    )
    is_valid, error = TradeValidator.validate_trade(trade)
    assert is_valid is False
    assert trade.is_valid_setup is False
    assert trade.validation_error is not None
