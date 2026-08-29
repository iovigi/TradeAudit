"""
Unit tests for BreakdownView UI component (Phase 9).
"""

from datetime import datetime
import pytest

from tradeaudit.domain.models import Trade
from tradeaudit.ui.views.breakdown_view import BreakdownView


def test_breakdown_view_instantiation(qtbot):
    view = BreakdownView()
    qtbot.addWidget(view)
    assert view is not None
    assert view.sub_tabs.count() == 3


def test_breakdown_view_set_trades(qtbot, sample_breakdown_trades):
    view = BreakdownView()
    qtbot.addWidget(view)
    view.set_trades(sample_breakdown_trades)

    # Verify tables populated
    assert view.symbol_table.rowCount() == 2
    assert view.direction_table.rowCount() == 2
    assert view.session_table.rowCount() == 5
    assert view.weekday_table.rowCount() == 7
    assert view.hour_table.rowCount() == 24
    assert view.context_table.rowCount() == 3
    assert view.streak_table.rowCount() == 7
    assert view.emotion_table.rowCount() == 3
