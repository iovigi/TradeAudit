"""
Quantitative Risk Research and Advanced Statistical Analytics View for TradeAudit.
Hosts Monte Carlo simulations, Risk of Ruin analysis, Rolling metrics, and Bootstrap Confidence Intervals.
"""

import logging
from typing import List, Optional

from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QFrame,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy
)
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis
)

from tradeaudit.domain.models import Trade
from tradeaudit.domain.analytics import (
    QuantResearchResult,
    MonteCarloResult,
    RuinRiskLevel
)
from tradeaudit.app.services.quant_research_analyzer import QuantResearchAnalyzer

logger = logging.getLogger("tradeaudit.ui.views.quant_research_view")


class QuantResearchView(QWidget):
    """Primary UI View for quantitative, probabilistic, and statistical risk research."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._raw_trades: List[Trade] = []
        self._analyzer = QuantResearchAnalyzer()
        self._current_result: Optional[QuantResearchResult] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #161b22;
            }
            QScrollBar:vertical {
                background: #121820;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #2a3444;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0078d7;
            }
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 1. Parameter Toolbar
        self.toolbar_card = self._create_toolbar()
        layout.addWidget(self.toolbar_card)

        # 2. KPI Cards Grid
        self.kpi_container = self._create_kpi_cards()
        layout.addWidget(self.kpi_container)

        # 3. Charts Area (Monte Carlo + Rolling Windows)
        self.charts_container = self._create_charts_area()
        layout.addWidget(self.charts_container)

        # 4. Detailed Tables & Diagnostic Insights
        self.details_container = self._create_details_area()
        layout.addWidget(self.details_container)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _create_toolbar(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                padding: 8px 14px;
            }
            QLabel {
                color: #8b9bb4;
                font-size: 11px;
                font-weight: bold;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #121820;
                color: #ffffff;
                border: 1px solid #2a3444;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 70px;
            }
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #1084e3;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        layout = QHBoxLayout(frame)
        layout.setSpacing(14)

        # Title / Icon
        title_lbl = QLabel("🔬 Quant Simulator:")
        title_lbl.setStyleSheet("color: #00a2e8; font-size: 13px; font-weight: bold;")
        layout.addWidget(title_lbl)

        # Simulations count
        layout.addWidget(QLabel("Simulations:"))
        self.combo_sims = QComboBox()
        self.combo_sims.addItems(["500", "1000", "2000", "5000"])
        self.combo_sims.setCurrentText("1000")
        layout.addWidget(self.combo_sims)

        # Horizon trades
        layout.addWidget(QLabel("Horizon (Trades):"))
        self.spin_horizon = QSpinBox()
        self.spin_horizon.setRange(10, 1000)
        self.spin_horizon.setValue(50)
        layout.addWidget(self.spin_horizon)

        # Ruin Tolerance R
        layout.addWidget(QLabel("Ruin DD (R):"))
        self.spin_ruin_r = QDoubleSpinBox()
        self.spin_ruin_r.setRange(1.0, 100.0)
        self.spin_ruin_r.setValue(15.0)
        self.spin_ruin_r.setSingleStep(1.0)
        layout.addWidget(self.spin_ruin_r)

        # Target Profit R
        layout.addWidget(QLabel("Target (R):"))
        self.spin_target_r = QDoubleSpinBox()
        self.spin_target_r.setRange(1.0, 500.0)
        self.spin_target_r.setValue(25.0)
        self.spin_target_r.setSingleStep(5.0)
        layout.addWidget(self.spin_target_r)

        # Rolling Window Size
        layout.addWidget(QLabel("Rolling Window:"))
        self.combo_window = QComboBox()
        self.combo_window.addItems(["20", "50", "100"])
        self.combo_window.setCurrentText("20")
        self.combo_window.currentIndexChanged.connect(self._on_window_size_changed)
        layout.addWidget(self.combo_window)

        layout.addStretch()

        # Run Button
        self.btn_run = QPushButton("🎲 Run Simulation")
        self.btn_run.clicked.connect(self._run_simulation)
        layout.addWidget(self.btn_run)

        return frame

    def _create_kpi_cards(self) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.card_ror = self._build_kpi_card("Risk of Ruin", "0.0%", "#ff5252")
        self.card_ci_exp = self._build_kpi_card("95% CI Expectancy", "[0.00, 0.00] R", "#00a2e8")
        self.card_mdd_95 = self._build_kpi_card("MC 95% Max DD", "-0.0 R", "#eab308")
        self.card_median_r = self._build_kpi_card("MC Median Final R", "+0.0 R", "#22c55e")
        self.card_stability = self._build_kpi_card("Edge Stability", "NO DATA", "#a855f7")

        layout.addWidget(self.card_ror, 0, 0)
        layout.addWidget(self.card_ci_exp, 0, 1)
        layout.addWidget(self.card_mdd_95, 0, 2)
        layout.addWidget(self.card_median_r, 0, 3)
        layout.addWidget(self.card_stability, 0, 4)

        return container

    def _build_kpi_card(self, title: str, initial_value: str, color_hex: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                padding: 12px 14px;
            }
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #8b9bb4; font-size: 11px; font-weight: bold;")
        lbl_title.setObjectName("card_title")

        lbl_value = QLabel(initial_value)
        lbl_value.setStyleSheet(f"color: {color_hex}; font-size: 16px; font-weight: bold;")
        lbl_value.setObjectName("card_value")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_value)
        return card

    def _update_kpi_card(self, card: QFrame, value: str, color_hex: Optional[str] = None):
        lbl = card.findChild(QLabel, "card_value")
        if lbl:
            lbl.setText(value)
            if color_hex:
                lbl.setStyleSheet(f"color: {color_hex}; font-size: 16px; font-weight: bold;")

    def _create_charts_area(self) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1. Monte Carlo Percentiles Chart
        self.chart_mc, self.view_mc = self._create_chart("🎲 Monte Carlo Resampled R-Curves (5th to 95th Percentiles)")
        self.chart_mc.legend().setVisible(True)
        self.chart_mc.legend().setAlignment(Qt.AlignBottom)
        self.chart_mc.legend().setFont(QFont("Segoe UI", 8))
        self.chart_mc.legend().setBrush(QBrush(QColor("#8b9bb4")))

        # 2. Rolling Expectancy & Win Rate Chart
        self.chart_rolling, self.view_rolling = self._create_chart("📈 Rolling Window Expectancy & Win Rate")
        self.chart_rolling.legend().setVisible(True)
        self.chart_rolling.legend().setAlignment(Qt.AlignBottom)
        self.chart_rolling.legend().setFont(QFont("Segoe UI", 8))
        self.chart_rolling.legend().setBrush(QBrush(QColor("#8b9bb4")))

        layout.addWidget(self.view_mc, 0, 0)
        layout.addWidget(self.view_rolling, 0, 1)

        return container

    def _create_chart(self, title: str):
        chart = QChart()
        chart.setTitle(title)
        chart.setTitleFont(QFont("Segoe UI", 10, QFont.Bold))
        chart.setTitleBrush(QBrush(QColor("#ffffff")))
        chart.setBackgroundBrush(QBrush(QColor("#161b22")))
        chart.setPlotAreaBackgroundBrush(QBrush(QColor("#121820")))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setMargins(QMargins(10, 10, 10, 10))

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(320)
        view.setStyleSheet("""
            QChartView {
                border: 1px solid #2a3444;
                border-radius: 6px;
                background-color: #161b22;
            }
        """)
        return chart, view

    def _create_details_area(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Left: Bootstrap CI & Quant Distribution Table
        self.table_details = QTableWidget()
        self.table_details.setColumnCount(4)
        self.table_details.setHorizontalHeaderLabels(["Metric", "Estimated Value", "95% Lower Bound", "95% Upper Bound"])
        self.table_details.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_details.verticalHeader().setVisible(False)
        self.table_details.setStyleSheet("""
            QTableWidget {
                background-color: #1a222d;
                color: #e2e8f0;
                border: 1px solid #2a3444;
                border-radius: 6px;
                gridline-color: #232d3d;
            }
            QHeaderView::section {
                background-color: #121820;
                color: #8b9bb4;
                padding: 6px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #2a3444;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)
        self.table_details.setMinimumHeight(200)

        # Right: Diagnostic Insights & Recommendations Card
        self.diag_card = QFrame()
        self.diag_card.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 6px;
                padding: 14px;
            }
        """)
        diag_vbox = QVBoxLayout(self.diag_card)
        diag_vbox.setContentsMargins(0, 0, 0, 0)
        diag_vbox.setSpacing(8)

        diag_title = QLabel("💡 Statistical Diagnostics & Risk Verdict")
        diag_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        diag_title.setStyleSheet("color: #00a2e8;")

        self.lbl_verdict = QLabel("Awaiting trade data analysis...")
        self.lbl_verdict.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        self.lbl_verdict.setWordWrap(True)

        self.lbl_recommendations = QLabel("Run simulation on imported trades to see quantitative recommendations.")
        self.lbl_recommendations.setStyleSheet("color: #8b9bb4; font-size: 11px;")
        self.lbl_recommendations.setWordWrap(True)

        diag_vbox.addWidget(diag_title)
        diag_vbox.addWidget(self.lbl_verdict)
        diag_vbox.addWidget(self.lbl_recommendations)
        diag_vbox.addStretch()

        layout.addWidget(self.table_details, stretch=3)
        layout.addWidget(self.diag_card, stretch=2)

        return container

    def set_trades(self, trades: List[Trade]):
        """Populate trades dataset and run initial analysis."""
        self._raw_trades = trades
        valid_r_count = len([t for t in trades if t.status and t.status.upper() == "CLOSED" and t.realized_r is not None])
        if valid_r_count > 0:
            self.spin_horizon.setValue(max(20, min(200, valid_r_count)))
        self._run_simulation()

    def _run_simulation(self):
        """Execute simulation with active toolbar parameters and refresh UI."""
        if not self._raw_trades:
            self._display_empty_state()
            return

        sim_count = int(self.combo_sims.currentText())
        horizon = self.spin_horizon.value()
        ruin_r = self.spin_ruin_r.value()
        target_r = self.spin_target_r.value()
        selected_window = int(self.combo_window.currentText())

        self._current_result = self._analyzer.analyze_quant_research(
            trades=self._raw_trades,
            num_simulations=sim_count,
            horizon_trades=horizon,
            ruin_threshold_r=ruin_r,
            target_r=target_r,
            max_drawdown_tolerance_r=ruin_r,
            rolling_windows=(20, 50, 100)
        )

        self._render_results(self._current_result, selected_window)

    def _on_window_size_changed(self):
        """Update rolling chart when window size combo changes."""
        if self._current_result:
            selected_window = int(self.combo_window.currentText())
            self._render_rolling_chart(self._current_result.rolling_analytics, selected_window)

    def _display_empty_state(self):
        """Display clear empty state when no trades with R are available."""
        self._update_kpi_card(self.card_ror, "N/A", "#8b9bb4")
        self._update_kpi_card(self.card_ci_exp, "N/A", "#8b9bb4")
        self._update_kpi_card(self.card_mdd_95, "N/A", "#8b9bb4")
        self._update_kpi_card(self.card_median_r, "N/A", "#8b9bb4")
        self._update_kpi_card(self.card_stability, "NO DATA", "#8b9bb4")
        self.lbl_verdict.setText("No trade records with realized R available.")
        self.lbl_recommendations.setText("Import trades from MT5 with initial stop-loss to enable quantitative risk research.")
        self.table_details.setRowCount(0)
        self.chart_mc.removeAllSeries()
        self.chart_rolling.removeAllSeries()

    def _render_results(self, result: QuantResearchResult, window_size: int):
        """Update KPI cards, charts, and details table."""
        # 1. Update KPI Cards
        ror_pct = result.risk_of_ruin.empirical_ruin_probability
        ror_color = "#22c55e" if ror_pct < 5.0 else ("#eab308" if ror_pct < 15.0 else "#ef4444")
        self._update_kpi_card(self.card_ror, f"{ror_pct:.1f}% ({result.risk_of_ruin.risk_level.value})", ror_color)

        ci = result.confidence_intervals
        self._update_kpi_card(
            self.card_ci_exp,
            f"[{ci.expectancy_ci[0]:+.2f}, {ci.expectancy_ci[1]:+.2f}] R",
            "#22c55e" if ci.is_statistically_significant else "#eab308"
        )

        mc = result.monte_carlo
        self._update_kpi_card(self.card_mdd_95, f"-{mc.max_drawdown_95th:.1f} R", "#ef4444")
        self._update_kpi_card(self.card_median_r, f"{mc.final_r_median:+.1f} R", "#00a2e8")

        rolling = result.rolling_analytics.get(window_size)
        if rolling and rolling.points:
            stability_text = f"{rolling.edge_stability_verdict} ({rolling.stability_score:.2f})"
            self._update_kpi_card(self.card_stability, stability_text, "#a855f7")
        else:
            self._update_kpi_card(self.card_stability, "INSUFFICIENT DATA", "#8b9bb4")

        # 2. Render Monte Carlo Chart
        self._render_mc_chart(mc)

        # 3. Render Rolling Chart
        self._render_rolling_chart(result.rolling_analytics, window_size)

        # 4. Populate Table
        self._render_details_table(result)

        # 5. Diagnostic Insights
        self.lbl_verdict.setText(result.risk_of_ruin.summary_verdict)
        rec_lines = [f"• {rec}" for rec in result.risk_of_ruin.recommendations]
        if ci.warnings:
            rec_lines.extend([f"⚠️ {w}" for w in ci.warnings])
        self.lbl_recommendations.setText("\n".join(rec_lines) if rec_lines else "No risk warnings.")

    def _render_mc_chart(self, mc: MonteCarloResult):
        """Render percentile curves on Monte Carlo chart."""
        self.chart_mc.removeAllSeries()
        for ax in self.chart_mc.axes():
            self.chart_mc.removeAxis(ax)

        if not mc.percentile_50th_r:
            return

        # Create series for 95th, 75th, 50th (median), 25th, 5th percentiles
        series_p95 = QLineSeries()
        series_p95.setName("95th %ile (Bullish)")
        series_p95.setPen(QPen(QColor("#22c55e"), 1.5, Qt.DashLine))

        series_p75 = QLineSeries()
        series_p75.setName("75th %ile")
        series_p75.setPen(QPen(QColor("#06b6d4"), 1.5))

        series_p50 = QLineSeries()
        series_p50.setName("50th %ile (Median)")
        series_p50.setPen(QPen(QColor("#00a2e8"), 3))

        series_p25 = QLineSeries()
        series_p25.setName("25th %ile")
        series_p25.setPen(QPen(QColor("#f59e0b"), 1.5))

        series_p5 = QLineSeries()
        series_p5.setName("5th %ile (Bearish)")
        series_p5.setPen(QPen(QColor("#ef4444"), 1.5, Qt.DashLine))

        n_steps = len(mc.percentile_50th_r)
        for i in range(n_steps):
            series_p95.append(i, mc.percentile_95th_r[i])
            series_p75.append(i, mc.percentile_75th_r[i])
            series_p50.append(i, mc.percentile_50th_r[i])
            series_p25.append(i, mc.percentile_25th_r[i])
            series_p5.append(i, mc.percentile_5th_r[i])

        self.chart_mc.addSeries(series_p95)
        self.chart_mc.addSeries(series_p75)
        self.chart_mc.addSeries(series_p50)
        self.chart_mc.addSeries(series_p25)
        self.chart_mc.addSeries(series_p5)

        axis_x = QValueAxis()
        axis_x.setTitleText("Trade Horizon")
        axis_x.setRange(0, n_steps - 1)
        axis_x.setLabelFormat("%d")
        axis_x.setLabelsColor(QColor("#8b9bb4"))
        axis_x.setGridLineColor(QColor("#232d3d"))

        min_y = min(min(mc.percentile_5th_r), -2.0)
        max_y = max(max(mc.percentile_95th_r), 2.0)
        padding = max(1.0, (max_y - min_y) * 0.1)

        axis_y = QValueAxis()
        axis_y.setTitleText("Cumulative R")
        axis_y.setRange(min_y - padding, max_y + padding)
        axis_y.setLabelFormat("%.1f R")
        axis_y.setLabelsColor(QColor("#8b9bb4"))
        axis_y.setGridLineColor(QColor("#232d3d"))

        self.chart_mc.addAxis(axis_x, Qt.AlignBottom)
        self.chart_mc.addAxis(axis_y, Qt.AlignLeft)

        for s in (series_p95, series_p75, series_p50, series_p25, series_p5):
            s.attachAxis(axis_x)
            s.attachAxis(axis_y)

    def _render_rolling_chart(self, rolling_dict: dict, window_size: int):
        """Render rolling expectancy and win rate curves."""
        self.chart_rolling.removeAllSeries()
        for ax in self.chart_rolling.axes():
            self.chart_rolling.removeAxis(ax)

        res = rolling_dict.get(window_size)
        if not res or not res.points:
            return

        series_exp = QLineSeries()
        series_exp.setName(f"Rolling Expectancy R (W={window_size})")
        series_exp.setPen(QPen(QColor("#00a2e8"), 2.5))

        series_wr = QLineSeries()
        series_wr.setName(f"Rolling Win Rate % / 100 (W={window_size})")
        series_wr.setPen(QPen(QColor("#22c55e"), 1.5, Qt.DashLine))

        series_zero = QLineSeries()
        series_zero.setName("Zero Baseline")
        series_zero.setPen(QPen(QColor("#555555"), 1, Qt.DotLine))

        for pt in res.points:
            series_exp.append(pt.trade_index, pt.expectancy_r)
            series_wr.append(pt.trade_index, pt.win_rate / 100.0)
            series_zero.append(pt.trade_index, 0.0)

        self.chart_rolling.addSeries(series_exp)
        self.chart_rolling.addSeries(series_wr)
        self.chart_rolling.addSeries(series_zero)

        min_idx = res.points[0].trade_index
        max_idx = res.points[-1].trade_index

        axis_x = QValueAxis()
        axis_x.setTitleText("Trade Sequence Index")
        axis_x.setRange(min_idx, max(min_idx + 1, max_idx))
        axis_x.setLabelFormat("%d")
        axis_x.setLabelsColor(QColor("#8b9bb4"))
        axis_x.setGridLineColor(QColor("#232d3d"))

        all_exp = [pt.expectancy_r for pt in res.points]
        min_y = min(min(all_exp), -0.5)
        max_y = max(max(all_exp), 1.0)
        pad = max(0.2, (max_y - min_y) * 0.15)

        axis_y = QValueAxis()
        axis_y.setTitleText("Expectancy (R) / Win Rate (Norm)")
        axis_y.setRange(min_y - pad, max_y + pad)
        axis_y.setLabelFormat("%.2f")
        axis_y.setLabelsColor(QColor("#8b9bb4"))
        axis_y.setGridLineColor(QColor("#232d3d"))

        self.chart_rolling.addAxis(axis_x, Qt.AlignBottom)
        self.chart_rolling.addAxis(axis_y, Qt.AlignLeft)

        series_exp.attachAxis(axis_x)
        series_exp.attachAxis(axis_y)
        series_wr.attachAxis(axis_x)
        series_wr.attachAxis(axis_y)
        series_zero.attachAxis(axis_x)
        series_zero.attachAxis(axis_y)

    def _render_details_table(self, result: QuantResearchResult):
        """Populate quantitative bootstrap confidence intervals and distribution table."""
        ci = result.confidence_intervals
        mc = result.monte_carlo
        ror = result.risk_of_ruin

        rows = [
            ("Win Rate (%)", f"{ci.win_rate_ci[0]:.1f}% - {ci.win_rate_ci[1]:.1f}%", f"{ci.win_rate_ci[0]:.1f}%", f"{ci.win_rate_ci[1]:.1f}%"),
            ("Expectancy (R)", f"[{ci.expectancy_ci[0]:+.2f}, {ci.expectancy_ci[1]:+.2f}]", f"{ci.expectancy_ci[0]:+.2f} R", f"{ci.expectancy_ci[1]:+.2f} R"),
            ("Profit Factor", f"{ci.profit_factor_ci[0]:.2f} - {ci.profit_factor_ci[1]:.2f}", f"{ci.profit_factor_ci[0]:.2f}", f"{ci.profit_factor_ci[1]:.2f}"),
            ("Average Trade (R)", f"[{ci.avg_r_ci[0]:+.2f}, {ci.avg_r_ci[1]:+.2f}]", f"{ci.avg_r_ci[0]:+.2f} R", f"{ci.avg_r_ci[1]:+.2f} R"),
            ("Monte Carlo Final R (Median)", f"{mc.final_r_median:+.2f} R", f"{mc.final_r_5th:+.2f} R (5th %ile)", f"{mc.final_r_95th:+.2f} R (95th %ile)"),
            ("Monte Carlo Max Drawdown (95th)", f"-{mc.max_drawdown_95th:.2f} R", f"-{mc.max_drawdown_median:.2f} R (Median)", f"-{mc.max_drawdown_worst:.2f} R (Worst)"),
            ("Prob. of Ruin (Empirical / Formulaic)", f"{ror.empirical_ruin_probability:.1f}% / {ror.formulaic_ruin_probability:.1f}%", f"Tolerance: {ror.max_drawdown_tolerance_r:.0f} R", f"Risk: {ror.risk_level.value}"),
            ("Probability of Target (+20R)", f"{mc.probability_of_target_r:.1f}%", "N/A", "N/A"),
            ("95th %ile Losing Streak", f"{mc.worst_consecutive_losses_95th} trades", "N/A", "N/A")
        ]

        self.table_details.setRowCount(len(rows))
        for row_idx, (col0, col1, col2, col3) in enumerate(rows):
            item0 = QTableWidgetItem(col0)
            item1 = QTableWidgetItem(col1)
            item2 = QTableWidgetItem(col2)
            item3 = QTableWidgetItem(col3)

            item0.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item1.setTextAlignment(Qt.AlignCenter)
            item2.setTextAlignment(Qt.AlignCenter)
            item3.setTextAlignment(Qt.AlignCenter)

            self.table_details.setItem(row_idx, 0, item0)
            self.table_details.setItem(row_idx, 1, item1)
            self.table_details.setItem(row_idx, 2, item2)
            self.table_details.setItem(row_idx, 3, item3)
