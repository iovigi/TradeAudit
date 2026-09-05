"""
Service for capturing, naming, saving, and copying high-resolution candlestick chart snapshots.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtGui import QPixmap, QClipboard, QGuiApplication
from PySide6.QtWidgets import QWidget

from tradeaudit.app.config import get_settings

logger = logging.getLogger(__name__)


class ChartScreenshotService(QObject):
    """Handles chart screenshot capturing, filesystem persistence, and clipboard export."""

    def __init__(self, target_dir: Optional[Path] = None):
        super().__init__()
        settings = get_settings()
        self.target_dir = target_dir or settings.screenshots_dir
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def capture_widget(
        self,
        widget: QWidget,
        ticket: int,
        symbol: str,
        timeframe: str = "M15",
        custom_suffix: str = ""
    ) -> Optional[Path]:
        """
        Capture a screenshot of the specified chart widget and save it to the screenshots directory.
        """
        try:
            pixmap = widget.grab()
            if pixmap.isNull():
                logger.error("Failed to capture widget screenshot: grabbed pixmap is null")
                return None

            now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            suffix_part = f"_{custom_suffix}" if custom_suffix else ""
            clean_symbol = symbol.replace("/", "_").replace("\\", "_")
            filename = f"Trade_{ticket}_{clean_symbol}_{timeframe}_{now_str}{suffix_part}.png"
            file_path = self.target_dir / filename

            saved = pixmap.save(str(file_path), "PNG")
            if saved:
                logger.info(f"Chart screenshot saved successfully to {file_path}")
                return file_path
            else:
                logger.error(f"Failed to save chart screenshot to {file_path}")
                return None
        except Exception as e:
            logger.error(f"Error capturing chart screenshot: {e}", exc_info=True)
            return None

    def copy_widget_to_clipboard(self, widget: QWidget) -> bool:
        """
        Grab the widget pixmap and copy it directly to the system clipboard.
        """
        try:
            pixmap = widget.grab()
            if pixmap.isNull():
                return False

            clipboard = QGuiApplication.clipboard()
            if clipboard:
                clipboard.setPixmap(pixmap, QClipboard.Clipboard)
                logger.info("Chart screenshot copied to clipboard")
                return True
            return False
        except Exception as e:
            logger.error(f"Error copying chart to clipboard: {e}", exc_info=True)
            return False
