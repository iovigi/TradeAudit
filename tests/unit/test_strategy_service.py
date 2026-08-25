"""
Unit tests for StrategyService.
"""

import pytest
from datetime import datetime, timezone
from tradeaudit.domain.models import Strategy, Trade, ComplianceStatus
from tradeaudit.infrastructure.repositories.strategy_repository import StrategyRepository
from tradeaudit.infrastructure.repositories.trade_repository import TradeRepository
from tradeaudit.app.services.strategy_service import StrategyService


@pytest.fixture
def service_setup(test_db_manager):
    strategy_repo = StrategyRepository(test_db_manager)
    trade_repo = TradeRepository(test_db_manager)
    service = StrategyService(strategy_repo, trade_repo)

    return service, strategy_repo, trade_repo


def test_assign_strategy_and_evaluate_compliance(service_setup):
    service, strategy_repo, trade_repo = service_setup

    strategy = Strategy(
        name="Strict Strategy",
        min_rr=2.0,
        requires_sl=True,
        allowed_direction="BUY"
    )
    saved_strategy = service.create_strategy(strategy)

    trade = Trade(
        account_id=12345,
        position_id=999,
        symbol="EURUSD",
        direction="BUY",
        open_time=datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc),
        initial_sl=1.0900,
        planned_rr=2.5
    )
    trade_repo.save_trades(12345, [trade])

    # Assign strategy
    updated_trade = service.assign_strategy_to_trade(
        account_id=12345,
        trade_id=trade.id,
        strategy_id=saved_strategy.id
    )

    assert updated_trade is not None
    assert updated_trade.strategy_id == saved_strategy.id
    assert updated_trade.compliance_status == ComplianceStatus.COMPLIANT.value
    assert updated_trade.compliance_details is not None


def test_reevaluate_account_compliance(service_setup):
    service, strategy_repo, trade_repo = service_setup

    strategy = Strategy(name="Test Strategy", min_rr=3.0)
    saved_strat = service.create_strategy(strategy)

    trade1 = Trade(account_id=555, position_id=1, planned_rr=1.5, strategy_id=saved_strat.id, open_time=datetime.now(timezone.utc))
    trade2 = Trade(account_id=555, position_id=2, planned_rr=4.0, strategy_id=saved_strat.id, open_time=datetime.now(timezone.utc))

    trade_repo.save_trades(555, [trade1, trade2])

    count = service.reevaluate_account_compliance(555)
    assert count == 2

    trades = trade_repo.get_trades(555)
    t1 = next(t for t in trades if t.position_id == 1)
    t2 = next(t for t in trades if t.position_id == 2)

    assert t1.compliance_status == ComplianceStatus.DEVIATION.value
    assert t2.compliance_status == ComplianceStatus.COMPLIANT.value
