from datetime import datetime, timezone
import pytest
from PySide6.QtWidgets import QApplication

from tradeaudit.ui.views.live_journal_view import LiveJournalView
from tradeaudit.domain.models import LivePosition, TradeEventRecord, TradeEventType


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_live_journal_view_instantiation_and_updates(qapp):
    view = LiveJournalView()
    assert view is not None

    positions = [
        LivePosition(
            ticket=7001,
            position_id=7001,
            symbol="EURUSD",
            type="BUY",
            volume=1.0,
            price_open=1.0850,
            sl=1.0800,
            tp=1.0950,
            profit=120.0,
            time=datetime.now(timezone.utc)
        )
    ]
    view.update_positions(positions)
    assert view.pos_table.rowCount() == 1
    assert view.pos_table.item(0, 1).text() == "EURUSD"

    events = [
        TradeEventRecord(
            position_id=7001,
            event_type=TradeEventType.POSITION_OPENED.value,
            timestamp=datetime.now(timezone.utc),
            details={"symbol": "EURUSD"}
        )
    ]
    view.update_events(events)
    assert view.events_table.rowCount() == 1
    assert view.events_table.item(0, 2).text() == TradeEventType.POSITION_OPENED.value
