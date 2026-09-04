"""
High-performance, interactive Candlestick Chart widget with trade execution overlays.
Renders OHLCV bars, entry/exit markers, initial and modified SL/TP lines, and supports zooming, panning, crosshair, and replay.
"""

from datetime import datetime
from typing import List, Optional, Tuple
import math

from PySide6.QtCore import Qt, QPoint, QRectF, Signal
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QPainterPath,
    QMouseEvent,
    QWheelEvent
)
from PySide6.QtWidgets import QWidget, QToolTip

from tradeaudit.domain.candles import Candle, TradeExecutionOverlay


class CandlestickChartWidget(QWidget):
    """Custom high-resolution Candlestick (OHLCV) chart with trade execution overlays."""

    hoverInfoChanged = Signal(str)  # Emits formatted text when hovering over a candle

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 300)

        self._candles: List[Candle] = []
        self._overlay: Optional[TradeExecutionOverlay] = None
        self._replay_index: Optional[int] = None  # None = show all candles, int = show up to replay_index

        # Navigation / Viewport state
        self._bar_width = 8.0
        self._bar_spacing = 3.0
        self._offset_x = 0.0  # panning horizontal offset
        self._is_dragging = False
        self._last_mouse_pos = QPoint()
        self._hover_pos: Optional[QPoint] = None
        self._hover_candle_idx: Optional[int] = None

        # Aesthetics Colors
        self._bg_color = QColor("#121820")
        self._panel_color = QColor("#161b22")
        self._grid_color = QColor("#1f2937")
        self._text_color = QColor("#9ca3af")
        self._bull_color = QColor("#26a69a")   # Teal Green
        self._bear_color = QColor("#ef5350")   # Crimson Red
        self._entry_color = QColor("#00a2e8")  # Cyan Blue
        self._sl_color = QColor("#ff5252")     # Red
        self._tp_color = QColor("#00e676")     # Vivid Green
        self._exit_color = QColor("#ffa726")   # Amber / Gold
        self._crosshair_color = QColor("#4b5563")

    def set_data(
        self,
        candles: List[Candle],
        overlay: Optional[TradeExecutionOverlay] = None,
        reset_view: bool = True
    ) -> None:
        """Set candles and trade overlay."""
        self._candles = candles or []
        self._overlay = overlay
        self._replay_index = None

        if reset_view:
            self._fit_to_view()

        self.update()

    def set_replay_index(self, index: Optional[int]) -> None:
        """Limit displayed candles to a replay bar index."""
        if index is not None and self._candles:
            self._replay_index = max(1, min(index, len(self._candles)))
        else:
            self._replay_index = None
        self.update()

    def _fit_to_view(self) -> None:
        """Automatically fit all bars within view width."""
        visible_count = len(self._visible_candles)
        if visible_count == 0 or self.width() <= 100:
            return

        total_avail_w = max(100, self.width() - 80)  # Reserve 80px for right price scale
        needed_slot = total_avail_w / visible_count
        self._bar_width = max(3.0, min(24.0, needed_slot * 0.75))
        self._bar_spacing = max(1.0, needed_slot * 0.25)
        self._offset_x = 0.0

    @property
    def _visible_candles(self) -> List[Candle]:
        if self._replay_index is not None and self._replay_index < len(self._candles):
            return self._candles[:self._replay_index]
        return self._candles

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        price_scale_width = 80
        chart_w = width - price_scale_width
        chart_h = height - 40  # Reserve bottom 40px for time axis

        # 1. Background
        painter.fillRect(0, 0, width, height, self._bg_color)
        painter.fillRect(chart_w, 0, price_scale_width, height, self._panel_color)
        painter.fillRect(0, chart_h, width, 40, self._panel_color)

        visible_candles = self._visible_candles
        if not visible_candles:
            painter.setPen(self._text_color)
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(QRectF(0, 0, width, height), Qt.AlignCenter, "No candlestick data available")
            return

        # 2. Determine Price Range (Min / Max)
        min_p = min(c.low for c in visible_candles)
        max_p = max(c.high for c in visible_candles)

        if self._overlay:
            if self._overlay.entry_price:
                min_p = min(min_p, self._overlay.entry_price)
                max_p = max(max_p, self._overlay.entry_price)
            if self._overlay.initial_sl:
                min_p = min(min_p, self._overlay.initial_sl)
                max_p = max(max_p, self._overlay.initial_sl)
            if self._overlay.initial_tp:
                min_p = min(min_p, self._overlay.initial_tp)
                max_p = max(max_p, self._overlay.initial_tp)
            if self._overlay.exit_price:
                min_p = min(min_p, self._overlay.exit_price)
                max_p = max(max_p, self._overlay.exit_price)

        price_pad = max((max_p - min_p) * 0.08, 0.0001)
        min_p -= price_pad
        max_p += price_pad
        price_range = max_p - min_p if max_p > min_p else 1.0

        def price_to_y(p: float) -> float:
            return chart_h - ((p - min_p) / price_range) * (chart_h - 20) - 10

        def idx_to_x(i: int) -> float:
            slot = self._bar_width + self._bar_spacing
            return 20 + (i * slot) + self._offset_x

        # 3. Draw Grid Lines & Price Labels
        self._draw_grid(painter, chart_w, chart_h, min_p, max_p, price_scale_width, price_to_y)

        # 4. Draw Candlesticks & Volumes
        max_vol = max((c.volume for c in visible_candles), default=1) or 1
        vol_max_h = chart_h * 0.18

        for idx, candle in enumerate(visible_candles):
            x = idx_to_x(idx)
            if x < -50 or x > chart_w + 50:
                continue

            y_open = price_to_y(candle.open)
            y_close = price_to_y(candle.close)
            y_high = price_to_y(candle.high)
            y_low = price_to_y(candle.low)

            is_bull = candle.is_bullish
            bar_color = self._bull_color if is_bull else self._bear_color

            # Volume Bar
            vol_h = (candle.volume / max_vol) * vol_max_h
            vol_color = QColor(bar_color)
            vol_color.setAlpha(40)
            painter.fillRect(QRectF(x - self._bar_width / 2, chart_h - vol_h, self._bar_width, vol_h), vol_color)

            # Wick Line
            painter.setPen(QPen(bar_color, 1.2))
            painter.drawLine(int(x), int(y_high), int(x), int(y_low))

            # Candle Body
            top_y = min(y_open, y_close)
            body_h = max(2.0, abs(y_close - y_open))
            painter.fillRect(QRectF(x - self._bar_width / 2, top_y, self._bar_width, body_h), bar_color)

        # 5. Draw Trade Execution Overlay (Entry, SL, TP, Exits)
        if self._overlay:
            self._draw_overlay(painter, chart_w, chart_h, visible_candles, price_scale_width, idx_to_x, price_to_y)

        # 6. Draw Crosshair and Tooltip if hovering
        if self._hover_pos and 0 <= self._hover_pos.x() <= chart_w and 0 <= self._hover_pos.y() <= chart_h:
            self._draw_crosshair(painter, chart_w, chart_h, price_scale_width, min_p, price_range)

    def _draw_grid(self, painter: QPainter, chart_w: int, chart_h: int, min_p: float, max_p: float, scale_w: int, price_to_y) -> None:
        """Draw background horizontal grid lines and price axis labels."""
        grid_steps = 6
        step_val = (max_p - min_p) / grid_steps
        painter.setFont(QFont("Segoe UI", 8))

        for i in range(grid_steps + 1):
            val = min_p + (i * step_val)
            y = price_to_y(val)
            
            # Horizontal grid line
            painter.setPen(QPen(self._grid_color, 1, Qt.DashLine))
            painter.drawLine(0, int(y), chart_w, int(y))
            
            # Price scale text
            painter.setPen(self._text_color)
            txt = f"{val:.5f}" if val < 10 else f"{val:.2f}"
            painter.drawText(QRectF(chart_w + 5, y - 8, scale_w - 10, 16), Qt.AlignLeft | Qt.AlignVCenter, txt)

    def _draw_overlay(self, painter: QPainter, chart_w: int, chart_h: int, visible_candles: List[Candle], scale_w: int, idx_to_x, price_to_y) -> None:
        """Draw Entry, SL, TP, SL trail, and Exit markers."""
        overlay = self._overlay
        if not overlay:
            return

        # Helper to draw horizontal level tag
        def draw_price_level(price: float, color: QColor, label: str, line_style=Qt.DashLine):
            y = price_to_y(price)
            if 0 <= y <= chart_h + 10:
                pen = QPen(color, 1.5, line_style)
                painter.setPen(pen)
                painter.drawLine(0, int(y), chart_w, int(y))
                
                # Badge on right scale
                badge_rect = QRectF(chart_w + 4, y - 9, scale_w - 8, 18)
                painter.fillRect(badge_rect, color)
                painter.setPen(QColor("#ffffff"))
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                txt = f"{label} {price:.4f}" if price < 10 else f"{label} {price:.2f}"
                painter.drawText(badge_rect, Qt.AlignCenter, txt)

        # 1. Entry Line
        if overlay.entry_price:
            draw_price_level(overlay.entry_price, self._entry_color, f"ENTRY ({overlay.direction})", Qt.SolidLine)

        # 2. Initial Stop Loss
        if overlay.initial_sl:
            draw_price_level(overlay.initial_sl, self._sl_color, "INIT SL", Qt.DashLine)

        # 3. Initial Take Profit
        if overlay.initial_tp:
            draw_price_level(overlay.initial_tp, self._tp_color, "TP", Qt.DashLine)

        # 4. Exit Price
        if overlay.exit_price:
            draw_price_level(overlay.exit_price, self._exit_color, "EXIT", Qt.DotLine)

        # 5. Visual Markers on nearest candle
        entry_idx = self._find_nearest_candle_idx(overlay.entry_time, visible_candles)
        if entry_idx is not None:
            ex = idx_to_x(entry_idx)
            ey = price_to_y(overlay.entry_price)
            # Draw Entry Arrow
            painter.setBrush(self._entry_color)
            painter.setPen(QPen(QColor("#ffffff"), 1))
            arrow = QPainterPath()
            if overlay.direction.upper() == "BUY":
                arrow.moveTo(ex, ey + 4)
                arrow.lineTo(ex - 6, ey + 16)
                arrow.lineTo(ex + 6, ey + 16)
                arrow.closeSubpath()
            else:
                arrow.moveTo(ex, ey - 4)
                arrow.lineTo(ex - 6, ey - 16)
                arrow.lineTo(ex + 6, ey - 16)
                arrow.closeSubpath()
            painter.drawPath(arrow)

        if overlay.exit_time and overlay.exit_price:
            exit_idx = self._find_nearest_candle_idx(overlay.exit_time, visible_candles)
            if exit_idx is not None and exit_idx < len(visible_candles):
                ex = idx_to_x(exit_idx)
                ey = price_to_y(overlay.exit_price)
                painter.setBrush(self._exit_color)
                painter.setPen(QPen(QColor("#ffffff"), 1.2))
                painter.drawEllipse(QPoint(int(ex), int(ey)), 5, 5)

    def _find_nearest_candle_idx(self, target_time: Optional[datetime], candles: List[Candle]) -> Optional[int]:
        if not target_time or not candles:
            return None
        # Binary search or closest timestamp
        best_idx = 0
        min_diff = abs((candles[0].timestamp - target_time).total_seconds())
        for i, c in enumerate(candles):
            diff = abs((c.timestamp - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                best_idx = i
        return best_idx

    def _draw_crosshair(self, painter: QPainter, chart_w: int, chart_h: int, scale_w: int, min_p: float, price_range: float) -> None:
        """Draw crosshair lines and current cursor coordinates."""
        if not self._hover_pos:
            return
        x = self._hover_pos.x()
        y = self._hover_pos.y()

        painter.setPen(QPen(self._crosshair_color, 1, Qt.DashLine))
        painter.drawLine(0, y, chart_w, y)
        painter.drawLine(x, 0, x, chart_h)

        # Hovered price box
        curr_price = min_p + ((chart_h - 10 - y) / (chart_h - 20)) * price_range
        badge = QRectF(chart_w + 2, y - 8, scale_w - 4, 16)
        painter.fillRect(badge, QColor("#374151"))
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 8))
        txt = f"{curr_price:.5f}" if curr_price < 10 else f"{curr_price:.2f}"
        painter.drawText(badge, Qt.AlignCenter, txt)

    # Mouse & Interactive Events (Panning & Zooming)
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._hover_pos = event.pos()

        if self._is_dragging:
            delta_x = event.pos().x() - self._last_mouse_pos.x()
            self._offset_x += delta_x
            self._last_mouse_pos = event.pos()

        # Check candle under hover
        slot = self._bar_width + self._bar_spacing
        calc_idx = int((event.pos().x() - 20 - self._offset_x + (slot / 2)) / slot)
        visible = self._visible_candles
        if 0 <= calc_idx < len(visible):
            c = visible[calc_idx]
            txt = (
                f"🕒 {c.timestamp.strftime('%Y-%m-%d %H:%M')}  |  "
                f"O: {c.open:.5f}  H: {c.high:.5f}  L: {c.low:.5f}  C: {c.close:.5f}  |  "
                f"Vol: {c.volume}"
            )
            self.hoverInfoChanged.emit(txt)
        else:
            self.hoverInfoChanged.emit("")

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in / Zoom out bar width."""
        delta = event.angleDelta().y()
        if delta > 0:
            self._bar_width = min(40.0, self._bar_width * 1.15)
            self._bar_spacing = max(1.0, self._bar_width * 0.3)
        else:
            self._bar_width = max(2.5, self._bar_width * 0.85)
            self._bar_spacing = max(1.0, self._bar_width * 0.3)
        self.update()
