"""
Application service for preparing candlestick data and execution overlays for trade visualization.
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from tradeaudit.domain.candles import Candle, TimeFrame, TradeExecutionOverlay
from tradeaudit.domain.models import Trade
from tradeaudit.infrastructure.mt5.candle_reader import MT5CandleReader
from tradeaudit.infrastructure.repositories.trade_event_repository import TradeEventRepository

logger = logging.getLogger(__name__)


class TradeChartService:
    """Coordinates candle data fetching and trade execution annotations."""

    def __init__(
        self,
        candle_reader: Optional[MT5CandleReader] = None,
        trade_event_repository: Optional[TradeEventRepository] = None
    ):
        self.candle_reader = candle_reader or MT5CandleReader()
        self.trade_event_repository = trade_event_repository
        # In-memory cache: (trade_id, timeframe) -> List[Candle]
        self._candle_cache = {}

    def build_overlay(self, trade: Trade) -> TradeExecutionOverlay:
        """Construct the TradeExecutionOverlay model for the given Trade."""
        sl_mods: List[Tuple[datetime, float]] = []
        tp_mods: List[Tuple[datetime, float]] = []

        if self.trade_event_repository and trade.position_id:
            try:
                sl_records = self.trade_event_repository.get_sl_history_for_position(trade.position_id)
                for rec in sl_records:
                    if rec.timestamp and rec.new_sl is not None:
                        sl_mods.append((rec.timestamp, float(rec.new_sl)))

                tp_records = self.trade_event_repository.get_tp_history_for_position(trade.position_id)
                for rec in tp_records:
                    if rec.timestamp and rec.new_tp is not None:
                        tp_mods.append((rec.timestamp, float(rec.new_tp)))
            except Exception as e:
                logger.warning("Could not load SL/TP history for position %s: %s", trade.position_id, e)

        compliance_tag = None
        if hasattr(trade, 'compliance_status') and trade.compliance_status:
            compliance_tag = getattr(trade.compliance_status, 'value', str(trade.compliance_status))

        emotion_tag = None
        if hasattr(trade, 'emotion_tag') and trade.emotion_tag:
            emotion_tag = getattr(trade.emotion_tag, 'value', str(trade.emotion_tag))

        return TradeExecutionOverlay(
            ticket=trade.position_id or trade.id or 0,
            symbol=trade.symbol,
            direction=trade.direction.upper(),
            entry_time=trade.open_time,
            entry_price=trade.open_price,
            volume=trade.volume,
            initial_sl=trade.initial_sl,
            initial_tp=trade.initial_tp,
            exit_time=trade.close_time,
            exit_price=trade.close_price,
            net_profit=trade.profit,
            realized_r=trade.realized_r,
            planned_rr=trade.planned_rr,
            strategy_name=getattr(trade, 'strategy_name', None),
            compliance_status=compliance_tag,
            emotion_tag=emotion_tag,
            sl_modifications=sl_mods,
            tp_modifications=tp_mods
        )

    def get_candles_for_trade(
        self,
        trade: Trade,
        timeframe: TimeFrame = TimeFrame.M15,
        bars_before: int = 40,
        bars_after: int = 25,
        force_refresh: bool = False
    ) -> List[Candle]:
        """
        Fetch candlestick bars for a given trade and timeframe.
        Caches results in memory for smooth UI switching.
        """
        cache_key = (trade.position_id or trade.id or 0, timeframe.value)
        if not force_refresh and cache_key in self._candle_cache:
            return self._candle_cache[cache_key]

        candles = self.candle_reader.fetch_rates_around_trade(
            symbol=trade.symbol,
            timeframe=timeframe,
            entry_time=trade.open_time,
            exit_time=trade.close_time,
            entry_price=trade.open_price,
            exit_price=trade.close_price,
            bars_before=bars_before,
            bars_after=bars_after
        )

        self._candle_cache[cache_key] = candles
        return candles

    def clear_cache(self) -> None:
        """Clear the cached candles."""
        self._candle_cache.clear()
