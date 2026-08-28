"""
Strategy vs Trader Performance View for TradeAudit (Phase 8).
Presents four-quadrant execution analysis, deviation cost in R, and comparative performance metrics.
"""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGridLayout,
    QScrollArea
)

from tradeaudit.domain.models import Trade
from tradeaudit.domain.analytics import StrategyVsTraderComparison
from tradeaudit.app.services.strategy_trader_comparator import StrategyTraderComparator


class StrategyVsTraderView(QWidget):
    """View displaying comparative performance analytics between strategy rules and trader execution."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
        self.set_trades([])

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        header_layout = QVBoxLayout(header_card)

        title = QLabel("⚖️ Strategy vs Trader Execution Audit")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")

        subtitle = QLabel("Measure whether losses stem from strategy rules or execution deviations and emotional mistakes.")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #8b9bb4;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        # KPI Summary Cards (Deviation Cost R)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.compliant_r_card = self._create_kpi_card("Compliant Strategy Net R", "0.00 R", "#00c853")
        self.total_r_card = self._create_kpi_card("Actual Realized Net R", "0.00 R", "#00a2e8")
        self.deviation_cost_card = self._create_kpi_card("Deviation Cost (R)", "0.00 R", "#ff5252")
        self.verdict_card = self._create_kpi_card("Execution Quality Verdict", "NO_TRADES", "#e2e8f0")

        kpi_layout.addWidget(self.compliant_r_card)
        kpi_layout.addWidget(self.total_r_card)
        kpi_layout.addWidget(self.deviation_cost_card)
        kpi_layout.addWidget(self.verdict_card)

        # Four-Quadrant Analysis Grid
        quadrant_title = QLabel("📊 Four-Quadrant Execution Matrix")
        quadrant_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        quadrant_title.setStyleSheet("color: #e2e8f0; margin-top: 8px;")

        quad_grid = QGridLayout()
        quad_grid.setSpacing(12)

        self.good_win_widget = self._create_quadrant_card(
            "🟢 Good Win (Strategy + Profit)", "0 Trades", "0.00 R", "$0.00", "#1b382b", "#2e7d32"
        )
        self.good_loss_widget = self._create_quadrant_card(
            "🔵 Good Loss (Strategy + Loss)", "0 Trades", "0.00 R", "$0.00", "#1a2c38", "#1565c0"
        )
        self.bad_win_widget = self._create_quadrant_card(
            "🟡 Bad Win (Violation + Profit)", "0 Trades", "0.00 R", "$0.00", "#38321a", "#f57f17"
        )
        self.bad_loss_widget = self._create_quadrant_card(
            "🔴 Bad Loss (Violation + Loss)", "0 Trades", "0.00 R", "$0.00", "#381a1a", "#c62828"
        )

        quad_grid.addWidget(self.good_win_widget, 0, 0)
        quad_grid.addWidget(self.good_loss_widget, 0, 1)
        quad_grid.addWidget(self.bad_win_widget, 1, 0)
        quad_grid.addWidget(self.bad_loss_widget, 1, 1)

        # Side-by-Side Comparison Table
        table_title = QLabel("📋 Strategy vs Execution Performance Comparison")
        table_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        table_title.setStyleSheet("color: #e2e8f0; margin-top: 8px;")

        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(5)
        self.comparison_table.setHorizontalHeaderLabels([
            "Metric", "All Trades", "Compliant (Strategy)", "Deviations (Violations)", "Emotional Trades"
        ])
        self.comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comparison_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                gridline-color: #2a3444;
                color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #121820;
                color: #8b9bb4;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #232d3d;
            }
        """)

        # Add components to container
        layout.addWidget(header_card)
        layout.addLayout(kpi_layout)
        layout.addWidget(quadrant_title)
        layout.addLayout(quad_grid)
        layout.addWidget(table_title)
        layout.addWidget(self.comparison_table)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _create_kpi_card(self, title: str, default_value: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        vbox = QVBoxLayout(card)
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 9))
        lbl_title.setStyleSheet("color: #8b9bb4;")

        lbl_val = QLabel(default_value)
        lbl_val.setObjectName("kpi_value")
        lbl_val.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl_val.setStyleSheet(f"color: {color};")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)
        return card

    def _create_quadrant_card(
        self, title: str, trades: str, r_val: str, money_val: str, bg_color: str, border_color: str
    ) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 14px;
            }}
        """)
        vbox = QVBoxLayout(card)
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_title.setStyleSheet("color: #ffffff;")

        lbl_trades = QLabel(trades)
        lbl_trades.setObjectName("quad_trades")
        lbl_trades.setFont(QFont("Segoe UI", 10))
        lbl_trades.setStyleSheet("color: #e2e8f0;")

        lbl_r = QLabel(r_val)
        lbl_r.setObjectName("quad_r")
        lbl_r.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_r.setStyleSheet("color: #ffffff;")

        lbl_money = QLabel(money_val)
        lbl_money.setObjectName("quad_money")
        lbl_money.setFont(QFont("Segoe UI", 10))
        lbl_money.setStyleSheet("color: #8b9bb4;")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_trades)
        vbox.addWidget(lbl_r)
        vbox.addWidget(lbl_money)
        return card

    def set_trades(self, trades: List[Trade]) -> None:
        """Analyze trades and populate Strategy vs Trader comparative UI elements."""
        comparison = StrategyTraderComparator.compare(trades)
        self.update_comparison(comparison)

    def update_comparison(self, comparison: StrategyVsTraderComparison) -> None:
        """Update UI widgets with calculated StrategyVsTraderComparison data."""
        comp_r = comparison.compliant_performance.net_r
        total_r = comparison.total_performance.net_r
        cost_r = comparison.deviation_cost_r

        # KPI values
        self.compliant_r_card.findChild(QLabel, "kpi_value").setText(f"{comp_r:+.2f} R")
        self.total_r_card.findChild(QLabel, "kpi_value").setText(f"{total_r:+.2f} R")
        
        cost_card_lbl = self.deviation_cost_card.findChild(QLabel, "kpi_value")
        if cost_r > 0:
            cost_card_lbl.setText(f"-{cost_r:.2f} R Lost")
            cost_card_lbl.setStyleSheet("color: #ff5252;")
        elif cost_r < 0:
            cost_card_lbl.setText(f"+{abs(cost_r):.2f} R Gained")
            cost_card_lbl.setStyleSheet("color: #00c853;")
        else:
            cost_card_lbl.setText("0.00 R")
            cost_card_lbl.setStyleSheet("color: #8b9bb4;")

        verdict_lbl = self.verdict_card.findChild(QLabel, "kpi_value")
        verdict_lbl.setText(comparison.quality_verdict.replace("_", " "))

        # Four Quadrants
        quads = comparison.four_quadrants

        self._update_quadrant_widget(self.good_win_widget, quads.good_wins_count, quads.good_wins_net_r, quads.good_wins_profit)
        self._update_quadrant_widget(self.good_loss_widget, quads.good_losses_count, quads.good_losses_net_r, quads.good_losses_profit)
        self._update_quadrant_widget(self.bad_win_widget, quads.bad_wins_count, quads.bad_wins_net_r, quads.bad_wins_profit)
        self._update_quadrant_widget(self.bad_loss_widget, quads.bad_losses_count, quads.bad_losses_net_r, quads.bad_losses_profit)

        # Populate Comparison Table
        tot = comparison.total_performance
        comp = comparison.compliant_performance
        dev = comparison.deviation_performance
        emo = comparison.emotional_performance

        metrics_rows = [
            ("Closed Trades", f"{tot.total_trades}", f"{comp.total_trades}", f"{dev.total_trades}", f"{emo.total_trades}"),
            ("Win Rate", f"{tot.win_rate * 100:.1f}%", f"{comp.win_rate * 100:.1f}%", f"{dev.win_rate * 100:.1f}%", f"{emo.win_rate * 100:.1f}%"),
            ("Net Profit ($)", f"${tot.net_profit:,.2f}", f"${comp.net_profit:,.2f}", f"${dev.net_profit:,.2f}", f"${emo.net_profit:,.2f}"),
            ("Net R", f"{tot.net_r:+.2f} R", f"{comp.net_r:+.2f} R", f"{dev.net_r:+.2f} R", f"{emo.net_r:+.2f} R"),
            ("Expectancy (R)", f"{tot.expectancy_r:+.2f} R", f"{comp.expectancy_r:+.2f} R", f"{dev.expectancy_r:+.2f} R", f"{emo.expectancy_r:+.2f} R"),
            ("Profit Factor", f"{tot.profit_factor:.2f}" if tot.profit_factor else "N/A",
                              f"{comp.profit_factor:.2f}" if comp.profit_factor else "N/A",
                              f"{dev.profit_factor:.2f}" if dev.profit_factor else "N/A",
                              f"{emo.profit_factor:.2f}" if emo.profit_factor else "N/A"),
            ("Max Drawdown (R)", f"{tot.max_drawdown_r:.2f} R", f"{comp.max_drawdown_r:.2f} R", f"{dev.max_drawdown_r:.2f} R", f"{emo.max_drawdown_r:.2f} R"),
        ]

        self.comparison_table.setRowCount(len(metrics_rows))
        for r_idx, row_data in enumerate(metrics_rows):
            for c_idx, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter if c_idx > 0 else Qt.AlignLeft | Qt.AlignVCenter)
                self.comparison_table.setItem(r_idx, c_idx, item)

    def _update_quadrant_widget(self, widget: QFrame, count: int, r_val: float, profit: float) -> None:
        widget.findChild(QLabel, "quad_trades").setText(f"{count} Trades")
        widget.findChild(QLabel, "quad_r").setText(f"{r_val:+.2f} R")
        widget.findChild(QLabel, "quad_money").setText(f"${profit:,.2f}")
