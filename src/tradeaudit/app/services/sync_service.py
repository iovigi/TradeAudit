"""
Synchronization service orchestrating history reading, normalization, aggregation, and local persistence.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from tradeaudit.domain.models import SyncResult, MT5AccountInfo, TradeDeal
from tradeaudit.infrastructure.mt5.history_reader import MT5HistoryReader
from tradeaudit.app.services.trade_aggregator import TradeAggregator
from tradeaudit.infrastructure.repositories.trade_repository import TradeRepository
from tradeaudit.app.exceptions import MT5Error

logger = logging.getLogger("tradeaudit.app.services.sync_service")


class SyncService:
    """Orchestrates MT5 history fetching, trade aggregation, and SQLite synchronization."""

    def __init__(
        self,
        trade_repo: TradeRepository,
        history_reader: Optional[MT5HistoryReader] = None,
        aggregator: Optional[TradeAggregator] = None
    ):
        self.trade_repo = trade_repo
        self.history_reader = history_reader or MT5HistoryReader()
        self.aggregator = aggregator or TradeAggregator()

    def sync_account_history(
        self,
        account_id: int,
        account_info: Optional[MT5AccountInfo] = None,
        from_date: Optional[datetime] = None
    ) -> SyncResult:
        """
        Perform incremental or full synchronization of MT5 deal history and update logical trades.

        :param account_id: Account login ID.
        :param account_info: Active MT5AccountInfo object if available.
        :param from_date: Optional explicit start datetime for sync.
        :return: SyncResult container with detailed execution statistics.
        """
        logger.info("Starting history synchronization for account %s...", account_id)
        sync_time = datetime.now(timezone.utc)

        # 1. Update account details in DB if available
        if account_info:
            self.trade_repo.save_account(account_info)

        # 2. Determine sync start time
        if from_date is None:
            from_date = self.trade_repo.get_last_sync_time(account_id)

        # 3. Fetch raw deals from MT5
        deals: List[TradeDeal] = []
        try:
            deals = self.history_reader.fetch_deals(account_id=account_id, from_date=from_date)
        except MT5Error as e:
            logger.error("Failed to fetch MT5 history: %s", e)
            return SyncResult(
                account_id=account_id,
                success=False,
                message=f"MT5 History fetch failed: {e.message}"
            )
        except Exception as e:
            logger.error("Unexpected error fetching MT5 history: %s", e)
            return SyncResult(
                account_id=account_id,
                success=False,
                message=f"Unexpected error: {e}"
            )

        # 4. Save raw deals to database
        new_deals_count = self.trade_repo.save_deals(deals)

        # 5. Fetch all stored deals for account to perform full position aggregation
        all_stored_trades = self.trade_repo.get_trades(account_id)
        all_stored_deals: List[TradeDeal] = []
        for t in all_stored_trades:
            all_stored_deals.extend(t.deals)

        # Merge newly fetched deals with existing ones
        deal_map = {d.ticket: d for d in all_stored_deals}
        for d in deals:
            deal_map[d.ticket] = d

        consolidated_deals = list(deal_map.values())

        # 6. Aggregate logical trades
        aggregated_trades = self.aggregator.aggregate_deals(consolidated_deals)

        # 7. Persist aggregated trades to DB
        saved_trades = self.trade_repo.save_trades(account_id, aggregated_trades)

        # 8. Update sync metadata
        self.trade_repo.update_sync_state(
            account_id=account_id,
            sync_time=sync_time,
            deals_count=len(consolidated_deals),
            trades_count=len(saved_trades)
        )

        logger.info(
            "Sync complete for account %s: %d new deals saved, %d trades aggregated/updated.",
            account_id, new_deals_count, len(saved_trades)
        )

        return SyncResult(
            account_id=account_id,
            deals_imported=new_deals_count,
            trades_created=len(saved_trades),
            trades_updated=len(saved_trades),
            success=True,
            message=f"Synced {new_deals_count} new deals. Total active trades: {len(saved_trades)}."
        )
