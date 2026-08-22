"""
Trade validation service to verify logical validity of trade parameters (SL/TP placement).
"""

from typing import Optional, Tuple
from tradeaudit.domain.models import Trade


class TradeValidator:
    """Service to validate initial setup rules for trades (SL/TP direction vs open price)."""

    @staticmethod
    def validate_setup(
        direction: str,
        open_price: float,
        initial_sl: Optional[float] = None,
        initial_tp: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate whether SL and TP parameters are logically positioned relative to open price.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, validation_error_reason)
        """
        direction_upper = direction.upper()
        if open_price <= 0:
            return False, "Open price must be positive."

        # Validate Stop Loss placement
        if initial_sl is not None and initial_sl > 0:
            if direction_upper == "BUY" and initial_sl >= open_price:
                return False, f"Invalid BUY setup: Stop Loss ({initial_sl}) must be strictly below entry price ({open_price})."
            elif direction_upper == "SELL" and initial_sl <= open_price:
                return False, f"Invalid SELL setup: Stop Loss ({initial_sl}) must be strictly above entry price ({open_price})."

        # Validate Take Profit placement
        if initial_tp is not None and initial_tp > 0:
            if direction_upper == "BUY" and initial_tp <= open_price:
                return False, f"Invalid BUY setup: Take Profit ({initial_tp}) must be strictly above entry price ({open_price})."
            elif direction_upper == "SELL" and initial_tp >= open_price:
                return False, f"Invalid SELL setup: Take Profit ({initial_tp}) must be strictly below entry price ({open_price})."

        return True, None

    @classmethod
    def validate_trade(cls, trade: Trade) -> Tuple[bool, Optional[str]]:
        """Validate trade instance and update its validation fields."""
        is_valid, error = cls.validate_setup(
            direction=trade.direction,
            open_price=trade.open_price,
            initial_sl=trade.initial_sl,
            initial_tp=trade.initial_tp,
        )
        trade.is_valid_setup = is_valid
        trade.validation_error = error
        return is_valid, error
