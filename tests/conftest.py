"""
Pytest global fixtures for TradeAudit testing.
"""

import tempfile
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from tradeaudit.app.config import Settings
from tradeaudit.infrastructure.database.connection import DatabaseManager


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test isolation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
        # Teardown: close logging handlers to release file handles on Windows
        from tradeaudit.app.logging import close_logging
        close_logging()


@pytest.fixture
def test_settings(temp_dir):
    """Provide isolated test settings with temporary file paths."""
    db_path = temp_dir / "test_tradeaudit.db"
    settings = Settings(
        app_name="TradeAuditTest",
        app_version="0.1.0-test",
        env="testing",
        debug=True,
        log_level="DEBUG",
        log_dir=temp_dir / "logs",
        log_file_name="test.log",
        database_url=f"sqlite:///{db_path}"
    )
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    return settings


@pytest.fixture
def test_db_manager(test_settings):
    """Provide initialized DatabaseManager backed by temp SQLite file."""
    manager = DatabaseManager(test_settings)
    manager.init_db()
    yield manager
    manager.close()

