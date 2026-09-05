"""
Unit tests for CandlestickChartWidget drawing tools and coordinate transformations.
"""

from datetime import datetime, timezone
import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent

from tradeaudit.domain.candles import Candle
from tradeaudit.domain.annotations import ChartAnnotation, AnnotationType
from tradeaudit.ui.widgets.candlestick_chart_widget import CandlestickChartWidget
from tradeaudit.ui.widgets.chart_drawing_toolbar import ChartDrawingToolbar


@pytest.fixture
def sample_candles():
    base = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    return [
        Candle(timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc), open=1.0800, high=1.0850, low=1.0790, close=1.0840, volume=100),
        Candle(timestamp=datetime(2026, 3, 1, 10, 15, tzinfo=timezone.utc), open=1.0840, high=1.0880, low=1.0830, close=1.0870, volume=150),
        Candle(timestamp=datetime(2026, 3, 1, 10, 30, tzinfo=timezone.utc), open=1.0870, high=1.0890, low=1.0820, close=1.0830, volume=200),
        Candle(timestamp=datetime(2026, 3, 1, 10, 45, tzinfo=timezone.utc), open=1.0830, high=1.0910, low=1.0825, close=1.0905, volume=250),
    ]


def test_chart_drawing_state_and_tools(qtbot, sample_candles):
    widget = CandlestickChartWidget()
    widget.resize(600, 400)
    qtbot.addWidget(widget)
    widget.show()

    widget.set_data(sample_candles)
    assert len(widget._visible_candles) == 4

    # Test tool selection
    widget.set_active_tool("TREND_LINE")
    assert widget._active_tool == "TREND_LINE"

    widget.set_draw_color("#ef5350")
    assert widget._draw_color == "#ef5350"

    widget.set_draw_line_width(4)
    assert widget._draw_line_width == 4


def test_chart_annotations_management(qtbot, sample_candles):
    widget = CandlestickChartWidget()
    widget.resize(600, 400)
    qtbot.addWidget(widget)
    widget.show()

    widget.set_data(sample_candles)

    ann1 = ChartAnnotation(
        id=1,
        trade_id=99,
        annotation_type=AnnotationType.TREND_LINE,
        p1_time=sample_candles[0].timestamp,
        p1_price=1.0800,
        p2_time=sample_candles[3].timestamp,
        p2_price=1.0900,
        color="#58a6ff"
    )
    ann2 = ChartAnnotation(
        id=2,
        trade_id=99,
        annotation_type=AnnotationType.RECTANGLE_ZONE,
        p1_time=sample_candles[1].timestamp,
        p1_price=1.0830,
        p2_time=sample_candles[2].timestamp,
        p2_price=1.0880,
        color="#26a69a"
    )

    widget.set_annotations([ann1, ann2])
    assert len(widget.get_annotations()) == 2

    # Clear
    widget.clear_annotations()
    assert len(widget.get_annotations()) == 0


def test_drawing_toolbar_signals(qtbot):
    toolbar = ChartDrawingToolbar()
    qtbot.addWidget(toolbar)

    tool_emitted = []
    color_emitted = []
    clear_emitted = []

    toolbar.toolChanged.connect(tool_emitted.append)
    toolbar.colorChanged.connect(color_emitted.append)
    toolbar.clearRequested.connect(lambda: clear_emitted.append(True))

    # Click a tool button
    for btn in toolbar.tool_group.buttons():
        if btn.property("tool_id") == "RECTANGLE_ZONE":
            btn.click()
            break

    assert "RECTANGLE_ZONE" in tool_emitted

    # Click a color button
    for btn in toolbar.color_group.buttons():
        if btn.property("color_hex") == "#ef5350":
            btn.click()
            break

    assert "#ef5350" in color_emitted
