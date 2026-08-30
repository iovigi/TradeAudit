"""
PySide6 View Component for generating and exporting Markdown & AI-Ready Reports (Phase 11).
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QComboBox,
    QCheckBox,
    QPushButton,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QSplitter
)

from tradeaudit.domain.models import Trade, Strategy, MT5AccountInfo
from tradeaudit.domain.filters import (
    AnalysisFilter,
    PeriodPreset,
    DirectionFilter,
    ResultFilter
)
from tradeaudit.domain.report import (
    ExportType,
    PrivacyOptions,
    ReportConfig
)
from tradeaudit.app.services.report_generator import MarkdownReportGenerator

logger = logging.getLogger("tradeaudit.ui.views.report_view")


class ReportView(QWidget):
    """Primary View for generating, viewing, and exporting Markdown & AI Audit Reports."""

    def __init__(
        self,
        report_generator: Optional[MarkdownReportGenerator] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.generator = report_generator or MarkdownReportGenerator()
        self._trades: List[Trade] = []
        self._strategies: Dict[int, Strategy] = {}
        self._account_info: Optional[MT5AccountInfo] = None
        self._last_generated_markdown: str = ""

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #1a222d;
                border: 1px solid #2a3444;
                border-radius: 8px;
                padding: 14px 18px;
            }
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        title = QLabel("📄 AI-Ready & Markdown Reporting")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")

        subtitle = QLabel("Generate institutional-grade audit reports for ChatGPT/Claude with customizable depth, privacy masking, and strategy intelligence.")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #8b9bb4;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_card)

        # Controls & Configuration Panel
        controls_card = QFrame()
        controls_card.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #232d3d;
                border-radius: 8px;
                padding: 12px;
            }
            QLabel {
                color: #8b9bb4;
                font-weight: bold;
                font-size: 11px;
            }
            QComboBox {
                background-color: #1e2633;
                color: #e2e8f0;
                border: 1px solid #2d3748;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
                min-width: 110px;
            }
            QCheckBox {
                color: #cbd5e1;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setSpacing(10)

        # Row 1: Filters & Depth
        grid_filters = QGridLayout()
        grid_filters.setSpacing(8)

        # Depth
        grid_filters.addWidget(QLabel("REPORT DEPTH:"), 0, 0)
        self.depth_combo = QComboBox()
        self.depth_combo.addItems([ExportType.STANDARD.value, ExportType.SUMMARY.value, ExportType.FULL.value])
        grid_filters.addWidget(self.depth_combo, 1, 0)

        # Period
        grid_filters.addWidget(QLabel("TIME PERIOD:"), 0, 1)
        self.period_combo = QComboBox()
        for preset in PeriodPreset:
            self.period_combo.addItem(preset.value.replace("_", " ").title(), preset.value)
        grid_filters.addWidget(self.period_combo, 1, 1)

        # Direction
        grid_filters.addWidget(QLabel("DIRECTION:"), 0, 2)
        self.direction_combo = QComboBox()
        for d in DirectionFilter:
            self.direction_combo.addItem(d.value, d.value)
        grid_filters.addWidget(self.direction_combo, 1, 2)

        # Strategy
        grid_filters.addWidget(QLabel("STRATEGY:"), 0, 3)
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("ALL STRATEGIES", None)
        grid_filters.addWidget(self.strategy_combo, 1, 3)

        # Compliance
        grid_filters.addWidget(QLabel("COMPLIANCE:"), 0, 4)
        self.compliance_combo = QComboBox()
        self.compliance_combo.addItem("ALL STATUSES", "ALL")
        self.compliance_combo.addItem("COMPLIANT ONLY", "COMPLIANT")
        self.compliance_combo.addItem("DEVIATION ONLY", "DEVIATION")
        self.compliance_combo.addItem("PARTIAL ONLY", "PARTIAL")
        self.compliance_combo.addItem("UNCHECKED", "UNCHECKED")
        grid_filters.addWidget(self.compliance_combo, 1, 4)

        # Result
        grid_filters.addWidget(QLabel("RESULT:"), 0, 5)
        self.result_combo = QComboBox()
        for r in ResultFilter:
            self.result_combo.addItem(r.value.title(), r.value)
        grid_filters.addWidget(self.result_combo, 1, 5)

        controls_layout.addLayout(grid_filters)

        # Row 2: Privacy Checkboxes and Action Buttons
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(14)

        # Privacy Checkboxes
        privacy_label = QLabel("PRIVACY:")
        privacy_label.setStyleSheet("color: #8b9bb4; font-weight: bold;")
        self.cb_mask_account = QCheckBox("Mask Account")
        self.cb_mask_account.setChecked(True)
        self.cb_hide_broker = QCheckBox("Hide Broker/Server")
        self.cb_hide_broker.setChecked(True)
        self.cb_mask_tickets = QCheckBox("Anonymize Tickets")
        self.cb_mask_tickets.setChecked(True)

        row2_layout.addWidget(privacy_label)
        row2_layout.addWidget(self.cb_mask_account)
        row2_layout.addWidget(self.cb_hide_broker)
        row2_layout.addWidget(self.cb_mask_tickets)
        row2_layout.addStretch()

        # Action Buttons
        self.btn_generate = QPushButton("⚡ Generate Report")
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #00a2e8;
                color: #ffffff;
                font-weight: bold;
                padding: 7px 18px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #008cc9;
            }
        """)
        self.btn_generate.clicked.connect(self.generate_report)

        self.btn_copy = QPushButton("📋 Copy to Clipboard")
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #232d3d;
                color: #e2e8f0;
                font-weight: bold;
                padding: 7px 14px;
                border-radius: 5px;
                border: 1px solid #334155;
            }
            QPushButton:hover {
                background-color: #2a374a;
            }
        """)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)

        self.btn_export = QPushButton("💾 Save .md")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #232d3d;
                color: #e2e8f0;
                font-weight: bold;
                padding: 7px 14px;
                border-radius: 5px;
                border: 1px solid #334155;
            }
            QPushButton:hover {
                background-color: #2a374a;
            }
        """)
        self.btn_export.clicked.connect(self._save_to_file)

        row2_layout.addWidget(self.btn_generate)
        row2_layout.addWidget(self.btn_copy)
        row2_layout.addWidget(self.btn_export)

        controls_layout.addLayout(row2_layout)
        main_layout.addWidget(controls_card)

        # Output Preview Card
        preview_card = QFrame()
        preview_card.setStyleSheet("""
            QFrame {
                background-color: #121820;
                border: 1px solid #232d3d;
                border-radius: 8px;
            }
        """)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(6)

        preview_header = QHBoxLayout()
        preview_title = QLabel("Markdown Output Preview")
        preview_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        preview_title.setStyleSheet("color: #8b9bb4;")

        self.status_feedback = QLabel("")
        self.status_feedback.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.status_feedback.setStyleSheet("color: #10b981;")

        preview_header.addWidget(preview_title)
        preview_header.addStretch()
        preview_header.addWidget(self.status_feedback)
        preview_layout.addLayout(preview_header)

        self.text_preview = QPlainTextEdit()
        self.text_preview.setFont(QFont("Consolas", 10))
        self.text_preview.setReadOnly(True)
        self.text_preview.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #21262d;
                border-radius: 6px;
                padding: 10px;
                line-height: 1.4;
            }
        """)
        preview_layout.addWidget(self.text_preview)

        main_layout.addWidget(preview_card, stretch=1)

    def set_trades(self, trades: List[Trade], account_info: Optional[MT5AccountInfo] = None) -> None:
        """Update active trades and refresh strategies."""
        self._trades = trades
        self._account_info = account_info
        if not self._last_generated_markdown:
            self.generate_report()

    def set_strategies(self, strategies: List[Strategy]) -> None:
        """Update available strategies dropdown."""
        self._strategies = {s.id: s for s in strategies if s.id is not None}
        current_sel = self.strategy_combo.currentData()

        self.strategy_combo.blockSignals(True)
        self.strategy_combo.clear()
        self.strategy_combo.addItem("ALL STRATEGIES", None)
        for s in strategies:
            if s.id is not None:
                self.strategy_combo.addItem(f"{s.name} (ID #{s.id})", s.id)

        # Restore selection if possible
        idx = self.strategy_combo.findData(current_sel)
        if idx >= 0:
            self.strategy_combo.setCurrentIndex(idx)
        self.strategy_combo.blockSignals(False)

    def build_report_config(self) -> ReportConfig:
        """Build ReportConfig from current UI controls."""
        export_type = ExportType(self.depth_combo.currentText())

        period_preset_str = self.period_combo.currentData() or PeriodPreset.ALL_TIME.value
        period_preset = PeriodPreset(period_preset_str)

        direction_str = self.direction_combo.currentData() or DirectionFilter.ALL.value
        direction = DirectionFilter(direction_str)

        strat_id = self.strategy_combo.currentData()
        compliance_str = self.compliance_combo.currentData()
        result_str = self.result_combo.currentData() or ResultFilter.ALL.value
        result_filter = ResultFilter(result_str)

        af = AnalysisFilter(
            period=period_preset,
            direction=direction,
            strategy_id=strat_id,
            compliance_status=compliance_str if compliance_str != "ALL" else None,
            result=result_filter
        )

        privacy = PrivacyOptions(
            mask_account_number=self.cb_mask_account.isChecked(),
            hide_broker=self.cb_hide_broker.isChecked(),
            mask_tickets=self.cb_mask_tickets.isChecked()
        )

        return ReportConfig(
            export_type=export_type,
            filters=af,
            privacy=privacy
        )

    def generate_report(self) -> str:
        """Generate and display markdown report."""
        config = self.build_report_config()
        md_text = self.generator.generate(
            trades=self._trades,
            config=config,
            account_info=self._account_info,
            strategies=self._strategies
        )
        self._last_generated_markdown = md_text
        self.text_preview.setPlainText(md_text)
        self._show_temp_feedback(f"✅ Generated {config.export_type.value} report ({len(md_text):,} chars).")
        return md_text

    def _copy_to_clipboard(self) -> None:
        """Copy generated markdown text to system clipboard."""
        if not self._last_generated_markdown:
            self.generate_report()

        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self._last_generated_markdown)
        self._show_temp_feedback("📋 Copied to clipboard! Ready to paste into ChatGPT.")

    def _save_to_file(self) -> None:
        """Export report to a .md file on disk."""
        if not self._last_generated_markdown:
            self.generate_report()

        default_filename = f"TradeAudit_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown Report",
            default_filename,
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)"
        )

        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self._last_generated_markdown)
                self._show_temp_feedback(f"💾 Report saved successfully to {filepath}")
            except Exception as e:
                logger.error("Failed to save report to file: %s", e)
                QMessageBox.critical(self, "Export Error", f"Failed to save file:\n{e}")

    def _show_temp_feedback(self, message: str) -> None:
        """Display a feedback status message for 4 seconds."""
        self.status_feedback.setText(message)
        QTimer.singleShot(4000, lambda: self.status_feedback.setText(""))
