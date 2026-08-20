"""
MetaTrader 5 connection service wrapping official MetaTrader5 Python API.
"""

import logging
from enum import Enum
from typing import Optional

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    mt5 = None
    HAS_MT5 = False

from tradeaudit.domain.models import MT5AccountInfo
from tradeaudit.app.exceptions import MT5ConnectionError, MT5AuthError, MT5Error

logger = logging.getLogger("tradeaudit.infrastructure.mt5.connection_service")


class ConnectionState(Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


class MT5ConnectionService:
    """Service to initialize, manage, and query MetaTrader 5 terminal connection."""

    def __init__(self):
        self._state = ConnectionState.DISCONNECTED
        self._last_error_message: Optional[str] = None
        self._cached_account_info: Optional[MT5AccountInfo] = None

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def last_error(self) -> Optional[str]:
        """Last error message encountered."""
        return self._last_error_message

    def is_connected(self) -> bool:
        """Check if active connection to MT5 terminal is established."""
        if not HAS_MT5 or self._state != ConnectionState.CONNECTED:
            return False
        try:
            terminal_info = mt5.terminal_info()
            return terminal_info is not None and getattr(terminal_info, "connected", False)
        except Exception:
            return False

    def connect(
        self,
        mt5_path: str,
        login: int,
        password: str,
        server: str,
        timeout_ms: int = 60000
    ) -> MT5AccountInfo:
        """Connect to MT5 terminal using provided credentials."""
        if not HAS_MT5 or mt5 is None:
            self._state = ConnectionState.ERROR
            self._last_error_message = "MetaTrader5 package is not installed."
            raise MT5ConnectionError(self._last_error_message)

        if not login:
            self._state = ConnectionState.ERROR
            self._last_error_message = "Invalid MT5 account number (login cannot be 0)."
            raise MT5AuthError(self._last_error_message)

        self._state = ConnectionState.CONNECTING
        logger.info("Connecting to MT5 (Login: %s, Server: %s, Path: %s)...", login, server, mt5_path)

        kwargs = {
            "login": login,
            "password": password,
            "server": server,
            "timeout": timeout_ms
        }
        if mt5_path:
            kwargs["path"] = mt5_path

        initialized = False
        try:
            initialized = mt5.initialize(**kwargs)
        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error_message = f"MT5 initialization exception: {e}"
            logger.error("MT5 initialization failed for account %s: %s", login, self._last_error_message)
            raise MT5ConnectionError(self._last_error_message) from e

        if not initialized:
            error_code, error_msg = mt5.last_error()
            self._state = ConnectionState.ERROR
            self._last_error_message = f"MT5 initialize failed (code {error_code}): {error_msg}"
            logger.error("Failed to connect MT5 for account %s: %s", login, self._last_error_message)

            if error_code in (-5, -6, 10004, 10013, 10015):
                raise MT5AuthError(f"Authentication failed: {error_msg} (code {error_code})")
            else:
                raise MT5ConnectionError(self._last_error_message)

        # Connection successful -> fetch account info
        try:
            account_info = self.get_account_info()
            self._state = ConnectionState.CONNECTED
            self._last_error_message = None
            self._cached_account_info = account_info
            logger.info("Successfully connected to MT5 account %s on %s.", login, server)
            return account_info
        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error_message = f"Connected but failed to fetch account info: {e}"
            mt5.shutdown()
            raise MT5Error(self._last_error_message) from e

    def disconnect(self) -> None:
        """Disconnect from MT5 terminal."""
        if HAS_MT5 and mt5 is not None:
            try:
                mt5.shutdown()
            except Exception as e:
                logger.warning("Error during MT5 shutdown: %s", e)
        self._state = ConnectionState.DISCONNECTED
        self._cached_account_info = None
        logger.info("MT5 connection disconnected.")

    def get_account_info(self) -> MT5AccountInfo:
        """Fetch account state from MT5."""
        if not HAS_MT5 or mt5 is None:
            raise MT5ConnectionError("MetaTrader5 package is not available.")

        raw_info = mt5.account_info()
        if raw_info is None:
            error_code, error_msg = mt5.last_error()
            raise MT5Error(f"Failed to fetch account info from MT5 (code {error_code}): {error_msg}")

        info_dict = raw_info._asdict() if hasattr(raw_info, "_asdict") else {}

        # Trade mode mapping
        trade_mode_val = info_dict.get("trade_mode", 0)
        mode_map = {0: "Demo", 1: "Contest", 2: "Real"}
        trade_mode_str = mode_map.get(trade_mode_val, "Demo")

        account_info = MT5AccountInfo(
            login=info_dict.get("login", getattr(raw_info, "login", 0)),
            name=info_dict.get("name", getattr(raw_info, "name", "")),
            server=info_dict.get("server", getattr(raw_info, "server", "")),
            company=info_dict.get("company", getattr(raw_info, "company", "")),
            currency=info_dict.get("currency", getattr(raw_info, "currency", "USD")),
            leverage=info_dict.get("leverage", getattr(raw_info, "leverage", 1)),
            balance=float(info_dict.get("balance", getattr(raw_info, "balance", 0.0))),
            equity=float(info_dict.get("equity", getattr(raw_info, "equity", 0.0))),
            profit=float(info_dict.get("profit", getattr(raw_info, "profit", 0.0))),
            margin=float(info_dict.get("margin", getattr(raw_info, "margin", 0.0))),
            margin_free=float(info_dict.get("margin_free", getattr(raw_info, "margin_free", 0.0))),
            margin_level=float(info_dict.get("margin_level", getattr(raw_info, "margin_level", 0.0))),
            trade_mode=trade_mode_str
        )
        self._cached_account_info = account_info
        return account_info
