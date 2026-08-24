"""
Domain filters and filter evaluation logic for TradeAudit.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from typing import Optional, List, Tuple

from tradeaudit.domain.models import Trade


class PeriodPreset(str, Enum):
    """Preset time range options for filtering trades."""
    ALL_TIME = "ALL_TIME"
    TODAY = "TODAY"
    YESTERDAY = "YESTERDAY"
    THIS_WEEK = "THIS_WEEK"
    LAST_WEEK = "LAST_WEEK"
    THIS_MONTH = "THIS_MONTH"
    LAST_MONTH = "LAST_MONTH"
    CUSTOM = "CUSTOM"


class DirectionFilter(str, Enum):
    """Direction filtering options."""
    ALL = "ALL"
    BUY = "BUY"
    SELL = "SELL"


class ResultFilter(str, Enum):
    """Trade outcome result filtering options."""
    ALL = "ALL"
    WINNERS = "WINNERS"
    LOSERS = "LOSERS"
    BREAKEVEN = "BREAKEVEN"


@dataclass
class AnalysisFilter:
    """Filter configuration container for trade analysis."""
    period: PeriodPreset = PeriodPreset.ALL_TIME
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None
    direction: DirectionFilter = DirectionFilter.ALL
    symbols: List[str] = field(default_factory=list)
    result: ResultFilter = ResultFilter.ALL


class FilterEvaluator:
    """Evaluates AnalysisFilter criteria against lists of Trade entities."""

    @staticmethod
    def get_date_range(
        preset: PeriodPreset,
        custom_start: Optional[datetime] = None,
        custom_end: Optional[datetime] = None,
        reference_date: Optional[datetime] = None
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Calculate datetime boundaries for a given PeriodPreset.

        Args:
            preset: PeriodPreset enum value.
            custom_start: Custom start datetime (used if preset == CUSTOM).
            custom_end: Custom end datetime (used if preset == CUSTOM).
            reference_date: Reference datetime for relative calculations (defaults to datetime.now()).

        Returns:
            Tuple of (start_datetime, end_datetime). Both can be None if ALL_TIME.
        """
        if preset == PeriodPreset.ALL_TIME:
            return (None, None)

        if preset == PeriodPreset.CUSTOM:
            return (custom_start, custom_end)

        ref = reference_date or datetime.now()
        today_date = ref.date()

        if preset == PeriodPreset.TODAY:
            start = datetime.combine(today_date, time.min)
            end = datetime.combine(today_date, time.max)
            return (start, end)

        elif preset == PeriodPreset.YESTERDAY:
            yest_date = today_date - timedelta(days=1)
            start = datetime.combine(yest_date, time.min)
            end = datetime.combine(yest_date, time.max)
            return (start, end)

        elif preset == PeriodPreset.THIS_WEEK:
            # ISO weekday: Monday=1 ... Sunday=7
            start_date = today_date - timedelta(days=today_date.weekday())
            end_date = start_date + timedelta(days=6)
            start = datetime.combine(start_date, time.min)
            end = datetime.combine(end_date, time.max)
            return (start, end)

        elif preset == PeriodPreset.LAST_WEEK:
            this_monday = today_date - timedelta(days=today_date.weekday())
            last_monday = this_monday - timedelta(days=7)
            last_sunday = last_monday + timedelta(days=6)
            start = datetime.combine(last_monday, time.min)
            end = datetime.combine(last_sunday, time.max)
            return (start, end)

        elif preset == PeriodPreset.THIS_MONTH:
            start_date = today_date.replace(day=1)
            # Find next month 1st day then minus 1 day
            if today_date.month == 12:
                next_month = today_date.replace(year=today_date.year + 1, month=1, day=1)
            else:
                next_month = today_date.replace(month=today_date.month + 1, day=1)
            end_date = next_month - timedelta(days=1)
            start = datetime.combine(start_date, time.min)
            end = datetime.combine(end_date, time.max)
            return (start, end)

        elif preset == PeriodPreset.LAST_MONTH:
            first_this_month = today_date.replace(day=1)
            last_day_last_month = first_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            start = datetime.combine(first_day_last_month, time.min)
            end = datetime.combine(last_day_last_month, time.max)
            return (start, end)

        return (None, None)

    @classmethod
    def apply(
        cls,
        trades: List[Trade],
        filter_obj: AnalysisFilter,
        reference_date: Optional[datetime] = None
    ) -> List[Trade]:
        """
        Filter a list of trades according to AnalysisFilter parameters.

        Args:
            trades: Raw list of Trade domain objects.
            filter_obj: AnalysisFilter configuration instance.
            reference_date: Reference datetime for relative date preset calculations.

        Returns:
            Filtered subset of Trade domain objects.
        """
        filtered = trades

        # 1. Date Period Filter
        start_dt, end_dt = cls.get_date_range(
            preset=filter_obj.period,
            custom_start=filter_obj.custom_start_date,
            custom_end=filter_obj.custom_end_date,
            reference_date=reference_date
        )

        if start_dt or end_dt:
            res = []
            for t in filtered:
                t_time = t.close_time or t.open_time
                if t_time is None:
                    continue
                if start_dt and t_time < start_dt:
                    continue
                if end_dt and t_time > end_dt:
                    continue
                res.append(t)
            filtered = res

        # 2. Direction Filter
        if filter_obj.direction != DirectionFilter.ALL:
            filtered = [
                t for t in filtered
                if t.direction and t.direction.upper() == filter_obj.direction.value
            ]

        # 3. Symbol Filter
        if filter_obj.symbols:
            allowed_symbols = {s.strip().upper() for s in filter_obj.symbols if s.strip()}
            if allowed_symbols:
                filtered = [
                    t for t in filtered
                    if t.symbol and t.symbol.upper() in allowed_symbols
                ]

        # 4. Result Outcome Filter
        if filter_obj.result == ResultFilter.WINNERS:
            filtered = [t for t in filtered if t.net_profit > 0]
        elif filter_obj.result == ResultFilter.LOSERS:
            filtered = [t for t in filtered if t.net_profit < 0]
        elif filter_obj.result == ResultFilter.BREAKEVEN:
            filtered = [t for t in filtered if t.net_profit == 0]

        return filtered
