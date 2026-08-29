"""
MetaTrader 5 position reader for fetching currently active open positions.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    mt5 = None
    HAS_MT5 = False

from tradeaudit.domain.models import LivePosition
from tradeaudit.app.exceptions import MT5Error, MT5ConnectionError

logger = logging.getLogger("tradeaudit.infrastructure.mt5.position_reader")


class MT5PositionReader:
    """Service to query live open positions directly from MetaTrader 5 terminal."""

    POSITION_TYPE_MAP = {
        0: "BUY",
        1: "SELL"
    }

    def fetch_open_positions(self, account_id: Optional[int] = None, symbol: Optional[str] = None) -> List[LivePosition]:
        """
        Fetch active open positions from MT5.

        :param account_id: Optional login account filter.
        :param symbol: Optional symbol filter.
        :return: List of LivePosition domain objects.
        """
        if not HAS_MT5 or mt5 is None:
            logger.warning("MetaTrader5 python package not available.")
            raise MT5ConnectionError("MetaTrader5 package is not available.")

        try:
            if symbol:
                raw_positions = mt5.positions_get(symbol=symbol)
            else:
                raw_positions = mt5.positions_get()
        except Exception as e:
            logger.error("Exception occurred while calling mt5.positions_get: %s", e)
            raise MT5Error(f"Failed to fetch MT5 open positions: {e}") from e

        if raw_positions is None:
            error_code, error_msg = mt5.last_error()
            # If no positions are open, MT5 might return None or empty tuple depending on version/state.
            # Code 1 means success but no positions, or last_error 0 means no error.
            if error_code in (0, 1):
                return []
            logger.warning("mt5.positions_get returned None (code %s): %s", error_code, error_msg)
            return []

        live_positions: List[LivePosition] = []
        for p in raw_positions:
            pos_dict = p._asdict() if hasattr(p, "_asdict") else {}

            ticket = int(pos_dict.get("ticket", getattr(p, "ticket", 0)))
            position_id = int(pos_dict.get("identifier", getattr(p, "identifier", ticket))) or ticket
            pos_symbol = str(pos_dict.get("symbol", getattr(p, "symbol", "")))

            raw_type = int(pos_dict.get("type", getattr(p, "type", 0)))
            type_str = self.POSITION_TYPE_MAP.get(raw_type, "BUY" if raw_type == 0 else "SELL")

            volume = float(pos_dict.get("volume", getattr(p, "volume", 0.0)))
            price_open = float(pos_dict.get("price_open", getattr(p, "price_open", 0.0)))
            sl = float(pos_dict.get("sl", getattr(p, "sl", 0.0)))
            tp = float(pos_dict.get("tp", getattr(p, "tp", 0.0)))
            profit = float(pos_dict.get("profit", getattr(p, "profit", 0.0)))
            swap = float(pos_dict.get("swap", getattr(p, "swap", 0.0)))

            timestamp = int(pos_dict.get("time", getattr(p, "time", 0)))
            pos_time = datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp > 0 else datetime.now(timezone.utc)
            magic = int(pos_dict.get("magic", getattr(p, "magic", 0)))

            pos = LivePosition(
                ticket=ticket,
                account_id=account_id or 0,
                position_id=position_id,
                symbol=pos_symbol,
                type=type_str,
                volume=volume,
                price_open=price_open,
                sl=sl,
                tp=tp,
                profit=profit,
                swap=swap,
                time=pos_time,
                magic=magic
            )
            live_positions.append(pos)

        logger.debug("Fetched %d open positions from MT5.", len(live_positions))
        return live_positions
