"""
Base declarative model and foundational database entities.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Index, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AuditMeta(Base):
    """Internal database metadata table for verification & schema version tracking."""
    __tablename__ = "audit_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class AppSettingsModel(Base):
    """Key-value storage table for application configuration & MT5 non-sensitive settings."""
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class AccountModel(Base):
    """Database representation of MetaTrader 5 trading accounts."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)  # MT5 login account number
    name = Column(String(255), nullable=True)
    server = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    currency = Column(String(10), default="USD")
    leverage = Column(Integer, default=1)
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    trade_mode = Column(String(20), default="Demo")
    last_sync_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    trades = relationship("TradeModel", back_populates="account", cascade="all, delete-orphan")


class StrategyModel(Base):
    """Database representation of user trading strategies and execution rules."""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    allowed_symbols = Column(Text, nullable=True)     # JSON array string or comma-separated
    allowed_sessions = Column(Text, nullable=True)    # JSON array string or comma-separated
    min_rr = Column(Float, nullable=True)
    max_risk_pct = Column(Float, nullable=True)
    max_trades_per_day = Column(Integer, nullable=True)
    requires_sl = Column(Boolean, default=False, nullable=False)
    requires_tp = Column(Boolean, default=False, nullable=False)
    allowed_direction = Column(String(10), default="ALL", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    trades = relationship("TradeModel", back_populates="strategy")


class TradeModel(Base):
    """Database representation of logical aggregated trades."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    position_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # BUY or SELL
    volume = Column(Float, nullable=False, default=0.0)
    open_time = Column(DateTime, nullable=False, index=True)
    close_time = Column(DateTime, nullable=True, index=True)
    open_price = Column(Float, nullable=False, default=0.0)
    close_price = Column(Float, nullable=True)
    initial_sl = Column(Float, nullable=True)
    initial_tp = Column(Float, nullable=True)
    profit = Column(Float, nullable=False, default=0.0)
    swap = Column(Float, nullable=False, default=0.0)
    commission = Column(Float, nullable=False, default=0.0)
    fee = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="OPEN", index=True)  # OPEN or CLOSED
    price_risk = Column(Float, nullable=True)
    planned_reward = Column(Float, nullable=True)
    planned_rr = Column(Float, nullable=True)
    monetary_risk = Column(Float, nullable=True)
    realized_r = Column(Float, nullable=True)
    risk_percentage = Column(Float, nullable=True)
    is_valid_setup = Column(Boolean, default=True, nullable=False)
    validation_error = Column(String(255), nullable=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True, index=True)
    compliance_status = Column(String(20), default="UNCHECKED", nullable=True)
    compliance_details = Column(Text, nullable=True)
    deviation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    account = relationship("AccountModel", back_populates="trades")
    strategy = relationship("StrategyModel", back_populates="trades")
    deals = relationship("TradeDealModel", back_populates="trade", cascade="all, delete-orphan")



class TradeDealModel(Base):
    """Database representation of raw MT5 deal execution records."""
    __tablename__ = "trade_deals"

    ticket = Column(Integer, primary_key=True)  # MT5 deal ticket number
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="CASCADE"), nullable=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    order_ticket = Column(Integer, default=0)
    position_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)   # BUY, SELL, BALANCE, etc.
    entry = Column(String(20), nullable=False)  # IN, OUT, INOUT, OUT_BY
    time = Column(DateTime, nullable=False, index=True)
    volume = Column(Float, nullable=False, default=0.0)
    price = Column(Float, nullable=False, default=0.0)
    profit = Column(Float, nullable=False, default=0.0)
    swap = Column(Float, nullable=False, default=0.0)
    commission = Column(Float, nullable=False, default=0.0)
    fee = Column(Float, nullable=False, default=0.0)
    sl = Column(Float, default=0.0)
    tp = Column(Float, default=0.0)
    comment = Column(Text, nullable=True)
    magic = Column(Integer, default=0)

    trade = relationship("TradeModel", back_populates="deals")


class SyncStateModel(Base):
    """Database representation of per-account synchronization metadata."""
    __tablename__ = "sync_state"

    account_id = Column(Integer, ForeignKey("accounts.id"), primary_key=True)
    last_sync_time = Column(DateTime, nullable=False)
    deals_count = Column(Integer, default=0)
    trades_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

