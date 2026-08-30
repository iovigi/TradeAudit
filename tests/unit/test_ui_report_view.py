"""
Unit tests for ReportView UI component (Phase 11).
"""

from datetime import datetime, timedelta
import pytest
from PySide6.QtCore import Qt

from tradeaudit.domain.models import (
    Trade,
    MT5AccountInfo,
    Strategy,
    ComplianceStatus,
    EmotionTag
)
from tradeaudit.ui.views.report_view import ReportView


@pytest.fixture
def sample_ui_trades() -> list[Trade]:
    base_time = datetime(2026, 8, 25, 10, 0, 0)
    return [
        Trade(
            id=1,
            account_id=1234567,
            position_id=9001,
            symbol="EURUSD",
            direction="BUY",
            volume=1.0,
            open_time=base_time,
            close_time=base_time + timedelta(hours=2),
            open_price=1.1000,
            close_price=1.1040,
            initial_sl=1.0980,
            initial_tp=1.1060,
            profit=400.0,
            status="CLOSED",
            monetary_risk=200.0,
            realized_r=2.0,
            risk_percentage=1.0,
            strategy_id=1,
            compliance_status=ComplianceStatus.COMPLIANT.value,
            emotion_tag=EmotionTag.CALM.value
        ),
        Trade(
            id=2,
            account_id=1234567,
            position_id=9002,
            symbol="GBPUSD",
            direction="SELL",
            volume=1.0,
            open_time=base_time + timedelta(days=1),
            close_time=base_time + timedelta(days=1, hours=1),
            open_price=1.3000,
            close_price=1.3030,
            initial_sl=1.3020,
            initial_tp=1.2940,
            profit=-300.0,
            status="CLOSED",
            monetary_risk=200.0,
            realized_r=-1.5,
            risk_percentage=1.0,
            strategy_id=1,
            compliance_status=ComplianceStatus.DEVIATION.value,
            deviation_reason="MAX_RISK_PERCENT violated",
            emotion_tag=EmotionTag.REVENGE.value
        )
    ]


def test_report_view_instantiation(qtbot):
    view = ReportView()
    qtbot.addWidget(view)
    assert view is not None
    assert view.depth_combo.count() == 3
    assert view.btn_generate is not None
    assert view.btn_copy is not None
    assert view.btn_export is not None


def test_report_view_set_trades_and_generate(qtbot, sample_ui_trades):
    view = ReportView()
    qtbot.addWidget(view)

    account = MT5AccountInfo(login=1234567, name="Test User", server="DemoServer")
    strategies = [Strategy(id=1, name="Trend Strategy")]

    view.set_strategies(strategies)
    view.set_trades(sample_ui_trades, account_info=account)

    text = view.text_preview.toPlainText()
    assert "---" in text
    assert "report_version: 1" in text
    assert "EURUSD" in text
    assert "GBPUSD" in text
    assert "Targeted AI Audit Questions" in text


def test_report_view_clipboard_copy(qtbot, sample_ui_trades):
    view = ReportView()
    qtbot.addWidget(view)
    view.set_trades(sample_ui_trades)

    # Click copy to clipboard
    qtbot.mouseClick(view.btn_copy, Qt.LeftButton)
    assert "Copied to clipboard" in view.status_feedback.text()


def test_report_view_filter_changes(qtbot, sample_ui_trades):
    view = ReportView()
    qtbot.addWidget(view)
    view.set_trades(sample_ui_trades)

    # Change direction combo to BUY
    idx = view.direction_combo.findText("BUY")
    view.direction_combo.setCurrentIndex(idx)
    view.generate_report()

    text = view.text_preview.toPlainText()
    assert "direction: 'BUY'" in text
    assert "1 Closed Trades" in text
