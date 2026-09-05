"""
High-performance, interactive Candlestick Chart widget with trade execution overlays and drawing annotations studio.
Renders OHLCV bars, entry/exit markers, initial and modified SL/TP lines, trendlines, horizontal rays, support/resistance zones, arrows, and text notes.
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
    QWheelEvent,
    QCursor
)
from PySide6.QtWidgets import QWidget, QInputDialog

from tradeaudit.domain.candles import Candle, TradeExecutionOverlay
from tradeaudit.domain.annotations import ChartAnnotation, AnnotationType


class CandlestickChartWidget(QWidget):
    """Custom high-resolution Candlestick (OHLCV) chart with trade overlays and drawing tools."""

    hoverInfoChanged = Signal(str)            # Emits formatted text when hovering over a candle
    annotationCreated = Signal(object)        # Emits newly created ChartAnnotation
    annotationDeleted = Signal(int)           # Emits deleted annotation ID or index
    annotationsChanged = Signal()             # Emits whenever annotations list changes

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 300)

        self._candles: List[Candle] = []
        self._overlay: Optional[TradeExecutionOverlay] = None
        self._replay_index: Optional[int] = None  # None = show all candles, int = show up to replay_index
        self._annotations: List[ChartAnnotation] = []

        # Active Drawing State
        self._active_tool: str = "PAN"  # PAN, TREND_LINE, HORIZONTAL_RAY, RECTANGLE_ZONE, TEXT_NOTE, ARROW_UP, ARROW_DOWN, ERASER
        self._draw_color: str = "#58a6ff"
        self._draw_line_width: int = 2
        self._drawing_start_point: Optional[Tuple[datetime, float]] = None  # (time, price)
        self._drawing_current_pos: Optional[QPoint] = None

        # Navigation / Viewport state
        self._bar_width = 8.0
        self._bar_spacing = 3.0
        self._offset_x = 0.0  # panning horizontal offset
        self._is_dragging = False
        self._last_mouse_pos = QPoint()
        self._hover_pos: Optional[QPoint] = None
        self._hover_candle_idx: Optional[int] = None

        # Cached Min/Max Price for coordinates
        self._last_min_p = 0.0
        self._last_max_p = 1.0
        self._last_chart_h = 1.0
        self._last_chart_w = 1.0

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

    def set_annotations(self, annotations: List[ChartAnnotation]) -> None:
        """Set list of chart annotations."""
        self._annotations = list(annotations) if annotations else []
        self.update()

    def get_annotations(self) -> List[ChartAnnotation]:
        """Return currently loaded annotations."""
        return list(self._annotations)

    def set_active_tool(self, tool_name: str) -> None:
        """Set active interactive tool (PAN, TREND_LINE, HORIZONTAL_RAY, RECTANGLE_ZONE, TEXT_NOTE, ARROW_UP, ARROW_DOWN, ERASER)."""
        self._active_tool = tool_name.upper()
        self._drawing_start_point = None
        self._drawing_current_pos = None

        if self._active_tool == "PAN":
            self.setCursor(QCursor(Qt.ArrowCursor))
        elif self._active_tool == "ERASER":
            self.setCursor(QCursor(Qt.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CrossCursor))
        self.update()

    def set_draw_color(self, color_hex: str) -> None:
        """Set active annotation color."""
        self._draw_color = color_hex
        self.update()

    def set_draw_line_width(self, width: int) -> None:
        """Set active drawing line width."""
        self._draw_line_width = max(1, min(10, width))

    def clear_annotations(self) -> None:
        """Clear all active annotations."""
        self._annotations.clear()
        self.annotationsChanged.emit()
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

    # Coordinate transformation helpers
    def price_to_y(self, price: float) -> float:
        min_p = self._last_min_p
        max_p = self._last_max_p
        price_range = max_p - min_p if max_p > min_p else 1.0
        chart_h = self._last_chart_h
        return chart_h - ((price - min_p) / price_range) * (chart_h - 20) - 10

    def y_to_price(self, y: float) -> float:
        min_p = self._last_min_p
        max_p = self._last_max_p
        price_range = max_p - min_p if max_p > min_p else 1.0
        chart_h = self._last_chart_h
        clamped_y = max(10, min(chart_h - 10, y))
        return min_p + ((chart_h - 10 - clamped_y) / max(1.0, (chart_h - 20))) * price_range

    def idx_to_x(self, i: int) -> float:
        slot = self._bar_width + self._bar_spacing
        return 20 + (i * slot) + self._offset_x

    def x_to_nearest_time(self, x: float) -> Optional[datetime]:
        visible = self._visible_candles
        if not visible:
            return None
        slot = self._bar_width + self._bar_spacing
        calc_idx = int((x - 20 - self._offset_x + (slot / 2)) / slot)
        clamped_idx = max(0, min(len(visible) - 1, calc_idx))
        return visible[clamped_idx].timestamp

    def time_to_x(self, dt: Optional[datetime]) -> float:
        visible = self._visible_candles
        if not dt or not visible:
            return 20.0 + self._offset_x
        best_idx = self._find_nearest_candle_idx(dt, visible)
        if best_idx is not None:
            return self.idx_to_x(best_idx)
        return 20.0 + self._offset_x

    def _find_nearest_candle_idx(self, target_time: Optional[datetime], candles: List[Candle]) -> Optional[int]:
        if not target_time or not candles:
            return None
        best_idx = 0
        min_diff = abs((candles[0].timestamp - target_time).total_seconds())
        for i, c in enumerate(candles):
            diff = abs((c.timestamp - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                best_idx = i
        return best_idx

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        price_scale_width = 80
        chart_w = width - price_scale_width
        chart_h = height - 40  # Reserve bottom 40px for time axis

        self._last_chart_w = chart_w
        self._last_chart_h = chart_h

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

        # Also account for annotations price range
        for ann in self._annotations:
            if ann.p1_price:
                min_p = min(min_p, ann.p1_price)
                max_p = max(max_p, ann.p1_price)
            if ann.p2_price:
                min_p = min(min_p, ann.p2_price)
                max_p = max(max_p, ann.p2_price)

        price_pad = max((max_p - min_p) * 0.08, 0.0001)
        min_p -= price_pad
        max_p += price_pad
        self._last_min_p = min_p
        self._last_max_p = max_p

        # 3. Draw Grid Lines & Price Labels
        self._draw_grid(painter, chart_w, chart_h, min_p, max_p, price_scale_width)

        # 4. Draw Candlesticks & Volumes
        max_vol = max((c.volume for c in visible_candles), default=1) or 1
        vol_max_h = chart_h * 0.18

        for idx, candle in enumerate(visible_candles):
            x = self.idx_to_x(idx)
            if x < -50 or x > chart_w + 50:
                continue

            y_open = self.price_to_y(candle.open)
            y_close = self.price_to_y(candle.close)
            y_high = self.price_to_y(candle.high)
            y_low = self.price_to_y(candle.low)

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
            self._draw_overlay(painter, chart_w, chart_h, visible_candles, price_scale_width)

        # 6. Draw User Annotations (Trendlines, Zones, Text Notes, Arrows)
        self._draw_annotations(painter, chart_w, chart_h)

        # 7. Draw Live Drawing Tool In-Progress Preview
        self._draw_live_preview(painter, chart_w, chart_h)

        # 8. Draw Crosshair and Tooltip if hovering
        if self._hover_pos and 0 <= self._hover_pos.x() <= chart_w and 0 <= self._hover_pos.y() <= chart_h:
            self._draw_crosshair(painter, chart_w, chart_h, price_scale_width, min_p, max_p - min_p)

    def _draw_grid(self, painter: QPainter, chart_w: int, chart_h: int, min_p: float, max_p: float, scale_w: int) -> None:
        """Draw background horizontal grid lines and price axis labels."""
        grid_steps = 6
        step_val = (max_p - min_p) / grid_steps
        painter.setFont(QFont("Segoe UI", 8))

        for i in range(grid_steps + 1):
            val = min_p + (i * step_val)
            y = self.price_to_y(val)

            # Horizontal grid line
            painter.setPen(QPen(self._grid_color, 1, Qt.DashLine))
            painter.drawLine(0, int(y), chart_w, int(y))

            # Price scale text
            painter.setPen(self._text_color)
            txt = f"{val:.5f}" if val < 10 else f"{val:.2f}"
            painter.drawText(QRectF(chart_w + 5, y - 8, scale_w - 10, 16), Qt.AlignLeft | Qt.AlignVCenter, txt)

    def _draw_overlay(self, painter: QPainter, chart_w: int, chart_h: int, visible_candles: List[Candle], scale_w: int) -> None:
        """Draw Entry, SL, TP, SL trail, and Exit markers."""
        overlay = self._overlay
        if not overlay:
            return

        def draw_price_level(price: float, color: QColor, label: str, line_style=Qt.DashLine):
            y = self.price_to_y(price)
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
            ex = self.idx_to_x(entry_idx)
            ey = self.price_to_y(overlay.entry_price)
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
                ex = self.idx_to_x(exit_idx)
                ey = self.price_to_y(overlay.exit_price)
                painter.setBrush(self._exit_color)
                painter.setPen(QPen(QColor("#ffffff"), 1.2))
                painter.drawEllipse(QPoint(int(ex), int(ey)), 5, 5)

    def _draw_annotations(self, painter: QPainter, chart_w: int, chart_h: int) -> None:
        """Render user drawing annotations (Trendlines, Horizontal Rays, Zones, Text, Arrows)."""
        for ann in self._annotations:
            ann_color = QColor(ann.color)
            pen = QPen(ann_color, ann.line_width)

            x1 = self.time_to_x(ann.p1_time)
            y1 = self.price_to_y(ann.p1_price)

            ann_type = ann.annotation_type.value if hasattr(ann.annotation_type, "value") else str(ann.annotation_type)

            if ann_type == AnnotationType.TREND_LINE.value:
                x2 = self.time_to_x(ann.p2_time)
                y2 = self.price_to_y(ann.p2_price)
                painter.setPen(pen)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            elif ann_type == AnnotationType.HORIZONTAL_RAY.value:
                painter.setPen(pen)
                painter.drawLine(0, int(y1), chart_w, int(y1))
                if ann.text:
                    painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    painter.drawText(int(x1 + 6), int(y1 - 4), ann.text)

            elif ann_type == AnnotationType.RECTANGLE_ZONE.value:
                x2 = self.time_to_x(ann.p2_time)
                y2 = self.price_to_y(ann.p2_price)
                rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
                fill_col = QColor(ann_color)
                fill_col.setAlpha(35)
                painter.fillRect(rect, fill_col)
                painter.setPen(pen)
                painter.drawRect(rect)
                if ann.text:
                    painter.setPen(ann_color)
                    painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                    painter.drawText(rect.adjusted(6, 6, -6, -6), Qt.AlignTop | Qt.AlignLeft, ann.text)

            elif ann_type == AnnotationType.TEXT_NOTE.value:
                painter.setPen(ann_color)
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                bg_rect = QRectF(x1, y1 - 18, 140, 22)
                bg_c = QColor("#1f2937")
                bg_c.setAlpha(200)
                painter.fillRect(bg_rect, bg_c)
                painter.drawRect(bg_rect)
                painter.drawText(bg_rect.adjusted(4, 0, -4, 0), Qt.AlignVCenter | Qt.AlignLeft, ann.text or "Note")

            elif ann_type == AnnotationType.ARROW_UP.value:
                painter.setBrush(ann_color)
                painter.setPen(QPen(QColor("#ffffff"), 1))
                arrow = QPainterPath()
                arrow.moveTo(x1, y1)
                arrow.lineTo(x1 - 7, y1 + 16)
                arrow.lineTo(x1 + 7, y1 + 16)
                arrow.closeSubpath()
                painter.drawPath(arrow)

            elif ann_type == AnnotationType.ARROW_DOWN.value:
                painter.setBrush(ann_color)
                painter.setPen(QPen(QColor("#ffffff"), 1))
                arrow = QPainterPath()
                arrow.moveTo(x1, y1)
                arrow.lineTo(x1 - 7, y1 - 16)
                arrow.lineTo(x1 + 7, y1 - 16)
                arrow.closeSubpath()
                painter.drawPath(arrow)

    def _draw_live_preview(self, painter: QPainter, chart_w: int, chart_h: int) -> None:
        """Draw interactive live drawing ghost preview while dragging."""
        if not self._drawing_start_point or not self._drawing_current_pos:
            return

        t1, p1 = self._drawing_start_point
        x1 = self.time_to_x(t1)
        y1 = self.price_to_y(p1)
        x2 = self._drawing_current_pos.x()
        y2 = self._drawing_current_pos.y()

        preview_color = QColor(self._draw_color)
        pen = QPen(preview_color, self._draw_line_width, Qt.DashLine)
        painter.setPen(pen)

        if self._active_tool == "TREND_LINE":
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        elif self._active_tool == "RECTANGLE_ZONE":
            rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            ghost_fill = QColor(preview_color)
            ghost_fill.setAlpha(25)
            painter.fillRect(rect, ghost_fill)
            painter.drawRect(rect)

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

    # Mouse & Interactive Events (Panning, Zooming, and Drawing Tools)
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            x = event.pos().x()
            y = event.pos().y()

            # Ignore clicks on right scale or bottom axis
            if x > self._last_chart_w or y > self._last_chart_h:
                return

            clicked_time = self.x_to_nearest_time(x)
            clicked_price = self.y_to_price(y)

            if self._active_tool == "PAN":
                self._is_dragging = True
                self._last_mouse_pos = event.pos()

            elif self._active_tool in ("TREND_LINE", "RECTANGLE_ZONE"):
                self._drawing_start_point = (clicked_time or datetime.utcnow(), clicked_price)
                self._drawing_current_pos = event.pos()

            elif self._active_tool == "HORIZONTAL_RAY":
                ann = ChartAnnotation(
                    trade_id=self._overlay.ticket if self._overlay else None,
                    timeframe="M15",
                    annotation_type=AnnotationType.HORIZONTAL_RAY,
                    p1_time=clicked_time,
                    p1_price=clicked_price,
                    color=self._draw_color,
                    line_width=self._draw_line_width,
                    text=f"Level {clicked_price:.4f}" if clicked_price < 10 else f"Level {clicked_price:.2f}"
                )
                self._annotations.append(ann)
                self.annotationCreated.emit(ann)
                self.annotationsChanged.emit()

            elif self._active_tool == "TEXT_NOTE":
                text, ok = QInputDialog.getText(self, "Chart Note", "Enter text for note:")
                if ok and text.strip():
                    ann = ChartAnnotation(
                        trade_id=self._overlay.ticket if self._overlay else None,
                        timeframe="M15",
                        annotation_type=AnnotationType.TEXT_NOTE,
                        p1_time=clicked_time,
                        p1_price=clicked_price,
                        color=self._draw_color,
                        line_width=self._draw_line_width,
                        text=text.strip()
                    )
                    self._annotations.append(ann)
                    self.annotationCreated.emit(ann)
                    self.annotationsChanged.emit()

            elif self._active_tool == "ARROW_UP":
                ann = ChartAnnotation(
                    trade_id=self._overlay.ticket if self._overlay else None,
                    timeframe="M15",
                    annotation_type=AnnotationType.ARROW_UP,
                    p1_time=clicked_time,
                    p1_price=clicked_price,
                    color=self._draw_color,
                    line_width=self._draw_line_width
                )
                self._annotations.append(ann)
                self.annotationCreated.emit(ann)
                self.annotationsChanged.emit()

            elif self._active_tool == "ARROW_DOWN":
                ann = ChartAnnotation(
                    trade_id=self._overlay.ticket if self._overlay else None,
                    timeframe="M15",
                    annotation_type=AnnotationType.ARROW_DOWN,
                    p1_time=clicked_time,
                    p1_price=clicked_price,
                    color=self._draw_color,
                    line_width=self._draw_line_width
                )
                self._annotations.append(ann)
                self.annotationCreated.emit(ann)
                self.annotationsChanged.emit()

            elif self._active_tool == "ERASER":
                # Find nearest annotation and remove it
                for i, ann in enumerate(reversed(self._annotations)):
                    ann_x = self.time_to_x(ann.p1_time)
                    ann_y = self.price_to_y(ann.p1_price)
                    if abs(x - ann_x) < 25 and abs(y - ann_y) < 25:
                        actual_idx = len(self._annotations) - 1 - i
                        removed = self._annotations.pop(actual_idx)
                        if removed.id:
                            self.annotationDeleted.emit(removed.id)
                        self.annotationsChanged.emit()
                        break

            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._hover_pos = event.pos()

        if self._is_dragging and self._active_tool == "PAN":
            delta_x = event.pos().x() - self._last_mouse_pos.x()
            self._offset_x += delta_x
            self._last_mouse_pos = event.pos()

        elif self._drawing_start_point and self._active_tool in ("TREND_LINE", "RECTANGLE_ZONE"):
            self._drawing_current_pos = event.pos()

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
            if self._is_dragging:
                self._is_dragging = False

            if self._drawing_start_point and self._active_tool in ("TREND_LINE", "RECTANGLE_ZONE"):
                end_time = self.x_to_nearest_time(event.pos().x())
                end_price = self.y_to_price(event.pos().y())

                t1, p1 = self._drawing_start_point
                tool_type = AnnotationType.TREND_LINE if self._active_tool == "TREND_LINE" else AnnotationType.RECTANGLE_ZONE

                ann = ChartAnnotation(
                    trade_id=self._overlay.ticket if self._overlay else None,
                    timeframe="M15",
                    annotation_type=tool_type,
                    p1_time=t1,
                    p1_price=p1,
                    p2_time=end_time or datetime.utcnow(),
                    p2_price=end_price,
                    color=self._draw_color,
                    line_width=self._draw_line_width,
                    text="Zone" if tool_type == AnnotationType.RECTANGLE_ZONE else ""
                )
                self._annotations.append(ann)
                self.annotationCreated.emit(ann)
                self.annotationsChanged.emit()

                self._drawing_start_point = None
                self._drawing_current_pos = None

            self.update()

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
