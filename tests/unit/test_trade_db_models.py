"""
Unit tests for database schema models (accounts, trades, trade_deals, sync_state).
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tradeaudit.infrastructure.database.models import (
    Base,
    AccountModel,
    TradeModel,
    TradeDealModel,
    SyncStateModel
)


@pytest.fixture
def in_memory_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_account_model_creation(in_memory_session):
    account = AccountModel(
        id=123456,
        name="John Doe",
        server="Broker-Demo",
        currency="USD",
        balance=10000.0,
        equity=10500.0
    )
    in_memory_session.add(account)
    in_memory_session.commit()

    saved = in_memory_session.query(AccountModel).filter_by(id=123456).first()
    assert saved is not None
    assert saved.name == "John Doe"
    assert saved.currency == "USD"
    assert saved.balance == 10000.0


def test_trade_and_deal_relationship(in_memory_session):
    account = AccountModel(id=1001, name="Test Account")
    in_memory_session.add(account)
    in_memory_session.commit()

    trade = TradeModel(
        account_id=1001,
        position_id=5001,
        symbol="EURUSD",
        direction="BUY",
        volume=1.0,
        open_time=datetime.now(timezone.utc),
        open_price=1.0850,
        status="CLOSED",
        profit=150.0
    )
    in_memory_session.add(trade)
    in_memory_session.commit()

    deal_in = TradeDealModel(
        ticket=10001,
        trade_id=trade.id,
        account_id=1001,
        position_id=5001,
        symbol="EURUSD",
        type="BUY",
        entry="IN",
        time=datetime.now(timezone.utc),
        volume=1.0,
        price=1.0850,
        profit=0.0
    )
    deal_out = TradeDealModel(
        ticket=10002,
        trade_id=trade.id,
        account_id=1001,
        position_id=5001,
        symbol="EURUSD",
        type="SELL",
        entry="OUT",
        time=datetime.now(timezone.utc),
        volume=1.0,
        price=1.0865,
        profit=150.0
    )
    in_memory_session.add_all([deal_in, deal_out])
    in_memory_session.commit()

    saved_trade = in_memory_session.query(TradeModel).filter_by(position_id=5001).first()
    assert saved_trade is not None
    assert len(saved_trade.deals) == 2
    assert saved_trade.deals[0].ticket == 10001
    assert saved_trade.deals[1].ticket == 10002


def test_sync_state_model(in_memory_session):
    account = AccountModel(id=2002, name="Sync Account")
    in_memory_session.add(account)
    in_memory_session.commit()

    now = datetime.now(timezone.utc)
    sync = SyncStateModel(account_id=2002, last_sync_time=now, deals_count=10, trades_count=5)
    in_memory_session.add(sync)
    in_memory_session.commit()

    saved_sync = in_memory_session.query(SyncStateModel).filter_by(account_id=2002).first()
    assert saved_sync is not None
    assert saved_sync.deals_count == 10
    assert saved_sync.trades_count == 5
