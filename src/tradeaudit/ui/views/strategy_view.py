"""
Strategy Management and Compliance View component for TradeAudit.
"""

from typing import Optional, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QGroupBox,
    QTextEdit,
    QFrame
)

from tradeaudit.domain.models import Strategy
from tradeaudit.app.services.strategy_service import StrategyService


class StrategyFormDialog(QDialog):
    """Dialog form for creating or editing a Strategy."""

    def __init__(self, parent: QWidget = None, strategy: Optional[Strategy] = None):
        super().__init__(parent)
        self.strategy = strategy or Strategy()
        self.setWindowTitle("Edit Strategy" if strategy else "Create New Strategy")
        self.resize(500, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #151c24;
                color: #ffffff;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: 500;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                background-color: #1a2330;
                color: #ffffff;
                border: 1px solid #2d3848;
                border-radius: 4px;
                padding: 6px 10px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #3b82f6;
            }
            QCheckBox {
                color: #ffffff;
            }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Name
        self.name_edit = QLineEdit(self.strategy.name)
        self.name_edit.setPlaceholderText("e.g., London Breakout Strategy")
        form_layout.addRow("Strategy Name*:", self.name_edit)

        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(self.strategy.description)
        self.desc_edit.setMaximumHeight(70)
        form_layout.addRow("Description:", self.desc_edit)

        # Allowed Direction
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["ALL", "BUY", "SELL"])
        self.direction_combo.setCurrentText(self.strategy.allowed_direction or "ALL")
        form_layout.addRow("Allowed Direction:", self.direction_combo)

        # Min R:R
        self.min_rr_spin = QDoubleSpinBox()
        self.min_rr_spin.setRange(0.0, 50.0)
        self.min_rr_spin.setSingleStep(0.25)
        self.min_rr_spin.setDecimals(2)
        if self.strategy.min_rr is not None:
            self.min_rr_spin.setValue(self.strategy.min_rr)
        else:
            self.min_rr_spin.setValue(0.0)
        form_layout.addRow("Min Planned R:R (0 = None):", self.min_rr_spin)

        # Max Risk %
        self.max_risk_spin = QDoubleSpinBox()
        self.max_risk_spin.setRange(0.0, 100.0)
        self.max_risk_spin.setSingleStep(0.5)
        self.max_risk_spin.setDecimals(2)
        if self.strategy.max_risk_pct is not None:
            self.max_risk_spin.setValue(self.strategy.max_risk_pct)
        else:
            self.max_risk_spin.setValue(0.0)
        form_layout.addRow("Max Risk % (0 = None):", self.max_risk_spin)

        # Max Trades / Day
        self.max_trades_spin = QSpinBox()
        self.max_trades_spin.setRange(0, 100)
        if self.strategy.max_trades_per_day is not None:
            self.max_trades_spin.setValue(self.strategy.max_trades_per_day)
        else:
            self.max_trades_spin.setValue(0)
        form_layout.addRow("Max Trades / Day (0 = None):", self.max_trades_spin)

        # Allowed Symbols
        self.symbols_edit = QLineEdit(", ".join(self.strategy.allowed_symbols))
        self.symbols_edit.setPlaceholderText("EURUSD, GBPUSD (leave empty for all)")
        form_layout.addRow("Allowed Symbols:", self.symbols_edit)

        # Allowed Sessions
        self.sessions_edit = QLineEdit(", ".join(self.strategy.allowed_sessions))
        self.sessions_edit.setPlaceholderText("LONDON, NEW_YORK (leave empty for all)")
        form_layout.addRow("Allowed Sessions:", self.sessions_edit)

        # Checkboxes
        self.requires_sl_cb = QCheckBox("Requires Stop Loss (SL)")
        self.requires_sl_cb.setChecked(self.strategy.requires_sl)
        form_layout.addRow("", self.requires_sl_cb)

        self.requires_tp_cb = QCheckBox("Requires Take Profit (TP)")
        self.requires_tp_cb.setChecked(self.strategy.requires_tp)
        form_layout.addRow("", self.requires_tp_cb)

        self.is_active_cb = QCheckBox("Active Strategy")
        self.is_active_cb.setChecked(self.strategy.is_active)
        form_layout.addRow("", self.is_active_cb)

        layout.addLayout(form_layout)

        # Button Box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_accept(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Strategy Name is required.")
            return

        self.strategy.name = name
        self.strategy.description = self.desc_edit.toPlainText().strip()
        self.strategy.allowed_direction = self.direction_combo.currentText()
        
        min_rr = self.min_rr_spin.value()
        self.strategy.min_rr = min_rr if min_rr > 0 else None

        max_risk = self.max_risk_spin.value()
        self.strategy.max_risk_pct = max_risk if max_risk > 0 else None

        max_trades = self.max_trades_spin.value()
        self.strategy.max_trades_per_day = max_trades if max_trades > 0 else None

        symbols_raw = self.symbols_edit.text().strip()
        self.strategy.allowed_symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()]

        sessions_raw = self.sessions_edit.text().strip()
        self.strategy.allowed_sessions = [s.strip().upper() for s in sessions_raw.split(",") if s.strip()]

        self.strategy.requires_sl = self.requires_sl_cb.isChecked()
        self.strategy.requires_tp = self.requires_tp_cb.isChecked()
        self.strategy.is_active = self.is_active_cb.isChecked()

        self.accept()


