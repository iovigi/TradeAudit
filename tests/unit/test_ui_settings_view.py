"""
Unit tests for SettingsView PySide6 component.
"""

from PySide6.QtWidgets import QLineEdit
from tradeaudit.domain.models import MT5Settings
from tradeaudit.ui.views.settings_view import SettingsView


def test_settings_view_instantiation(qapp):
    view = SettingsView()
    assert view is not None
    assert view.edit_password.echoMode() == QLineEdit.Password


def test_settings_view_populate_and_get(qapp):
    view = SettingsView()
    settings = MT5Settings(
        mt5_path="C:\\mt5\\terminal64.exe",
        login=1234567,
        server="TestServer",
        timeout_ms=15000
    )
    view.populate_settings(settings, password="TestPassword123")

    extracted = view.get_settings()
    assert extracted.mt5_path == "C:\\mt5\\terminal64.exe"
    assert extracted.login == 1234567
    assert extracted.server == "TestServer"
    assert extracted.timeout_ms == 15000
    assert view.get_password() == "TestPassword123"


def test_settings_view_toggle_password(qapp):
    view = SettingsView()
    assert view.edit_password.echoMode() == QLineEdit.Password

    view._toggle_password_visibility()
    assert view.edit_password.echoMode() == QLineEdit.Normal

    view._toggle_password_visibility()
    assert view.edit_password.echoMode() == QLineEdit.Password


def test_settings_view_feedback(qapp):
    view = SettingsView()
    view.show()
    assert not view.feedback_box.isVisible()

    view.show_feedback("Connection success!")
    assert view.feedback_box.isVisible()
    assert view.lbl_feedback.text() == "Connection success!"

    view.clear_feedback()
    assert not view.feedback_box.isVisible()
    view.close()
