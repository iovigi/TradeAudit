"""
Full-page Tab View for Trade Chart Visualizer, Drawing Annotations Studio & Execution Replay.
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
    QFrame,
    QMessageBox
)
from PySide6.QtGui import QFont

from tradeaudit.domain.candles import Candle, TimeFrame, TradeExecutionOverlay
from tradeaudit.domain.models import Trade
from tradeaudit.app.services.trade_chart_service import TradeChartService
from tradeaudit.app.services.chart_screenshot_service import ChartScreenshotService
from tradeaudit.app.services.trade_journal_service import TradeJournalService
from tradeaudit.ui.widgets.candlestick_chart_widget import CandlestickChartWidget
from tradeaudit.ui.widgets.chart_drawing_toolbar import ChartDrawingToolbar
from tradeaudit.ui.dialogs.trade_journal_dialog import TradeJournalDialog


class TradeChartView(QWidget):
    """Integrated full-page tab view for visual candlestick trade analysis, drawing tools, and journal review."""

    def __init__(
        self,
        chart_service: Optional[TradeChartService] = None,
        screenshot_service: Optional[ChartScreenshotService] = None,
        journal_service: Optional[TradeJournalService] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.chart_service = chart_service or TradeChartService()
        self.screenshot_service = screenshot_service or ChartScreenshotService()
        self.journal_service = journal_service or TradeJournalService()
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
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
            QPushButton#JournalBtn {
                background-color: #1f6feb;
                color: #ffffff;
                border-color: #388bfd;
                font-weight: bold;
            }
            QPushButton#JournalBtn:hover {
                background-color: #388bfd;
            }
            QComboBox {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(4)

        top_row = QHBoxLayout()
        self.title_label = QLabel("📈 Trade Chart & Drawing Studio")
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

        self.journal_btn = QPushButton("📝 Journal Review Note")
        self.journal_btn.setObjectName("JournalBtn")
        self.journal_btn.clicked.connect(self._on_open_journal_dialog)
        top_row.addWidget(self.journal_btn)

        self.snap_btn = QPushButton("📸 Snapshot")
        self.snap_btn.clicked.connect(self._on_take_snapshot)
        top_row.addWidget(self.snap_btn)

        self.copy_img_btn = QPushButton("📋 Copy Image")
        self.copy_img_btn.clicked.connect(self._on_copy_chart_image)
        top_row.addWidget(self.copy_img_btn)

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

        # Drawing Toolbar
        self.drawing_toolbar = ChartDrawingToolbar(self)
        self.drawing_toolbar.toolChanged.connect(self._on_drawing_tool_changed)
        self.drawing_toolbar.colorChanged.connect(self._on_drawing_color_changed)
        self.drawing_toolbar.clearRequested.connect(self._on_drawing_clear)
        layout.addWidget(self.drawing_toolbar)

        # Candlestick Chart Center
        self.chart_widget = CandlestickChartWidget()
        self.chart_widget.hoverInfoChanged.connect(self._on_hover_info)
        self.chart_widget.annotationCreated.connect(self._on_annotation_created)
        self.chart_widget.annotationDeleted.connect(self._on_annotation_deleted)
        layout.addWidget(self.chart_widget, 1)

        # Replay Controls
        replay_card = QFrame()
        replay_card.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 6px;
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
            QSlider::groove:horizontal {
                height: 6px;
                background: #30363d;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #1f6feb;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #58a6ff;
                border: 1px solid #1f6feb;
                width: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }
            QComboBox {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 3px 6px;
            }
        """)
        replay_layout = QHBoxLayout(replay_card)
        replay_layout.setContentsMargins(8, 6, 8, 6)
        replay_layout.setSpacing(10)

        replay_lbl = QLabel("🎬 Trade Replay:")
        replay_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px;")
        replay_layout.addWidget(replay_lbl)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self._toggle_replay)
        self.btn_play = self.play_btn
        replay_layout.addWidget(self.play_btn)

        self.step_back_btn = QPushButton("⏮ Step")
        self.step_back_btn.clicked.connect(self._on_step_back)
        replay_layout.addWidget(self.step_back_btn)

        self.step_fwd_btn = QPushButton("⏭ Step")
        self.step_fwd_btn.clicked.connect(self._on_step_forward)
        replay_layout.addWidget(self.step_fwd_btn)

        self.reset_replay_btn = QPushButton("🔄 Show All")
        self.reset_replay_btn.clicked.connect(self._on_reset_replay)
        replay_layout.addWidget(self.reset_replay_btn)

        self.replay_slider = QSlider(Qt.Horizontal)
        self.replay_slider.setMinimum(1)
        self.replay_slider.setValue(1)
        self.replay_slider.valueChanged.connect(self._on_slider_changed)
        replay_layout.addWidget(self.replay_slider, 1)

        self.bar_counter_lbl = QLabel("0 / 0 bars")
        self.bar_counter_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.bar_counter_lbl.setMinimumWidth(80)
        replay_layout.addWidget(self.bar_counter_lbl)

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
        """Populate view with trades list."""
        self._trades = trades or []
        self.trade_selector_combo.blockSignals(True)
        self.trade_selector_combo.clear()

        for t in self._trades:
            pnl_sign = "+" if (t.profit or 0) >= 0 else ""
            r_part = f" ({pnl_sign}{t.realized_r:.2f}R)" if t.realized_r is not None else ""
            label = f"#{t.position_id} {t.direction.upper()} {t.symbol} — {pnl_sign}${t.profit:.2f}{r_part}"
            self.trade_selector_combo.addItem(label)

        self.trade_selector_combo.blockSignals(False)

        if self._trades:
            self._current_trade_index = 0
            self.trade_selector_combo.setCurrentIndex(0)
            self._load_current_trade()
        else:
            self._current_trade_index = -1
            self.title_label.setText("📈 Trade Chart Visualizer")
            self.details_label.setText("No trades available in current filter selection.")
            self.chart_widget.set_data([])

    def show_trade_by_position_id(self, position_id: int) -> None:
        """Find and select a trade by its position ticket ID."""
        for i, t in enumerate(self._trades):
            if t.position_id == position_id:
                self._current_trade_index = i
                self.trade_selector_combo.blockSignals(True)
                self.trade_selector_combo.setCurrentIndex(i)
                self.trade_selector_combo.blockSignals(False)
                self._load_current_trade()
                break

    def show_trade_by_ticket(self, ticket: int) -> None:
        """Alias for show_trade_by_position_id."""
        self.show_trade_by_position_id(ticket)

    def _load_current_trade(self) -> None:
        if self._current_trade_index < 0 or self._current_trade_index >= len(self._trades):
            return

        trade = self._trades[self._current_trade_index]
        overlay = self.chart_service.build_overlay(trade)

        pnl_sign = "+" if (trade.profit or 0) >= 0 else ""
        r_str = f" ({pnl_sign}{trade.realized_r:.2f}R)" if trade.realized_r is not None else ""

        self.title_label.setText(
            f"📈 #{trade.position_id} — {trade.direction.upper()} {trade.symbol} "
            f"| Lots: {trade.volume:.2f} "
            f"| P/L: {pnl_sign}${trade.profit:.2f}{r_str}"
        )

        details = (
            f"Entry: {trade.open_price:.5f} @ {trade.open_time.strftime('%Y-%m-%d %H:%M:%S') if trade.open_time else '-'}  |  "
            f"Exit: {trade.close_price or 0:.5f} @ {trade.close_time.strftime('%Y-%m-%d %H:%M:%S') if trade.close_time else 'OPEN'}  |  "
            f"SL: {trade.initial_sl or 'None'}  |  TP: {trade.initial_tp or 'None'}  |  "
            f"Strategy: {overlay.strategy_name or 'None'}  |  "
            f"Compliance: {overlay.compliance_status or 'UNCHECKED'}"
        )
        self.details_label.setText(details)

        self.btn_prev.setEnabled(self._current_trade_index > 0)
        self.btn_next.setEnabled(self._current_trade_index < len(self._trades) - 1)

        candles = self.chart_service.get_candles_for_trade(
            trade=trade,
            timeframe=self._current_timeframe
        )

        self.chart_widget.set_data(candles=candles, overlay=overlay, reset_view=True)

        # Load Annotations
        trade_id = trade.id or trade.position_id
        annotations = self.journal_service.get_annotations(trade_id, self._current_timeframe.value)
        self.chart_widget.set_annotations(annotations)

        # Update Slider
        self._replay_timer.stop()
        self.play_btn.setText("▶ Play")
        if candles:
            self.replay_slider.blockSignals(True)
            self.replay_slider.setMaximum(len(candles))
            self.replay_slider.setValue(len(candles))
            self.replay_slider.blockSignals(False)
            self.bar_counter_lbl.setText(f"{len(candles)} / {len(candles)} bars")
        else:
            self.bar_counter_lbl.setText("0 / 0 bars")

    def _on_trade_combo_changed(self, index: int) -> None:
        if 0 <= index < len(self._trades):
            self._current_trade_index = index
            self._load_current_trade()

    def _on_prev_trade(self) -> None:
        if self._current_trade_index > 0:
            self._current_trade_index -= 1
            self.trade_selector_combo.setCurrentIndex(self._current_trade_index)

    def _on_next_trade(self) -> None:
        if self._current_trade_index < len(self._trades) - 1:
            self._current_trade_index += 1
            self.trade_selector_combo.setCurrentIndex(self._current_trade_index)

    def _on_timeframe_selected(self, tf: TimeFrame) -> None:
        self._current_timeframe = tf
        self._load_current_trade()

    def _on_fit_zoom(self) -> None:
        self.chart_widget._fit_to_view()
        self.chart_widget.update()

    def _on_hover_info(self, txt: str) -> None:
        if txt:
            self.hover_label.setText(txt)
        else:
            self.hover_label.setText("Hover over candles to inspect OHLCV data")

    # Drawing Tools Handlers
    def _on_drawing_tool_changed(self, tool_id: str) -> None:
        self.chart_widget.set_active_tool(tool_id)

    def _on_drawing_color_changed(self, color_hex: str) -> None:
        self.chart_widget.set_draw_color(color_hex)

    def _on_drawing_clear(self) -> None:
        if 0 <= self._current_trade_index < len(self._trades):
            trade = self._trades[self._current_trade_index]
            trade_id = trade.id or trade.position_id
            self.journal_service.clear_annotations(trade_id, self._current_timeframe.value)
        self.chart_widget.clear_annotations()

    def _on_annotation_created(self, ann) -> None:
        if 0 <= self._current_trade_index < len(self._trades):
            trade = self._trades[self._current_trade_index]
            ann.trade_id = trade.id or trade.position_id
            ann.timeframe = self._current_timeframe.value
            saved = self.journal_service.save_annotation(ann)
            ann.id = saved.id

    def _on_annotation_deleted(self, ann_id: int) -> None:
        self.journal_service.delete_annotation(ann_id)

    # Screenshot & Journal Handlers
    def _on_take_snapshot(self) -> None:
        if 0 <= self._current_trade_index < len(self._trades):
            trade = self._trades[self._current_trade_index]
            trade_id = trade.id or trade.position_id
            path = self.screenshot_service.capture_widget(
                widget=self.chart_widget,
                ticket=trade.position_id,
                symbol=trade.symbol,
                timeframe=self._current_timeframe.value
            )
            if path:
                self.journal_service.attach_screenshot_to_trade(trade_id, str(path))
                QMessageBox.information(
                    self,
                    "Snapshot Captured",
                    f"Chart snapshot saved and attached to journal:\n{path.name}"
                )
            else:
                QMessageBox.warning(self, "Capture Failed", "Could not capture chart screenshot.")

    def _on_copy_chart_image(self) -> None:
        ok = self.screenshot_service.copy_widget_to_clipboard(self.chart_widget)
        if ok:
            QMessageBox.information(self, "Copied", "Chart image copied to clipboard!")
        else:
            QMessageBox.warning(self, "Copy Failed", "Could not copy chart image to clipboard.")

    def _on_open_journal_dialog(self) -> None:
        if 0 <= self._current_trade_index < len(self._trades):
            trade = self._trades[self._current_trade_index]
            dialog = TradeJournalDialog(trade=trade, journal_service=self.journal_service, parent=self)
            dialog.exec()

    # Replay Handlers
    def _toggle_replay(self) -> None:
        if self._replay_timer.isActive():
            self._replay_timer.stop()
            self.play_btn.setText("▶ Play")
        else:
            if self.replay_slider.value() >= self.replay_slider.maximum():
                self.replay_slider.setValue(1)
            self._replay_timer.start(self._replay_speed_ms)
            self.play_btn.setText("⏸ Pause")

    def _on_replay_tick(self) -> None:
        val = self.replay_slider.value()
        if val < self.replay_slider.maximum():
            self.replay_slider.setValue(val + 1)
        else:
            self._replay_timer.stop()
            self.play_btn.setText("▶ Play")

    def _on_step_back(self) -> None:
        self._replay_timer.stop()
        self.play_btn.setText("▶ Play")
        val = max(1, self.replay_slider.value() - 1)
        self.replay_slider.setValue(val)

    def _on_step_forward(self) -> None:
        self._replay_timer.stop()
        self.play_btn.setText("▶ Play")
        val = min(self.replay_slider.maximum(), self.replay_slider.value() + 1)
        self.replay_slider.setValue(val)

    def _on_reset_replay(self) -> None:
        self._replay_timer.stop()
        self.play_btn.setText("▶ Play")
        self.replay_slider.setValue(self.replay_slider.maximum())
        self.chart_widget.set_replay_index(None)

    def _on_slider_changed(self, value: int) -> None:
        self.bar_counter_lbl.setText(f"{value} / {self.replay_slider.maximum()} bars")
        if value >= self.replay_slider.maximum():
            self.chart_widget.set_replay_index(None)
        else:
            self.chart_widget.set_replay_index(value)

    def _on_speed_changed(self, speed_txt: str) -> None:
        speeds = {
            "0.5x": 800,
            "1.0x": 400,
            "2.0x": 200,
            "4.0x": 80
        }
        self._replay_speed_ms = speeds.get(speed_txt, 400)
        if self._replay_timer.isActive():
            self._replay_timer.setInterval(self._replay_speed_ms)
