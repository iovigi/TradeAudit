"""
Unit tests for AnnotationRepository persistence of candlestick chart drawings.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tradeaudit.infrastructure.database.models import Base
from tradeaudit.infrastructure.repositories.annotation_repository import AnnotationRepository
from tradeaudit.domain.annotations import ChartAnnotation, AnnotationType


@pytest.fixture
def db_session_factory():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


def test_save_and_get_annotation(db_session_factory):
    repo = AnnotationRepository(db_session_factory)

    t1 = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 1, 11, 30, tzinfo=timezone.utc)

    ann = ChartAnnotation(
        trade_id=101,
        timeframe="M15",
        annotation_type=AnnotationType.TREND_LINE,
        p1_time=t1,
        p1_price=1.0850,
        p2_time=t2,
        p2_price=1.0920,
        color="#26a69a",
        line_width=3,
        text="Bullish Trendline"
    )

    saved = repo.save_annotation(ann)
    assert saved.id is not None
    assert saved.trade_id == 101
    assert saved.timeframe == "M15"
    assert saved.annotation_type == AnnotationType.TREND_LINE
    assert saved.p1_price == 1.0850
    assert saved.p2_price == 1.0920
    assert saved.color == "#26a69a"
    assert saved.line_width == 3
    assert saved.text == "Bullish Trendline"

    # Query back
    results = repo.get_annotations_for_trade(101, "M15")
    assert len(results) == 1
    assert results[0].id == saved.id
    assert results[0].text == "Bullish Trendline"


def test_update_annotation(db_session_factory):
    repo = AnnotationRepository(db_session_factory)

    ann = ChartAnnotation(
        trade_id=102,
        timeframe="H1",
        annotation_type=AnnotationType.RECTANGLE_ZONE,
        p1_time=datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc),
        p1_price=1.0800,
        p2_time=datetime(2026, 3, 1, 16, 0, tzinfo=timezone.utc),
        p2_price=1.0830,
        color="#f59e0b",
        text="Demand Zone"
    )
    saved = repo.save_annotation(ann)

    # Update price and text
    saved.p2_price = 1.0840
    saved.text = "Expanded Demand Zone"
    updated = repo.save_annotation(saved)

    assert updated.id == saved.id
    assert updated.p2_price == 1.0840
    assert updated.text == "Expanded Demand Zone"

    results = repo.get_annotations_for_trade(102, "H1")
    assert len(results) == 1
    assert results[0].p2_price == 1.0840


def test_delete_and_clear_annotations(db_session_factory):
    repo = AnnotationRepository(db_session_factory)

    ann1 = ChartAnnotation(trade_id=103, timeframe="M15", annotation_type=AnnotationType.ARROW_UP, p1_price=1.0900)
    ann2 = ChartAnnotation(trade_id=103, timeframe="M15", annotation_type=AnnotationType.ARROW_DOWN, p1_price=1.0950)
    ann3 = ChartAnnotation(trade_id=103, timeframe="H4", annotation_type=AnnotationType.HORIZONTAL_RAY, p1_price=1.1000)

    s1 = repo.save_annotation(ann1)
    s2 = repo.save_annotation(ann2)
    s3 = repo.save_annotation(ann3)

    assert len(repo.get_annotations_for_trade(103)) == 3

    # Delete single annotation
    deleted = repo.delete_annotation(s1.id)
    assert deleted is True
    assert len(repo.get_annotations_for_trade(103, "M15")) == 1

    # Clear M15 annotations
    cleared = repo.clear_annotations_for_trade(103, "M15")
    assert cleared == 1
    assert len(repo.get_annotations_for_trade(103, "M15")) == 0
    # H4 remains
    assert len(repo.get_annotations_for_trade(103, "H4")) == 1
