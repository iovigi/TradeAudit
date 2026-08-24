"""
Filter bar widget for interactive trade filtering in TradeAudit.
"""

from datetime import datetime, date
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QDateEdit,
    QPushButton,
    QFrame
)

from tradeaudit.domain.filters import (
    AnalysisFilter,
    PeriodPreset,
    DirectionFilter,
    ResultFilter
)


class CheckableComboBox(QComboBox):
    """QComboBox supporting multi-selection via checkable items."""
    selection_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.view().pressed.connect(self._on_item_pressed)
        self._placeholder_text = "All Symbols"

    def _on_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.isCheckable():
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self._update_text()
            self.selection_changed.emit()

    def _update_text(self):
        checked = self.get_checked_items()
        if not checked:
            self.setCurrentText(self._placeholder_text)
        elif len(checked) == 1:
            self.setCurrentText(checked[0])
        else:
            self.setCurrentText(f"{len(checked)} Symbols Selected")

    def set_items(self, items: List[str]):
        """Populate list with checkable items."""
        model = self.model()
        model.clear()
        for text in items:
            item = QStandardItem(text)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            model.appendRow(item)
        self._update_text()

    def get_checked_items(self) -> List[str]:
        """Return list of text strings for checked items."""
        checked = []
        model = self.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked.append(item.text())
        return checked

    def reset_selection(self):
        """Uncheck all items."""
        model = self.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item:
                item.setCheckState(Qt.Unchecked)
        self._update_text()


class FilterBarWidget(QFrame):
    """Control panel widget hosting period, direction, symbol, and result filters."""

    filter_changed = Signal(AnalysisFilter)

    PERIOD_MAP = {
        "All Time": PeriodPreset.ALL_TIME,
        "Today": PeriodPreset.TODAY,
        "Yesterday": PeriodPreset.YESTERDAY,
        "This Week": PeriodPreset.THIS_WEEK,
        "Last Week": PeriodPreset.LAST_WEEK,
        "This Month": PeriodPreset.THIS_MONTH,
        "Last Month": PeriodPreset.LAST_MONTH,
        "Custom Range": PeriodPreset.CUSTOM,
    }

    DIRECTION_MAP = {
        "All Directions": DirectionFilter.ALL,
        "BUY": DirectionFilter.BUY,
        "SELL": DirectionFilter.SELL,
    }

    RESULT_MAP = {
        "All Outcomes": ResultFilter.ALL,
        "Winners Only": ResultFilter.WINNERS,
        "Losers Only": ResultFilter.LOSERS,
        "Breakeven Only": ResultFilter.BREAKEVEN,
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._block_signals = False
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QLabel {
                color: #8b9bb4;
                font-weight: bold;
                font-size: 12px;
            }
            QComboBox, QDateEdit {
                background-color: #121820;
                color: #ffffff;
                border: 1px solid #2a3444;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QComboBox::drop-down, QDateEdit::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a222d;
                color: #ffffff;
                selection-background-color: #004080;
                border: 1px solid #2a3444;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Period Preset
        layout.addWidget(QLabel("Period:"))
        self.cmb_period = QComboBox()
        self.cmb_period.addItems(list(self.PERIOD_MAP.keys()))
        self.cmb_period.currentTextChanged.connect(self._on_period_changed)
        layout.addWidget(self.cmb_period)

        # Custom Date Inputs
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-30))
        self.date_start.setEnabled(False)
        self.date_start.dateChanged.connect(self._emit_filter_changed)

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setEnabled(False)
        self.date_end.dateChanged.connect(self._emit_filter_changed)

        layout.addWidget(self.date_start)
        layout.addWidget(QLabel("to"))
        layout.addWidget(self.date_end)

        # Direction
        layout.addWidget(QLabel("Direction:"))
        self.cmb_direction = QComboBox()
        self.cmb_direction.addItems(list(self.DIRECTION_MAP.keys()))
        self.cmb_direction.currentTextChanged.connect(self._emit_filter_changed)
        layout.addWidget(self.cmb_direction)

        # Symbols Checkable ComboBox
        layout.addWidget(QLabel("Symbols:"))
        self.cmb_symbols = CheckableComboBox()
        self.cmb_symbols.setMinimumWidth(130)
        self.cmb_symbols.selection_changed.connect(self._emit_filter_changed)
        layout.addWidget(self.cmb_symbols)

        # Result Outcome
        layout.addWidget(QLabel("Result:"))
        self.cmb_result = QComboBox()
        self.cmb_result.addItems(list(self.RESULT_MAP.keys()))
        self.cmb_result.currentTextChanged.connect(self._emit_filter_changed)
        layout.addWidget(self.cmb_result)

        layout.addStretch()

        # Reset Button
        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #232d3d;
                color: #e2e8f0;
                border: 1px solid #2a3444;
                border-radius: 4px;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: #2c3848;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #1a222d;
            }
        """)
        self.btn_reset.clicked.connect(self.reset_filters)
        layout.addWidget(self.btn_reset)

    def set_available_symbols(self, symbols: List[str]):
        """Update available symbol choices in multi-select dropdown."""
        self._block_signals = True
        current_checked = self.cmb_symbols.get_checked_items()
        unique_symbols = sorted(list({s.strip().upper() for s in symbols if s.strip()}))
        self.cmb_symbols.set_items(unique_symbols)

        # Restore checked state if applicable
        if current_checked:
            model = self.cmb_symbols.model()
            for i in range(model.rowCount()):
                item = model.item(i)
                if item and item.text() in current_checked:
                    item.setCheckState(Qt.Checked)
            self.cmb_symbols._update_text()

        self._block_signals = False

    def get_filter(self) -> AnalysisFilter:
        """Construct AnalysisFilter based on current UI state."""
        period_str = self.cmb_period.currentText()
        period_preset = self.PERIOD_MAP.get(period_str, PeriodPreset.ALL_TIME)

        custom_start = None
        custom_end = None
        if period_preset == PeriodPreset.CUSTOM:
            qstart = self.date_start.date()
            qend = self.date_end.date()
            custom_start = datetime(qstart.year(), qstart.month(), qstart.day(), 0, 0, 0)
            custom_end = datetime(qend.year(), qend.month(), qend.day(), 23, 59, 59)

        direction_str = self.cmb_direction.currentText()
        direction = self.DIRECTION_MAP.get(direction_str, DirectionFilter.ALL)

        symbols = self.cmb_symbols.get_checked_items()

        result_str = self.cmb_result.currentText()
        result = self.RESULT_MAP.get(result_str, ResultFilter.ALL)

        return AnalysisFilter(
            period=period_preset,
            custom_start_date=custom_start,
            custom_end_date=custom_end,
            direction=direction,
            symbols=symbols,
            result=result
        )

    def reset_filters(self):
        """Reset all filter controls to defaults."""
        self._block_signals = True
        self.cmb_period.setCurrentText("All Time")
        self.date_start.setEnabled(False)
        self.date_end.setEnabled(False)
        self.cmb_direction.setCurrentText("All Directions")
        self.cmb_symbols.reset_selection()
        self.cmb_result.setCurrentText("All Outcomes")
        self._block_signals = False
        self._emit_filter_changed()

    def _on_period_changed(self, text: str):
        is_custom = (text == "Custom Range")
        self.date_start.setEnabled(is_custom)
        self.date_end.setEnabled(is_custom)
        self._emit_filter_changed()

    def _emit_filter_changed(self):
        if not self._block_signals:
            self.filter_changed.emit(self.get_filter())
