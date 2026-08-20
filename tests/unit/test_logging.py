"""
Unit tests for logging system setup.
"""

from tradeaudit.app.logging import setup_logging


def test_logging_file_created(test_settings):
    logger = setup_logging(test_settings)
    test_msg = "Test log message for unit testing"
    logger.info(test_msg)

    log_file = test_settings.log_dir / test_settings.log_file_name
    assert log_file.exists()

    content = log_file.read_text(encoding="utf-8")
    assert test_msg in content
