"""
Risk calculation engine for determining price risk, monetary risk ($), and risk percentage.
"""

from typing import Optional
from tradeaudit.domain.models import Trade


class RiskCalculator:
    """Service for computing price risk, monetary risk, and account risk percentage."""

    @staticmethod
    def calculate_price_risk(
        direction: str,
        open_price: float,
        initial_sl: Optional[float] = None,
    ) -> Optional[float]:
        """
        Calculate absolute price risk (|Entry - InitialSL|).

        Returns:
            Optional[float]: Price risk delta or None if SL is not defined/zero.
        """
        if initial_sl is None or initial_sl <= 0:
            return None
        return abs(open_price - initial_sl)

    @staticmethod
    def calculate_planned_reward(
        direction: str,
        open_price: float,
        initial_tp: Optional[float] = None,
    ) -> Optional[float]:
        """
        Calculate absolute planned reward (|InitialTP - Entry|).

        Returns:
            Optional[float]: Planned reward delta or None if TP is not defined/zero.
        """
        if initial_tp is None or initial_tp <= 0:
            return None
        return abs(initial_tp - open_price)

    @classmethod
    def calculate_monetary_risk(
        cls,
        trade: Trade,
        contract_size: float = 100000.0,
        account_balance: Optional[float] = None,
    ) -> Optional[float]:
        """
        Calculate initial monetary risk ($) associated with a trade.

        Monetary Risk = Price Risk * Total Volume * (Contract Size or conversion factor)
        If deal results allow dynamic point-value calculation, uses implied point value.
        """
        if trade.initial_sl is None or trade.initial_sl <= 0:
            return None

        price_risk = cls.calculate_price_risk(trade.direction, trade.open_price, trade.initial_sl)
        if price_risk is None or price_risk <= 0:
            return None

        # Check if trade has closed deals to derive exact monetary conversion factor
        if trade.close_price and trade.close_price != trade.open_price and trade.profit != 0:
            price_delta = abs(trade.close_price - trade.open_price)
            # Implied monetary value per price unit for total volume
            value_per_price_unit = abs(trade.profit) / price_delta
            return round(price_risk * value_per_price_unit, 4)

        # Standard lot estimation using contract size or price risk * volume
        # For forex (standard lot 100k): price_risk * volume * contract_size
        # For indices/commodities where price is direct (e.g. Gold $1 = $100 per lot):
        if trade.volume > 0:
            # Standard price risk money approximation
            return round(price_risk * trade.volume * contract_size, 4)

        return None

    @staticmethod
    def calculate_risk_percentage(
        monetary_risk: Optional[float],
        account_balance: Optional[float],
    ) -> Optional[float]:
        """
        Calculate risk percentage relative to total account balance.

        Returns:
            Optional[float]: Risk % (e.g., 1.5 for 1.5%), or None if risk or balance is invalid.
        """
        if monetary_risk is None or account_balance is None or account_balance <= 0:
            return None
        return round((monetary_risk / account_balance) * 100.0, 2)
