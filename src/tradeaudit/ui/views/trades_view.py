"""
PySide6 view component for displaying aggregated trade history and sync controls.
"""

import logging
from typing import List, Optional
from datetime import datetime

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableView,
    QHeaderView,
    QFrame,
    QLineEdit,
    QComboBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem
)

from tradeaudit.domain.models import Trade, TradeDeal

logger = logging.getLogger("tradeaudit.ui.views.trades_view")


class TradesTableModel(QAbstractTableModel):
    """Qt Data model wrapping a list of Trade domain entities."""

    COLUMNS = [
        "Position ID",
        "Symbol",
        "Type",
        "Volume",
        "Open Time",
        "Open Price",
        "Close Price",
        "Initial SL",
        "Initial TP",
        "Planned R:R",
        "Risk ($)",
        "Risk %",
        "Realized R",
        "Net Profit",
        "Emotion",
        "Behavior Flags",
        "Status"
    ]

    def __init__(self, trades: Optional[List[Trade]] = None):
        super().__init__()
        self._trades: List[Trade] = trades or []

    def set_trades(self, trades: List[Trade]) -> None:
        """Update dataset and refresh view."""
        self.beginResetModel()
        self._trades = trades
        self.endResetModel()

    def get_trade(self, row: int) -> Optional[Trade]:
        """Get Trade instance at row index."""
        if 0 <= row < len(self._trades):
            return self._trades[row]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._trades)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._trades)):
            return None

        trade = self._trades[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return str(trade.position_id)
            elif col == 1:
                return trade.symbol
            elif col == 2:
                return trade.direction
            elif col == 3:
                return f"{trade.volume:.2f}"
            elif col == 4:
                return trade.open_time.strftime("%Y-%m-%d %H:%M:%S") if trade.open_time else ""
            elif col == 5:
                return f"{trade.open_price:.5f}"
            elif col == 6:
                return f"{trade.close_price:.5f}" if trade.close_price is not None else "—"
            elif col == 7:
                return f"{trade.initial_sl:.5f}" if trade.initial_sl is not None else "—"
            elif col == 8:
                return f"{trade.initial_tp:.5f}" if trade.initial_tp is not None else "—"
            elif col == 9:
                return f"1:{trade.planned_rr:.2f}" if trade.planned_rr is not None else "—"
            elif col == 10:
                return f"${trade.monetary_risk:.2f}" if trade.monetary_risk is not None else "—"
            elif col == 11:
                return f"{trade.risk_percentage:.2f}%" if trade.risk_percentage is not None else "—"
            elif col == 12:
                return f"{trade.realized_r:+.2f} R" if trade.realized_r is not None else "UNKNOWN"
            elif col == 13:
                return f"{trade.net_profit:+.2f}"
            elif col == 14:
                return trade.emotion_tag or "—"
            elif col == 15:
                if not trade.auto_behavior_flags:
                    return "—"
                flag_names = [f.flag_type.value if hasattr(f.flag_type, 'value') else str(f.flag_type) for f in trade.auto_behavior_flags]
                action_str = f" [{trade.user_behavior_action}]" if trade.user_behavior_action and trade.user_behavior_action != "UNREVIEWED" else ""
                return ", ".join(flag_names) + action_str
            elif col == 16:
                return trade.status if trade.is_valid_setup else f"{trade.status} (⚠️ Invalid Setup)"

        elif role == Qt.ToolTipRole:
            if col == 15 and trade.auto_behavior_flags:
                details = [f"[{f.confidence.value if hasattr(f.confidence, 'value') else f.confidence}] {f.reason}" for f in trade.auto_behavior_flags]
                return "\n".join(details)
            if not trade.is_valid_setup and trade.validation_error:
                return f"Validation Alert: {trade.validation_error}"
            if trade.initial_sl is None:
                return "Warning: No initial Stop Loss defined. Realized R is UNKNOWN."

        elif role == Qt.ForegroundRole:
            if col == 2:  # Type BUY/SELL
                return QBrush(QColor("#00e676") if trade.direction == "BUY" else QColor("#ff5252"))
            elif col == 12:  # Realized R
                if trade.realized_r is not None:
                    if trade.realized_r > 0:
                        return QBrush(QColor("#00e676"))
                    elif trade.realized_r < 0:
                        return QBrush(QColor("#ff5252"))
                    else:
                        return QBrush(QColor("#a0aec0"))
                else:
                    return QBrush(QColor("#ffb74d"))  # Warning gold for UNKNOWN
            elif col == 13:  # Net Profit
                if trade.net_profit > 0:
                    return QBrush(QColor("#00e676"))
                elif trade.net_profit < 0:
                    return QBrush(QColor("#ff5252"))
                else:
                    return QBrush(QColor("#a0aec0"))
            elif col == 14:  # Emotion
                if trade.emotion_tag in ("FOMO", "REVENGE", "FRUSTRATION", "IMPULSIVE"):
                    return QBrush(QColor("#ff5252"))
                elif trade.emotion_tag == "CALM":
                    return QBrush(QColor("#00e676"))
                return QBrush(QColor("#ffb74d")) if trade.emotion_tag else QBrush(QColor("#a0aec0"))
            elif col == 15:  # Behavior Flags
                if trade.auto_behavior_flags:
                    if trade.user_behavior_action == "CONFIRMED":
                        return QBrush(QColor("#ff5252"))
                    elif trade.user_behavior_action == "REJECTED":
                        return QBrush(QColor("#8b9bb4"))
                    return QBrush(QColor("#ffb74d"))
            elif col == 16:  # Status
                if not trade.is_valid_setup:
                    return QBrush(QColor("#ff5252"))
                return QBrush(QColor("#00b0ff") if trade.status == "OPEN" else QBrush(QColor("#8b9bb4")))

        elif role == Qt.TextAlignmentRole:
            if col in (3, 5, 6, 7, 8, 9, 10, 11, 12, 13):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            elif col in (0, 1, 2, 14, 16):
                return int(Qt.AlignCenter | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        return None


class TradesView(QWidget):
    """View container for displaying aggregated MT5 trade history."""

    sync_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._all_trades: List[Trade] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Toolbar Frame
        toolbar_card = QFrame()
        toolbar_card.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 6px;
                padding: 6px 12px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        self.btn_sync = QPushButton("🔄 Sync MT5 History")
        self.btn_sync.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_sync.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #1084e3; }
            QPushButton:pressed { background-color: #005a9e; }
            QPushButton:disabled { background-color: #2c3848; color: #64748b; }
        """)
        self.btn_sync.clicked.connect(self.sync_requested.emit)

        self.lbl_sync_status = QLabel("Last Sync: Never")
        self.lbl_sync_status.setStyleSheet("color: #8b9bb4; font-size: 12px; margin-left: 10px;")

        # Search / Filters
        self.txt_filter_symbol = QLineEdit()
        self.txt_filter_symbol.setPlaceholderText("Filter Symbol (e.g. EURUSD)...")
        self.txt_filter_symbol.setMaximumWidth(200)
        self.txt_filter_symbol.setStyleSheet("""
            QLineEdit {
                background-color: #121820;
                color: #ffffff;
                border: 1px solid #2a3444;
                border-radius: 4px;
                padding: 6px 10px;
            }
        """)
        self.txt_filter_symbol.textChanged.connect(self._apply_filters)

        self.cmb_filter_status = QComboBox()
        self.cmb_filter_status.addItems(["All Statuses", "CLOSED", "OPEN"])
        self.cmb_filter_status.setStyleSheet("""
            QComboBox {
                background-color: #121820;
                color: #ffffff;
                border: 1px solid #2a3444;
                border-radius: 4px;
                padding: 6px 10px;
            }
        """)
        self.cmb_filter_status.currentTextChanged.connect(self._apply_filters)

        toolbar_layout.addWidget(self.btn_sync)
        toolbar_layout.addWidget(self.lbl_sync_status)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Filter:"))
        toolbar_layout.addWidget(self.txt_filter_symbol)
        toolbar_layout.addWidget(self.cmb_filter_status)

        # Splitter: Upper Main Trades Table, Lower Deal Execution Breakdown
        splitter = QSplitter(Qt.Vertical)

        # Trades Main Table
        self.model = TradesTableModel()
        self.table_trades = QTableView()
        self.table_trades.setModel(self.model)
        self.table_trades.setSelectionBehavior(QTableView.SelectRows)
        self.table_trades.setSelectionMode(QTableView.SingleSelection)
        self.table_trades.setAlternatingRowColors(True)
        self.table_trades.setStyleSheet("""
            QTableView {
                background-color: #161b22;
                alternate-background-color: #1c232e;
                gridline-color: #232d3d;
                color: #e2e8f0;
                border: 1px solid #2a3444;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #1f2733;
                color: #a0aec0;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #2a3444;
            }
            QTableView::item:selected {
                background-color: #004080;
                color: #ffffff;
            }
        """)
        self.table_trades.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_trades.horizontalHeader().setStretchLastSection(True)
        self.table_trades.selectionModel().selectionChanged.connect(self._on_trade_selected)

        # Deals Breakdown Section
        deals_container = QWidget()
        deals_layout = QVBoxLayout(deals_container)
        deals_layout.setContentsMargins(0, 8, 0, 0)

        deals_header = QLabel("🔍 Position Execution Deals Breakdown")
        deals_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        deals_header.setStyleSheet("color: #00a2e8;")

        self.table_deals = QTableWidget()
        self.table_deals.setColumnCount(8)
        self.table_deals.setHorizontalHeaderLabels([
            "Deal Ticket", "Order Ticket", "Type", "Entry", "Time", "Volume", "Price", "Profit"
        ])
        self.table_deals.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_deals.setStyleSheet("""
            QTableWidget {
                background-color: #121820;
                color: #cbd5e0;
                border: 1px solid #2a3444;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #1a222d;
                color: #718096;
                padding: 4px;
                font-size: 11px;
                border: none;
            }
        """)

        deals_layout.addWidget(deals_header)
        deals_layout.addWidget(self.table_deals)

        splitter.addWidget(self.table_trades)
        splitter.addWidget(deals_container)
        splitter.setSizes([450, 200])

        layout.addWidget(toolbar_card)
        layout.addWidget(splitter, stretch=1)

    def set_trades(self, trades: List[Trade], last_sync: Optional[datetime] = None) -> None:
        """Populate trades dataset into view."""
        self._all_trades = trades
        self._apply_filters()

        if last_sync:
            sync_str = last_sync.strftime("%Y-%m-%d %H:%M:%S")
            self.lbl_sync_status.setText(f"Last Sync: {sync_str}")
        else:
            self.lbl_sync_status.setText("Last Sync: Updated")

    def _apply_filters(self) -> None:
        """Filter trade list based on user inputs."""
        symbol_query = self.txt_filter_symbol.text().strip().upper()
        status_query = self.cmb_filter_status.currentText()

        filtered = self._all_trades
        if symbol_query:
            filtered = [t for t in filtered if symbol_query in t.symbol.upper()]
        if status_query != "All Statuses":
            filtered = [t for t in filtered if t.status == status_query]

        self.model.set_trades(filtered)

    def _on_trade_selected(self) -> None:
        """Display details for currently selected trade."""
        selected_indexes = self.table_trades.selectionModel().selectedRows()
        if not selected_indexes:
            self.table_deals.setRowCount(0)
            return

        row = selected_indexes[0].row()
        trade = self.model.get_trade(row)
        if not trade or not trade.deals:
            self.table_deals.setRowCount(0)
            return

        self.table_deals.setRowCount(len(trade.deals))
        for r, deal in enumerate(trade.deals):
            self.table_deals.setItem(r, 0, QTableWidgetItem(str(deal.ticket)))
            self.table_deals.setItem(r, 1, QTableWidgetItem(str(deal.order_ticket)))
            self.table_deals.setItem(r, 2, QTableWidgetItem(deal.type))
            self.table_deals.setItem(r, 3, QTableWidgetItem(deal.entry))
            self.table_deals.setItem(r, 4, QTableWidgetItem(deal.time.strftime("%H:%M:%S") if deal.time else ""))
            self.table_deals.setItem(r, 5, QTableWidgetItem(f"{deal.volume:.2f}"))
            self.table_deals.setItem(r, 6, QTableWidgetItem(f"{deal.price:.5f}"))

            profit_item = QTableWidgetItem(f"{deal.profit:+.2f}")
            if deal.profit > 0:
                profit_item.setForeground(QBrush(QColor("#00e676")))
            elif deal.profit < 0:
                profit_item.setForeground(QBrush(QColor("#ff5252")))
            self.table_deals.setItem(r, 7, profit_item)
