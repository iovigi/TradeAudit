"""
Interactive toolbar for chart drawing annotations and color selection.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QButtonGroup,
    QColorDialog,
    QFrame
)
from PySide6.QtGui import QColor, QIcon


class ChartDrawingToolbar(QFrame):
    """Toolbar providing drawing mode selection, color palette, and clear actions for candlestick charts."""

    toolChanged = Signal(str)      # Emits tool name (PAN, TREND_LINE, etc.)
    colorChanged = Signal(str)     # Emits hex color (#58a6ff)
    clearRequested = Signal()      # Emits when user requests to clear all drawings

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("DrawingToolbar")
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet("""
            QFrame#DrawingToolbar {
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
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QPushButton:checked {
                background-color: #1f6feb;
                color: #ffffff;
                border-color: #388bfd;
            }
            QPushButton.color-btn {
                min-width: 18px;
                max-width: 18px;
                min-height: 18px;
                max-height: 18px;
                border-radius: 9px;
                padding: 0;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Tool button group
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)

        tools = [
            ("PAN", "🖱️ Pan"),
            ("TREND_LINE", "📈 Trendline"),
            ("HORIZONTAL_RAY", "➖ Level / Ray"),
            ("RECTANGLE_ZONE", "🔲 Zone Box"),
            ("TEXT_NOTE", "🔤 Text Note"),
            ("ARROW_UP", "⬆️ Bull Arrow"),
            ("ARROW_DOWN", "⬇️ Bear Arrow"),
            ("ERASER", "🧹 Eraser"),
        ]

        for tool_id, label in tools:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("tool_id", tool_id)
            if tool_id == "PAN":
                btn.setChecked(True)
            btn.clicked.connect(self._on_tool_clicked)
            self.tool_group.addButton(btn)
            layout.addWidget(btn)

        layout.addSpacing(10)

        # Color palette buttons
        palette_colors = ["#58a6ff", "#26a69a", "#ef5350", "#f59e0b", "#bc8cff", "#ffffff"]
        self.color_group = QButtonGroup(self)
        self.color_group.setExclusive(True)

        for col in palette_colors:
            btn = QPushButton()
            btn.setProperty("color_hex", col)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {col};
                    border: 2px solid #30363d;
                    border-radius: 9px;
                    min-width: 18px; max-width: 18px;
                    min-height: 18px; max-height: 18px;
                }}
                QPushButton:checked {{
                    border: 2px solid #ffffff;
                }}
            """)
            if col == "#58a6ff":
                btn.setChecked(True)
            btn.clicked.connect(self._on_color_clicked)
            self.color_group.addButton(btn)
            layout.addWidget(btn)

        layout.addSpacing(10)

        # Clear button
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setStyleSheet("background-color: #8b1d1d; color: #ffffff; border-color: #b91c1c;")
        clear_btn.clicked.connect(self.clearRequested.emit)
        layout.addWidget(clear_btn)

        layout.addStretch()

    def _on_tool_clicked(self) -> None:
        sender = self.sender()
        if sender and sender.property("tool_id"):
            self.toolChanged.emit(sender.property("tool_id"))

    def _on_color_clicked(self) -> None:
        sender = self.sender()
        if sender and sender.property("color_hex"):
            self.colorChanged.emit(sender.property("color_hex"))
