"""
Unit tests for SettingsRepository using temporary SQLite database.
"""

from tradeaudit.domain.models import MT5Settings
from tradeaudit.infrastructure.repositories.settings_repository import SettingsRepository


def test_settings_repository_save_and_load(test_db_manager):
    repo = SettingsRepository(test_db_manager)

    # Initial load when empty
    assert repo.load_mt5_settings() is None

    # Save settings
    original_settings = MT5Settings(
        mt5_path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        login=99887766,
        server="MetaQuotes-Demo",
        timeout_ms=30000
    )
    repo.save_mt5_settings(original_settings)

    # Reload settings
    loaded_settings = repo.load_mt5_settings()
    assert loaded_settings is not None
    assert loaded_settings.mt5_path == original_settings.mt5_path
    assert loaded_settings.login == original_settings.login
    assert loaded_settings.server == original_settings.server
    assert loaded_settings.timeout_ms == original_settings.timeout_ms


def test_settings_repository_update_existing(test_db_manager):
    repo = SettingsRepository(test_db_manager)

    settings_v1 = MT5Settings(mt5_path="C:\\mt5\\terminal64.exe", login=111, server="Server1", timeout_ms=5000)
    repo.save_mt5_settings(settings_v1)

    settings_v2 = MT5Settings(mt5_path="C:\\mt5_v2\\terminal64.exe", login=222, server="Server2", timeout_ms=10000)
    repo.save_mt5_settings(settings_v2)

    loaded = repo.load_mt5_settings()
    assert loaded.login == 222
    assert loaded.server == "Server2"
    assert loaded.mt5_path == "C:\\mt5_v2\\terminal64.exe"
    assert loaded.timeout_ms == 10000
