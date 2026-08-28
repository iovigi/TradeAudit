"""
Unit tests for StrategyVsTraderView PySide6 GUI component (Phase 8).
"""

from datetime import datetime
import pytest

from tradeaudit.domain.models import Trade, ComplianceStatus, EmotionTag
from tradeaudit.ui.views.strategy_vs_trader_view import StrategyVsTraderView


def test_strategy_vs_trader_view_instantiation(qtbot):
    view = StrategyVsTraderView()
    qtbot.addWidget(view)
    assert view is not None
    assert view.comparison_table.columnCount() == 5
    assert view.comparison_table.rowCount() == 7


def test_strategy_vs_trader_view_set_trades(qtbot):
    view = StrategyVsTraderView()
    qtbot.addWidget(view)

    now = datetime.now()
    trades = [
        Trade(
            id=1, status="CLOSED", direction="BUY", profit=150.0,
            realized_r=1.5, compliance_status=ComplianceStatus.COMPLIANT.value,
            emotion_tag=EmotionTag.CALM.value, open_time=now, close_time=now
        ),
        Trade(
            id=2, status="CLOSED", direction="SELL", profit=-100.0,
            realized_r=-1.0, compliance_status=ComplianceStatus.DEVIATION.value,
            emotion_tag=EmotionTag.FOMO.value, open_time=now, close_time=now
        ),
    ]

    view.set_trades(trades)

    # Table item checks
    # Row 0: Closed Trades
    assert view.comparison_table.item(0, 1).text() == "2"  # All
    assert view.comparison_table.item(0, 2).text() == "1"  # Compliant
    assert view.comparison_table.item(0, 3).text() == "1"  # Deviations
    assert view.comparison_table.item(0, 4).text() == "1"  # Emotional

    # Row 3: Net R
    assert view.comparison_table.item(3, 1).text() == "+0.50 R"
    assert view.comparison_table.item(3, 2).text() == "+1.50 R"
    assert view.comparison_table.item(3, 3).text() == "-1.00 R"
    assert view.comparison_table.item(3, 4).text() == "-1.00 R"
