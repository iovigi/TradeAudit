from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from tradeaudit.infrastructure.mt5.position_reader import MT5PositionReader
from tradeaudit.domain.models import LivePosition


def test_fetch_open_positions_with_mock_mt5():
    reader = MT5PositionReader()

    mock_pos_1 = MagicMock()
    mock_pos_1._asdict.return_value = {
        "ticket": 1001,
        "identifier": 1001,
        "symbol": "EURUSD",
        "type": 0,  # BUY
        "volume": 1.0,
        "price_open": 1.0850,
        "sl": 1.0800,
        "tp": 1.0950,
        "profit": 150.0,
        "swap": -2.5,
        "time": 1700000000,
        "magic": 123456
    }

    mock_pos_2 = MagicMock()
    mock_pos_2._asdict.return_value = {
        "ticket": 1002,
        "identifier": 1002,
        "symbol": "GBPUSD",
        "type": 1,  # SELL
        "volume": 0.5,
        "price_open": 1.2650,
        "sl": 1.2700,
        "tp": 1.2550,
        "profit": -40.0,
        "swap": 0.0,
        "time": 1700000100,
        "magic": 0
    }

    with patch("tradeaudit.infrastructure.mt5.position_reader.mt5") as mock_mt5, \
         patch("tradeaudit.infrastructure.mt5.position_reader.HAS_MT5", True):
        mock_mt5.positions_get.return_value = (mock_pos_1, mock_pos_2)

        positions = reader.fetch_open_positions(account_id=123456)

        assert len(positions) == 2
        assert positions[0].ticket == 1001
        assert positions[0].symbol == "EURUSD"
        assert positions[0].type == "BUY"
        assert positions[0].volume == 1.0
        assert positions[0].sl == 1.0800

        assert positions[1].ticket == 1002
        assert positions[1].symbol == "GBPUSD"
        assert positions[1].type == "SELL"
        assert positions[1].volume == 0.5


def test_fetch_open_positions_empty():
    reader = MT5PositionReader()

    with patch("tradeaudit.infrastructure.mt5.position_reader.mt5") as mock_mt5, \
         patch("tradeaudit.infrastructure.mt5.position_reader.HAS_MT5", True):
        mock_mt5.positions_get.return_value = ()
        positions = reader.fetch_open_positions(account_id=123456)
        assert positions == []
