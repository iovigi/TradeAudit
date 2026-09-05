"""
Repository for saving, updating, retrieving, and deleting ChartAnnotation entities.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from contextlib import contextmanager
from tradeaudit.domain.annotations import ChartAnnotation, AnnotationType
from tradeaudit.infrastructure.database.models import ChartAnnotationModel

logger = logging.getLogger(__name__)


class AnnotationRepository:
    """SQLAlchemy-backed repository for candlestick chart annotations."""

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

    def save_annotation(self, annotation: ChartAnnotation) -> ChartAnnotation:
        """Save a new or update an existing chart annotation."""
        with self._session_scope() as session:
            if annotation.id:
                model = session.query(ChartAnnotationModel).filter_by(id=annotation.id).first()
                if model:
                    model.timeframe = annotation.timeframe
                    model.annotation_type = annotation.annotation_type.value if isinstance(annotation.annotation_type, AnnotationType) else str(annotation.annotation_type)
                    model.p1_time = annotation.p1_time
                    model.p1_price = annotation.p1_price
                    model.p2_time = annotation.p2_time
                    model.p2_price = annotation.p2_price
                    model.color = annotation.color
                    model.line_width = annotation.line_width
                    model.text = annotation.text
                    session.commit()
                    return self._to_domain(model)

            type_val = annotation.annotation_type.value if isinstance(annotation.annotation_type, AnnotationType) else str(annotation.annotation_type)
            model = ChartAnnotationModel(
                trade_id=annotation.trade_id,
                timeframe=annotation.timeframe,
                annotation_type=type_val,
                p1_time=annotation.p1_time,
                p1_price=annotation.p1_price,
                p2_time=annotation.p2_time,
                p2_price=annotation.p2_price,
                color=annotation.color,
                line_width=annotation.line_width,
                text=annotation.text,
                created_at=annotation.created_at or datetime.now(timezone.utc)
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_domain(model)

    def get_annotations_for_trade(self, trade_id: int, timeframe: Optional[str] = None) -> List[ChartAnnotation]:
        """Fetch all annotations for a specific trade, optionally filtered by timeframe."""
        with self._session_scope() as session:
            query = session.query(ChartAnnotationModel).filter(ChartAnnotationModel.trade_id == trade_id)
            if timeframe:
                query = query.filter(ChartAnnotationModel.timeframe == timeframe)
            models = query.order_by(ChartAnnotationModel.created_at.asc()).all()
            return [self._to_domain(m) for m in models]

    def delete_annotation(self, annotation_id: int) -> bool:
        """Delete an annotation by ID."""
        with self._session_scope() as session:
            model = session.query(ChartAnnotationModel).filter_by(id=annotation_id).first()
            if model:
                session.delete(model)
                session.commit()
                return True
            return False

    def clear_annotations_for_trade(self, trade_id: int, timeframe: Optional[str] = None) -> int:
        """Delete all annotations for a trade, optionally for a specific timeframe."""
        with self._session_scope() as session:
            query = session.query(ChartAnnotationModel).filter(ChartAnnotationModel.trade_id == trade_id)
            if timeframe:
                query = query.filter(ChartAnnotationModel.timeframe == timeframe)
            count = query.delete(synchronize_session=False)
            session.commit()
            return count

    def _to_domain(self, model: ChartAnnotationModel) -> ChartAnnotation:
        try:
            ann_type = AnnotationType(model.annotation_type)
        except Exception:
            ann_type = AnnotationType.TREND_LINE

        return ChartAnnotation(
            id=model.id,
            trade_id=model.trade_id,
            timeframe=model.timeframe,
            annotation_type=ann_type,
            p1_time=model.p1_time,
            p1_price=model.p1_price,
            p2_time=model.p2_time,
            p2_price=model.p2_price,
            color=model.color,
            line_width=model.line_width,
            text=model.text or "",
            created_at=model.created_at
        )
