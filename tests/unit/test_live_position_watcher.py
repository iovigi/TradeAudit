from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from tradeaudit.app.services.live_position_watcher import LivePositionWatcherService
from tradeaudit.domain.models import LivePosition, TradeEventType


def test_live_position_watcher_lifecycle():
    mock_reader = MagicMock()
    mock_event_repo = MagicMock()
    mock_sync_service = MagicMock()

    service = LivePositionWatcherService(
        position_reader=mock_reader,
        event_repository=mock_event_repo,
        sync_service=mock_sync_service
    )

    pos_1 = LivePosition(
        ticket=5001,
        position_id=5001,
        symbol="EURUSD",
        type="BUY",
        volume=1.0,
        price_open=1.0850,
        sl=1.0800,
        tp=1.0950,
        profit=50.0,
        time=datetime.now(timezone.utc)
    )

    # 1. First poll: Position newly opened
    mock_reader.fetch_open_positions.return_value = [pos_1]
    active_1 = service.poll_positions(account_id=1001)

    assert len(active_1) == 1
    assert active_1[0].position_id == 5001

    # Check event repository received POSITION_OPENED and SL/TP records
    assert mock_event_repo.save_trade_event.called
    assert mock_event_repo.save_sl_history.called
    assert mock_event_repo.save_tp_history.called

    # Reset mocks to test modifications
    mock_event_repo.reset_mock()

    # 2. Second poll: SL modified, volume reduced (partial close)
    pos_1_mod = LivePosition(
        ticket=5001,
        position_id=5001,
        symbol="EURUSD",
        type="BUY",
        volume=0.5,      # volume reduced
        price_open=1.0850,
        sl=1.0850,       # SL moved up to breakeven
        tp=1.0950,
        profit=75.0,
        time=datetime.now(timezone.utc)
    )
    mock_reader.fetch_open_positions.return_value = [pos_1_mod]
    active_2 = service.poll_positions(account_id=1001)

    assert len(active_2) == 1
    assert active_2[0].volume == 0.5
    assert active_2[0].sl == 1.0850
    assert mock_event_repo.save_sl_history.called

    # Check save_trade_event calls for SL_MODIFIED and PARTIAL_CLOSE
    event_types = [call.args[0].event_type for call in mock_event_repo.save_trade_event.call_args_list]
    assert TradeEventType.SL_MODIFIED.value in event_types
    assert TradeEventType.PARTIAL_CLOSE.value in event_types

    # Reset mocks to test closure
    mock_event_repo.reset_mock()

    # 3. Third poll: Position closed (no positions active)
    mock_reader.fetch_open_positions.return_value = []
    active_3 = service.poll_positions(account_id=1001)

    assert len(active_3) == 0
    event_types = [call.args[0].event_type for call in mock_event_repo.save_trade_event.call_args_list]
    assert TradeEventType.POSITION_CLOSED.value in event_types

    # Sync service should be called when position closes
    assert mock_sync_service.sync_account_history.called
