"""
Repository for persisting and querying strategy configurations and rules in SQLite.
"""

import json
import logging
from typing import List, Optional

from tradeaudit.domain.models import Strategy
from tradeaudit.infrastructure.database.connection import DatabaseManager
from tradeaudit.infrastructure.database.models import StrategyModel

logger = logging.getLogger("tradeaudit.infrastructure.repositories.strategy_repository")


class StrategyRepository:
    """Repository handling database operations for trading strategies."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save_strategy(self, strategy: Strategy) -> Strategy:
        """Create or update a strategy in the database."""
        with self.db_manager.session_scope() as session:
            if strategy.id:
                model = session.query(StrategyModel).filter(StrategyModel.id == strategy.id).first()
            else:
                model = None

            if not model:
                model = StrategyModel()
                session.add(model)

            model.name = strategy.name
            model.description = strategy.description
            model.allowed_symbols = json.dumps(strategy.allowed_symbols)
            model.allowed_sessions = json.dumps(strategy.allowed_sessions)
            model.min_rr = strategy.min_rr
            model.max_risk_pct = strategy.max_risk_pct
            model.max_trades_per_day = strategy.max_trades_per_day
            model.requires_sl = strategy.requires_sl
            model.requires_tp = strategy.requires_tp
            model.allowed_direction = strategy.allowed_direction
            model.is_active = strategy.is_active

            session.flush()
            strategy.id = model.id

        logger.info("Saved strategy '%s' (ID: %s)", strategy.name, strategy.id)
        return strategy

    def get_strategy(self, strategy_id: int) -> Optional[Strategy]:
        """Fetch a single strategy by ID."""
        with self.db_manager.session_scope() as session:
            model = session.query(StrategyModel).filter(StrategyModel.id == strategy_id).first()
            if not model:
                return None
            return self._model_to_domain(model)

    def get_all_strategies(self, only_active: bool = False) -> List[Strategy]:
        """Fetch all strategies."""
        with self.db_manager.session_scope() as session:
            query = session.query(StrategyModel)
            if only_active:
                query = query.filter(StrategyModel.is_active == True)
            models = query.order_by(StrategyModel.name.asc()).all()
            return [self._model_to_domain(m) for m in models]

    def delete_strategy(self, strategy_id: int) -> bool:
        """Delete a strategy by ID."""
        with self.db_manager.session_scope() as session:
            model = session.query(StrategyModel).filter(StrategyModel.id == strategy_id).first()
            if model:
                session.delete(model)
                logger.info("Deleted strategy ID %s", strategy_id)
                return True
            return False

    @staticmethod
    def _model_to_domain(model: StrategyModel) -> Strategy:
        """Convert StrategyModel ORM entity to domain Strategy entity."""
        allowed_symbols = []
        if model.allowed_symbols:
            try:
                allowed_symbols = json.loads(model.allowed_symbols)
            except (json.JSONDecodeError, TypeError):
                allowed_symbols = [s.strip() for s in model.allowed_symbols.split(",") if s.strip()]

        allowed_sessions = []
        if model.allowed_sessions:
            try:
                allowed_sessions = json.loads(model.allowed_sessions)
            except (json.JSONDecodeError, TypeError):
                allowed_sessions = [s.strip() for s in model.allowed_sessions.split(",") if s.strip()]

        return Strategy(
            id=model.id,
            name=model.name,
            description=model.description or "",
            allowed_symbols=allowed_symbols,
            allowed_sessions=allowed_sessions,
            min_rr=model.min_rr,
            max_risk_pct=model.max_risk_pct,
            max_trades_per_day=model.max_trades_per_day,
            requires_sl=model.requires_sl,
            requires_tp=model.requires_tp,
            allowed_direction=model.allowed_direction or "ALL",
            is_active=model.is_active
        )
