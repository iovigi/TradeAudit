"""
Domain models for MetaTrader 5 configuration and account information.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MT5Settings:
    """Configuration settings for MetaTrader 5 terminal connection."""
    mt5_path: str = ""
    login: int = 0
    server: str = ""
    timeout_ms: int = 60000


@dataclass
class MT5AccountInfo:
    """MetaTrader 5 Account State Information."""
    login: int = 0
    name: str = ""
    server: str = ""
    company: str = ""
    currency: str = "USD"
    leverage: int = 1
    balance: float = 0.0
    equity: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    trade_mode: str = "Demo"
