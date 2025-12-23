"""Tests for the GuildConfig model."""

import pytest
from datetime import datetime, timezone

from src.models.guild_config import GuildConfig


class TestGuildConfigModel:
    """Tests for the GuildConfig model."""

    def test_create_guild_config(self):
        """Test creating a guild config."""
        config = GuildConfig(
            guild_id=123456789,
            admin_role_ids=[111111111, 222222222],
        )

        assert config.guild_id == 123456789
        assert config.admin_role_ids == [111111111, 222222222]

    def test_default_guild_config(self):
        """Test creating a default guild config."""
        config = GuildConfig.default(123456789)

        assert config.guild_id == 123456789
        assert config.admin_role_ids == []

    def test_add_admin_role(self):
        """Test adding an admin role."""
        config = GuildConfig(guild_id=123456789)

        result = config.add_admin_role(111111111)

        assert result is True
        assert 111111111 in config.admin_role_ids

    def test_add_admin_role_duplicate(self):
        """Test adding a duplicate admin role."""
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111])

        result = config.add_admin_role(111111111)

        assert result is False
        assert config.admin_role_ids.count(111111111) == 1

    def test_remove_admin_role(self):
        """Test removing an admin role."""
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111, 222222222])

        result = config.remove_admin_role(111111111)

        assert result is True
        assert 111111111 not in config.admin_role_ids
        assert 222222222 in config.admin_role_ids

    def test_remove_admin_role_not_found(self):
        """Test removing a role that doesn't exist."""
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111])

        result = config.remove_admin_role(222222222)

        assert result is False
        assert config.admin_role_ids == [111111111]

    def test_is_admin_role(self):
        """Test checking if a role is an admin role."""
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111])

        assert config.is_admin_role(111111111) is True
        assert config.is_admin_role(222222222) is False

    def test_to_dict(self):
        """Test converting to dictionary."""
        config = GuildConfig(
            guild_id=123456789,
            admin_role_ids=[111111111, 222222222],
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        result = config.to_dict()

        assert result["guild_id"] == 123456789
        assert result["admin_role_ids"] == "[111111111, 222222222]"
        assert "2024-01-01" in result["created_at"]

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "guild_id": 123456789,
            "admin_role_ids": "[111111111, 222222222]",
            "created_at": "2024-01-01T12:00:00+00:00",
        }

        config = GuildConfig.from_dict(data)

        assert config.guild_id == 123456789
        assert config.admin_role_ids == [111111111, 222222222]

    def test_from_dict_with_list(self):
        """Test creating from dictionary with list instead of string."""
        data = {
            "guild_id": 123456789,
            "admin_role_ids": [111111111, 222222222],
            "created_at": "2024-01-01T12:00:00+00:00",
        }

        config = GuildConfig.from_dict(data)

        assert config.admin_role_ids == [111111111, 222222222]

    def test_from_dict_no_created_at(self):
        """Test creating from dictionary without created_at."""
        data = {
            "guild_id": 123456789,
            "admin_role_ids": "[]",
        }

        config = GuildConfig.from_dict(data)

        assert config.guild_id == 123456789
        assert config.created_at is not None
