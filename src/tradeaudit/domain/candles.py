"""
Domain models for Candlestick (OHLCV) market data and trade chart execution overlays.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple


class TimeFrame(str, Enum):
    """Supported candlestick chart timeframes."""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"

    @property
    def minutes(self) -> int:
        """Return duration of the timeframe in minutes."""
        mapping = {
            TimeFrame.M1: 1,
            TimeFrame.M5: 5,
            TimeFrame.M15: 15,
            TimeFrame.M30: 30,
            TimeFrame.H1: 60,
            TimeFrame.H4: 240,
            TimeFrame.D1: 1440,
            TimeFrame.W1: 10080,
        }
        return mapping.get(self, 15)

    @property
    def mt5_timeframe(self) -> int:
        """Map to MetaTrader5 TIMEFRAME constants if available."""
        try:
            import MetaTrader5 as mt5
            mapping = {
                TimeFrame.M1: mt5.TIMEFRAME_M1,
                TimeFrame.M5: mt5.TIMEFRAME_M5,
                TimeFrame.M15: mt5.TIMEFRAME_M15,
                TimeFrame.M30: mt5.TIMEFRAME_M30,
                TimeFrame.H1: mt5.TIMEFRAME_H1,
                TimeFrame.H4: mt5.TIMEFRAME_H4,
                TimeFrame.D1: mt5.TIMEFRAME_D1,
                TimeFrame.W1: mt5.TIMEFRAME_W1,
            }
            return mapping.get(self, 15)
        except Exception:
            # Fallback numeric constants from MT5 SDK
            fallback_map = {
                TimeFrame.M1: 1,
                TimeFrame.M5: 5,
                TimeFrame.M15: 15,
                TimeFrame.M30: 30,
                TimeFrame.H1: 16385,
                TimeFrame.H4: 16388,
                TimeFrame.D1: 16408,
                TimeFrame.W1: 32769,
            }
            return fallback_map.get(self, 15)


@dataclass(frozen=True)
class Candle:
    """Individual candlestick (OHLCV) bar."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    spread: int = 0

    @property
    def is_bullish(self) -> bool:
        return self.close >= self.open

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def total_range(self) -> float:
        return self.high - self.low


@dataclass
class TradeExecutionOverlay:
    """Rich execution overlay data to annotate a candlestick chart for a specific trade."""
    ticket: int
    symbol: str
    direction: str  # BUY / SELL
    entry_time: datetime
    entry_price: float
    volume: float
    
    initial_sl: Optional[float] = None
    initial_tp: Optional[float] = None
    
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    net_profit: Optional[float] = None
    realized_r: Optional[float] = None
    planned_rr: Optional[float] = None
    
    strategy_name: Optional[str] = None
    compliance_status: Optional[str] = None
    emotion_tag: Optional[str] = None
    
    # Modifications list of (timestamp, price)
    sl_modifications: List[Tuple[datetime, float]] = field(default_factory=list)
    tp_modifications: List[Tuple[datetime, float]] = field(default_factory=list)
    # Partial exits list of (timestamp, price, volume)
    partial_exits: List[Tuple[datetime, float, float]] = field(default_factory=list)
