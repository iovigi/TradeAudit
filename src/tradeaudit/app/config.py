"""
Application configuration management.
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import os

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


if HAS_PYDANTIC:
    class Settings(BaseSettings):
        app_name: str = "TradeAudit"
        app_version: str = "0.1.0"
        env: str = "development"
        debug: bool = True

        log_level: str = "INFO"
        log_dir: Path = field(default_factory=lambda: BASE_DIR / "logs")
        log_file_name: str = "tradeaudit.log"

        database_url: str = field(default_factory=lambda: f"sqlite:///{BASE_DIR / 'tradeaudit.db'}")
        
        model_config = SettingsConfigDict(
            env_prefix="TRADEAUDIT_",
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )
else:
    @dataclass
    class Settings:
        app_name: str = "TradeAudit"
        app_version: str = "0.1.0"
        env: str = os.getenv("TRADEAUDIT_ENV", "development")
        debug: bool = os.getenv("TRADEAUDIT_DEBUG", "True").lower() in ("true", "1")

        log_level: str = os.getenv("TRADEAUDIT_LOG_LEVEL", "INFO")
        log_dir: Path = field(default_factory=lambda: BASE_DIR / "logs")
        log_file_name: str = "tradeaudit.log"

        database_url: str = field(
            default_factory=lambda: os.getenv(
                "TRADEAUDIT_DATABASE_URL",
                f"sqlite:///{BASE_DIR / 'tradeaudit.db'}"
            )
        )


def get_settings() -> Settings:
    """Retrieve application settings instance."""
    settings = Settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    return settings
