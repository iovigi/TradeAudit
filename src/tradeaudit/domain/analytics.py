"""
Domain structures and enums for core performance analytics.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List


class ProfitabilityVerdict(str, Enum):
    """Profitability verdict evaluation for a sample of trades."""
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NEGATIVE_EXPECTANCY = "NEGATIVE_EXPECTANCY"
    BREAK_EVEN = "BREAK_EVEN"
    POSITIVE_EXPECTANCY = "POSITIVE_EXPECTANCY"


@dataclass
class PerformanceMetrics:
    """Aggregated core performance analytics metrics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0
    win_rate: float = 0.0
    loss_rate: float = 0.0
    net_profit: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: Optional[float] = None
    net_r: float = 0.0
    trades_with_r: int = 0
    avg_win_monetary: float = 0.0
    avg_loss_monetary: float = 0.0
    avg_win_r: float = 0.0
    avg_loss_r: float = 0.0
    expectancy_r: float = 0.0
    expectancy_monetary: float = 0.0
    max_drawdown_r: float = 0.0
    max_drawdown_monetary: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    verdict: ProfitabilityVerdict = ProfitabilityVerdict.INSUFFICIENT_DATA
    min_sample_size: int = 30
    is_sample_sufficient: bool = False
    cumulative_r_series: List[float] = field(default_factory=list)
    drawdown_r_series: List[float] = field(default_factory=list)
    cumulative_monetary_series: List[float] = field(default_factory=list)
