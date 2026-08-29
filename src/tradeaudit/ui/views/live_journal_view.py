"""
Live Trade Journal View component for TradeAudit.
Displays live MT5 open positions, real-time SL/TP modification history, and trade lifecycle events.
"""

import logging
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from tradeaudit.domain.models import LivePosition, TradeEventRecord

logger = logging.getLogger("tradeaudit.ui.views.live_journal_view")


class LiveJournalView(QWidget):
    """View displaying active open positions and live modification event timeline."""

    poll_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._active_positions: List[LivePosition] = []
        self._trade_events: List[TradeEventRecord] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header bar
        header_layout = QHBoxLayout()
        title_label = QLabel("Live Trade Journal & Event Monitor")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #58a6ff;")

        self.status_label = QLabel("Status: Standby")
        self.status_label.setStyleSheet("font-size: 13px; color: #8b949e; margin-left: 10px;")

        self.refresh_btn = QPushButton("Poll Now")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
        """)
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)

        header_layout.addWidget(title_label)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)

        # Main splitter dividing positions table and events timeline
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: #30363d; height: 3px; }")

        # Upper Box: Active Open Positions
        pos_box = QGroupBox("Active MT5 Open Positions")
        pos_box.setStyleSheet("""
            QGroupBox {
                color: #c9d1d9;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #30363d;
                border-radius: 6px;
                margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        pos_layout = QVBoxLayout(pos_box)

        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(9)
        self.pos_table.setHorizontalHeaderLabels([
            "Ticket / ID", "Symbol", "Type", "Volume", "Open Price", "SL", "TP", "Profit ($)", "Open Time"
        ])
        self.pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pos_table.verticalHeader().setVisible(False)
        self.pos_table.setStyleSheet(self._table_stylesheet())
        pos_layout.addWidget(self.pos_table)

        splitter.addWidget(pos_box)

        # Lower Box: Event Log & Modification Timeline
        events_box = QGroupBox("Live Modification & Lifecycle Events Timeline")
        events_box.setStyleSheet(pos_box.styleSheet())
        events_layout = QVBoxLayout(events_box)

        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels([
            "Timestamp", "Position ID", "Event Type", "Event Details"
        ])
        self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.events_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.setStyleSheet(self._table_stylesheet())
        events_layout.addWidget(self.events_table)

        splitter.addWidget(events_box)
        splitter.setSizes([300, 300])

        layout.addWidget(splitter)

    def _table_stylesheet(self) -> str:
        return """
            QTableWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                gridline-color: #21262d;
                border: none;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #161b22;
                color: #8b949e;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #21262d;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """

    def _on_refresh_clicked(self):
        self.poll_requested.emit()

    def set_status(self, text: str):
        """Update status label."""
        self.status_label.setText(f"Status: {text}")

    def update_positions(self, positions: List[LivePosition]):
        """Populate active open positions table."""
        self._active_positions = positions
        self.pos_table.setRowCount(len(positions))

        for row, pos in enumerate(positions):
            # Ticket
            item_id = QTableWidgetItem(str(pos.position_id))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.pos_table.setItem(row, 0, item_id)

            # Symbol
            item_sym = QTableWidgetItem(pos.symbol)
            item_sym.setTextAlignment(Qt.AlignCenter)
            self.pos_table.setItem(row, 1, item_sym)

            # Type
            item_type = QTableWidgetItem(pos.type)
            item_type.setTextAlignment(Qt.AlignCenter)
            if pos.type == "BUY":
                item_type.setForeground(QColor("#3fb950"))
            else:
                item_type.setForeground(QColor("#f85149"))
            self.pos_table.setItem(row, 2, item_type)

            # Volume
            item_vol = QTableWidgetItem(f"{pos.volume:.2f}")
            item_vol.setTextAlignment(Qt.AlignCenter)
            self.pos_table.setItem(row, 3, item_vol)

            # Open Price
            item_price = QTableWidgetItem(f"{pos.price_open:.5f}")
            item_price.setTextAlignment(Qt.AlignCenter)
            self.pos_table.setItem(row, 4, item_price)

            # SL
            sl_str = f"{pos.sl:.5f}" if pos.sl > 0 else "None"
            item_sl = QTableWidgetItem(sl_str)
            item_sl.setTextAlignment(Qt.AlignCenter)
            self.pos_table.setItem(row, 5, item_sl)

            # TP
            tp_str = f"{pos.tp:.5f}" if pos.tp > 0 else "None"
            item_tp = QTableWidgetItem(tp_str)
            item_tp.setTextAlignment(Qt.AlignCenter)
            self.pos_table.setItem(row, 6, item_tp)

            # Profit
            item_profit = QTableWidgetItem(f"${pos.profit:+.2f}")
            item_profit.setTextAlignment(Qt.AlignCenter)
            if pos.profit > 0:
                item_profit.setForeground(QColor("#3fb950"))
            elif pos.profit < 0:
                item_profit.setForeground(QColor("#f85149"))
            self.pos_table.setItem(row, 7, item_profit)

            # Open Time
            time_str = pos.time.strftime("%Y-%m-%d %H:%M:%S") if pos.time else ""
            item_time = QTableWidgetItem(time_str)
            item_time.setTextAlignment(Qt.AlignCenter)
            self.pos_table.setItem(row, 8, item_time)

    def update_events(self, events: List[TradeEventRecord]):
        """Populate trade events timeline table."""
        self._trade_events = events
        self.events_table.setRowCount(len(events))

        for row, evt in enumerate(events):
            # Timestamp
            ts_str = evt.timestamp.strftime("%Y-%m-%d %H:%M:%S") if evt.timestamp else ""
            item_ts = QTableWidgetItem(ts_str)
            item_ts.setTextAlignment(Qt.AlignCenter)
            self.events_table.setItem(row, 0, item_ts)

            # Position ID
            item_pos = QTableWidgetItem(str(evt.position_id))
            item_pos.setTextAlignment(Qt.AlignCenter)
            self.events_table.setItem(row, 1, item_pos)

            # Event Type
            item_type = QTableWidgetItem(evt.event_type)
            item_type.setTextAlignment(Qt.AlignCenter)
            item_type.setFont(QFont("Consolas", 9, QFont.Bold))
            if "OPENED" in evt.event_type:
                item_type.setForeground(QColor("#58a6ff"))
            elif "SL_MODIFIED" in evt.event_type:
                item_type.setForeground(QColor("#d29922"))
            elif "TP_MODIFIED" in evt.event_type:
                item_type.setForeground(QColor("#a5d6ff"))
            elif "CLOSED" in evt.event_type:
                item_type.setForeground(QColor("#8b949e"))
            elif "PARTIAL" in evt.event_type:
                item_type.setForeground(QColor("#f0883e"))
            self.events_table.setItem(row, 2, item_type)

            # Details
            details_str = str(evt.details) if evt.details else ""
            item_det = QTableWidgetItem(details_str)
            self.events_table.setItem(row, 3, item_det)
