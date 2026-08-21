"""
Trade aggregator service to group raw MT5 deals into logical Trade entities.
"""

import logging
from collections import defaultdict
from typing import List, Dict
from datetime import datetime

from tradeaudit.domain.models import TradeDeal, Trade
from tradeaudit.app.services.trade_normalizer import TradeNormalizer

logger = logging.getLogger("tradeaudit.app.services.trade_aggregator")


class TradeAggregator:
    """Aggregates raw deal execution records into logical Trade entities by position ID."""

    def aggregate_deals(self, deals: List[TradeDeal]) -> List[Trade]:
        """
        Group deals by position_id and convert them into logical domain Trade entities.

        :param deals: List of TradeDeal objects.
        :return: List of aggregated Trade domain objects.
        """
        normalized_deals = TradeNormalizer.normalize_deals(deals)
        
        # 1. Filter out balance/credit non-position deals
        position_deals = [
            d for d in normalized_deals
            if d.position_id > 0 and d.type in ("BUY", "SELL")
        ]

        if not position_deals:
            logger.info("No position deals found to aggregate.")
            return []

        # 2. Group deals by position_id
        grouped: Dict[int, List[TradeDeal]] = defaultdict(list)
        for deal in position_deals:
            grouped[deal.position_id].append(deal)

        aggregated_trades: List[Trade] = []

        # 3. Aggregate each position group into a Trade
        for position_id, pos_deals in grouped.items():
            # Sort chronologically by time, then ticket
            sorted_deals = sorted(pos_deals, key=lambda d: (d.time or datetime.min, d.ticket))

            entry_deals = [d for d in sorted_deals if d.entry in ("IN", "INOUT")]
            exit_deals = [d for d in sorted_deals if d.entry in ("OUT", "OUT_BY")]

            first_deal = sorted_deals[0]
            first_entry = entry_deals[0] if entry_deals else first_deal

            account_id = first_deal.account_id
            symbol = first_deal.symbol
            direction = "BUY" if first_entry.type == "BUY" else "SELL"

            open_time = first_entry.time
            
            # Initial SL / TP from earliest entry deal
            initial_sl = first_entry.sl if first_entry.sl > 0 else None
            initial_tp = first_entry.tp if first_entry.tp > 0 else None

            # Calculate volume-weighted open price
            total_entry_volume = sum(d.volume for d in entry_deals) if entry_deals else sum(d.volume for d in sorted_deals)
            entry_cost = sum(d.volume * d.price for d in entry_deals) if entry_deals else sum(d.volume * d.price for d in sorted_deals)
            open_price = (entry_cost / total_entry_volume) if total_entry_volume > 0 else first_deal.price

            # Calculate volume-weighted close price
            total_exit_volume = sum(d.volume for d in exit_deals)
            exit_cost = sum(d.volume * d.price for d in exit_deals)
            close_price = (exit_cost / total_exit_volume) if total_exit_volume > 0 else None

            # Sum financial metrics
            total_profit = sum(d.profit for d in sorted_deals)
            total_swap = sum(d.swap for d in sorted_deals)
            total_commission = sum(d.commission for d in sorted_deals)
            total_fee = sum(d.fee for d in sorted_deals)

            # Determine trade status
            is_closed = (total_exit_volume >= total_entry_volume - 1e-6) and bool(exit_deals)
            status = "CLOSED" if is_closed else "OPEN"
            close_time = exit_deals[-1].time if (is_closed and exit_deals) else None

            trade = Trade(
                id=None,
                account_id=account_id,
                position_id=position_id,
                symbol=symbol,
                direction=direction,
                volume=round(total_entry_volume, 4),
                open_time=open_time,
                close_time=close_time,
                open_price=round(open_price, 6),
                close_price=round(close_price, 6) if close_price is not None else None,
                initial_sl=initial_sl,
                initial_tp=initial_tp,
                profit=round(total_profit, 2),
                swap=round(total_swap, 2),
                commission=round(total_commission, 2),
                fee=round(total_fee, 2),
                status=status,
                deals=sorted_deals
            )
            aggregated_trades.append(trade)

        # Sort aggregated trades by open_time descending for UI presentation
        aggregated_trades.sort(key=lambda t: t.open_time or datetime.min, reverse=True)
        logger.info("Aggregated %d raw deals into %d logical trades.", len(position_deals), len(aggregated_trades))
        return aggregated_trades
