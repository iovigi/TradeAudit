"""
QApplication wrapper for TradeAudit GUI.
"""

import sys
import logging
from typing import List, Optional
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from tradeaudit.app.config import Settings, get_resource_path
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

        # Set application icon if available
        icon_path = get_resource_path("resources/icons/tradeaudit.ico")
        if not icon_path.exists():
            icon_path = get_resource_path("resources/icons/tradeaudit.png")
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            self.qapp.setWindowIcon(app_icon)

        self.main_window = MainWindow(settings=self.settings, db_manager=self.db_manager)

    def run(self) -> int:
        """Start the Qt event loop."""
        logger.info("Displaying main window and starting Qt event loop...")
        self.main_window.show()
        return self.qapp.exec()
