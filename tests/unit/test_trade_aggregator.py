"""
Unit tests for TradeAggregator service.
"""

from datetime import datetime, timezone
import pytest

from tradeaudit.domain.models import TradeDeal
from tradeaudit.app.services.trade_aggregator import TradeAggregator


@pytest.fixture
def aggregator():
    return TradeAggregator()


def test_aggregate_simple_closed_trade(aggregator):
    t_open = datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
    t_close = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)

    deals = [
        TradeDeal(
            ticket=1, account_id=100, position_id=500, symbol="EURUSD",
            type="BUY", entry="IN", time=t_open, volume=1.0, price=1.0800,
            sl=1.0750, tp=1.0900, commission=-5.0
        ),
        TradeDeal(
            ticket=2, account_id=100, position_id=500, symbol="EURUSD",
            type="SELL", entry="OUT", time=t_close, volume=1.0, price=1.0850,
            profit=500.0, swap=-2.0, commission=-5.0
        )
    ]

    trades = aggregator.aggregate_deals(deals)
    assert len(trades) == 1
    trade = trades[0]

    assert trade.position_id == 500
    assert trade.symbol == "EURUSD"
    assert trade.direction == "BUY"
    assert trade.volume == 1.0
    assert trade.open_price == 1.0800
    assert trade.close_price == 1.0850
    assert trade.initial_sl == 1.0750
    assert trade.initial_tp == 1.0900
    assert trade.profit == 500.0
    assert trade.commission == -10.0
    assert trade.swap == -2.0
    assert trade.net_profit == 488.0
    assert trade.status == "CLOSED"
    assert trade.open_time == t_open
    assert trade.close_time == t_close


def test_aggregate_scale_in_trade(aggregator):
    t1 = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc)
    t3 = datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc)

    # 1 lot @ 1.1000 + 1 lot @ 1.1020 -> weighted open price 1.1010
    deals = [
        TradeDeal(ticket=10, account_id=100, position_id=600, symbol="GBPUSD", type="BUY", entry="IN", time=t1, volume=1.0, price=1.1000),
        TradeDeal(ticket=11, account_id=100, position_id=600, symbol="GBPUSD", type="BUY", entry="IN", time=t2, volume=1.0, price=1.1020),
        TradeDeal(ticket=12, account_id=100, position_id=600, symbol="GBPUSD", type="SELL", entry="OUT", time=t3, volume=2.0, price=1.1050, profit=800.0)
    ]

    trades = aggregator.aggregate_deals(deals)
    assert len(trades) == 1
    trade = trades[0]

    assert trade.volume == 2.0
    assert trade.open_price == 1.1010
    assert trade.close_price == 1.1050
    assert trade.status == "CLOSED"


def test_aggregate_partial_close_trade(aggregator):
    t1 = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)

    # Entry 2.0 lots -> Partial exit 1 1.0 lot -> Partial exit 2 1.0 lot
    deals = [
        TradeDeal(ticket=20, account_id=100, position_id=700, symbol="XAUUSD", type="SELL", entry="IN", time=t1, volume=2.0, price=2000.0),
        TradeDeal(ticket=21, account_id=100, position_id=700, symbol="XAUUSD", type="BUY", entry="OUT", time=t2, volume=1.0, price=1990.0, profit=1000.0),
        TradeDeal(ticket=22, account_id=100, position_id=700, symbol="XAUUSD", type="BUY", entry="OUT", time=t3, volume=1.0, price=1980.0, profit=2000.0)
    ]

    trades = aggregator.aggregate_deals(deals)
    assert len(trades) == 1
    trade = trades[0]

    assert trade.direction == "SELL"
    assert trade.volume == 2.0
    assert trade.open_price == 2000.0
    assert trade.close_price == 1985.0  # (1990 + 1980) / 2
    assert trade.profit == 3000.0
    assert trade.status == "CLOSED"
    assert trade.close_time == t3


def test_aggregate_filters_balance_deals(aggregator):
    deals = [
        TradeDeal(ticket=99, account_id=100, position_id=0, symbol="", type="BALANCE", entry="IN", volume=0.0, price=0.0, profit=5000.0),
        TradeDeal(ticket=100, account_id=100, position_id=800, symbol="EURUSD", type="BUY", entry="IN", volume=0.5, price=1.0800)
    ]

    trades = aggregator.aggregate_deals(deals)
    assert len(trades) == 1
    assert trades[0].position_id == 800
    assert trades[0].status == "OPEN"
