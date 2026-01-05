"""Integration tests for the StorageService."""

import pytest
from datetime import datetime, timedelta, timezone

from src.models.giveaway import Giveaway
from src.models.guild_config import GuildConfig


class TestStorageServiceGiveaways:
    """Integration tests for giveaway storage operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_giveaway(self, storage_service):
        """Test creating and retrieving a giveaway.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )

        saved = await storage_service.create_giveaway(giveaway)
        assert saved.id is not None

        retrieved = await storage_service.get_giveaway(saved.id)
        assert retrieved is not None
        assert retrieved.guild_id == 123456789
        assert retrieved.prize == "Test Prize"

    @pytest.mark.asyncio
    async def test_update_giveaway(self, storage_service):
        """Test updating a giveaway.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Original Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )

        saved = await storage_service.create_giveaway(giveaway)
        saved.prize = "Updated Prize"
        saved.message_id = 555555555

        await storage_service.update_giveaway(saved)

        retrieved = await storage_service.get_giveaway(saved.id)
        assert retrieved.prize == "Updated Prize"
        assert retrieved.message_id == 555555555

    @pytest.mark.asyncio
    async def test_get_active_giveaways(self, storage_service):
        """Test retrieving active giveaways for a guild.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        guild_id = 123456789

        # Create active giveaway
        active = Giveaway(
            guild_id=guild_id,
            channel_id=987654321,
            prize="Active Giveaway",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        await storage_service.create_giveaway(active)

        # Create ended giveaway
        ended = Giveaway(
            guild_id=guild_id,
            channel_id=987654321,
            prize="Ended Giveaway",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            ended=True,
        )
        await storage_service.create_giveaway(ended)

        # Only active should be returned
        active_giveaways = await storage_service.get_active_giveaways(guild_id)
        assert len(active_giveaways) == 1
        assert active_giveaways[0].prize == "Active Giveaway"

    @pytest.mark.asyncio
    async def test_add_and_get_entries(self, storage_service):
        """Test adding and retrieving giveaway entries.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        saved = await storage_service.create_giveaway(giveaway)

        # Add entries
        await storage_service.add_entry(saved.id, 222222222)
        await storage_service.add_entry(saved.id, 333333333)
        await storage_service.add_entry(saved.id, 444444444)

        # Get entries
        entries = await storage_service.get_entries(saved.id)
        assert len(entries) == 3
        assert 222222222 in entries
        assert 333333333 in entries

    @pytest.mark.asyncio
    async def test_remove_entry(self, storage_service):
        """Test removing a giveaway entry.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        saved = await storage_service.create_giveaway(giveaway)

        await storage_service.add_entry(saved.id, 222222222)
        await storage_service.add_entry(saved.id, 333333333)

        await storage_service.remove_entry(saved.id, 222222222)

        entries = await storage_service.get_entries(saved.id)
        assert len(entries) == 1
        assert 333333333 in entries

    @pytest.mark.asyncio
    async def test_check_entry_exists(self, storage_service):
        """Test checking if an entry exists.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        saved = await storage_service.create_giveaway(giveaway)

        await storage_service.add_entry(saved.id, 222222222)

        assert await storage_service.has_entered(saved.id, 222222222) is True
        assert await storage_service.has_entered(saved.id, 333333333) is False

    @pytest.mark.asyncio
    async def test_add_winners(self, storage_service):
        """Test adding winners to a giveaway.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        saved = await storage_service.create_giveaway(giveaway)

        await storage_service.add_winner(saved.id, 222222222)
        await storage_service.add_winner(saved.id, 333333333)

        winners = await storage_service.get_winners(saved.id)
        assert len(winners) == 2
        assert 222222222 in winners


class TestStorageServiceGuildConfig:
    """Integration tests for guild configuration storage."""

    @pytest.mark.asyncio
    async def test_get_default_config(self, storage_service):
        """Test getting config for a guild with no config.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        config = await storage_service.get_guild_config(123456789)

        assert config is not None
        assert config.guild_id == 123456789
        assert config.admin_role_ids == []

    @pytest.mark.asyncio
    async def test_save_and_get_config(self, storage_service):
        """Test saving and retrieving guild configuration.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        config = GuildConfig(
            guild_id=123456789,
            admin_role_ids=[111111111, 222222222],
        )

        await storage_service.save_guild_config(config)

        retrieved = await storage_service.get_guild_config(123456789)
        assert retrieved.admin_role_ids == [111111111, 222222222]

    @pytest.mark.asyncio
    async def test_update_config(self, storage_service):
        """Test updating guild configuration.

        Args:
            storage_service: The storage service fixture for database operations.
        """
        config = GuildConfig(
            guild_id=123456789,
            admin_role_ids=[111111111],
        )
        await storage_service.save_guild_config(config)

        # Update
        config.add_admin_role(222222222)
        await storage_service.save_guild_config(config)

        retrieved = await storage_service.get_guild_config(123456789)
        assert 111111111 in retrieved.admin_role_ids
        assert 222222222 in retrieved.admin_role_ids
