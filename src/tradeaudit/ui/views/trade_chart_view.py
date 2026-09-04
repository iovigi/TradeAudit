"""
Full-page Tab View for Trade Chart Visualizer & Execution Replay.
"""

from typing import List, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QButtonGroup,
    QSlider,
    QComboBox,
    QFrame
)
from PySide6.QtGui import QFont

from tradeaudit.domain.candles import Candle, TimeFrame, TradeExecutionOverlay
from tradeaudit.domain.models import Trade
from tradeaudit.app.services.trade_chart_service import TradeChartService
from tradeaudit.ui.widgets.candlestick_chart_widget import CandlestickChartWidget


class TradeChartView(QWidget):
    """Integrated full-page tab view for visual candlestick trade analysis."""

    def __init__(
        self,
        chart_service: Optional[TradeChartService] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.chart_service = chart_service or TradeChartService()
        self._trades: List[Trade] = []
        self._current_trade_index: int = -1
        self._current_timeframe: TimeFrame = TimeFrame.M15

        self._replay_timer = QTimer(self)
        self._replay_timer.timeout.connect(self._on_replay_tick)
        self._replay_speed_ms = 400

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(4)

        top_row = QHBoxLayout()
        self.title_label = QLabel("📈 Trade Chart Visualizer")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: #ffffff;")
        top_row.addWidget(self.title_label)

        top_row.addStretch()

        # Trade Selector Combo
        self.trade_selector_combo = QComboBox()
        self.trade_selector_combo.setMinimumWidth(260)
        self.trade_selector_combo.currentIndexChanged.connect(self._on_trade_combo_changed)
        top_row.addWidget(QLabel("Select Trade:"))
        top_row.addWidget(self.trade_selector_combo)

        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.clicked.connect(self._on_prev_trade)
        self.btn_next = QPushButton("Next ▶")
        self.btn_next.clicked.connect(self._on_next_trade)
        top_row.addWidget(self.btn_prev)
        top_row.addWidget(self.btn_next)
        header_layout.addLayout(top_row)

        self.details_label = QLabel("Select a trade to inspect historical candlestick chart and execution overlays.")
        self.details_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        header_layout.addWidget(self.details_label)

        self.hover_label = QLabel("Hover over candles to inspect OHLCV data")
        self.hover_label.setStyleSheet("color: #58a6ff; font-family: monospace; font-size: 11px;")
        header_layout.addWidget(self.hover_label)

        layout.addWidget(header_card)

        # Timeframe toolbar
        tf_panel = QFrame()
        tf_panel.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
            QPushButton:checked {
                background-color: #1f6feb;
                color: #ffffff;
                border-color: #388bfd;
            }
        """)
        tf_layout = QHBoxLayout(tf_panel)
        tf_layout.setContentsMargins(6, 4, 6, 4)
        tf_layout.setSpacing(6)

        tf_lbl = QLabel("Timeframe:")
        tf_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px;")
        tf_layout.addWidget(tf_lbl)

        self.tf_group = QButtonGroup(self)
        self.tf_group.setExclusive(True)
        timeframes = [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.M30, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
        for tf in timeframes:
            btn = QPushButton(tf.value)
            btn.setCheckable(True)
            if tf == self._current_timeframe:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, t=tf: self._on_timeframe_selected(t))
            self.tf_group.addButton(btn)
            tf_layout.addWidget(btn)

        tf_layout.addStretch()

        self.fit_btn = QPushButton("🔍 Fit Zoom")
        self.fit_btn.clicked.connect(self._on_fit_zoom)
        tf_layout.addWidget(self.fit_btn)

        layout.addWidget(tf_panel)

        # Candlestick Chart Center
        self.chart_widget = CandlestickChartWidget()
        self.chart_widget.hoverInfoChanged.connect(self._on_hover_info)
        layout.addWidget(self.chart_widget, 1)

        # Replay Controls
        replay_card = QFrame()
        replay_card.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
        """)
        replay_layout = QHBoxLayout(replay_card)
        replay_layout.setContentsMargins(8, 4, 8, 4)
        replay_layout.setSpacing(8)

        replay_lbl = QLabel("🎬 Trade Replay:")
        replay_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px;")
        replay_layout.addWidget(replay_lbl)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.clicked.connect(self._toggle_replay)
        replay_layout.addWidget(self.btn_play)

        self.btn_step_back = QPushButton("⏮ Step")
        self.btn_step_back.clicked.connect(self._on_step_back)
        replay_layout.addWidget(self.btn_step_back)

        self.btn_step_fwd = QPushButton("⏭ Step")
        self.btn_step_fwd.clicked.connect(self._on_step_forward)
        replay_layout.addWidget(self.btn_step_fwd)

        self.btn_reset = QPushButton("🔄 Show All")
        self.btn_reset.clicked.connect(self._on_reset_replay)
        replay_layout.addWidget(self.btn_reset)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setValue(1)
        self.slider.valueChanged.connect(self._on_slider_changed)
        replay_layout.addWidget(self.slider, 1)

        self.lbl_bars = QLabel("0 / 0 bars")
        self.lbl_bars.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.lbl_bars.setMinimumWidth(75)
        replay_layout.addWidget(self.lbl_bars)

        speed_lbl = QLabel("Speed:")
        speed_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        replay_layout.addWidget(speed_lbl)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "2.0x", "4.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        replay_layout.addWidget(self.speed_combo)

        layout.addWidget(replay_card)

    def set_trades(self, trades: List[Trade]) -> None:
        """Update available trade dataset for the chart view."""
        self._trades = trades or []
        self.trade_selector_combo.blockSignals(True)
        self.trade_selector_combo.clear()

        for idx, t in enumerate(self._trades):
            r_str = f" ({t.realized_r:+.2f}R)" if t.realized_r is not None else ""
            item_text = f"#{t.position_id} | {t.direction} {t.symbol} | ${t.profit:+.2f}{r_str}"
            self.trade_selector_combo.addItem(item_text, idx)

        self.trade_selector_combo.blockSignals(False)

        if self._trades:
            self._current_trade_index = 0
            self.trade_selector_combo.setCurrentIndex(0)
            self._load_trade(0)
        else:
            self._current_trade_index = -1
            self.title_label.setText("📈 Trade Chart Visualizer — No Trades")
            self.details_label.setText("No trades available for charting.")
            self.chart_widget.set_data([])

    def show_trade_by_position_id(self, position_id: int) -> None:
        """Find and display a specific trade by position ID."""
        for idx, t in enumerate(self._trades):
            if t.position_id == position_id:
                self.trade_selector_combo.setCurrentIndex(idx)
                self._load_trade(idx)
                return

    def show_trade_by_ticket(self, ticket: int) -> None:
        """Alias for show_trade_by_position_id."""
        self.show_trade_by_position_id(ticket)

    def _load_trade(self, index: int) -> None:
        if index < 0 or index >= len(self._trades):
            return
        self._current_trade_index = index
        trade = self._trades[index]
        overlay = self.chart_service.build_overlay(trade)

        pnl_sign = "+" if (trade.profit or 0) >= 0 else ""
        r_str = f" ({pnl_sign}{trade.realized_r:.2f}R)" if trade.realized_r is not None else ""
        self.title_label.setText(
            f"📈 #{trade.position_id} — {trade.direction.upper()} {trade.symbol} | Lots: {trade.volume:.2f} | P/L: {pnl_sign}${trade.profit:.2f}{r_str}"
        )

        details = (
            f"Entry: {trade.open_price:.5f} @ {trade.open_time.strftime('%Y-%m-%d %H:%M:%S')}  |  "
            f"Exit: {trade.close_price or 0:.5f} @ {trade.close_time.strftime('%Y-%m-%d %H:%M:%S') if trade.close_time else 'OPEN'}  |  "
            f"SL: {trade.initial_sl or 'None'}  |  TP: {trade.initial_tp or 'None'}  |  "
            f"Strategy: {overlay.strategy_name or 'None'}  |  "
            f"Compliance: {overlay.compliance_status or 'UNCHECKED'}"
        )
        self.details_label.setText(details)

        self.btn_prev.setEnabled(index > 0)
        self.btn_next.setEnabled(index < len(self._trades) - 1)

        candles = self.chart_service.get_candles_for_trade(
            trade=trade,
            timeframe=self._current_timeframe
        )
        self.chart_widget.set_data(candles, overlay, reset_view=True)

        self._replay_timer.stop()
        self.btn_play.setText("▶ Play")
        if candles:
            self.slider.blockSignals(True)
            self.slider.setMaximum(len(candles))
            self.slider.setValue(len(candles))
            self.slider.blockSignals(False)
            self.lbl_bars.setText(f"{len(candles)} / {len(candles)} bars")
        else:
            self.lbl_bars.setText("0 / 0 bars")

    def _on_trade_combo_changed(self, index: int) -> None:
        if 0 <= index < len(self._trades):
            self._load_trade(index)

    def _on_prev_trade(self) -> None:
        if self._current_trade_index > 0:
            self.trade_selector_combo.setCurrentIndex(self._current_trade_index - 1)

    def _on_next_trade(self) -> None:
        if self._current_trade_index < len(self._trades) - 1:
            self.trade_selector_combo.setCurrentIndex(self._current_trade_index + 1)

    def _on_timeframe_selected(self, tf: TimeFrame) -> None:
        self._current_timeframe = tf
        if self._current_trade_index >= 0:
            self._load_trade(self._current_trade_index)

    def _on_fit_zoom(self) -> None:
        self.chart_widget._fit_to_view()
        self.chart_widget.update()

    def _on_hover_info(self, txt: str) -> None:
        if txt:
            self.hover_label.setText(txt)
        else:
            self.hover_label.setText("Hover over candles to inspect OHLCV data")

    # Replay
    def _toggle_replay(self) -> None:
        if self._replay_timer.isActive():
            self._replay_timer.stop()
            self.btn_play.setText("▶ Play")
        else:
            if self.slider.value() >= self.slider.maximum():
                self.slider.setValue(1)
            self._replay_timer.start(self._replay_speed_ms)
            self.btn_play.setText("⏸ Pause")

    def _on_replay_tick(self) -> None:
        val = self.slider.value()
        if val < self.slider.maximum():
            self.slider.setValue(val + 1)
        else:
            self._replay_timer.stop()
            self.btn_play.setText("▶ Play")

    def _on_step_back(self) -> None:
        self._replay_timer.stop()
        self.btn_play.setText("▶ Play")
        val = max(1, self.slider.value() - 1)
        self.slider.setValue(val)

    def _on_step_forward(self) -> None:
        self._replay_timer.stop()
        self.btn_play.setText("▶ Play")
        val = min(self.slider.maximum(), self.slider.value() + 1)
        self.slider.setValue(val)

    def _on_reset_replay(self) -> None:
        self._replay_timer.stop()
        self.btn_play.setText("▶ Play")
        self.slider.setValue(self.slider.maximum())
        self.chart_widget.set_replay_index(None)

    def _on_slider_changed(self, value: int) -> None:
        self.lbl_bars.setText(f"{value} / {self.slider.maximum()} bars")
        if value >= self.slider.maximum():
            self.chart_widget.set_replay_index(None)
        else:
            self.chart_widget.set_replay_index(value)

    def _on_speed_changed(self, speed_txt: str) -> None:
        speeds = {"0.5x": 800, "1.0x": 400, "2.0x": 200, "4.0x": 80}
        self._replay_speed_ms = speeds.get(speed_txt, 400)
        if self._replay_timer.isActive():
            self._replay_timer.setInterval(self._replay_speed_ms)
