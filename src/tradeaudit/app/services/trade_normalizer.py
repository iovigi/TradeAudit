"""
Normalizer service to map raw execution records to clean domain models.
"""

import logging
from typing import List, Dict, Any, Union
from datetime import datetime, timezone

from tradeaudit.domain.models import TradeDeal

logger = logging.getLogger("tradeaudit.app.services.trade_normalizer")


class TradeNormalizer:
    """Utility class to sanitize and convert raw deal data into TradeDeal instances."""

    @staticmethod
    def normalize_deal(deal_data: Union[TradeDeal, Dict[str, Any]]) -> TradeDeal:
        """
        Convert raw dictionary or TradeDeal into standardized TradeDeal instance.
        """
        if isinstance(deal_data, TradeDeal):
            return deal_data

        ticket = int(deal_data.get("ticket", 0))
        account_id = int(deal_data.get("account_id", 0))
        order_ticket = int(deal_data.get("order_ticket", deal_data.get("order", 0)))
        position_id = int(deal_data.get("position_id", 0))
        symbol = str(deal_data.get("symbol", "")).upper()
        
        deal_type = str(deal_data.get("type", "BUY")).upper()
        entry = str(deal_data.get("entry", "IN")).upper()

        raw_time = deal_data.get("time")
        if isinstance(raw_time, datetime):
            deal_time = raw_time
        elif isinstance(raw_time, (int, float)) and raw_time > 0:
            deal_time = datetime.fromtimestamp(raw_time, tz=timezone.utc)
        else:
            deal_time = datetime.now(timezone.utc)

        return TradeDeal(
            ticket=ticket,
            account_id=account_id,
            order_ticket=order_ticket,
            position_id=position_id,
            symbol=symbol,
            type=deal_type,
            entry=entry,
            time=deal_time,
            volume=float(deal_data.get("volume", 0.0)),
            price=float(deal_data.get("price", 0.0)),
            profit=float(deal_data.get("profit", 0.0)),
            swap=float(deal_data.get("swap", 0.0)),
            commission=float(deal_data.get("commission", 0.0)),
            fee=float(deal_data.get("fee", 0.0)),
            sl=float(deal_data.get("sl", 0.0)),
            tp=float(deal_data.get("tp", 0.0)),
            comment=str(deal_data.get("comment", "")),
            magic=int(deal_data.get("magic", 0))
        )

    @classmethod
    def normalize_deals(cls, deal_list: List[Union[TradeDeal, Dict[str, Any]]]) -> List[TradeDeal]:
        """Normalize a list of raw deals."""
        return [cls.normalize_deal(d) for d in deal_list]
