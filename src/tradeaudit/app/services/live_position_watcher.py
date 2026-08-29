"""
Live position watcher service for monitoring real-time MetaTrader 5 positions and modifications.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from tradeaudit.domain.models import (
    LivePosition,
    SLHistoryRecord,
    TPHistoryRecord,
    TradeEventRecord,
    TradeEventType
)
from tradeaudit.infrastructure.mt5.position_reader import MT5PositionReader
from tradeaudit.infrastructure.repositories.trade_event_repository import TradeEventRepository

logger = logging.getLogger("tradeaudit.app.services.live_position_watcher")


class LivePositionWatcherService:
    """Service to track open positions, detect live modifications (SL, TP, volume), and log lifecycle events."""

    def __init__(
        self,
        position_reader: Optional[MT5PositionReader] = None,
        event_repository: Optional[TradeEventRepository] = None,
        sync_service: Optional[object] = None
    ):
        self.position_reader = position_reader or MT5PositionReader()
        self.event_repository = event_repository
        self.sync_service = sync_service
        self._active_positions: Dict[int, LivePosition] = {}

    def poll_positions(self, account_id: int) -> List[LivePosition]:
        """
        Poll active positions from MT5, compare against previous state, and emit/persist modification events.

        :param account_id: MT5 account ID.
        :return: List of current active LivePosition domain objects.
        """
        try:
            current_positions = self.position_reader.fetch_open_positions(account_id=account_id)
        except Exception as e:
            logger.error("Failed to poll open positions for account %s: %s", account_id, e)
            return list(self._active_positions.values())

        current_by_id: Dict[int, LivePosition] = {p.position_id: p for p in current_positions}

        now = datetime.now(timezone.utc)

        # 1. Check for new positions and modifications to existing positions
        for pos_id, pos in current_by_id.items():
            pos.account_id = account_id
            if pos_id not in self._active_positions:
                # NEW POSITION DETECTED
                logger.info("New position detected: %s (symbol: %s, volume: %s)", pos_id, pos.symbol, pos.volume)
                self._record_event(
                    position_id=pos_id,
                    event_type=TradeEventType.POSITION_OPENED.value,
                    timestamp=pos.time or now,
                    details={
                        "symbol": pos.symbol,
                        "type": pos.type,
                        "volume": pos.volume,
                        "price_open": pos.price_open,
                        "initial_sl": pos.sl if pos.sl > 0 else None,
                        "initial_tp": pos.tp if pos.tp > 0 else None
                    }
                )
                if pos.sl > 0:
                    self._record_sl_change(pos_id, None, pos.sl, now, reason="INITIAL_SL")
                if pos.tp > 0:
                    self._record_tp_change(pos_id, None, pos.tp, now)

            else:
                # EXISTING POSITION - CHECK FOR MODIFICATIONS
                prev = self._active_positions[pos_id]

                # Check SL modification
                if abs(pos.sl - prev.sl) > 1e-6:
                    logger.info("Position %s SL modified: %s -> %s", pos_id, prev.sl, pos.sl)
                    reason = "SL_SET" if prev.sl == 0 else ("SL_MOVED_AWAY" if (pos.type == "BUY" and pos.sl < prev.sl) or (pos.type == "SELL" and pos.sl > prev.sl) else "SL_MODIFIED")
                    self._record_sl_change(pos_id, prev.sl, pos.sl, now, reason=reason)
                    self._record_event(
                        position_id=pos_id,
                        event_type=TradeEventType.SL_MODIFIED.value,
                        timestamp=now,
                        details={"old_sl": prev.sl, "new_sl": pos.sl, "reason": reason}
                    )

                # Check TP modification
                if abs(pos.tp - prev.tp) > 1e-6:
                    logger.info("Position %s TP modified: %s -> %s", pos_id, prev.tp, pos.tp)
                    self._record_tp_change(pos_id, prev.tp, pos.tp, now)
                    self._record_event(
                        position_id=pos_id,
                        event_type=TradeEventType.TP_MODIFIED.value,
                        timestamp=now,
                        details={"old_tp": prev.tp, "new_tp": pos.tp}
                    )

                # Check volume modification (partial close or scale in)
                if abs(pos.volume - prev.volume) > 1e-6:
                    event_type = TradeEventType.PARTIAL_CLOSE.value if pos.volume < prev.volume else TradeEventType.SCALE_IN.value
                    logger.info("Position %s volume changed (%s): %s -> %s", pos_id, event_type, prev.volume, pos.volume)
                    self._record_event(
                        position_id=pos_id,
                        event_type=event_type,
                        timestamp=now,
                        details={"old_volume": prev.volume, "new_volume": pos.volume}
                    )

        # 2. Check for closed positions (were active previously, missing now)
        closed_ids = set(self._active_positions.keys()) - set(current_by_id.keys())
        for closed_id in closed_ids:
            closed_pos = self._active_positions[closed_id]
            logger.info("Position closed: %s (symbol: %s)", closed_id, closed_pos.symbol)
            self._record_event(
                position_id=closed_id,
                event_type=TradeEventType.POSITION_CLOSED.value,
                timestamp=now,
                details={"symbol": closed_pos.symbol, "ticket": closed_pos.ticket}
            )

        # Trigger sync if positions closed
        if closed_ids and self.sync_service:
            try:
                logger.info("Position(s) closed. Triggering account sync for account %s...", account_id)
                if hasattr(self.sync_service, "sync_account_history"):
                    self.sync_service.sync_account_history(account_id)
            except Exception as e:
                logger.error("Failed to sync account history after position close: %s", e)

        # Update cache
        self._active_positions = current_by_id
        return list(self._active_positions.values())

    def get_active_positions(self) -> List[LivePosition]:
        """Return currently cached active positions."""
        return list(self._active_positions.values())

    def _record_event(self, position_id: int, event_type: str, timestamp: datetime, details: dict) -> None:
        if self.event_repository:
            record = TradeEventRecord(
                position_id=position_id,
                event_type=event_type,
                timestamp=timestamp,
                details=details
            )
            try:
                self.event_repository.save_trade_event(record)
            except Exception as e:
                logger.error("Failed to save trade event for position %s: %s", position_id, e)

    def _record_sl_change(self, position_id: int, old_sl: Optional[float], new_sl: float, timestamp: datetime, reason: Optional[str] = None) -> None:
        if self.event_repository:
            record = SLHistoryRecord(
                position_id=position_id,
                old_sl=old_sl,
                new_sl=new_sl,
                timestamp=timestamp,
                change_reason=reason
            )
            try:
                self.event_repository.save_sl_history(record)
            except Exception as e:
                logger.error("Failed to save SL history for position %s: %s", position_id, e)

    def _record_tp_change(self, position_id: int, old_tp: Optional[float], new_tp: float, timestamp: datetime) -> None:
        if self.event_repository:
            record = TPHistoryRecord(
                position_id=position_id,
                old_tp=old_tp,
                new_tp=new_tp,
                timestamp=timestamp
            )
            try:
                self.event_repository.save_tp_history(record)
            except Exception as e:
                logger.error("Failed to save TP history for position %s: %s", position_id, e)
