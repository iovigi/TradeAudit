import json
import logging
from typing import List, Optional
from datetime import datetime, timezone

from tradeaudit.infrastructure.database.connection import DatabaseManager
from tradeaudit.infrastructure.database.models import (
    SLHistoryModel,
    TPHistoryModel,
    TradeEventModel,
    TradeModel
)
from tradeaudit.domain.models import (
    SLHistoryRecord,
    TPHistoryRecord,
    TradeEventRecord
)

logger = logging.getLogger("tradeaudit.infrastructure.repositories.trade_event_repository")


class TradeEventRepository:
    """Repository handling persistence for SL/TP history and trade lifecycle events."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save_sl_history(self, record: SLHistoryRecord) -> SLHistoryRecord:
        """Save a Stop-Loss modification record."""
        with self.db_manager.session_scope() as session:
            model = SLHistoryModel(
                trade_id=record.trade_id,
                position_id=record.position_id,
                old_sl=record.old_sl,
                new_sl=record.new_sl,
                timestamp=record.timestamp or datetime.now(timezone.utc),
                change_reason=record.change_reason
            )
            session.add(model)
            session.flush()
            record.id = model.id
            logger.info("Saved SL history record for position %s (old: %s, new: %s)", record.position_id, record.old_sl, record.new_sl)
            return record

    def get_sl_history_for_position(self, position_id: int) -> List[SLHistoryRecord]:
        """Fetch all SL modification records for a position_id."""
        with self.db_manager.session_scope() as session:
            models = (
                session.query(SLHistoryModel)
                .filter(SLHistoryModel.position_id == position_id)
                .order_by(SLHistoryModel.timestamp.asc())
                .all()
            )
            return [
                SLHistoryRecord(
                    id=m.id,
                    trade_id=m.trade_id,
                    position_id=m.position_id,
                    old_sl=m.old_sl,
                    new_sl=m.new_sl,
                    timestamp=m.timestamp,
                    change_reason=m.change_reason
                )
                for m in models
            ]

    def save_tp_history(self, record: TPHistoryRecord) -> TPHistoryRecord:
        """Save a Take-Profit modification record."""
        with self.db_manager.session_scope() as session:
            model = TPHistoryModel(
                trade_id=record.trade_id,
                position_id=record.position_id,
                old_tp=record.old_tp,
                new_tp=record.new_tp,
                timestamp=record.timestamp or datetime.now(timezone.utc)
            )
            session.add(model)
            session.flush()
            record.id = model.id
            logger.info("Saved TP history record for position %s (old: %s, new: %s)", record.position_id, record.old_tp, record.new_tp)
            return record

    def get_tp_history_for_position(self, position_id: int) -> List[TPHistoryRecord]:
        """Fetch all TP modification records for a position_id."""
        with self.db_manager.session_scope() as session:
            models = (
                session.query(TPHistoryModel)
                .filter(TPHistoryModel.position_id == position_id)
                .order_by(TPHistoryModel.timestamp.asc())
                .all()
            )
            return [
                TPHistoryRecord(
                    id=m.id,
                    trade_id=m.trade_id,
                    position_id=m.position_id,
                    old_tp=m.old_tp,
                    new_tp=m.new_tp,
                    timestamp=m.timestamp
                )
                for m in models
            ]

    def save_trade_event(self, record: TradeEventRecord) -> TradeEventRecord:
        """Save a trade event record."""
        with self.db_manager.session_scope() as session:
            details_json = json.dumps(record.details) if record.details else None
            model = TradeEventModel(
                trade_id=record.trade_id,
                position_id=record.position_id,
                event_type=record.event_type,
                timestamp=record.timestamp or datetime.now(timezone.utc),
                details=details_json
            )
            session.add(model)
            session.flush()
            record.id = model.id
            logger.info("Saved trade event '%s' for position %s", record.event_type, record.position_id)
            return record

    def get_events_for_position(self, position_id: int) -> List[TradeEventRecord]:
        """Fetch all events for a position_id."""
        with self.db_manager.session_scope() as session:
            models = (
                session.query(TradeEventModel)
                .filter(TradeEventModel.position_id == position_id)
                .order_by(TradeEventModel.timestamp.asc())
                .all()
            )
            records = []
            for m in models:
                details_dict = {}
                if m.details:
                    try:
                        details_dict = json.loads(m.details)
                    except Exception:
                        details_dict = {}
                records.append(
                    TradeEventRecord(
                        id=m.id,
                        trade_id=m.trade_id,
                        position_id=m.position_id,
                        event_type=m.event_type,
                        timestamp=m.timestamp,
                        details=details_dict
                    )
                )
            return records

    def get_all_events(self, limit: int = 100) -> List[TradeEventRecord]:
        """Fetch recent trade events across all positions."""
        with self.db_manager.session_scope() as session:
            models = (
                session.query(TradeEventModel)
                .order_by(TradeEventModel.timestamp.desc())
                .limit(limit)
                .all()
            )
            records = []
            for m in models:
                details_dict = {}
                if m.details:
                    try:
                        details_dict = json.loads(m.details)
                    except Exception:
                        details_dict = {}
                records.append(
                    TradeEventRecord(
                        id=m.id,
                        trade_id=m.trade_id,
                        position_id=m.position_id,
                        event_type=m.event_type,
                        timestamp=m.timestamp,
                        details=details_dict
                    )
                )
            return records
