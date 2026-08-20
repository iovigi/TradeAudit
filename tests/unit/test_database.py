"""
Unit tests for database initialization, connection, and sessions.
"""

from sqlalchemy import text
from tradeaudit.infrastructure.database.models import AuditMeta


def test_database_connection_check(test_db_manager):
    assert test_db_manager.check_connection() is True


def test_database_tables_created(test_db_manager):
    with test_db_manager.engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_meta';"))
        tables = result.fetchall()
        assert len(tables) == 1


def test_database_session_insert_query(test_db_manager):
    for session in test_db_manager.get_session():
        meta = AuditMeta()
        session.add(meta)

    for session in test_db_manager.get_session():
        records = session.query(AuditMeta).all()
        assert len(records) == 1
