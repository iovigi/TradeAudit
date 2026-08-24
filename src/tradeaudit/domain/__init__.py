"""
Domain layer package containing core domain entities, value objects, and business rules.
"""

from tradeaudit.domain.models import MT5Settings, MT5AccountInfo, TradeDeal, Trade, SyncResult
from tradeaudit.domain.analytics import PerformanceMetrics, ProfitabilityVerdict
from tradeaudit.domain.filters import (
    AnalysisFilter,
    PeriodPreset,
    DirectionFilter,
    ResultFilter,
    FilterEvaluator
)

__all__ = [
    "MT5Settings",
    "MT5AccountInfo",
    "TradeDeal",
    "Trade",
    "SyncResult",
    "PerformanceMetrics",
    "ProfitabilityVerdict",
    "AnalysisFilter",
    "PeriodPreset",
    "DirectionFilter",
    "ResultFilter",
    "FilterEvaluator",
]

