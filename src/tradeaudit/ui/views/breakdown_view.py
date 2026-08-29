"""
Advanced Breakdown Analytics View component for TradeAudit (Phase 9).
Displays performance metrics across symbols, direction, sessions, weekdays, hours, contextual sequences, streaks, and emotions.
"""

from typing import List, Optional, Dict
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
    QTabWidget,
    QScrollArea
)

from tradeaudit.domain.models import Trade
from tradeaudit.domain.analytics import PerformanceMetrics
from tradeaudit.app.services.breakdown_analyzer import BreakdownAnalyzer, AdvancedBreakdownResults


class BreakdownView(QWidget):
    """Primary Breakdown Analytics tab view for TradeAudit."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._trades: List[Trade] = []
        self._init_ui()
        self.set_trades([])

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

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

        title = QLabel("🔍 Advanced Breakdown Analytics")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")

        subtitle = QLabel("Pinpoint where your edge is strongest and weakest across symbols, directions, sessions, time parameters, context sequences, and emotions.")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #8b9bb4;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_card)

        # Sub-tab Widget
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2a3444;
                background-color: #161b22;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #121820;
                color: #8b9bb4;
                padding: 8px 16px;
                font-weight: bold;
                border: 1px solid #232d3d;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1a222d;
                color: #00a2e8;
                border-top: 2px solid #00a2e8;
            }
        """)

        # Tab 1: Symbol & Direction
        self.sub_tabs.addTab(self._create_symbol_direction_tab(), "📊 Symbol & Direction")

        # Tab 2: Session & Time
        self.sub_tabs.addTab(self._create_session_time_tab(), "⏰ Session & Time")

        # Tab 3: Context & Emotion
        self.sub_tabs.addTab(self._create_context_emotion_tab(), "🧠 Context & Behavior")

        main_layout.addWidget(self.sub_tabs, stretch=1)

    def _create_styled_table(self, headers: List[str]) -> QTableWidget:
        """Helper to create standard styled QTableWidget."""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 6px;
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
        return table

    def _create_symbol_direction_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(16)

        # Symbol Breakdown Section
        sym_label = QLabel("🎯 Symbol Performance Breakdown")
        sym_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        sym_label.setStyleSheet("color: #00a2e8;")
        self.symbol_table = self._create_styled_table([
            "Symbol", "Trades", "Win Rate", "Net P/L ($)", "Net R", "Expectancy (R)", "Profit Factor", "Max DD (R)"
        ])
        inner_layout.addWidget(sym_label)
        inner_layout.addWidget(self.symbol_table)

        # Direction Breakdown Section
        dir_label = QLabel("↕️ Direction Performance Breakdown (BUY vs SELL)")
        dir_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        dir_label.setStyleSheet("color: #00a2e8;")
        self.direction_table = self._create_styled_table([
            "Direction", "Trades", "Win Rate", "Net P/L ($)", "Net R", "Expectancy (R)", "Profit Factor", "Max DD (R)"
        ])
        inner_layout.addWidget(dir_label)
        inner_layout.addWidget(self.direction_table)

        scroll.setWidget(inner_widget)
        layout.addWidget(scroll)
        return container

    def _create_session_time_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(16)

        # Session Breakdown
        sess_label = QLabel("🌐 Trading Session Breakdown (UTC)")
        sess_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        sess_label.setStyleSheet("color: #00a2e8;")
        self.session_table = self._create_styled_table([
            "Session", "Trades", "Win Rate", "Net P/L ($)", "Net R", "Expectancy (R)", "Profit Factor", "Max DD (R)"
        ])
        inner_layout.addWidget(sess_label)
        inner_layout.addWidget(self.session_table)

        # Weekday Breakdown
        day_label = QLabel("📅 Day of Week Breakdown")
        day_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        day_label.setStyleSheet("color: #00a2e8;")
        self.weekday_table = self._create_styled_table([
            "Weekday", "Trades", "Win Rate", "Net P/L ($)", "Net R", "Expectancy (R)", "Profit Factor", "Max DD (R)"
        ])
        inner_layout.addWidget(day_label)
        inner_layout.addWidget(self.weekday_table)

        # Hourly Breakdown
        hour_label = QLabel("🕐 Hourly Entry Distribution (00:00 - 23:00)")
        hour_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        hour_label.setStyleSheet("color: #00a2e8;")
        self.hour_table = self._create_styled_table([
            "Hour", "Trades", "Win Rate", "Net P/L ($)", "Net R", "Expectancy (R)", "Profit Factor", "Max DD (R)"
        ])
        inner_layout.addWidget(hour_label)
        inner_layout.addWidget(self.hour_table)

        scroll.setWidget(inner_widget)
        layout.addWidget(scroll)
        return container

    def _create_context_emotion_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(16)

        # Context Breakdown
        ctx_label = QLabel("🔄 Post-Win vs Post-Loss Contextual Sequence")
        ctx_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        ctx_label.setStyleSheet("color: #00a2e8;")
        self.context_table = self._create_styled_table([
            "Context Sequence", "Trades", "Win Rate", "Net P/L ($)", "Net R", "Expectancy (R)", "Profit Factor"
        ])
        inner_layout.addWidget(ctx_label)
        inner_layout.addWidget(self.context_table)

        # Streak Breakdown
        streak_label = QLabel("🔥 Win / Loss Streak Length Analysis")
        streak_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        streak_label.setStyleSheet("color: #00a2e8;")
        self.streak_table = self._create_styled_table([
            "Preceding Streak", "Trades", "Win Rate", "Net P/L ($)", "Net R", "Expectancy (R)", "Profit Factor"
        ])
        inner_layout.addWidget(streak_label)
        inner_layout.addWidget(self.streak_table)

        # Emotion Breakdown
        emo_label = QLabel("🧘 Emotion Tag Impact Analysis")
        emo_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        emo_label.setStyleSheet("color: #00a2e8;")
        self.emotion_table = self._create_styled_table([
            "Emotion Tag", "Trades", "Win Rate", "Net P/L ($)", "Net R", "Expectancy (R)", "Profit Factor"
        ])
        inner_layout.addWidget(emo_label)
        inner_layout.addWidget(self.emotion_table)

        scroll.setWidget(inner_widget)
        layout.addWidget(scroll)
        return container

    def set_trades(self, trades: List[Trade]) -> None:
        """Update active trade dataset and recalculate breakdown analytics across all tables."""
        self._trades = trades
        results = BreakdownAnalyzer.analyze_all(trades)

        self._populate_metrics_table(self.symbol_table, results.by_symbol)
        self._populate_metrics_table(self.direction_table, results.by_direction)
        self._populate_metrics_table(self.session_table, results.by_session)
        self._populate_metrics_table(self.weekday_table, results.by_weekday)

        # Hourly table format
        hour_metrics = {f"{h:02d}:00": m for h, m in results.by_hour.items()}
        self._populate_metrics_table(self.hour_table, hour_metrics)

        self._populate_metrics_table(self.context_table, results.by_context)
        self._populate_metrics_table(self.streak_table, results.by_streak)
        self._populate_metrics_table(self.emotion_table, results.by_emotion)

    def _populate_metrics_table(self, table: QTableWidget, data: Dict[str, PerformanceMetrics]) -> None:
        """Populate a table widget with category key and PerformanceMetrics values."""
        table.setRowCount(len(data))
        for row, (category_key, metrics) in enumerate(data.items()):
            win_rate_str = f"{metrics.win_rate * 100:.1f}%"
            profit_str = f"${metrics.net_profit:+,.2f}"
            net_r_str = f"{metrics.net_r:+.2f} R"
            expectancy_str = f"{metrics.expectancy_r:+.2f} R"
            pf_str = f"{metrics.profit_factor:.2f}" if metrics.profit_factor is not None else "N/A"
            max_dd_str = f"{metrics.max_drawdown_r:.2f} R"

            items = [
                QTableWidgetItem(str(category_key)),
                QTableWidgetItem(str(metrics.total_trades)),
                QTableWidgetItem(win_rate_str),
                QTableWidgetItem(profit_str),
                QTableWidgetItem(net_r_str),
                QTableWidgetItem(expectancy_str),
                QTableWidgetItem(pf_str),
            ]

            if table.columnCount() >= 8:
                items.append(QTableWidgetItem(max_dd_str))

            for col, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter if col > 0 else Qt.AlignLeft | Qt.AlignVCenter)

                # Color formatting for P/L and R
                if col == 3:  # Net P/L
                    if metrics.net_profit > 0:
                        item.setForeground(Qt.green)
                    elif metrics.net_profit < 0:
                        item.setForeground(Qt.red)
                elif col in (4, 5):  # Net R and Expectancy
                    val = metrics.net_r if col == 4 else metrics.expectancy_r
                    if val > 0:
                        item.setForeground(Qt.green)
                    elif val < 0:
                        item.setForeground(Qt.red)

                table.setItem(row, col, item)
