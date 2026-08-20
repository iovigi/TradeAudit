"""
Unit tests for MT5ConnectionService using MetaTrader5 module mocks.
"""

import pytest
from unittest.mock import patch, MagicMock

from tradeaudit.infrastructure.mt5.connection_service import MT5ConnectionService, ConnectionState
from tradeaudit.app.exceptions import MT5ConnectionError, MT5AuthError, MT5Error


def test_mt5_connection_service_successful_connect():
    mock_raw_account = MagicMock()
    mock_raw_account._asdict.return_value = {
        "login": 12345,
        "name": "Trader Test",
        "server": "DemoServer",
        "company": "Broker Co",
        "currency": "EUR",
        "leverage": 100,
        "balance": 10000.0,
        "equity": 10500.0,
        "profit": 500.0,
        "margin": 200.0,
        "margin_free": 10300.0,
        "margin_level": 5250.0,
        "trade_mode": 0
    }

    with patch("tradeaudit.infrastructure.mt5.connection_service.HAS_MT5", True), \
         patch("tradeaudit.infrastructure.mt5.connection_service.mt5") as mock_mt5:

        mock_mt5.initialize.return_value = True
        mock_mt5.account_info.return_value = mock_raw_account

        service = MT5ConnectionService()
        account_info = service.connect(
            mt5_path="C:\\mt5\\terminal64.exe",
            login=12345,
            password="pass",
            server="DemoServer"
        )

        assert service.state == ConnectionState.CONNECTED
        assert account_info.login == 12345
        assert account_info.currency == "EUR"
        assert account_info.balance == 10000.0
        assert account_info.equity == 10500.0
        assert account_info.profit == 500.0
        assert account_info.trade_mode == "Demo"


def test_mt5_connection_service_auth_failure():
    with patch("tradeaudit.infrastructure.mt5.connection_service.HAS_MT5", True), \
         patch("tradeaudit.infrastructure.mt5.connection_service.mt5") as mock_mt5:

        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (-5, "Invalid credentials")

        service = MT5ConnectionService()
        with pytest.raises(MT5AuthError):
            service.connect(mt5_path="", login=12345, password="wrong", server="Server")

        assert service.state == ConnectionState.ERROR


def test_mt5_connection_service_disconnect():
    with patch("tradeaudit.infrastructure.mt5.connection_service.HAS_MT5", True), \
         patch("tradeaudit.infrastructure.mt5.connection_service.mt5") as mock_mt5:

        service = MT5ConnectionService()
        service.disconnect()

        assert service.state == ConnectionState.DISCONNECTED
        mock_mt5.shutdown.assert_called_once()
