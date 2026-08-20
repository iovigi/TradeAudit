"""
Unit tests for PySide6 MainWindow GUI initialization.
"""

from tradeaudit.ui.main_window import MainWindow


def test_main_window_instantiation(qapp, test_settings, test_db_manager):
    window = MainWindow(settings=test_settings, db_manager=test_db_manager)
    assert window.windowTitle() == f"{test_settings.app_name} v{test_settings.app_version}"
    assert window.isVisible() is False
    assert "🟢 DB Connected" in window.db_label.text()
    window.close()
