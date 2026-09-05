"""
Unit tests for ChartScreenshotService.
"""

from pathlib import Path
import pytest
from PySide6.QtWidgets import QLabel, QApplication

from tradeaudit.app.services.chart_screenshot_service import ChartScreenshotService


@pytest.fixture
def test_widget(qtbot):
    widget = QLabel("Chart Screenshot Test Widget")
    widget.resize(400, 300)
    qtbot.addWidget(widget)
    widget.show()
    return widget


def test_screenshot_capture_and_save(test_widget):
    target = Path("build/test_screenshots")
    target.mkdir(parents=True, exist_ok=True)
    service = ChartScreenshotService(target_dir=target)

    saved_path = service.capture_widget(
        widget=test_widget,
        ticket=123456,
        symbol="EUR/USD",
        timeframe="M15"
    )

    assert saved_path is not None
    assert saved_path.exists()
    assert saved_path.stat().st_size > 0
    assert "Trade_123456_EUR_USD_M15_" in saved_path.name
    assert saved_path.suffix.lower() == ".png"

    # Clean up file
    if saved_path.exists():
        saved_path.unlink()


def test_copy_widget_to_clipboard(test_widget):
    service = ChartScreenshotService()
    copied = service.copy_widget_to_clipboard(test_widget)
    assert copied is True
