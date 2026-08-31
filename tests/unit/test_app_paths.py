"""
Unit tests for application paths and AppData directory resolution (Phase 12).
"""

from pathlib import Path
import os
import sys
import pytest

from tradeaudit.app.config import (
    Settings,
    get_settings,
    get_default_data_dir,
    get_default_database_url,
    get_resource_path,
    is_frozen,
)


def test_default_dev_paths(temp_dir, monkeypatch):
    """Test paths when running in standard development mode."""
    monkeypatch.delenv("TRADEAUDIT_DATA_DIR", raising=False)
    monkeypatch.setenv("TRADEAUDIT_ENV", "development")
    
    settings = Settings(data_dir=temp_dir)
    assert settings.data_dir == temp_dir
    assert settings.database_dir == temp_dir / "database"
    assert settings.log_dir == temp_dir / "logs"
    assert settings.export_dir == temp_dir / "exports"
    assert settings.backup_dir == temp_dir / "backups"
    assert settings.config_dir == temp_dir / "config"


def test_custom_data_dir_env(temp_dir, monkeypatch):
    """Test custom directory override using TRADEAUDIT_DATA_DIR env variable."""
    custom_path = temp_dir / "custom_audit_data"
    monkeypatch.setenv("TRADEAUDIT_DATA_DIR", str(custom_path))
    
    resolved = get_default_data_dir()
    assert resolved == custom_path


def test_ensure_directories_creation(temp_dir):
    """Test that ensure_directories() creates all subdirectories."""
    settings = Settings(data_dir=temp_dir)
    settings.ensure_directories()

    assert settings.data_dir.exists()
    assert settings.database_dir.exists()
    assert settings.log_dir.exists()
    assert settings.export_dir.exists()
    assert settings.backup_dir.exists()
    assert settings.config_dir.exists()


def test_resource_path_resolution():
    """Test get_resource_path locates existing files or valid paths."""
    p = get_resource_path("resources/icons/tradeaudit.ico")
    assert isinstance(p, Path)
    # Check root resource path
    root_res = get_resource_path()
    assert root_res.exists()
