"""Tests for the configuration module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from src.config import Config, get_config


class TestConfig:
    """Tests for the Config class."""

    def test_config_creation(self):
        """Test creating a config with required fields.

        Verifies that a Config object can be created with required fields
        and that default values are applied correctly.
        """
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
        """Test creating a config with custom check interval.

        Verifies that the giveaway_check_interval can be customized
        when creating a Config object.
        """
        config = Config(
            token="test-token",
            database_path=Path("data/test.db"),
            log_level="INFO",
            giveaway_check_interval=60,
        )

        assert config.giveaway_check_interval == 60

    @patch.dict(os.environ, {"DISCORD_TOKEN": "env-token"}, clear=False)
    def test_from_env_with_token(self):
        """Test creating config from environment variables.

        Verifies that Config.from_env() correctly reads the DISCORD_TOKEN
        and applies default values for other settings.
        """
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
        """Test creating config with all environment variables.

        Verifies that Config.from_env() correctly reads all supported
        environment variables including DISCORD_TOKEN, DATABASE_PATH,
        and LOG_LEVEL.
        """
        config = Config.from_env()

        assert config.token == "env-token"
        assert config.database_path == Path("custom/path.db")
        assert config.log_level == "DEBUG"

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_without_token_raises(self):
        """Test that missing token raises ValueError.

        Verifies that Config.from_env() raises a ValueError when the
        required DISCORD_TOKEN environment variable is not set.

        Raises:
            ValueError: When DISCORD_TOKEN is missing from environment.
        """
        with pytest.raises(ValueError) as exc_info:
            Config.from_env()

        assert "DISCORD_TOKEN" in str(exc_info.value)

    def test_ensure_data_directory(self, tmp_path):
        """Test that ensure_data_directory creates the directory.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        db_path = tmp_path / "subdir" / "test.db"
        config = Config(
            token="test-token",
            database_path=db_path,
            log_level="INFO",
        )

        config.ensure_data_directory()

        assert db_path.parent.exists()

    def test_ensure_data_directory_existing(self, tmp_path):
        """Test ensure_data_directory with existing directory.

        Verifies that calling ensure_data_directory on an already existing
        directory does not raise an error and can be called multiple times.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
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
        """Test get_config function.

        Verifies that the get_config convenience function returns a
        properly configured Config instance.
        """
        config = get_config()

        assert config.token == "func-token"
        assert isinstance(config, Config)
