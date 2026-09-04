"""
Infrastructure service for fetching historical OHLCV candlestick data from MetaTrader 5,
with fallback deterministic candle generation for offline testing.
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False

from tradeaudit.domain.candles import Candle, TimeFrame

logger = logging.getLogger(__name__)


class MT5CandleReader:
    """Reads historical candlestick (OHLCV) rates from MT5 terminal."""

    def __init__(self, connection_service=None):
        self._connection_service = connection_service

    def is_connected(self) -> bool:
        """Check if MT5 connection is active."""
        if self._connection_service:
            return self._connection_service.is_connected
        if MT5_AVAILABLE and mt5 is not None:
            try:
                term_info = mt5.terminal_info()
                return term_info is not None and term_info.connected
            except Exception:
                return False
        return False

    def fetch_rates_range(
        self,
        symbol: str,
        timeframe: TimeFrame,
        date_from: datetime,
        date_to: datetime
    ) -> List[Candle]:
        """
        Fetch OHLCV candlestick bars for a symbol and timeframe between date_from and date_to.
        If MT5 is offline or fails, falls back to generating deterministic synthetic candles.
        """
        if self.is_connected() and MT5_AVAILABLE and mt5 is not None:
            try:
                # Ensure UTC datetime objects
                tf_constant = timeframe.mt5_timeframe
                rates = mt5.copy_rates_range(symbol, tf_constant, date_from, date_to)
                if rates is not None and len(rates) > 0:
                    candles: List[Candle] = []
                    for r in rates:
                        # r structure: ('time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume')
                        dt = datetime.fromtimestamp(r['time'], tz=timezone.utc)
                        candles.append(
                            Candle(
                                timestamp=dt,
                                open=float(r['open']),
                                high=float(r['high']),
                                low=float(r['low']),
                                close=float(r['close']),
                                volume=int(r['tick_volume']),
                                spread=int(r['spread']) if 'spread' in rates.dtype.names else 0
                            )
                        )
                    if candles:
                        logger.debug("Fetched %d candles from MT5 for %s %s", len(candles), symbol, timeframe.value)
                        return candles
            except Exception as e:
                logger.warning("MT5 copy_rates_range failed for %s (%s): %s. Using synthetic fallback.", symbol, timeframe.value, e)

        # Fallback synthetic generation
        return self.generate_synthetic_candles(
            symbol=symbol,
            timeframe=timeframe,
            date_from=date_from,
            date_to=date_to
        )

    def fetch_rates_around_trade(
        self,
        symbol: str,
        timeframe: TimeFrame,
        entry_time: datetime,
        exit_time: Optional[datetime],
        entry_price: float,
        exit_price: Optional[float] = None,
        bars_before: int = 40,
        bars_after: int = 25
    ) -> List[Candle]:
        """
        Fetch candlestick bars centered around a trade execution window.
        """
        tf_delta = timedelta(minutes=timeframe.minutes)
        start_time = entry_time - (tf_delta * bars_before)
        end_time = (exit_time or (entry_time + tf_delta * 10)) + (tf_delta * bars_after)

        candles = self.fetch_rates_range(symbol, timeframe, start_time, end_time)
        if not candles:
            candles = self.generate_synthetic_candles(
                symbol=symbol,
                timeframe=timeframe,
                date_from=start_time,
                date_to=end_time,
                anchor_price=entry_price,
                target_price=exit_price
            )
        return candles

    def generate_synthetic_candles(
        self,
        symbol: str,
        timeframe: TimeFrame,
        date_from: datetime,
        date_to: datetime,
        anchor_price: float = 1.1000,
        target_price: Optional[float] = None
    ) -> List[Candle]:
        """
        Generate realistic, deterministic synthetic candles for offline view or tests.
        """
        step = timedelta(minutes=timeframe.minutes)
        candles: List[Candle] = []
        
        current_time = date_from
        base_price = anchor_price if anchor_price > 0 else 1.1000
        volatility = base_price * 0.0008 * math.sqrt(max(1, timeframe.minutes / 15.0))
        
        total_steps = max(1, int((date_to - date_from).total_seconds() / step.total_seconds()))
        curr_p = base_price
        
        step_idx = 0
        while current_time <= date_to and len(candles) < 1000:
            # Deterministic wave oscillation + subtle drift towards target_price if provided
            wave = math.sin(step_idx * 0.3) * volatility * 1.2
            noise = math.cos(step_idx * 0.7) * (volatility * 0.5)
            
            if target_price and total_steps > 0:
                progress = min(1.0, step_idx / total_steps)
                drift_target = base_price + (target_price - base_price) * progress
                curr_p = (curr_p * 0.7) + (drift_target * 0.3)
            
            open_p = curr_p
            close_p = open_p + wave + noise
            high_p = max(open_p, close_p) + abs(math.sin(step_idx * 1.1)) * volatility * 0.6
            low_p = min(open_p, close_p) - abs(math.cos(step_idx * 0.9)) * volatility * 0.6
            
            # Ensure high >= low and valid range
            high_p = max(high_p, open_p, close_p)
            low_p = min(low_p, open_p, close_p)
            
            candles.append(
                Candle(
                    timestamp=current_time,
                    open=round(open_p, 5),
                    high=round(high_p, 5),
                    low=round(low_p, 5),
                    close=round(close_p, 5),
                    volume=int(100 + abs(math.sin(step_idx)) * 500),
                    spread=10
                )
            )
            
            curr_p = close_p
            current_time += step
            step_idx += 1

        return candles
