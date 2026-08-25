"""
Unit tests for StrategyRepository CRUD operations.
"""

import pytest
from tradeaudit.domain.models import Strategy
from tradeaudit.infrastructure.repositories.strategy_repository import StrategyRepository


@pytest.fixture
def repo(test_db_manager):
    return StrategyRepository(test_db_manager)


def test_save_and_get_strategy(repo):
    strategy = Strategy(
        name="Breakout Strategy",
        description="Trade London session breakouts",
        allowed_symbols=["EURUSD", "GBPUSD"],
        allowed_sessions=["LONDON", "NEW_YORK"],
        min_rr=1.5,
        max_risk_pct=2.0,
        max_trades_per_day=3,
        requires_sl=True,
        requires_tp=True,
        allowed_direction="BUY",
        is_active=True
    )

    saved = repo.save_strategy(strategy)
    assert saved.id is not None
    assert saved.name == "Breakout Strategy"

    retrieved = repo.get_strategy(saved.id)
    assert retrieved is not None
    assert retrieved.name == "Breakout Strategy"
    assert retrieved.allowed_symbols == ["EURUSD", "GBPUSD"]
    assert retrieved.allowed_sessions == ["LONDON", "NEW_YORK"]
    assert retrieved.min_rr == 1.5
    assert retrieved.max_risk_pct == 2.0
    assert retrieved.max_trades_per_day == 3
    assert retrieved.requires_sl is True
    assert retrieved.requires_tp is True
    assert retrieved.allowed_direction == "BUY"


def test_update_and_delete_strategy(repo):
    strategy = Strategy(name="Initial Name")
    saved = repo.save_strategy(strategy)

    saved.name = "Updated Name"
    saved.min_rr = 2.0
    updated = repo.save_strategy(saved)

    retrieved = repo.get_strategy(updated.id)
    assert retrieved.name == "Updated Name"
    assert retrieved.min_rr == 2.0

    all_strats = repo.get_all_strategies()
    assert len(all_strats) == 1

    deleted = repo.delete_strategy(updated.id)
    assert deleted is True
    assert repo.get_strategy(updated.id) is None
    assert len(repo.get_all_strategies()) == 0
