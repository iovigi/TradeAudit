"""
QtCharts dashboard charts component for TradeAudit.
Displays Cumulative R, Drawdown R, Performance by Symbol, and BUY vs SELL comparison.
"""

from typing import List, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QFrame
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QLineSeries,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis
)

from tradeaudit.domain.analytics import PerformanceMetrics


class DashboardChartsWidget(QWidget):
    """Container hosting 4 performance visualization charts powered by QtCharts."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1. Cumulative R Line Chart
        self.chart_cum_r, self.view_cum_r = self._create_line_chart(
            title="📈 Cumulative R Equity Curve",
            line_color="#00a2e8"
        )

        # 2. Drawdown Line Chart
        self.chart_drawdown, self.view_drawdown = self._create_line_chart(
            title="📉 R Drawdown Curve",
            line_color="#ff5252"
        )

        # 3. Performance by Symbol Bar Chart
        self.chart_symbol, self.view_symbol = self._create_bar_chart(
            title="📊 Net R by Symbol"
        )

        # 4. BUY vs SELL Direction Bar Chart
        self.chart_direction, self.view_direction = self._create_bar_chart(
            title="⚖️ BUY vs SELL Performance"
        )

        # 2x2 Grid Layout
        layout.addWidget(self.view_cum_r, 0, 0)
        layout.addWidget(self.view_drawdown, 0, 1)
        layout.addWidget(self.view_symbol, 1, 0)
        layout.addWidget(self.view_direction, 1, 1)

    def _apply_chart_dark_style(self, chart: QChart, title: str):
        """Apply uniform dark theme styling to QChart."""
        chart.setTitle(title)
        chart.setTitleFont(QFont("Segoe UI", 10, QFont.Bold))
        chart.setTitleBrush(QBrush(QColor("#ffffff")))
        chart.setBackgroundBrush(QBrush(QColor("#161b22")))
        chart.setPlotAreaBackgroundBrush(QBrush(QColor("#121820")))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setMargins(self.ChartMargins(10, 10, 10, 10))
        if chart.legend():
            chart.legend().setVisible(False)

    @staticmethod
    def ChartMargins(top, bottom, left, right):
        from PySide6.QtCore import QMargins
        return QMargins(top, bottom, left, right)

    def _create_line_chart(self, title: str, line_color: str):
        chart = QChart()
        self._apply_chart_dark_style(chart, title)

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("""
            QChartView {
                border: 1px solid #2a3444;
                border-radius: 6px;
                background-color: #161b22;
            }
        """)

        return chart, view

    def _create_bar_chart(self, title: str):
        chart = QChart()
        self._apply_chart_dark_style(chart, title)

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("""
            QChartView {
                border: 1px solid #2a3444;
                border-radius: 6px;
                background-color: #161b22;
            }
        """)

        return chart, view

    def update_charts(
        self,
        metrics: PerformanceMetrics,
        by_symbol: Dict[str, PerformanceMetrics],
        by_direction: Dict[str, PerformanceMetrics]
    ):
        """Redraw all 4 charts with updated analytics data."""
        self._update_cumulative_r_chart(metrics.cumulative_r_series)
        self._update_drawdown_chart(metrics.drawdown_r_series)
        self._update_symbol_chart(by_symbol)
        self._update_direction_chart(by_direction)

    def _update_cumulative_r_chart(self, r_series: List[float]):
        self.chart_cum_r.removeAllSeries()
        for axis in list(self.chart_cum_r.axes()):
            self.chart_cum_r.removeAxis(axis)

        series = QLineSeries()
        pen = QPen(QColor("#00a2e8"))
        pen.setWidth(2)
        series.setPen(pen)

        series.append(0, 0)
        for i, val in enumerate(r_series, start=1):
            series.append(i, val)

        self.chart_cum_r.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setLabelFormat("%d")
        axis_x.setTitleText("Trades")
        axis_x.setLabelsBrush(QBrush(QColor("#8b9bb4")))
        axis_x.setGridLineColor(QColor("#232d3d"))
        axis_x.setRange(0, max(len(r_series), 1))

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.2f R")
        axis_y.setTitleText("Cumulative R")
        axis_y.setLabelsBrush(QBrush(QColor("#8b9bb4")))
        axis_y.setGridLineColor(QColor("#232d3d"))

        min_val = min(r_series) if r_series else 0.0
        max_val = max(r_series) if r_series else 0.0
        padding = max(abs(max_val - min_val) * 0.1, 1.0)
        axis_y.setRange(min_val - padding, max_val + padding)

        self.chart_cum_r.addAxis(axis_x, Qt.AlignBottom)
        self.chart_cum_r.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    def _update_drawdown_chart(self, dd_series: List[float]):
        self.chart_drawdown.removeAllSeries()
        for axis in list(self.chart_drawdown.axes()):
            self.chart_drawdown.removeAxis(axis)

        series = QLineSeries()
        pen = QPen(QColor("#ff5252"))
        pen.setWidth(2)
        series.setPen(pen)

        series.append(0, 0)
        for i, val in enumerate(dd_series, start=1):
            series.append(i, val)

        self.chart_drawdown.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setLabelFormat("%d")
        axis_x.setTitleText("Trades")
        axis_x.setLabelsBrush(QBrush(QColor("#8b9bb4")))
        axis_x.setGridLineColor(QColor("#232d3d"))
        axis_x.setRange(0, max(len(dd_series), 1))

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.2f R")
        axis_y.setTitleText("Drawdown R")
        axis_y.setLabelsBrush(QBrush(QColor("#8b9bb4")))
        axis_y.setGridLineColor(QColor("#232d3d"))

        max_dd = max(dd_series) if dd_series else 0.0
        axis_y.setRange(0, max(max_dd * 1.1, 1.0))

        self.chart_drawdown.addAxis(axis_x, Qt.AlignBottom)
        self.chart_drawdown.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    def _update_symbol_chart(self, by_symbol: Dict[str, PerformanceMetrics]):
        self.chart_symbol.removeAllSeries()
        for axis in list(self.chart_symbol.axes()):
            self.chart_symbol.removeAxis(axis)

        if not by_symbol:
            return

        bar_set_win = QBarSet("Positive R")
        bar_set_win.setBrush(QBrush(QColor("#00e676")))
        bar_set_loss = QBarSet("Negative R")
        bar_set_loss.setBrush(QBrush(QColor("#ff5252")))

        categories = []
        for sym, metrics in by_symbol.items():
            categories.append(sym)
            if metrics.net_r >= 0:
                bar_set_win.append(metrics.net_r)
                bar_set_loss.append(0.0)
            else:
                bar_set_win.append(0.0)
                bar_set_loss.append(metrics.net_r)

        series = QBarSeries()
        series.append(bar_set_win)
        series.append(bar_set_loss)
        self.chart_symbol.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsBrush(QBrush(QColor("#8b9bb4")))
        axis_x.setGridLineColor(QColor("#232d3d"))

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.1f R")
        axis_y.setTitleText("Net R")
        axis_y.setLabelsBrush(QBrush(QColor("#8b9bb4")))
        axis_y.setGridLineColor(QColor("#232d3d"))

        net_r_vals = [m.net_r for m in by_symbol.values()]
        min_val = min(net_r_vals) if net_r_vals else 0.0
        max_val = max(net_r_vals) if net_r_vals else 0.0
        padding = max(abs(max_val - min_val) * 0.1, 1.0)
        axis_y.setRange(min(min_val - padding, -1.0), max(max_val + padding, 1.0))

        self.chart_symbol.addAxis(axis_x, Qt.AlignBottom)
        self.chart_symbol.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    def _update_direction_chart(self, by_direction: Dict[str, PerformanceMetrics]):
        self.chart_direction.removeAllSeries()
        for axis in list(self.chart_direction.axes()):
            self.chart_direction.removeAxis(axis)

        buy_m = by_direction.get("BUY")
        sell_m = by_direction.get("SELL")

        bar_set_buy = QBarSet("BUY Trades")
        bar_set_buy.setBrush(QBrush(QColor("#00e676")))

        bar_set_sell = QBarSet("SELL Trades")
        bar_set_sell.setBrush(QBrush(QColor("#ff5252")))

        buy_r = buy_m.net_r if buy_m else 0.0
        sell_r = sell_m.net_r if sell_m else 0.0

        bar_set_buy.append(buy_r)
        bar_set_sell.append(sell_r)

        series = QBarSeries()
        series.append(bar_set_buy)
        series.append(bar_set_sell)
        self.chart_direction.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(["Net R Performance"])
        axis_x.setLabelsBrush(QBrush(QColor("#8b9bb4")))
        axis_x.setGridLineColor(QColor("#232d3d"))

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.1f R")
        axis_y.setTitleText("Net R")
        axis_y.setLabelsBrush(QBrush(QColor("#8b9bb4")))
        axis_y.setGridLineColor(QColor("#232d3d"))

        min_val = min(buy_r, sell_r, 0.0)
        max_val = max(buy_r, sell_r, 0.0)
        padding = max(abs(max_val - min_val) * 0.1, 1.0)
        axis_y.setRange(min_val - padding, max_val + padding)

        self.chart_direction.addAxis(axis_x, Qt.AlignBottom)
        self.chart_direction.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
