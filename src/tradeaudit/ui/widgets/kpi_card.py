"""
KPI summary card and grid container widgets for TradeAudit Dashboard.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame
)

from tradeaudit.domain.analytics import PerformanceMetrics, ProfitabilityVerdict


class KPICardWidget(QFrame):
    """Individual KPI summary display card."""

    def __init__(
        self,
        title: str,
        value: str = "—",
        subtitle: str = "",
        theme_color: str = "#00a2e8",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.title = title
        self._theme_color = theme_color
        self._init_ui(title, value, subtitle)

    def _init_ui(self, title: str, value: str, subtitle: str):
        self.setObjectName("KPICard")
        self.setStyleSheet(f"""
            QFrame#KPICard {{
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-left: 4px solid {self._theme_color};
                border-radius: 6px;
                padding: 10px 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.lbl_title.setStyleSheet("color: #718096; letter-spacing: 1px;")

        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_value.setStyleSheet(f"color: {self._theme_color};")

        self.lbl_subtitle = QLabel(subtitle)
        self.lbl_subtitle.setFont(QFont("Segoe UI", 9))
        self.lbl_subtitle.setStyleSheet("color: #8b9bb4;")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addWidget(self.lbl_subtitle)

    def update_card(self, value: str, subtitle: str = "", theme_color: Optional[str] = None):
        """Update displayed card data and theme color."""
        self.lbl_value.setText(value)
        self.lbl_subtitle.setText(subtitle)

        if theme_color:
            self._theme_color = theme_color
            self.setStyleSheet(f"""
                QFrame#KPICard {{
                    background-color: #1a222d;
                    border: 1px solid #2a3444;
                    border-left: 4px solid {self._theme_color};
                    border-radius: 6px;
                    padding: 10px 14px;
                }}
            """)
            self.lbl_value.setStyleSheet(f"color: {self._theme_color};")


