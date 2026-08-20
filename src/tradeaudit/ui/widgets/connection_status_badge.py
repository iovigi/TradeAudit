"""
Connection status badge widget displaying real-time MT5 connection status.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame

from tradeaudit.infrastructure.mt5.connection_service import ConnectionState


class ConnectionStatusBadge(QWidget):
    """Badge widget indicating MT5 connection state."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._init_ui()
        self.set_status(ConnectionState.DISCONNECTED)

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.container = QFrame()
        self.container.setObjectName("BadgeContainer")
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(10, 4, 10, 4)
        container_layout.setSpacing(8)

        self.dot_label = QLabel("●")
        self.dot_label.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.text_label = QLabel("Disconnected")
        self.text_label.setFont(QFont("Segoe UI", 9, QFont.DemiBold))

        container_layout.addWidget(self.dot_label)
        container_layout.addWidget(self.text_label)

        layout.addWidget(self.container)

    def set_status(self, state: ConnectionState, server: str = "", login: int = 0) -> None:
        """Update badge appearance based on connection state."""
        if state == ConnectionState.CONNECTED:
            server_info = f" ({server})" if server else ""
            self.dot_label.setStyleSheet("color: #00e676;")
            self.text_label.setText(f"Connected to MT5{server_info}")
            self.text_label.setStyleSheet("color: #00e676;")
            self.container.setStyleSheet("""
                QFrame#BadgeContainer {
                    background-color: rgba(0, 230, 118, 0.12);
                    border: 1px solid #00e676;
                    border-radius: 12px;
                }
            """)
        elif state == ConnectionState.CONNECTING:
            self.dot_label.setStyleSheet("color: #ffb300;")
            self.text_label.setText("Connecting...")
            self.text_label.setStyleSheet("color: #ffb300;")
            self.container.setStyleSheet("""
                QFrame#BadgeContainer {
                    background-color: rgba(255, 179, 0, 0.12);
                    border: 1px solid #ffb300;
                    border-radius: 12px;
                }
            """)
        elif state == ConnectionState.ERROR:
            self.dot_label.setStyleSheet("color: #ff5252;")
            self.text_label.setText("Connection Error")
            self.text_label.setStyleSheet("color: #ff5252;")
            self.container.setStyleSheet("""
                QFrame#BadgeContainer {
                    background-color: rgba(255, 82, 82, 0.12);
                    border: 1px solid #ff5252;
                    border-radius: 12px;
                }
            """)
        else:  # DISCONNECTED
            self.dot_label.setStyleSheet("color: #78909c;")
            self.text_label.setText("MT5 Disconnected")
            self.text_label.setStyleSheet("color: #78909c;")
            self.container.setStyleSheet("""
                QFrame#BadgeContainer {
                    background-color: rgba(120, 144, 156, 0.12);
                    border: 1px solid #455a64;
                    border-radius: 12px;
                }
            """)
