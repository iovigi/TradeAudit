"""
Unit tests for SyncService orchestrator.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from tradeaudit.infrastructure.repositories.trade_repository import TradeRepository
from tradeaudit.app.services.sync_service import SyncService
from tradeaudit.domain.models import MT5AccountInfo, TradeDeal


@pytest.fixture
def repo(test_db_manager):
    return TradeRepository(test_db_manager)


def test_sync_account_history_successful(repo):
    mock_history_reader = MagicMock()
    now = datetime.now(timezone.utc)

    mock_history_reader.fetch_deals.return_value = [
        TradeDeal(ticket=1001, account_id=9999, position_id=123, symbol="EURUSD", type="BUY", entry="IN", time=now, volume=1.0, price=1.0800),
        TradeDeal(ticket=1002, account_id=9999, position_id=123, symbol="EURUSD", type="SELL", entry="OUT", time=now, volume=1.0, price=1.0850, profit=500.0)
    ]

    service = SyncService(trade_repo=repo, history_reader=mock_history_reader)
    acc_info = MT5AccountInfo(login=9999, name="Demo Trader")

    res = service.sync_account_history(account_id=9999, account_info=acc_info)

    assert res.success is True
    assert res.deals_imported == 2
    assert res.trades_created == 1

    stored_trades = repo.get_trades(9999)
    assert len(stored_trades) == 1
    assert stored_trades[0].symbol == "EURUSD"
    assert stored_trades[0].profit == 500.0
    assert stored_trades[0].status == "CLOSED"

    last_sync = repo.get_last_sync_time(9999)
    assert last_sync is not None