class KPICardGridWidget(QWidget):
    """Grid container managing all dashboard KPI metric cards."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1. Total Trades
        self.card_trades = KPICardWidget(
            title="Total Trades",
            value="0",
            subtitle="0 Wins | 0 Losses",
            theme_color="#00a2e8"
        )
        # 2. Win Rate
        self.card_winrate = KPICardWidget(
            title="Win Rate",
            value="0.0%",
            subtitle="Loss Rate: 0.0%",
            theme_color="#00e676"
        )
        # 3. Net P/L
        self.card_net_profit = KPICardWidget(
            title="Net Profit",
            value="$0.00",
            subtitle="Gross: $0.00",
            theme_color="#00e676"
        )
        # 4. Net R
        self.card_net_r = KPICardWidget(
            title="Net R",
            value="0.00 R",
            subtitle="0 Trades with R",
            theme_color="#00e676"
        )
        # 5. Average R
        self.card_avg_r = KPICardWidget(
            title="Average R",
            value="0.00 R",
            subtitle="Win: 0.00 R | Loss: 0.00 R",
            theme_color="#00a2e8"
        )
        # 6. Expectancy
        self.card_expectancy = KPICardWidget(
            title="Expectancy",
            value="0.00 R / trade",
            subtitle="$0.00 / trade",
            theme_color="#00a2e8"
        )
        # 7. Profit Factor
        self.card_profit_factor = KPICardWidget(
            title="Profit Factor",
            value="—",
            subtitle="Gross Win / Gross Loss",
            theme_color="#ab47bc"
        )
        # 8. Max Drawdown
        self.card_drawdown = KPICardWidget(
            title="Max Drawdown",
            value="0.00 R",
            subtitle="$0.00 monetary DD",
            theme_color="#ff5252"
        )
        # 9. Avg Risk %
        self.card_avg_risk = KPICardWidget(
            title="Average Risk %",
            value="0.00%",
            subtitle="Per trade account risk",
            theme_color="#ffb74d"
        )
        # 10. Sample Verdict
        self.card_verdict = KPICardWidget(
            title="Edge Verdict",
            value="INSUFFICIENT_DATA",
            subtitle="Requires min 30 trades",
            theme_color="#718096"
        )

        # Populate Grid Layout (2 rows x 5 columns)
        layout.addWidget(self.card_trades, 0, 0)
        layout.addWidget(self.card_winrate, 0, 1)
        layout.addWidget(self.card_net_profit, 0, 2)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_net_r, 0, 3)

        # Clear and arrange cleanly:
        # Row 0: Trades | Win Rate | Net Profit | Net R | Average R
        # Row 1: Expectancy | Profit Factor | Max Drawdown | Avg Risk % | Edge Verdict
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

        layout.addWidget(self.card_trades, 0, 0)
        layout.addWidget(self.card_winrate, 0, 1)
        layout.addWidget(self.card_net_profit, 0, 2)
        layout.addWidget(self.card_net_r, 0, 3)
        layout.addWidget(self.card_avg_r, 0, 4)

        layout.addWidget(self.card_expectancy, 1, 0)
        layout.addWidget(self.card_profit_factor, 1, 1)
        layout.addWidget(self.card_drawdown, 1, 2)
        layout.addWidget(self.card_avg_risk, 1, 3)
        layout.addWidget(self.card_verdict, 1, 4)

    def update_metrics(self, metrics: PerformanceMetrics):
        """Populate all KPI cards with computed performance metrics."""
        # 1. Trades
        trades_sub = f"{metrics.winning_trades} W | {metrics.losing_trades} L | {metrics.breakeven_trades} BE"
        self.card_trades.update_card(str(metrics.total_trades), trades_sub, theme_color="#00a2e8")

        # 2. Win Rate
        winrate_pct = f"{metrics.win_rate * 100:.1f}%"
        winrate_sub = f"Loss Rate: {metrics.loss_rate * 100:.1f}%"
        win_color = "#00e676" if metrics.win_rate >= 0.5 else "#ffb74d" if metrics.win_rate >= 0.4 else "#ff5252"
        self.card_winrate.update_card(winrate_pct, winrate_sub, theme_color=win_color)

        # 3. Net Profit
        profit_str = f"${metrics.net_profit:+,.2f}"
        profit_sub = f"Gross Win: ${metrics.gross_profit:,.2f}"
        profit_color = "#00e676" if metrics.net_profit > 0 else "#ff5252" if metrics.net_profit < 0 else "#a0aec0"
        self.card_net_profit.update_card(profit_str, profit_sub, theme_color=profit_color)

        # 4. Net R
        net_r_str = f"{metrics.net_r:+.2f} R"
        net_r_sub = f"Evaluated: {metrics.trades_with_r} / {metrics.total_trades} trades"
        r_color = "#00e676" if metrics.net_r > 0 else "#ff5252" if metrics.net_r < 0 else "#a0aec0"
        self.card_net_r.update_card(net_r_str, net_r_sub, theme_color=r_color)

        # 5. Average R
        avg_r_str = f"{metrics.avg_r:+.2f} R"
        avg_r_sub = f"Win: +{metrics.avg_win_r:.2f}R | Loss: -{metrics.avg_loss_r:.2f}R"
        self.card_avg_r.update_card(avg_r_str, avg_r_sub, theme_color="#00a2e8")

        # 6. Expectancy
        exp_str = f"{metrics.expectancy_r:+.2f} R / trade"
        exp_sub = f"${metrics.expectancy_monetary:+.2f} / trade"
        exp_color = "#00e676" if metrics.expectancy_r > 0 else "#ff5252" if metrics.expectancy_r < 0 else "#a0aec0"
        self.card_expectancy.update_card(exp_str, exp_sub, theme_color=exp_color)

        # 7. Profit Factor
        pf_str = f"{metrics.profit_factor:.2f}" if metrics.profit_factor is not None else "∞"
        pf_sub = f"Gross Win: ${metrics.gross_profit:,.0f} | Loss: ${metrics.gross_loss:,.0f}"
        pf_color = "#00e676" if (metrics.profit_factor or 0) >= 1.5 else "#ffb74d" if (metrics.profit_factor or 0) >= 1.0 else "#ff5252"
        self.card_profit_factor.update_card(pf_str, pf_sub, theme_color=pf_color)

        # 8. Max Drawdown
        dd_str = f"-{metrics.max_drawdown_r:.2f} R"
        dd_sub = f"-${metrics.max_drawdown_monetary:,.2f} max monetary DD"
        self.card_drawdown.update_card(dd_str, dd_sub, theme_color="#ff5252")

        # 9. Avg Risk %
        risk_str = f"{metrics.avg_risk_percentage:.2f}%"
        risk_sub = "Average risk per trade"
        self.card_avg_risk.update_card(risk_str, risk_sub, theme_color="#ffb74d")

        # 10. Verdict Badge
        verdict_str = metrics.verdict.value
        if metrics.verdict == ProfitabilityVerdict.POSITIVE_EXPECTANCY:
            verdict_color = "#00e676"
            verdict_sub = f"✅ Positive edge verified ({metrics.total_trades} trades)"
        elif metrics.verdict == ProfitabilityVerdict.NEGATIVE_EXPECTANCY:
            verdict_color = "#ff5252"
            verdict_sub = f"❌ Negative expectancy ({metrics.total_trades} trades)"
        elif metrics.verdict == ProfitabilityVerdict.BREAK_EVEN:
            verdict_color = "#ffb74d"
            verdict_sub = f"⚠️ Break-even system ({metrics.total_trades} trades)"
        else:
            verdict_color = "#718096"
            verdict_sub = f"Sample < {metrics.min_sample_size} trades ({metrics.total_trades}/{metrics.min_sample_size})"

        self.card_verdict.update_card(verdict_str, verdict_sub, theme_color=verdict_color)
