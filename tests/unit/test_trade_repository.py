"""
Unit tests for TradeRepository SQLite operations.
"""

from datetime import datetime, timezone
import pytest

from tradeaudit.infrastructure.repositories.trade_repository import TradeRepository
from tradeaudit.domain.models import MT5AccountInfo, TradeDeal, Trade


@pytest.fixture
def repo(test_db_manager):
    return TradeRepository(test_db_manager)


def test_save_account(repo):
    acc = MT5AccountInfo(login=5050, name="Alice Trader", server="LiveServer", balance=25000.0)
    repo.save_account(acc)

    with repo.db_manager.session_scope() as session:
        from tradeaudit.infrastructure.database.models import AccountModel
        saved = session.query(AccountModel).filter_by(id=5050).first()
        assert saved is not None
        assert saved.name == "Alice Trader"
        assert saved.balance == 25000.0


def test_save_deals_and_duplicate_prevention(repo):
    acc = MT5AccountInfo(login=6060, name="Bob")
    repo.save_account(acc)

    now = datetime.now(timezone.utc)
    deals = [
        TradeDeal(ticket=101, account_id=6060, position_id=1, symbol="EURUSD", type="BUY", entry="IN", time=now, volume=1.0, price=1.08),
        TradeDeal(ticket=102, account_id=6060, position_id=1, symbol="EURUSD", type="SELL", entry="OUT", time=now, volume=1.0, price=1.09, profit=100.0)
    ]

    inserted_first = repo.save_deals(deals)
    assert inserted_first == 2

    # Try saving duplicate deals again
    inserted_second = repo.save_deals(deals)
    assert inserted_second == 0


def test_save_and_get_trades(repo):
    acc = MT5AccountInfo(login=7070, name="Charlie")
    repo.save_account(acc)

    now = datetime.now(timezone.utc)
    deals = [
        TradeDeal(ticket=201, account_id=7070, position_id=99, symbol="USDJPY", type="BUY", entry="IN", time=now, volume=1.0, price=150.0),
        TradeDeal(ticket=202, account_id=7070, position_id=99, symbol="USDJPY", type="SELL", entry="OUT", time=now, volume=1.0, price=151.0, profit=1000.0)
    ]
    repo.save_deals(deals)

    trade = Trade(
        account_id=7070,
        position_id=99,
        symbol="USDJPY",
        direction="BUY",
        volume=1.0,
        open_time=now,
        close_time=now,
        open_price=150.0,
        close_price=151.0,
        profit=1000.0,
        status="CLOSED",
        deals=deals
    )

    saved_trades = repo.save_trades(7070, [trade])
    assert len(saved_trades) == 1
    assert saved_trades[0].id is not None

    loaded_trades = repo.get_trades(7070)
    assert len(loaded_trades) == 1
    assert loaded_trades[0].symbol == "USDJPY"
    assert loaded_trades[0].profit == 1000.0
    assert len(loaded_trades[0].deals) == 2


def test_sync_state_tracking(repo):
    acc = MT5AccountInfo(login=8080)
    repo.save_account(acc)

    sync_time = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    repo.update_sync_state(8080, sync_time=sync_time, deals_count=15, trades_count=8)

    last_sync = repo.get_last_sync_time(8080)
    assert last_sync is not None
    assert last_sync.year == 2026
    assert last_sync.hour == 12
