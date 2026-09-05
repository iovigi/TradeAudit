"""
Repository for saving, updating, retrieving, and deleting TradeJournalNote entities.
"""

import json
import logging
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from contextlib import contextmanager
from tradeaudit.domain.annotations import TradeJournalNote, TradeGrade
from tradeaudit.infrastructure.database.models import TradeJournalNoteModel

logger = logging.getLogger(__name__)


class TradeNoteRepository:
    """SQLAlchemy-backed repository for rich trade journal notes and reviews."""

    def __init__(self, db_or_factory):
        self.db_or_factory = db_or_factory

    @contextmanager
    def _session_scope(self):
        if hasattr(self.db_or_factory, "session_scope"):
            with self.db_or_factory.session_scope() as session:
                yield session
        elif hasattr(self.db_or_factory, "get_session"):
            with self.db_or_factory.get_session() as session:
                yield session
        else:
            session = self.db_or_factory()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

    def save_note(self, note: TradeJournalNote) -> TradeJournalNote:
        """Save a new or update an existing trade journal note."""
        with self._session_scope() as session:
            model = session.query(TradeJournalNoteModel).filter_by(trade_id=note.trade_id).first()
            mistakes_str = json.dumps(note.mistakes_identified, ensure_ascii=False)
            checklist_str = json.dumps(note.checklist_data, ensure_ascii=False)
            screenshots_str = json.dumps(note.screenshot_paths, ensure_ascii=False)

            if model:
                model.setup_name = note.setup_name
                model.rating = note.rating.value if isinstance(note.rating, TradeGrade) else str(note.rating)
                model.pre_trade_thesis = note.pre_trade_thesis
                model.post_trade_review = note.post_trade_review
                model.lessons_learned = note.lessons_learned
                model.mistakes_json = mistakes_str
                model.checklist_json = checklist_str
                model.screenshots_json = screenshots_str
                model.updated_at = datetime.now(timezone.utc)
                session.commit()
                return self._to_domain(model)

            model = TradeJournalNoteModel(
                trade_id=note.trade_id,
                setup_name=note.setup_name,
                rating=note.rating.value if isinstance(note.rating, TradeGrade) else str(note.rating),
                pre_trade_thesis=note.pre_trade_thesis,
                post_trade_review=note.post_trade_review,
                lessons_learned=note.lessons_learned,
                mistakes_json=mistakes_str,
                checklist_json=checklist_str,
                screenshots_json=screenshots_str,
                created_at=note.created_at or datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_domain(model)

    def get_note_for_trade(self, trade_id: int) -> Optional[TradeJournalNote]:
        """Fetch the journal note for a specific trade."""
        with self._session_scope() as session:
            model = session.query(TradeJournalNoteModel).filter_by(trade_id=trade_id).first()
            if model:
                return self._to_domain(model)
            return None

    def delete_note(self, trade_id: int) -> bool:
        """Delete a trade journal note."""
        with self._session_scope() as session:
            model = session.query(TradeJournalNoteModel).filter_by(trade_id=trade_id).first()
            if model:
                session.delete(model)
                session.commit()
                return True
            return False

    def _to_domain(self, model: TradeJournalNoteModel) -> TradeJournalNote:
        try:
            mistakes = json.loads(model.mistakes_json) if model.mistakes_json else []
        except Exception:
            mistakes = []

        try:
            checklist = json.loads(model.checklist_json) if model.checklist_json else {}
        except Exception:
            checklist = {}

        try:
            screenshots = json.loads(model.screenshots_json) if model.screenshots_json else []
        except Exception:
            screenshots = []

        return TradeJournalNote(
            id=model.id,
            trade_id=model.trade_id,
            setup_name=model.setup_name or "",
            rating=model.rating or TradeGrade.A.value,
            pre_trade_thesis=model.pre_trade_thesis or "",
            post_trade_review=model.post_trade_review or "",
            lessons_learned=model.lessons_learned or "",
            mistakes_identified=mistakes,
            checklist_data=checklist,
            screenshot_paths=screenshots,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
