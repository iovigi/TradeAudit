"""
Settings repository for persisting non-sensitive MT5 settings into SQLite database.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from tradeaudit.domain.models import MT5Settings
from tradeaudit.infrastructure.database.connection import DatabaseManager
from tradeaudit.infrastructure.database.models import AppSettingsModel

logger = logging.getLogger("tradeaudit.infrastructure.repositories.settings_repository")

KEY_MT5_PATH = "mt5.path"
KEY_MT5_LOGIN = "mt5.login"
KEY_MT5_SERVER = "mt5.server"
KEY_MT5_TIMEOUT = "mt5.timeout_ms"


class SettingsRepository:
    """Repository for managing app settings in SQLite database."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save_mt5_settings(self, settings: MT5Settings) -> None:
        """Save or update MT5 settings in database."""
        with self.db_manager.session_scope() as session:
            self._set_setting(session, KEY_MT5_PATH, settings.mt5_path)
            self._set_setting(session, KEY_MT5_LOGIN, str(settings.login))
            self._set_setting(session, KEY_MT5_SERVER, settings.server)
            self._set_setting(session, KEY_MT5_TIMEOUT, str(settings.timeout_ms))
        logger.info("Saved MT5 settings to database (Login: %s, Server: %s).", settings.login, settings.server)

    def load_mt5_settings(self) -> Optional[MT5Settings]:
        """Load MT5 settings from database."""
        with self.db_manager.session_scope() as session:
            path = self._get_setting(session, KEY_MT5_PATH, "")
            login_str = self._get_setting(session, KEY_MT5_LOGIN, "0")
            server = self._get_setting(session, KEY_MT5_SERVER, "")
            timeout_str = self._get_setting(session, KEY_MT5_TIMEOUT, "60000")

            try:
                login = int(login_str) if login_str else 0
            except ValueError:
                login = 0

            try:
                timeout_ms = int(timeout_str) if timeout_str else 60000
            except ValueError:
                timeout_ms = 60000

            if not path and not login and not server:
                return None

            return MT5Settings(
                mt5_path=path,
                login=login,
                server=server,
                timeout_ms=timeout_ms
            )

    @staticmethod
    def _set_setting(session: Session, key: str, value: str) -> None:
        setting = session.query(AppSettingsModel).filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            session.add(AppSettingsModel(key=key, value=value))

    @staticmethod
    def _get_setting(session: Session, key: str, default: str = "") -> str:
        setting = session.query(AppSettingsModel).filter_by(key=key).first()
        return setting.value if setting and setting.value is not None else default
