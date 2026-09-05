"""
Interactive Trade Journal, Setup Review, and Execution Grading Dialog.
Allows traders to document pre-trade thesis, post-trade reviews, setup checklists, execution grades, mistake tags, and attached chart screenshots.
"""

import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QWidget,
    QFrame,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QGridLayout
)
from PySide6.QtGui import QFont, QPixmap, QDesktopServices

from tradeaudit.domain.models import Trade
from tradeaudit.domain.annotations import (
    TradeJournalNote,
    TradeGrade,
    DEFAULT_SETUP_CHECKLIST,
    DEFAULT_MISTAKE_TAGS
)
from tradeaudit.app.services.trade_journal_service import TradeJournalService


class TradeJournalDialog(QDialog):
    """Modal dialog for editing trade review notes, checklists, grading, and attached screenshots."""

    noteSaved = Signal(object)  # Emits saved TradeJournalNote

    def __init__(
        self,
        trade: Trade,
        journal_service: Optional[TradeJournalService] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.trade = trade
        self.journal_service = journal_service or TradeJournalService()
        self.note = self.journal_service.get_or_create_note(trade.id or trade.position_id)

        self.setWindowTitle(f"📝 Trade Journal & Review — Ticket #{trade.position_id} ({trade.symbol})")
        self.resize(850, 720)
        self.setMinimumSize(700, 550)

        self._checklist_checkboxes = {}
        self._mistake_checkboxes = {}
        self._screenshot_items = []

        self._init_ui()
        self._load_note_data()

    def _init_ui(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QFrame#Card {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: #c9d1d9;
            }
            QLabel#HeaderTitle {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#SectionTitle {
                color: #58a6ff;
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #21262d;
                color: #ffffff;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #58a6ff;
            }
            QCheckBox {
                color: #c9d1d9;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #30363d;
                background-color: #21262d;
            }
            QCheckBox::indicator:checked {
                background-color: #26a69a;
                border-color: #26a69a;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QPushButton#SaveBtn {
                background-color: #238636;
                color: #ffffff;
                border-color: #2ea043;
            }
            QPushButton#SaveBtn:hover {
                background-color: #2ea043;
            }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                background-color: #21262d;
                height: 14px;
            }
            QProgressBar::chunk {
                background-color: #26a69a;
                border-radius: 3px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Top Trade Summary Card
        top_card = QFrame()
        top_card.setObjectName("Card")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(4)

        title_row = QHBoxLayout()
        trade_dir = self.trade.direction.upper()
        dir_color = "#26a69a" if trade_dir == "BUY" else "#ef5350"
        r_str = f"{self.trade.realized_r:+.2f}R" if self.trade.realized_r is not None else "N/A"
        pnl_str = f"${self.trade.net_profit:+.2f}"

        title_lbl = QLabel(f"Trade #{self.trade.position_id} — {self.trade.symbol} ({trade_dir}) | P/L: {pnl_str} ({r_str})")
        title_lbl.setObjectName("HeaderTitle")
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        top_layout.addLayout(title_row)

        details_lbl = QLabel(
            f"Open: {self.trade.open_time.strftime('%Y-%m-%d %H:%M') if self.trade.open_time else '-'}  |  "
            f"Close: {self.trade.close_time.strftime('%Y-%m-%d %H:%M') if self.trade.close_time else 'OPEN'}  |  "
            f"Lots: {self.trade.volume:.2f}  |  Initial SL: {self.trade.initial_sl or '-'}  |  Initial TP: {self.trade.initial_tp or '-'}"
        )
        details_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        top_layout.addWidget(details_lbl)

        main_layout.addWidget(top_card)

        # 2. Scrollable Journal Form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        form_layout = QVBoxLayout(content_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)

        # Setup & Grade Row
        setup_card = QFrame()
        setup_card.setObjectName("Card")
        setup_layout = QHBoxLayout(setup_card)

        setup_name_lbl = QLabel("🎯 Setup / Strategy Name:")
        setup_name_lbl.setStyleSheet("font-weight: bold;")
        setup_layout.addWidget(setup_name_lbl)

        self.setup_combo = QComboBox()
        self.setup_combo.setEditable(True)
        self.setup_combo.addItems([
            "",
            "Liquidity Sweep & MSS",
            "Order Block / FVG Retest",
            "London Breakout",
            "Asia Range Expansion",
            "Trend Pullback",
            "Support / Resistance Reversal",
            "Break & Retest"
        ])
        setup_layout.addWidget(self.setup_combo, 2)

        grade_lbl = QLabel("⭐ Execution Grade:")
        grade_lbl.setStyleSheet("font-weight: bold;")
        setup_layout.addWidget(grade_lbl)

        self.grade_combo = QComboBox()
        for g in [TradeGrade.A_PLUS.value, TradeGrade.A.value, TradeGrade.B.value, TradeGrade.C.value, TradeGrade.D.value, TradeGrade.F.value]:
            self.grade_combo.addItem(g)
        setup_layout.addWidget(self.grade_combo, 1)

        form_layout.addWidget(setup_card)

        # Pre-Trade Checklist Card
        checklist_card = QFrame()
        checklist_card.setObjectName("Card")
        chk_layout = QVBoxLayout(checklist_card)
        chk_layout.setSpacing(6)

        chk_header = QHBoxLayout()
        chk_title = QLabel("📋 Pre-Trade Setup Checklist")
        chk_title.setObjectName("SectionTitle")
        chk_header.addWidget(chk_title)
        chk_header.addStretch()

        self.chk_progress = QProgressBar()
        self.chk_progress.setFixedWidth(160)
        self.chk_progress.setValue(0)
        chk_header.addWidget(self.chk_progress)
        chk_layout.addLayout(chk_header)

        # Checklist items in 2 columns
        chk_grid = QGridLayout()
        col = 0
        row = 0
        for criterion in DEFAULT_SETUP_CHECKLIST.keys():
            cb = QCheckBox(criterion)
            cb.stateChanged.connect(self._update_checklist_progress)
            self._checklist_checkboxes[criterion] = cb
            chk_grid.addWidget(cb, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        chk_layout.addLayout(chk_grid)

        form_layout.addWidget(checklist_card)

        # Pre-Trade Thesis & Post-Trade Review (2 Columns)
        notes_card = QFrame()
        notes_card.setObjectName("Card")
        notes_layout = QHBoxLayout(notes_card)
        notes_layout.setSpacing(10)

        pre_col = QVBoxLayout()
        pre_title = QLabel("💡 Pre-Trade Thesis & Market Context")
        pre_title.setObjectName("SectionTitle")
        pre_col.addWidget(pre_title)
        self.pre_thesis_text = QTextEdit()
        self.pre_thesis_text.setPlaceholderText("What was the market structure, HTF narrative, catalyst, and invalidation criteria before entering?")
        self.pre_thesis_text.setMinimumHeight(100)
        pre_col.addWidget(self.pre_thesis_text)
        notes_layout.addLayout(pre_col)

        post_col = QVBoxLayout()
        post_title = QLabel("🔍 Post-Trade Review & Lessons Learned")
        post_title.setObjectName("SectionTitle")
        post_col.addWidget(post_title)
        self.post_review_text = QTextEdit()
        self.post_review_text.setPlaceholderText("How was execution? Did you follow your plan, manage emotions, or exit early/late?")
        self.post_review_text.setMinimumHeight(100)
        post_col.addWidget(self.post_review_text)
        notes_layout.addLayout(post_col)

        form_layout.addWidget(notes_card)

        # Mistakes Tags Card
        mistakes_card = QFrame()
        mistakes_card.setObjectName("Card")
        mst_layout = QVBoxLayout(mistakes_card)
        mst_layout.setSpacing(6)

        mst_title = QLabel("⚠️ Identified Execution Mistakes & Psychological Traps")
        mst_title.setObjectName("SectionTitle")
        mst_layout.addWidget(mst_title)

        mst_grid = QGridLayout()
        col = 0
        row = 0
        for tag in DEFAULT_MISTAKE_TAGS:
            cb = QCheckBox(tag)
            self._mistake_checkboxes[tag] = cb
            mst_grid.addWidget(cb, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        mst_layout.addLayout(mst_grid)

        form_layout.addWidget(mistakes_card)

        # Attached Screenshots Gallery Card
        shots_card = QFrame()
        shots_card.setObjectName("Card")
        shots_layout = QVBoxLayout(shots_card)
        shots_layout.setSpacing(6)

        shots_header = QHBoxLayout()
        shots_title = QLabel("📸 Attached Candlestick Chart Screenshots")
        shots_title.setObjectName("SectionTitle")
        shots_header.addWidget(shots_title)
        shots_header.addStretch()

        attach_btn = QPushButton("➕ Attach Image...")
        attach_btn.clicked.connect(self._on_attach_custom_image)
        shots_header.addWidget(attach_btn)
        shots_layout.addLayout(shots_header)

        self.screenshots_list = QListWidget()
        self.screenshots_list.setMaximumHeight(90)
        self.screenshots_list.itemDoubleClicked.connect(self._on_open_screenshot_item)
        shots_layout.addWidget(self.screenshots_list)

        actions_row = QHBoxLayout()
        open_shot_btn = QPushButton("👁️ Open Selected Image")
        open_shot_btn.clicked.connect(self._on_open_selected_screenshot)
        remove_shot_btn = QPushButton("🗑️ Remove Image")
        remove_shot_btn.clicked.connect(self._on_remove_selected_screenshot)
        actions_row.addWidget(open_shot_btn)
        actions_row.addWidget(remove_shot_btn)
        actions_row.addStretch()
        shots_layout.addLayout(actions_row)

        form_layout.addWidget(shots_card)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # 3. Bottom Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Save Journal Entry")
        save_btn.setObjectName("SaveBtn")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

    def _load_note_data(self) -> None:
        """Populate form with existing note data."""
        self.setup_combo.setEditText(self.note.setup_name or "")
        self.grade_combo.setCurrentText(self.note.rating or TradeGrade.A.value)
        self.pre_thesis_text.setPlainText(self.note.pre_trade_thesis or "")
        self.post_review_text.setPlainText(self.note.post_trade_review or "")

        # Checklists
        if self.note.checklist_data:
            for k, checked in self.note.checklist_data.items():
                if k in self._checklist_checkboxes:
                    self._checklist_checkboxes[k].setChecked(bool(checked))

        # Mistakes
        if self.note.mistakes_identified:
            for m in self.note.mistakes_identified:
                if m in self._mistake_checkboxes:
                    self._mistake_checkboxes[m].setChecked(True)

        # Screenshots
        self._screenshot_items = list(self.note.screenshot_paths)
        self._refresh_screenshots_list()
        self._update_checklist_progress()

    def _update_checklist_progress(self) -> None:
        total = len(self._checklist_checkboxes)
        if total == 0:
            self.chk_progress.setValue(100)
            return
        checked = sum(1 for cb in self._checklist_checkboxes.values() if cb.isChecked())
        pct = int((checked / total) * 100)
        self.chk_progress.setValue(pct)
        self.chk_progress.setFormat(f"{checked}/{total} ({pct}%)")

    def _refresh_screenshots_list(self) -> None:
        self.screenshots_list.clear()
        for p in self._screenshot_items:
            item = QListWidgetItem(f"🖼️ {Path(p).name}  ({p})")
            item.setData(Qt.UserRole, p)
            self.screenshots_list.addItem(item)

    def _on_attach_custom_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Attach Screenshot",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*.*)"
        )
        if file_path and file_path not in self._screenshot_items:
            self._screenshot_items.append(file_path)
            self._refresh_screenshots_list()

    def _on_open_selected_screenshot(self) -> None:
        selected = self.screenshots_list.currentItem()
        if selected:
            p = selected.data(Qt.UserRole)
            if p and os.path.exists(p):
                QDesktopServices.openUrl(QUrl.fromLocalFile(p))
            else:
                QMessageBox.warning(self, "File Not Found", f"Screenshot file does not exist:\n{p}")

    def _on_open_screenshot_item(self, item: QListWidgetItem) -> None:
        p = item.data(Qt.UserRole)
        if p and os.path.exists(p):
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def _on_remove_selected_screenshot(self) -> None:
        row = self.screenshots_list.currentRow()
        if row >= 0 and row < len(self._screenshot_items):
            self._screenshot_items.pop(row)
            self._refresh_screenshots_list()

    def _on_save(self) -> None:
        """Gather values and save via TradeJournalService."""
        checklist_dict = {k: cb.isChecked() for k, cb in self._checklist_checkboxes.items()}
        mistakes_list = [k for k, cb in self._mistake_checkboxes.items() if cb.isChecked()]

        self.note.setup_name = self.setup_combo.currentText().strip()
        self.note.rating = self.grade_combo.currentText().strip()
        self.note.pre_trade_thesis = self.pre_thesis_text.toPlainText().strip()
        self.note.post_trade_review = self.post_review_text.toPlainText().strip()
        self.note.checklist_data = checklist_dict
        self.note.mistakes_identified = mistakes_list
        self.note.screenshot_paths = list(self._screenshot_items)
        self.note.updated_at = datetime.now(timezone.utc)

        saved = self.journal_service.save_note(self.note)
        self.noteSaved.emit(saved)
        self.accept()
