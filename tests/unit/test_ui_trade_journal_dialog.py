"""
Unit tests for TradeJournalDialog.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tradeaudit.infrastructure.database.models import Base
from tradeaudit.domain.models import Trade
from tradeaudit.domain.annotations import TradeGrade
from tradeaudit.infrastructure.repositories.trade_note_repository import TradeNoteRepository
from tradeaudit.app.services.trade_journal_service import TradeJournalService
from tradeaudit.ui.dialogs.trade_journal_dialog import TradeJournalDialog


@pytest.fixture
def sample_trade():
    return Trade(
        id=1,
        account_id=123456,
        position_id=98765,
        symbol="EURUSD",
        direction="BUY",
        volume=1.0,
        open_time=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        close_time=datetime(2026, 3, 1, 11, 0, tzinfo=timezone.utc),
        open_price=1.0850,
        close_price=1.0900,
        initial_sl=1.0820,
        initial_tp=1.0910,
        profit=500.0,
        realized_r=1.67,
        status="CLOSED"
    )


@pytest.fixture
def journal_service():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    repo = TradeNoteRepository(session_factory)
    return TradeJournalService(trade_note_repo=repo)


def test_trade_journal_dialog_instantiation_and_save(qtbot, sample_trade, journal_service):
    dialog = TradeJournalDialog(trade=sample_trade, journal_service=journal_service)
    qtbot.addWidget(dialog)

    assert "Ticket #98765" in dialog.windowTitle()
    assert dialog.setup_combo.currentText() == ""
    assert dialog.grade_combo.currentText() == TradeGrade.A.value

    # Edit form fields
    dialog.setup_combo.setEditText("London Breakout")
    dialog.grade_combo.setCurrentText(TradeGrade.A_PLUS.value)
    dialog.pre_thesis_text.setPlainText("Asian range sweep entry")
    dialog.post_review_text.setPlainText("Clean take profit reached")

    # Check a checklist item
    for name, cb in dialog._checklist_checkboxes.items():
        if "Higher Timeframe" in name:
            cb.setChecked(True)

    # Save
    dialog._on_save()

    # Verify saved via journal service
    saved = journal_service.get_or_create_note(sample_trade.id)
    assert saved.setup_name == "London Breakout"
    assert saved.rating == TradeGrade.A_PLUS.value
    assert saved.pre_trade_thesis == "Asian range sweep entry"
    assert saved.post_trade_review == "Clean take profit reached"
    assert any(k for k, v in saved.checklist_data.items() if "Higher Timeframe" in k and v)
