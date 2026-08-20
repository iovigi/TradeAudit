"""
Account information dashboard widget displaying live MetaTrader 5 account metrics.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame
)

from tradeaudit.domain.models import MT5AccountInfo


class AccountInfoCard(QFrame):
    """Dashboard card component summarizing MT5 Account metrics."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("AccountInfoCard")
        self.setStyleSheet("""
            QFrame#AccountInfoCard {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header Row
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("📊 MT5 Account Overview")
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.title_label.setStyleSheet("color: #ffffff;")

        self.mode_badge = QLabel("DISCONNECTED")
        self.mode_badge.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.mode_badge.setStyleSheet("""
            background-color: #2d3748;
            color: #a0aec0;
            padding: 4px 8px;
            border-radius: 4px;
        """)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.mode_badge)

        layout.addLayout(header_layout)

        # Metrics Grid (3 columns)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)

        # Account / Trader info
        self.val_login = self._create_metric_item(grid_layout, 0, 0, "Account Login", "—")
        self.val_name = self._create_metric_item(grid_layout, 0, 1, "Trader Name", "—")
        self.val_company = self._create_metric_item(grid_layout, 0, 2, "Broker / Company", "—")

        # Balance / Equity / Profit
        self.val_balance = self._create_metric_item(grid_layout, 1, 0, "Balance", "$0.00", highlight=True)
        self.val_equity = self._create_metric_item(grid_layout, 1, 1, "Equity", "$0.00", highlight=True)
        self.val_profit = self._create_metric_item(grid_layout, 1, 2, "Floating Profit", "$0.00", highlight=True)

        # Margin / Leverage
        self.val_margin = self._create_metric_item(grid_layout, 2, 0, "Margin", "$0.00")
        self.val_free_margin = self._create_metric_item(grid_layout, 2, 1, "Free Margin", "$0.00")
        self.val_leverage = self._create_metric_item(grid_layout, 2, 2, "Leverage", "1:1")

        layout.addLayout(grid_layout)

    def _create_metric_item(
        self,
        grid: QGridLayout,
        row: int,
        col: int,
        label_text: str,
        initial_val: str,
        highlight: bool = False
    ) -> QLabel:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #121820;
                border: 1px solid #232d3d;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setFont(QFont("Segoe UI", 8))
        lbl.setStyleSheet("color: #718096;")

        val_lbl = QLabel(initial_val)
        if highlight:
            val_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
            val_lbl.setStyleSheet("color: #ffffff;")
        else:
            val_lbl.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
            val_lbl.setStyleSheet("color: #e2e8f0;")

        vbox.addWidget(lbl)
        vbox.addWidget(val_lbl)

        grid.addWidget(card, row, col)
        return val_lbl

    def update_account_info(self, info: Optional[MT5AccountInfo]) -> None:
        """Update metric fields with latest MT5 account info."""
        if not info or not info.login:
            self.mode_badge.setText("DISCONNECTED")
            self.mode_badge.setStyleSheet("background-color: #2d3748; color: #a0aec0; padding: 4px 8px; border-radius: 4px;")
            self.val_login.setText("—")
            self.val_name.setText("—")
            self.val_company.setText("—")
            self.val_balance.setText("$0.00")
            self.val_equity.setText("$0.00")
            self.val_profit.setText("$0.00")
            self.val_profit.setStyleSheet("color: #ffffff;")
            self.val_margin.setText("$0.00")
            self.val_free_margin.setText("$0.00")
            self.val_leverage.setText("1:1")
            return

        mode_color = "#00e676" if info.trade_mode == "Real" else "#00b0ff"
        self.mode_badge.setText(f"{info.trade_mode.upper()} ACCOUNT")
        self.mode_badge.setStyleSheet(f"background-color: rgba(0, 176, 255, 0.15); color: {mode_color}; padding: 4px 8px; border-radius: 4px; border: 1px solid {mode_color};")

        curr = info.currency or "USD"
        self.val_login.setText(str(info.login))
        self.val_name.setText(info.name or "N/A")
        self.val_company.setText(info.company or info.server or "N/A")

        self.val_balance.setText(f"{info.balance:,.2f} {curr}")
        self.val_equity.setText(f"{info.equity:,.2f} {curr}")

        profit_prefix = "+" if info.profit > 0 else ""
        profit_color = "#00e676" if info.profit >= 0 else "#ff5252"
        self.val_profit.setText(f"{profit_prefix}{info.profit:,.2f} {curr}")
        self.val_profit.setStyleSheet(f"color: {profit_color}; font-weight: bold;")

        self.val_margin.setText(f"{info.margin:,.2f} {curr}")
        self.val_free_margin.setText(f"{info.margin_free:,.2f} {curr}")
        self.val_leverage.setText(f"1:{info.leverage}")
