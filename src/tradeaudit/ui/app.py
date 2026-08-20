"""
QApplication wrapper for TradeAudit GUI.
"""

import sys
import logging
from typing import List, Optional
from PySide6.QtWidgets import QApplication

from tradeaudit.app.config import Settings
from tradeaudit.infrastructure.database.connection import DatabaseManager
from tradeaudit.ui.main_window import MainWindow

logger = logging.getLogger("tradeaudit.ui.app")


class TradeAuditApplication:
    """Wrapper class managing Qt application lifecycle."""

    def __init__(self, settings: Settings, db_manager: DatabaseManager, args: Optional[List[str]] = None):
        self.settings = settings
        self.db_manager = db_manager
        self.qapp = QApplication.instance() or QApplication(args or sys.argv)
        self.qapp.setApplicationName(self.settings.app_name)
        self.qapp.setApplicationVersion(self.settings.app_version)

        self.main_window = MainWindow(settings=self.settings, db_manager=self.db_manager)

    def run(self) -> int:
        """Start the Qt event loop."""
        logger.info("Displaying main window and starting Qt event loop...")
        self.main_window.show()
        return self.qapp.exec()