class StrategyView(QWidget):
    """View containing strategy list management and rule configuration."""

    strategy_changed = Signal()

    def __init__(self, strategy_service: Optional[StrategyService] = None, parent: QWidget = None):
        super().__init__(parent)
        self.strategy_service = strategy_service
        self._init_ui()

    def set_strategy_service(self, strategy_service: StrategyService) -> None:
        self.strategy_service = strategy_service
        self.refresh_strategies()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Bar
        header_layout = QHBoxLayout()

        title_label = QLabel("🎯 Trading Strategy Management")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.btn_new_strategy = QPushButton("➕ Create New Strategy")
        self.btn_new_strategy.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.btn_new_strategy.clicked.connect(self._on_create_strategy)
        header_layout.addWidget(self.btn_new_strategy)

        layout.addLayout(header_layout)

        # Strategies Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Direction", "Min R:R", "Max Risk %", "Allowed Symbols", "Allowed Sessions", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a222d;
                color: #e0e0e0;
                gridline-color: #2a3444;
                border: 1px solid #2a3444;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #151c24;
                color: #94a3b8;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        layout.addWidget(self.table)

    def refresh_strategies(self) -> None:
        if not self.strategy_service:
            return

        strategies = self.strategy_service.get_all_strategies()
        self.table.setRowCount(len(strategies))

        for row, strat in enumerate(strategies):
            self.table.setItem(row, 0, QTableWidgetItem(str(strat.id)))
            self.table.setItem(row, 1, QTableWidgetItem(strat.name))
            self.table.setItem(row, 2, QTableWidgetItem(strat.allowed_direction or "ALL"))
            
            min_rr_str = f"{strat.min_rr:.2f}" if strat.min_rr is not None else "-"
            self.table.setItem(row, 3, QTableWidgetItem(min_rr_str))

            max_risk_str = f"{strat.max_risk_pct:.2f}%" if strat.max_risk_pct is not None else "-"
            self.table.setItem(row, 4, QTableWidgetItem(max_risk_str))

            symbols_str = ", ".join(strat.allowed_symbols) if strat.allowed_symbols else "ALL"
            self.table.setItem(row, 5, QTableWidgetItem(symbols_str))

            sessions_str = ", ".join(strat.allowed_sessions) if strat.allowed_sessions else "ALL"
            self.table.setItem(row, 6, QTableWidgetItem(sessions_str))

            status_str = "Active" if strat.is_active else "Inactive"
            self.table.setItem(row, 7, QTableWidgetItem(status_str))

            # Action Buttons container
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(6)

            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_edit.clicked.connect(lambda _, s=strat: self._on_edit_strategy(s))
            action_layout.addWidget(btn_edit)

            btn_delete = QPushButton("Delete")
            btn_delete.setStyleSheet("background-color: #ef4444; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_delete.clicked.connect(lambda _, sid=strat.id: self._on_delete_strategy(sid))
            action_layout.addWidget(btn_delete)

            self.table.setCellWidget(row, 8, action_widget)

    def _on_create_strategy(self) -> None:
        if not self.strategy_service:
            return
        dialog = StrategyFormDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.strategy_service.create_strategy(dialog.strategy)
            self.refresh_strategies()
            self.strategy_changed.emit()

    def _on_edit_strategy(self, strategy: Strategy) -> None:
        if not self.strategy_service:
            return
        dialog = StrategyFormDialog(self, strategy)
        if dialog.exec_() == QDialog.Accepted:
            self.strategy_service.update_strategy(dialog.strategy)
            self.refresh_strategies()
            self.strategy_changed.emit()

    def _on_delete_strategy(self, strategy_id: int) -> None:
        if not self.strategy_service or not strategy_id:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this strategy?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.strategy_service.delete_strategy(strategy_id)
            self.refresh_strategies()
            self.strategy_changed.emit()
