"""
Domain models for MetaTrader 5 configuration and account information.
"""

from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    DEVIATION = "DEVIATION"
    UNCHECKED = "UNCHECKED"


class EmotionTag(str, Enum):
    CALM = "CALM"
    FOMO = "FOMO"
    FEAR = "FEAR"
    GREED = "GREED"
    REVENGE = "REVENGE"
    BOREDOM = "BOREDOM"
    FRUSTRATION = "FRUSTRATION"
    OVERCONFIDENCE = "OVERCONFIDENCE"
    IMPULSIVE = "IMPULSIVE"
    OTHER = "OTHER"


class BehaviorFlagType(str, Enum):
    POSSIBLE_REVENGE_TRADE = "POSSIBLE_REVENGE_TRADE"
    POSSIBLE_FOMO = "POSSIBLE_FOMO"
    OVERTRADING = "OVERTRADING"
    RISK_ESCALATION = "RISK_ESCALATION"
    SL_MOVED_AWAY = "SL_MOVED_AWAY"


class ConfidenceLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class UserBehaviorAction(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


@dataclass
class BehaviorFlag:
    """Represents an automatically detected behavioral issue."""
    flag_type: BehaviorFlagType
    confidence: ConfidenceLevel
    reason: str
    metrics: dict = field(default_factory=dict)


@dataclass
class RuleViolation:
    """Represents a single rule check failure."""
    rule_name: str
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class ComplianceResult:
    """Summary of compliance evaluation for a trade against a strategy."""
    status: ComplianceStatus = ComplianceStatus.UNCHECKED
    violations: List[RuleViolation] = field(default_factory=list)
    passed_rules: List[str] = field(default_factory=list)


@dataclass
class Strategy:
    """Domain model representing a trading strategy and its execution rules."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    allowed_symbols: List[str] = field(default_factory=list)   # Empty list means all symbols allowed
    allowed_sessions: List[str] = field(default_factory=list)  # e.g., ["ASIA", "LONDON", "NEW_YORK"], empty = all
    min_rr: Optional[float] = None
    max_risk_pct: Optional[float] = None
    max_trades_per_day: Optional[int] = None
    requires_sl: bool = False
    requires_tp: bool = False
    allowed_direction: str = "ALL"                             # ALL, BUY, SELL
    is_active: bool = True


@dataclass
class MT5Settings:
    """Configuration settings for MetaTrader 5 terminal connection."""
    mt5_path: str = ""
    login: int = 0
    server: str = ""
    timeout_ms: int = 60000


@dataclass
class MT5AccountInfo:
    """MetaTrader 5 Account State Information."""
    login: int = 0
    name: str = ""
    server: str = ""
    company: str = ""
    currency: str = "USD"
    leverage: int = 1
    balance: float = 0.0
    equity: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    trade_mode: str = "Demo"


@dataclass
class TradeDeal:
    """Domain entity representing a single raw execution deal from MT5."""
    ticket: int
    account_id: int
    order_ticket: int = 0
    position_id: int = 0
    symbol: str = ""
    type: str = "BUY"          # BUY, SELL, BALANCE, CREDIT, etc.
    entry: str = "IN"          # IN, OUT, INOUT, OUT_BY
    time: Optional[datetime] = None
    volume: float = 0.0
    price: float = 0.0
    profit: float = 0.0
    swap: float = 0.0
    commission: float = 0.0
    fee: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    comment: str = ""
    magic: int = 0


@dataclass
class Trade:
    """Domain entity representing a logical aggregated trade position."""
    id: Optional[int] = None
    account_id: int = 0
    position_id: int = 0
    symbol: str = ""
    direction: str = "BUY"     # BUY, SELL
    volume: float = 0.0        # Total open lot size
    open_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    open_price: float = 0.0     # Volume-weighted average entry price
    close_price: Optional[float] = None  # Volume-weighted average exit price
    initial_sl: Optional[float] = None
    initial_tp: Optional[float] = None
    profit: float = 0.0        # Gross deal profit
    swap: float = 0.0          # Total swap
    commission: float = 0.0    # Total commission
    fee: float = 0.0           # Total fee
    status: str = "OPEN"       # OPEN, CLOSED
    price_risk: Optional[float] = None
    planned_reward: Optional[float] = None
    planned_rr: Optional[float] = None
    monetary_risk: Optional[float] = None
    realized_r: Optional[float] = None
    risk_percentage: Optional[float] = None
    is_valid_setup: bool = True
    validation_error: Optional[str] = None
    strategy_id: Optional[int] = None
    compliance_status: Optional[str] = ComplianceStatus.UNCHECKED.value
    compliance_details: Optional[str] = None
    deviation_reason: Optional[str] = None
    emotion_tag: Optional[str] = None
    auto_behavior_flags: List[BehaviorFlag] = field(default_factory=list)
    user_behavior_action: Optional[str] = UserBehaviorAction.UNREVIEWED.value
    behavior_notes: Optional[str] = None
    deals: List[TradeDeal] = field(default_factory=list)

    @property
    def net_profit(self) -> float:
        """Calculate total net monetary outcome including swap, commission and fees."""
        return self.profit + self.swap + self.commission + self.fee


@dataclass
class SyncResult:
    """Summary result of a synchronization operation."""
    account_id: int
    deals_imported: int = 0
    trades_created: int = 0
    trades_updated: int = 0
    success: bool = True
    message: str = ""


