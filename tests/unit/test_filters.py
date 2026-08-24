"""
Unit tests for domain filters and FilterEvaluator.
"""

from datetime import datetime, timedelta
import pytest

from tradeaudit.domain.models import Trade
from tradeaudit.domain.filters import (
    AnalysisFilter,
    PeriodPreset,
    DirectionFilter,
    ResultFilter,
    FilterEvaluator
)


@pytest.fixture
def sample_trades():
    now = datetime(2026, 8, 25, 12, 0, 0)
    return [
        Trade(
            id=1,
            symbol="EURUSD",
            direction="BUY",
            open_time=now - timedelta(days=1),
            close_time=now - timedelta(days=1),
            profit=100.0,
            status="CLOSED",
            realized_r=2.0
        ),
        Trade(
            id=2,
            symbol="EURUSD",
            direction="SELL",
            open_time=now - timedelta(days=3),
            close_time=now - timedelta(days=3),
            profit=-50.0,
            status="CLOSED",
            realized_r=-1.0
        ),
        Trade(
            id=3,
            symbol="GBPUSD",
            direction="BUY",
            open_time=now - timedelta(days=10),
            close_time=now - timedelta(days=10),
            profit=0.0,
            status="CLOSED",
            realized_r=0.0
        ),
        Trade(
            id=4,
            symbol="XAUUSD",
            direction="SELL",
            open_time=now - timedelta(days=40),
            close_time=now - timedelta(days=40),
            profit=200.0,
            status="CLOSED",
            realized_r=4.0
        )
    ]


def test_date_range_presets():
    ref = datetime(2026, 8, 25, 12, 0, 0)  # Tuesday

    # ALL_TIME
    start, end = FilterEvaluator.get_date_range(PeriodPreset.ALL_TIME, reference_date=ref)
    assert start is None and end is None

    # TODAY
    start, end = FilterEvaluator.get_date_range(PeriodPreset.TODAY, reference_date=ref)
    assert start.date() == ref.date()
    assert end.date() == ref.date()

    # YESTERDAY
    start, end = FilterEvaluator.get_date_range(PeriodPreset.YESTERDAY, reference_date=ref)
    assert start.date() == (ref - timedelta(days=1)).date()

    # THIS_WEEK (Monday 2026-08-24 to Sunday 2026-08-30)
    start, end = FilterEvaluator.get_date_range(PeriodPreset.THIS_WEEK, reference_date=ref)
    assert start.strftime("%Y-%m-%d") == "2026-08-24"
    assert end.strftime("%Y-%m-%d") == "2026-08-30"

    # LAST_WEEK (Monday 2026-08-17 to Sunday 2026-08-23)
    start, end = FilterEvaluator.get_date_range(PeriodPreset.LAST_WEEK, reference_date=ref)
    assert start.strftime("%Y-%m-%d") == "2026-08-17"
    assert end.strftime("%Y-%m-%d") == "2026-08-23"

    # THIS_MONTH (2026-08-01 to 2026-08-31)
    start, end = FilterEvaluator.get_date_range(PeriodPreset.THIS_MONTH, reference_date=ref)
    assert start.strftime("%Y-%m-%d") == "2026-08-01"
    assert end.strftime("%Y-%m-%d") == "2026-08-31"


def test_filter_by_direction(sample_trades):
    # BUY
    flt_buy = AnalysisFilter(direction=DirectionFilter.BUY)
    buys = FilterEvaluator.apply(sample_trades, flt_buy)
    assert len(buys) == 2
    assert all(t.direction == "BUY" for t in buys)

    # SELL
    flt_sell = AnalysisFilter(direction=DirectionFilter.SELL)
    sells = FilterEvaluator.apply(sample_trades, flt_sell)
    assert len(sells) == 2
    assert all(t.direction == "SELL" for t in sells)


def test_filter_by_symbols(sample_trades):
    flt = AnalysisFilter(symbols=["EURUSD"])
    res = FilterEvaluator.apply(sample_trades, flt)
    assert len(res) == 2
    assert all(t.symbol == "EURUSD" for t in res)

    flt_multi = AnalysisFilter(symbols=["EURUSD", "XAUUSD"])
    res_multi = FilterEvaluator.apply(sample_trades, flt_multi)
    assert len(res_multi) == 3


def test_filter_by_result_outcome(sample_trades):
    # WINNERS
    flt_win = AnalysisFilter(result=ResultFilter.WINNERS)
    winners = FilterEvaluator.apply(sample_trades, flt_win)
    assert len(winners) == 2

    # LOSERS
    flt_loss = AnalysisFilter(result=ResultFilter.LOSERS)
    losers = FilterEvaluator.apply(sample_trades, flt_loss)
    assert len(losers) == 1
    assert losers[0].id == 2

    # BREAKEVEN
    flt_be = AnalysisFilter(result=ResultFilter.BREAKEVEN)
    be = FilterEvaluator.apply(sample_trades, flt_be)
    assert len(be) == 1
    assert be[0].id == 3
