"""
R-Multiple engine for calculating planned Risk/Reward ratios and realized R outcomes.
"""

from typing import Optional


class RMultipleCalculator:
    """Service for computing planned Risk:Reward (R:R) and realized R-Multiple metrics."""

    @staticmethod
    def calculate_planned_rr(
        price_risk: Optional[float],
        planned_reward: Optional[float],
    ) -> Optional[float]:
        """
        Calculate planned Risk:Reward ratio (PlannedRR = PlannedReward / PriceRisk).

        Returns:
            Optional[float]: Planned R:R ratio (e.g. 2.5 for 1:2.5 RR), or None if SL/TP is undefined.
        """
        if price_risk is None or price_risk <= 0 or planned_reward is None:
            return None
        return round(planned_reward / price_risk, 4)

    @staticmethod
    def calculate_realized_r(
        net_profit: float,
        monetary_risk: Optional[float],
    ) -> Optional[float]:
        """
        Calculate realized R-Multiple (RealizedR = NetProfit / InitialRiskMoney).

        Important:
            If monetary risk is None or <= 0 (e.g. trade without known initial SL),
            realized_r MUST be None (representing UNKNOWN).

        Returns:
            Optional[float]: Realized R (e.g. +2.5 or -1.0), or None if SL was not specified.
        """
        if monetary_risk is None or monetary_risk <= 0:
            return None
        return round(net_profit / monetary_risk, 4)
