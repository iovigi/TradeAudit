"""
Service for automated behavioral analysis of trades.
Identifies discipline issues like revenge trading, FOMO, overtrading, risk escalation, and SL violations.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from tradeaudit.domain.models import (
    Trade,
    Strategy,
    BehaviorFlag,
    BehaviorFlagType,
    ConfidenceLevel
)

logger = logging.getLogger("tradeaudit.app.services.behavior_analyzer")


class BehaviorAnalyzer:
    """Analyzes trade history for behavioral patterns and discipline flags."""

    REVENGE_MAX_MINUTES = 30
    DEFAULT_MAX_TRADES_PER_DAY = 5
    RISK_ESCALATION_RATIO = 1.5
    HIGH_RISK_ESCALATION_RATIO = 2.0

    def analyze_trade(
        self,
        trade: Trade,
        history: List[Trade],
        strategy: Optional[Strategy] = None
    ) -> List[BehaviorFlag]:
        """
        Analyze a single trade in the context of preceding trade history and optional strategy rules.

        :param trade: Target Trade to analyze.
        :param history: List of historical trades (should include trade or prior trades ordered chronologically).
        :param strategy: Associated Strategy instance, if any.
        :return: List of detected BehaviorFlag objects.
        """
        flags: List[BehaviorFlag] = []

        if not trade.open_time:
            return flags

        # Sort history chronologically by open_time
        sorted_history = [t for t in history if t.open_time is not None]
        sorted_history.sort(key=lambda t: t.open_time)

        # Find prior trades opened strictly before current trade's open_time
        prior_trades = [t for t in sorted_history if t.open_time < trade.open_time]

        # 1. Check Revenge Trade Heuristic
        revenge_flag = self._check_revenge_trading(trade, prior_trades)
        if revenge_flag:
            flags.append(revenge_flag)

        # 2. Check Overtrading Heuristic
        overtrading_flag = self._check_overtrading(trade, prior_trades, strategy)
        if overtrading_flag:
            flags.append(overtrading_flag)

        # 3. Check Risk Escalation Heuristic
        risk_esc_flag = self._check_risk_escalation(trade, prior_trades, strategy)
        if risk_esc_flag:
            flags.append(risk_esc_flag)

        # 4. Check SL Moved Away Heuristic
        sl_flag = self._check_sl_moved_away(trade)
        if sl_flag:
            flags.append(sl_flag)

        # 5. Check FOMO Heuristic
        fomo_flag = self._check_fomo(trade, prior_trades, strategy)
        if fomo_flag:
            flags.append(fomo_flag)

        return flags

    def _check_revenge_trading(self, trade: Trade, prior_trades: List[Trade]) -> Optional[BehaviorFlag]:
        """Detect if trade was opened shortly after a losing trade."""
        if not prior_trades or not trade.open_time:
            return None

        # Get immediate prior closed trade
        prior_closed = [t for t in prior_trades if t.status == "CLOSED" and t.close_time is not None]
        if not prior_closed:
            return None

        last_trade = max(prior_closed, key=lambda t: t.close_time)
        if last_trade.net_profit >= 0:
            return None  # Last trade was a win or breakeven; not revenge

        # Calculate time elapsed in minutes between last trade close and current trade open
        time_diff = (trade.open_time - last_trade.close_time).total_seconds() / 60.0

        if time_diff < 0:
            # Overlapping trade, not a sequential revenge entry
            return None

        if time_diff <= self.REVENGE_MAX_MINUTES:
            # Check if volume or monetary risk escalated relative to the losing trade
            is_risk_escalated = (
                (trade.monetary_risk and last_trade.monetary_risk and trade.monetary_risk > last_trade.monetary_risk)
                or trade.volume > last_trade.volume
            )
            is_same_symbol = (trade.symbol == last_trade.symbol)

            if time_diff <= 15 and is_risk_escalated:
                confidence = ConfidenceLevel.HIGH
                reason = (
                    f"Trade opened {int(time_diff)} min after a loss on {last_trade.symbol} "
                    f"({last_trade.net_profit:.2f}) with increased risk/volume."
                )
            elif time_diff <= 15 or (is_risk_escalated and is_same_symbol):
                confidence = ConfidenceLevel.MEDIUM
                reason = (
                    f"Trade opened {int(time_diff)} min after a loss on {last_trade.symbol} "
                    f"({last_trade.net_profit:.2f})."
                )
            else:
                confidence = ConfidenceLevel.LOW
                reason = (
                    f"Trade opened within {int(time_diff)} min of previous loss."
                )

            return BehaviorFlag(
                flag_type=BehaviorFlagType.POSSIBLE_REVENGE_TRADE,
                confidence=confidence,
                reason=reason,
                metrics={
                    "minutes_since_loss": round(time_diff, 1),
                    "last_loss_amount": last_trade.net_profit,
                    "last_symbol": last_trade.symbol,
                    "volume_ratio": round(trade.volume / last_trade.volume, 2) if last_trade.volume else 1.0
                }
            )

        return None

    def _check_overtrading(self, trade: Trade, prior_trades: List[Trade], strategy: Optional[Strategy]) -> Optional[BehaviorFlag]:
        """Detect if daily trade count exceeds strategy or threshold limits."""
        if not trade.open_time:
            return None

        trade_date = trade.open_time.date()
        same_day_prior = [t for t in prior_trades if t.open_time and t.open_time.date() == trade_date]
        trades_today_count = len(same_day_prior) + 1  # Including current trade

        max_allowed = (
            strategy.max_trades_per_day
            if strategy and strategy.max_trades_per_day is not None
            else self.DEFAULT_MAX_TRADES_PER_DAY
        )

        if trades_today_count > max_allowed:
            excess = trades_today_count - max_allowed
            confidence = ConfidenceLevel.HIGH if excess >= 3 else ConfidenceLevel.MEDIUM
            reason = (
                f"Trade is #{trades_today_count} today, exceeding maximum limit of {max_allowed} trades/day."
            )

            return BehaviorFlag(
                flag_type=BehaviorFlagType.OVERTRADING,
                confidence=confidence,
                reason=reason,
                metrics={
                    "trades_today": trades_today_count,
                    "max_allowed": max_allowed,
                    "excess_trades": excess
                }
            )

        return None

    def _check_risk_escalation(self, trade: Trade, prior_trades: List[Trade], strategy: Optional[Strategy]) -> Optional[BehaviorFlag]:
        """Detect if current trade risk is significantly higher than historical average risk."""
        current_risk = trade.monetary_risk or (trade.risk_percentage if trade.risk_percentage else None)
        if current_risk is None or current_risk <= 0:
            return None

        # Check strategy max_risk_pct if specified
        if strategy and strategy.max_risk_pct and trade.risk_percentage:
            if trade.risk_percentage > strategy.max_risk_pct * 1.2:
                return BehaviorFlag(
                    flag_type=BehaviorFlagType.RISK_ESCALATION,
                    confidence=ConfidenceLevel.HIGH,
                    reason=(
                        f"Risk percentage ({trade.risk_percentage:.2f}%) exceeds strategy limit "
                        f"({strategy.max_risk_pct:.2f}%) by over 20%."
                    ),
                    metrics={
                        "risk_pct": trade.risk_percentage,
                        "strategy_max_risk_pct": strategy.max_risk_pct
                    }
                )

        # Calculate average monetary risk from prior trades that had monetary_risk
        prior_risks = [t.monetary_risk for t in prior_trades if t.monetary_risk and t.monetary_risk > 0]
        if len(prior_risks) < 3:
            return None  # Insufficient baseline history

        avg_risk = sum(prior_risks) / len(prior_risks)
        risk_ratio = current_risk / avg_risk

        if risk_ratio >= self.RISK_ESCALATION_RATIO:
            confidence = ConfidenceLevel.HIGH if risk_ratio >= self.HIGH_RISK_ESCALATION_RATIO else ConfidenceLevel.MEDIUM
            reason = (
                f"Monetary risk (${current_risk:.2f}) is {risk_ratio:.1f}x higher than baseline average "
                f"risk (${avg_risk:.2f})."
            )

            return BehaviorFlag(
                flag_type=BehaviorFlagType.RISK_ESCALATION,
                confidence=confidence,
                reason=reason,
                metrics={
                    "current_risk": current_risk,
                    "avg_historical_risk": round(avg_risk, 2),
                    "escalation_ratio": round(risk_ratio, 2)
                }
            )

        return None

    def _check_sl_moved_away(self, trade: Trade) -> Optional[BehaviorFlag]:
        """Detect if Stop Loss was moved away from entry price during execution (increasing risk)."""
        if trade.initial_sl is None or trade.initial_sl == 0.0 or not trade.deals:
            return None

        # Find deals that occurred after entry deal
        in_deals = [d for d in trade.deals if d.entry in ("IN", "INOUT")]
        if not in_deals:
            return None

        # Check subsequent deals for SL modification changes
        for deal in trade.deals:
            if deal.sl and deal.sl > 0:
                if trade.direction == "BUY":
                    # For BUY, moving SL lower means moving away / increasing risk
                    if deal.sl < trade.initial_sl:
                        diff = trade.initial_sl - deal.sl
                        return BehaviorFlag(
                            flag_type=BehaviorFlagType.SL_MOVED_AWAY,
                            confidence=ConfidenceLevel.HIGH,
                            reason=f"Stop Loss was widened down from {trade.initial_sl:.5f} to {deal.sl:.5f}.",
                            metrics={
                                "initial_sl": trade.initial_sl,
                                "modified_sl": deal.sl,
                                "sl_widened_amount": round(diff, 5)
                            }
                        )
                elif trade.direction == "SELL":
                    # For SELL, moving SL higher means moving away / increasing risk
                    if deal.sl > trade.initial_sl:
                        diff = deal.sl - trade.initial_sl
                        return BehaviorFlag(
                            flag_type=BehaviorFlagType.SL_MOVED_AWAY,
                            confidence=ConfidenceLevel.HIGH,
                            reason=f"Stop Loss was widened up from {trade.initial_sl:.5f} to {deal.sl:.5f}.",
                            metrics={
                                "initial_sl": trade.initial_sl,
                                "modified_sl": deal.sl,
                                "sl_widened_amount": round(diff, 5)
                            }
                        )

        return None

    def _check_fomo(self, trade: Trade, prior_trades: List[Trade], strategy: Optional[Strategy]) -> Optional[BehaviorFlag]:
        """Detect potential FOMO entries (rapid entry, missing SL in high volatility, or consecutive quick entries)."""
        if not trade.open_time or not prior_trades:
            return None

        # Check if trade was opened within 3 minutes of previous trade open time (chasing market / multi-entry spike)
        prior_sorted = sorted(prior_trades, key=lambda t: t.open_time, reverse=True)
        most_recent = prior_sorted[0]

        if most_recent.open_time:
            open_diff = (trade.open_time - most_recent.open_time).total_seconds() / 60.0
            if 0 <= open_diff <= 3 and (trade.initial_sl is None or trade.initial_sl == 0.0):
                return BehaviorFlag(
                    flag_type=BehaviorFlagType.POSSIBLE_FOMO,
                    confidence=ConfidenceLevel.MEDIUM,
                    reason=f"Trade opened within {int(open_diff*60)} sec of previous trade without setting a Stop Loss.",
                    metrics={
                        "seconds_after_prev_open": round(open_diff * 60, 1)
                    }
                )

        return None

    def analyze_all_trades(
        self,
        trades: List[Trade],
        strategy_map: Optional[Dict[int, Strategy]] = None
    ) -> Dict[int, List[BehaviorFlag]]:
        """
        Analyze a list of trades and return a mapping of trade ID -> list of detected BehaviorFlags.
        """
        sorted_trades = sorted([t for t in trades if t.open_time is not None], key=lambda t: t.open_time)
        results: Dict[int, List[BehaviorFlag]] = {}

        for i, trade in enumerate(sorted_trades):
            if trade.id is None:
                continue
            history_before = sorted_trades[:i]
            strategy = strategy_map.get(trade.strategy_id) if (strategy_map and trade.strategy_id) else None
            flags = self.analyze_trade(trade, history_before, strategy)
            results[trade.id] = flags

        return results
