"""
Settings View component for MT5 terminal connection & credentials configuration.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QFrame,
    QGroupBox
)

from tradeaudit.domain.models import MT5Settings


class SettingsView(QWidget):
    """View containing MetaTrader 5 configuration form and credential controls."""

    settings_saved = Signal(MT5Settings)
    connect_requested = Signal(MT5Settings, str)  # settings, password
    disconnect_requested = Signal()
    backup_requested = Signal()
    open_data_folder_requested = Signal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Settings Group Box
        group_box = QGroupBox("⚙️ MetaTrader 5 Terminal Configuration")
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #2a3444;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: #1a222d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                background-color: #1a222d;
            }
        """)

        form_layout = QFormLayout(group_box)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(14)

        # Styles for inputs
        input_style = """
            QLineEdit, QSpinBox {
                background-color: #121820;
                color: #e2e8f0;
                border: 1px solid #2d3748;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #00a2e8;
            }
        """
        self.setStyleSheet(input_style)

        # MT5 Executable Path
        path_container = QWidget()
        path_layout = QHBoxLayout(path_container)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(8)

        self.edit_path = QLineEdit()
        self.edit_path.setPlaceholderText("C:\\Program Files\\MetaTrader 5\\terminal64.exe")

        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #2b3648;
                color: #ffffff;
                border: 1px solid #3a475d;
                border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #3a475d;
            }
        """)
        self.btn_browse.clicked.connect(self._on_browse_clicked)

        path_layout.addWidget(self.edit_path, stretch=1)
        path_layout.addWidget(self.btn_browse)

        # Account Login
        self.spin_login = QSpinBox()
        self.spin_login.setRange(0, 2147483647)
        self.spin_login.setSingleStep(1)
        self.spin_login.setGroupSeparatorShown(False)

        # Password
        pass_container = QWidget()
        pass_layout = QHBoxLayout(pass_container)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.setSpacing(8)

        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)
        self.edit_password.setPlaceholderText("Stored securely in OS Credential Locker")

        self.btn_toggle_pass = QPushButton("👁")
        self.btn_toggle_pass.setToolTip("Show/Hide password")
        self.btn_toggle_pass.setFixedWidth(40)
        self.btn_toggle_pass.setStyleSheet("""
            QPushButton {
                background-color: #2b3648;
                color: #ffffff;
                border: 1px solid #3a475d;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self.btn_toggle_pass.clicked.connect(self._toggle_password_visibility)

        pass_layout.addWidget(self.edit_password, stretch=1)
        pass_layout.addWidget(self.btn_toggle_pass)

        # Server
        self.edit_server = QLineEdit()
        self.edit_server.setPlaceholderText("e.g. MetaQuotes-Demo")

        # Timeout
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(1000, 300000)
        self.spin_timeout.setValue(60000)
        self.spin_timeout.setSuffix(" ms")

        # Add rows to form
        form_layout.addRow(self._create_field_label("MT5 Path:"), path_container)
        form_layout.addRow(self._create_field_label("Account Login:"), self.spin_login)
        form_layout.addRow(self._create_field_label("Password:"), pass_container)
        form_layout.addRow(self._create_field_label("Server:"), self.edit_server)
        form_layout.addRow(self._create_field_label("Timeout:"), self.spin_timeout)

        layout.addWidget(group_box)

        # Actions Row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        self.btn_save = QPushButton("💾 Save Settings")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #38bdf8;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        self.btn_save.clicked.connect(self._on_save_clicked)

        self.btn_connect = QPushButton("⚡ Connect to MT5")
        self.btn_connect.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                border: 1px solid #10b981;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #10b981;
            }
        """)
        self.btn_connect.clicked.connect(self._on_connect_clicked)

        self.btn_disconnect = QPushButton("🔌 Disconnect")
        self.btn_disconnect.setStyleSheet("""
            QPushButton {
                background-color: #7f1d1d;
                color: #fca5a5;
                border: 1px solid #ef4444;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #991b1b;
            }
        """)
        self.btn_disconnect.clicked.connect(self._on_disconnect_clicked)

        actions_layout.addWidget(self.btn_save)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_disconnect)
        layout.addLayout(actions_layout)

        # Storage & Backup Management Group Box
        storage_box = QGroupBox("📦 Storage & Database Backups")
        storage_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #2a3444;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: #1a222d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                background-color: #1a222d;
            }
        """)
        storage_layout = QVBoxLayout(storage_box)
        storage_layout.setContentsMargins(20, 20, 20, 20)
        storage_layout.setSpacing(12)

        self.lbl_storage_info = QLabel("App Data Directory: %LOCALAPPDATA%\\TradeAudit")
        self.lbl_storage_info.setStyleSheet("color: #94a3b8; font-size: 12px;")

        storage_btn_layout = QHBoxLayout()
        storage_btn_layout.setSpacing(12)

        self.btn_open_data_dir = QPushButton("📁 Open Data Folder")
        self.btn_open_data_dir.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        self.btn_open_data_dir.clicked.connect(self._on_open_data_dir_clicked)

        self.btn_create_backup = QPushButton("💾 Create Backup Now")
        self.btn_create_backup.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0369a1;
                color: #ffffff;
            }
        """)
        self.btn_create_backup.clicked.connect(self._on_create_backup_clicked)

        storage_btn_layout.addWidget(self.btn_open_data_dir)
        storage_btn_layout.addWidget(self.btn_create_backup)
        storage_btn_layout.addStretch()

        storage_layout.addWidget(self.lbl_storage_info)
        storage_layout.addLayout(storage_btn_layout)

        layout.addWidget(storage_box)

        # Feedback Panel
        self.feedback_box = QFrame()
        self.feedback_box.setVisible(False)
        feedback_layout = QVBoxLayout(self.feedback_box)
        feedback_layout.setContentsMargins(12, 12, 12, 12)

        self.lbl_feedback = QLabel()
        self.lbl_feedback.setWordWrap(True)
        self.lbl_feedback.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        feedback_layout.addWidget(self.lbl_feedback)

        layout.addWidget(self.feedback_box)
        layout.addStretch()

    def _create_field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        lbl.setStyleSheet("color: #a0aec0;")
        return lbl

    def _on_browse_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MetaTrader 5 Terminal Executable",
            "",
            "Executable Files (*terminal64.exe *.exe);;All Files (*)"
        )
        if file_path:
            self.edit_path.setText(file_path)

    def _toggle_password_visibility(self) -> None:
        if self.edit_password.echoMode() == QLineEdit.Password:
            self.edit_password.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_pass.setText("🔒")
        else:
            self.edit_password.setEchoMode(QLineEdit.Password)
            self.btn_toggle_pass.setText("👁")

    def get_settings(self) -> MT5Settings:
        """Extract settings from form inputs."""
        return MT5Settings(
            mt5_path=self.edit_path.text().strip(),
            login=self.spin_login.value(),
            server=self.edit_server.text().strip(),
            timeout_ms=self.spin_timeout.value()
        )

    def get_password(self) -> str:
        """Retrieve password text input."""
        return self.edit_password.text()

    def populate_settings(self, settings: Optional[MT5Settings], password: str = "") -> None:
        """Populate form fields from domain model and password."""
        if settings:
            self.edit_path.setText(settings.mt5_path or "")
            self.spin_login.setValue(settings.login or 0)
            self.edit_server.setText(settings.server or "")
            self.spin_timeout.setValue(settings.timeout_ms or 60000)

        if password:
            self.edit_password.setText(password)

    def show_feedback(self, message: str, is_error: bool = False) -> None:
        """Display success or error feedback message."""
        self.lbl_feedback.setText(message)
        if is_error:
            self.feedback_box.setStyleSheet("""
                QFrame {
                    background-color: rgba(239, 68, 68, 0.12);
                    border: 1px solid #ef4444;
                    border-radius: 6px;
                }
                QLabel { color: #fca5a5; }
            """)
        else:
            self.feedback_box.setStyleSheet("""
                QFrame {
                    background-color: rgba(16, 185, 129, 0.12);
                    border: 1px solid #10b981;
                    border-radius: 6px;
                }
                QLabel { color: #6ee7b7; }
            """)
        self.feedback_box.setVisible(True)

    def clear_feedback(self) -> None:
        self.feedback_box.setVisible(False)

    def set_storage_info(self, data_dir_str: str, db_url_str: str) -> None:
        """Update storage info text."""
        self.lbl_storage_info.setText(
            f"📁 Data Directory: {data_dir_str}\n"
            f"🗄️ Database: {db_url_str}"
        )

    def _on_create_backup_clicked(self) -> None:
        self.backup_requested.emit()

    def _on_open_data_dir_clicked(self) -> None:
        self.open_data_folder_requested.emit()

    def _on_save_clicked(self) -> None:
        settings = self.get_settings()
        self.settings_saved.emit(settings)

    def _on_connect_clicked(self) -> None:
        settings = self.get_settings()
        password = self.get_password()
        self.connect_requested.emit(settings, password)

    def _on_disconnect_clicked(self) -> None:
        self.disconnect_requested.emit()
