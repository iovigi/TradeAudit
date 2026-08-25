"""
Engine for evaluating trade execution compliance against strategy rules.
"""

from typing import List, Optional
from datetime import datetime, timezone

from tradeaudit.domain.models import (
    Trade,
    Strategy,
    ComplianceStatus,
    ComplianceResult,
    RuleViolation
)


class StrategyComplianceEngine:
    """Evaluates rules defined in a Strategy against a given Trade."""

    SESSION_WINDOWS = {
        "ASIA": (0, 8),        # 00:00 - 08:00 UTC
        "LONDON": (8, 16),     # 08:00 - 16:00 UTC
        "NEW_YORK": (13, 21),  # 13:00 - 21:00 UTC
    }

    def evaluate(self, trade: Trade, strategy: Strategy, all_trades: Optional[List[Trade]] = None) -> ComplianceResult:
        """
        Evaluate a single trade against strategy rules.

        :param trade: Trade entity to evaluate.
        :param strategy: Strategy configuration with rules.
        :param all_trades: Optional list of all trades to check multi-trade rules (e.g. max_trades_per_day).
        :return: ComplianceResult entity with status and violations list.
        """
        violations: List[RuleViolation] = []
        passed_rules: List[str] = []

        # 1. MIN_RR
        if strategy.min_rr is not None:
            if trade.planned_rr is None or trade.planned_rr < strategy.min_rr:
                actual_val = f"{trade.planned_rr:.2f}" if trade.planned_rr is not None else "None"
                violations.append(RuleViolation(
                    rule_name="MIN_RR",
                    message=f"Planned R:R ({actual_val}) is below minimum required ({strategy.min_rr:.2f}).",
                    expected=f">= {strategy.min_rr:.2f}",
                    actual=actual_val
                ))
            else:
                passed_rules.append("MIN_RR")

        # 2. MAX_RISK_PERCENT
        if strategy.max_risk_pct is not None:
            if trade.risk_percentage is None or trade.risk_percentage > strategy.max_risk_pct:
                actual_val = f"{trade.risk_percentage:.2f}%" if trade.risk_percentage is not None else "None"
                violations.append(RuleViolation(
                    rule_name="MAX_RISK_PERCENT",
                    message=f"Risk percentage ({actual_val}) exceeds allowed maximum ({strategy.max_risk_pct:.2f}%).",
                    expected=f"<= {strategy.max_risk_pct:.2f}%",
                    actual=actual_val
                ))
            else:
                passed_rules.append("MAX_RISK_PERCENT")

        # 3. REQUIRES_STOP_LOSS
        if strategy.requires_sl:
            if trade.initial_sl is None:
                violations.append(RuleViolation(
                    rule_name="REQUIRES_STOP_LOSS",
                    message="Trade opened without initial Stop Loss.",
                    expected="SL present",
                    actual="No SL"
                ))
            else:
                passed_rules.append("REQUIRES_STOP_LOSS")

        # 4. REQUIRES_TAKE_PROFIT
        if strategy.requires_tp:
            if trade.initial_tp is None:
                violations.append(RuleViolation(
                    rule_name="REQUIRES_TAKE_PROFIT",
                    message="Trade opened without initial Take Profit.",
                    expected="TP present",
                    actual="No TP"
                ))
            else:
                passed_rules.append("REQUIRES_TAKE_PROFIT")

        # 5. ALLOWED_DIRECTION
        if strategy.allowed_direction and strategy.allowed_direction != "ALL":
            if trade.direction != strategy.allowed_direction:
                violations.append(RuleViolation(
                    rule_name="ALLOWED_DIRECTION",
                    message=f"Trade direction ({trade.direction}) is not allowed by strategy ({strategy.allowed_direction}).",
                    expected=strategy.allowed_direction,
                    actual=trade.direction
                ))
            else:
                passed_rules.append("ALLOWED_DIRECTION")

        # 6. ALLOWED_SYMBOL
        if strategy.allowed_symbols:
            clean_allowed = [s.strip().upper() for s in strategy.allowed_symbols]
            if trade.symbol.strip().upper() not in clean_allowed:
                violations.append(RuleViolation(
                    rule_name="ALLOWED_SYMBOL",
                    message=f"Symbol '{trade.symbol}' is not in allowed strategy symbols.",
                    expected=", ".join(clean_allowed),
                    actual=trade.symbol
                ))
            else:
                passed_rules.append("ALLOWED_SYMBOL")

        # 7. ALLOWED_SESSION
        if strategy.allowed_sessions and trade.open_time:
            open_hour = trade.open_time.hour
            in_allowed_session = False

            for session_name in strategy.allowed_sessions:
                s_upper = session_name.strip().upper()
                if s_upper in self.SESSION_WINDOWS:
                    start, end = self.SESSION_WINDOWS[s_upper]
                    if start <= open_hour < end:
                        in_allowed_session = True
                        break

            if not in_allowed_session:
                violations.append(RuleViolation(
                    rule_name="ALLOWED_SESSION",
                    message=f"Trade opened at {trade.open_time.strftime('%H:%M')} UTC outside allowed sessions.",
                    expected=", ".join(strategy.allowed_sessions),
                    actual=trade.open_time.strftime("%H:%M UTC")
                ))
            else:
                passed_rules.append("ALLOWED_SESSION")

        # 8. MAX_TRADES_PER_DAY
        if strategy.max_trades_per_day is not None and trade.open_time and all_trades:
            trade_date = trade.open_time.date()
            same_day_trades = [
                t for t in all_trades
                if t.open_time and t.open_time.date() == trade_date
                and (t.strategy_id == strategy.id or t.strategy_id is None)
            ]
            if len(same_day_trades) > strategy.max_trades_per_day:
                violations.append(RuleViolation(
                    rule_name="MAX_TRADES_PER_DAY",
                    message=f"Total trades on {trade_date} ({len(same_day_trades)}) exceed daily limit ({strategy.max_trades_per_day}).",
                    expected=f"<= {strategy.max_trades_per_day}",
                    actual=str(len(same_day_trades))
                ))
            else:
                passed_rules.append("MAX_TRADES_PER_DAY")

        status = ComplianceStatus.COMPLIANT if not violations else ComplianceStatus.DEVIATION
        return ComplianceResult(status=status, violations=violations, passed_rules=passed_rules)
