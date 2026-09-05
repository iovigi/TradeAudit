"""
Domain models for Candlestick Chart Annotations, Drawing Tools, and Trade Journal Notes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class AnnotationType(str, Enum):
    """Supported interactive chart annotation types."""
    TREND_LINE = "TREND_LINE"
    HORIZONTAL_RAY = "HORIZONTAL_RAY"
    RECTANGLE_ZONE = "RECTANGLE_ZONE"
    TEXT_NOTE = "TEXT_NOTE"
    ARROW_UP = "ARROW_UP"
    ARROW_DOWN = "ARROW_DOWN"


class TradeGrade(str, Enum):
    """Standardized grading for trade execution quality."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class ChartAnnotation:
    """Domain model representing a geometric or textual annotation on a candlestick chart."""
    id: Optional[int] = None
    trade_id: Optional[int] = None
    timeframe: str = "M15"
    annotation_type: AnnotationType = AnnotationType.TREND_LINE
    p1_time: Optional[datetime] = None
    p1_price: float = 0.0
    p2_time: Optional[datetime] = None
    p2_price: float = 0.0
    color: str = "#58a6ff"  # Hex color string (e.g. #58a6ff, #26a69a, #ef5350, #f59e0b)
    line_width: int = 2
    text: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TradeJournalNote:
    """
    Domain entity capturing rich pre-trade thesis, post-trade review,
    setup checklist validation, execution grade, and linked chart screenshots.
    """
    id: Optional[int] = None
    trade_id: int = 0
    setup_name: str = ""
    rating: str = TradeGrade.A.value  # A+, A, B, C, D, F or 1-5
    pre_trade_thesis: str = ""
    post_trade_review: str = ""
    lessons_learned: str = ""
    mistakes_identified: List[str] = field(default_factory=list)
    checklist_data: Dict[str, bool] = field(default_factory=dict)
    screenshot_paths: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def checklist_completed_count(self) -> int:
        return sum(1 for checked in self.checklist_data.values() if checked)

    @property
    def checklist_total_count(self) -> int:
        return len(self.checklist_data)

    @property
    def checklist_score_pct(self) -> float:
        total = self.checklist_total_count
        if total == 0:
            return 100.0
        return (self.checklist_completed_count / total) * 100.0


# Standardized default pre-trade checklist templates
DEFAULT_SETUP_CHECKLIST = {
    "Higher Timeframe Bias Aligned": False,
    "Key Support/Resistance Level Confirmed": False,
    "Planned R:R >= 2.0 Confirmed": False,
    "Risk Size <= Max Risk %": False,
    "No High-Impact News in Next 30m": False,
    "Stop Loss Placed Beyond Structural Invalidation": False,
}

# Standardized mistake tags for rapid classification
DEFAULT_MISTAKE_TAGS = [
    "FOMO / Chased Entry",
    "Moved Stop Loss Away",
    "Early Exit / Weak Hands",
    "Late Exit / Ignored TP",
    "Risk / Lot Size Too Large",
    "Traded Against HTF Trend",
    "Revenge / Impulsive Re-entry",
    "Traded During High-Impact News",
    "Overtraded Daily Limit",
    "Hesitated on Entry",
    "None / Perfect Execution",
]
