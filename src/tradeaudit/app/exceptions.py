"""
Core exception hierarchy and uncaught exception handling for TradeAudit.
"""

import logging
import sys
import traceback
from typing import Type, Optional
from types import TracebackType


logger = logging.getLogger("tradeaudit.exceptions")


class TradeAuditError(Exception):
    """Base exception class for all custom TradeAudit exceptions."""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class ConfigurationError(TradeAuditError):
    """Raised when application configuration is invalid or missing."""
    def __init__(self, message: str):
        super().__init__(message, code="CONFIG_ERROR")


class DatabaseInitializationError(TradeAuditError):
    """Raised when SQLite or SQLAlchemy database setup fails."""
    def __init__(self, message: str):
        super().__init__(message, code="DB_INIT_ERROR")


def handle_uncaught_exception(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[TracebackType]
) -> None:
    """Global exception hook to log unhandled exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical(
        "Unhandled exception encountered: %s",
        exc_value,
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def install_global_exception_handler() -> None:
    """Install the global exception handler into sys.excepthook."""
    sys.excepthook = handle_uncaught_exception
