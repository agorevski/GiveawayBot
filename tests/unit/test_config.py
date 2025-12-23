"""Tests for the configuration module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from src.config import Config, get_config


class TestConfig:
    """Tests for the Config class."""

    def test_config_creation(self):
        """Test creating a config with required fields."""
        config = Config(
            token="test-token",
            database_path=Path("data/test.db"),
            log_level="DEBUG",
        )

        assert config.token == "test-token"
        assert config.database_path == Path("data/test.db")
        assert config.log_level == "DEBUG"
        assert config.giveaway_check_interval == 30  # Default value

    def test_config_with_custom_interval(self):
        """Test creating a config with custom check interval."""
        config = Config(
            token="test-token",
            database_path=Path("data/test.db"),
            log_level="INFO",
            giveaway_check_interval=60,
        )

        assert config.giveaway_check_interval == 60

    @patch.dict(os.environ, {"DISCORD_TOKEN": "env-token"}, clear=False)
    def test_from_env_with_token(self):
        """Test creating config from environment variables."""
        config = Config.from_env()

        assert config.token == "env-token"
        assert config.database_path == Path("data/giveaway.db")
        assert config.log_level == "INFO"

    @patch.dict(os.environ, {
        "DISCORD_TOKEN": "env-token",
        "DATABASE_PATH": "custom/path.db",
        "LOG_LEVEL": "DEBUG"
    }, clear=False)
    def test_from_env_with_all_vars(self):
        """Test creating config with all environment variables."""
        config = Config.from_env()

        assert config.token == "env-token"
        assert config.database_path == Path("custom/path.db")
        assert config.log_level == "DEBUG"

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_without_token_raises(self):
        """Test that missing token raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Config.from_env()

        assert "DISCORD_TOKEN" in str(exc_info.value)

    def test_ensure_data_directory(self, tmp_path):
        """Test that ensure_data_directory creates the directory."""
        db_path = tmp_path / "subdir" / "test.db"
        config = Config(
            token="test-token",
            database_path=db_path,
            log_level="INFO",
        )

        config.ensure_data_directory()

        assert db_path.parent.exists()

    def test_ensure_data_directory_existing(self, tmp_path):
        """Test ensure_data_directory with existing directory."""
        db_path = tmp_path / "test.db"
        config = Config(
            token="test-token",
            database_path=db_path,
            log_level="INFO",
        )

        # Should not raise
        config.ensure_data_directory()
        config.ensure_data_directory()  # Call twice

        assert db_path.parent.exists()


class TestGetConfig:
    """Tests for the get_config function."""

    @patch.dict(os.environ, {"DISCORD_TOKEN": "func-token"}, clear=False)
    def test_get_config(self):
        """Test get_config function."""
        config = get_config()

        assert config.token == "func-token"
        assert isinstance(config, Config)
