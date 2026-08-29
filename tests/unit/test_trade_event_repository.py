from datetime import datetime, timezone
import pytest

from tradeaudit.infrastructure.repositories.trade_event_repository import TradeEventRepository
from tradeaudit.domain.models import (
    SLHistoryRecord,
    TPHistoryRecord,
    TradeEventRecord,
    TradeEventType
)


def test_sl_and_tp_history_persistence(test_db_manager):
    repo = TradeEventRepository(test_db_manager)

    sl_rec = SLHistoryRecord(
        position_id=2001,
        old_sl=1.0800,
        new_sl=1.0820,
        timestamp=datetime.now(timezone.utc),
        change_reason="SL_MOVED_TO_LOCK_PROFIT"
    )
    saved_sl = repo.save_sl_history(sl_rec)
    assert saved_sl.id is not None

    sl_list = repo.get_sl_history_for_position(2001)
    assert len(sl_list) == 1
    assert sl_list[0].old_sl == 1.0800
    assert sl_list[0].new_sl == 1.0820
    assert sl_list[0].change_reason == "SL_MOVED_TO_LOCK_PROFIT"

    tp_rec = TPHistoryRecord(
        position_id=2001,
        old_tp=1.0950,
        new_tp=1.1000,
        timestamp=datetime.now(timezone.utc)
    )
    saved_tp = repo.save_tp_history(tp_rec)
    assert saved_tp.id is not None

    tp_list = repo.get_tp_history_for_position(2001)
    assert len(tp_list) == 1
    assert tp_list[0].old_tp == 1.0950
    assert tp_list[0].new_tp == 1.1000


def test_trade_event_persistence(test_db_manager):
    repo = TradeEventRepository(test_db_manager)

    event = TradeEventRecord(
        position_id=3001,
        event_type=TradeEventType.POSITION_OPENED.value,
        timestamp=datetime.now(timezone.utc),
        details={"symbol": "EURUSD", "volume": 1.0}
    )

    saved = repo.save_trade_event(event)
    assert saved.id is not None

    events = repo.get_events_for_position(3001)
    assert len(events) == 1
    assert events[0].event_type == TradeEventType.POSITION_OPENED.value
    assert events[0].details["symbol"] == "EURUSD"

    all_events = repo.get_all_events(limit=10)
    assert len(all_events) == 1
