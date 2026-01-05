"""Tests for the StorageService."""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.models.giveaway import Giveaway
from src.models.guild_config import GuildConfig
from src.services.storage_service import StorageService


class TestStorageServiceInit:
    """Tests for StorageService initialization."""

    @pytest.mark.asyncio
    async def test_initialize_creates_directory(self, tmp_path):
        """Test that initialize creates the database directory.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        db_path = tmp_path / "subdir" / "test.db"
        storage = StorageService(db_path)

        await storage.initialize()

        assert db_path.parent.exists()
        await storage.close()

    @pytest.mark.asyncio
    async def test_close_when_not_initialized(self, tmp_path):
        """Test closing when not initialized doesn't raise.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        await storage.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_clears_connection(self, storage_service):
        """Test that close clears the connection.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        await storage_service.close()
        assert storage_service._connection is None


class TestGiveawayOperations:
    """Tests for giveaway database operations."""

    @pytest.mark.asyncio
    async def test_create_giveaway(self, storage_service, sample_giveaway):
        """Test creating a giveaway.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)

        assert created.id is not None
        assert created.prize == "Test Prize"

    @pytest.mark.asyncio
    async def test_get_giveaway(self, storage_service, sample_giveaway):
        """Test retrieving a giveaway.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        retrieved = await storage_service.get_giveaway(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.prize == sample_giveaway.prize

    @pytest.mark.asyncio
    async def test_get_nonexistent_giveaway(self, storage_service):
        """Test getting a non-existent giveaway.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        result = await storage_service.get_giveaway(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_giveaway_by_message(self, storage_service, sample_giveaway):
        """Test getting giveaway by message ID.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        sample_giveaway.message_id = 555555555
        created = await storage_service.create_giveaway(sample_giveaway)

        retrieved = await storage_service.get_giveaway_by_message(555555555)

        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_get_giveaway_by_nonexistent_message(self, storage_service):
        """Test getting giveaway by non-existent message ID.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        result = await storage_service.get_giveaway_by_message(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_giveaways(self, storage_service, sample_giveaway):
        """Test getting active giveaways.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        await storage_service.create_giveaway(sample_giveaway)

        active = await storage_service.get_active_giveaways(sample_giveaway.guild_id)

        assert len(active) >= 1
        assert all(not g.ended and not g.cancelled for g in active)

    @pytest.mark.asyncio
    async def test_get_active_giveaways_all_guilds(self, storage_service, sample_giveaway):
        """Test getting active giveaways across all guilds.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        await storage_service.create_giveaway(sample_giveaway)

        active = await storage_service.get_active_giveaways()

        assert len(active) >= 1

    @pytest.mark.asyncio
    async def test_get_scheduled_giveaways(self, storage_service):
        """Test getting scheduled giveaways.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Scheduled Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        await storage_service.create_giveaway(giveaway)

        scheduled = await storage_service.get_scheduled_giveaways()

        assert len(scheduled) >= 1
        assert all(g.scheduled_start is not None for g in scheduled)

    @pytest.mark.asyncio
    async def test_update_giveaway(self, storage_service, sample_giveaway):
        """Test updating a giveaway.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        created.prize = "Updated Prize"
        created.message_id = 123456

        await storage_service.update_giveaway(created)

        retrieved = await storage_service.get_giveaway(created.id)
        assert retrieved.prize == "Updated Prize"
        assert retrieved.message_id == 123456

    @pytest.mark.asyncio
    async def test_delete_giveaway(self, storage_service, sample_giveaway):
        """Test deleting a giveaway.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        await storage_service.add_entry(created.id, 222222222)
        await storage_service.add_winner(created.id, 222222222)

        await storage_service.delete_giveaway(created.id)

        retrieved = await storage_service.get_giveaway(created.id)
        assert retrieved is None


class TestEntryOperations:
    """Tests for entry database operations."""

    @pytest.mark.asyncio
    async def test_add_entry(self, storage_service, sample_giveaway):
        """Test adding an entry.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)

        success = await storage_service.add_entry(created.id, 222222222)

        assert success is True

    @pytest.mark.asyncio
    async def test_add_duplicate_entry(self, storage_service, sample_giveaway):
        """Test adding a duplicate entry.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        await storage_service.add_entry(created.id, 222222222)

        success = await storage_service.add_entry(created.id, 222222222)

        assert success is False

    @pytest.mark.asyncio
    async def test_remove_entry(self, storage_service, sample_giveaway):
        """Test removing an entry.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        await storage_service.add_entry(created.id, 222222222)

        success = await storage_service.remove_entry(created.id, 222222222)

        assert success is True

    @pytest.mark.asyncio
    async def test_remove_nonexistent_entry(self, storage_service, sample_giveaway):
        """Test removing a non-existent entry.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)

        success = await storage_service.remove_entry(created.id, 222222222)

        assert success is False

    @pytest.mark.asyncio
    async def test_get_entries(self, storage_service, sample_giveaway):
        """Test getting entries for a giveaway.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        await storage_service.add_entry(created.id, 111111111)
        await storage_service.add_entry(created.id, 222222222)

        entries = await storage_service.get_entries(created.id)

        assert len(entries) == 2
        assert 111111111 in entries
        assert 222222222 in entries

    @pytest.mark.asyncio
    async def test_get_entries_none_id(self, storage_service):
        """Test getting entries with None giveaway ID.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        entries = await storage_service.get_entries(None)
        assert entries == []

    @pytest.mark.asyncio
    async def test_has_entered_true(self, storage_service, sample_giveaway):
        """Test checking if user has entered - true case.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        await storage_service.add_entry(created.id, 222222222)

        result = await storage_service.has_entered(created.id, 222222222)

        assert result is True

    @pytest.mark.asyncio
    async def test_has_entered_false(self, storage_service, sample_giveaway):
        """Test checking if user has entered - false case.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)

        result = await storage_service.has_entered(created.id, 222222222)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_entries(self, storage_service, sample_giveaway):
        """Test getting a user's entries.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        await storage_service.add_entry(created.id, 222222222)

        entries = await storage_service.get_user_entries(
            sample_giveaway.guild_id, 222222222
        )

        assert len(entries) >= 1
        assert entries[0].id == created.id


class TestWinnerOperations:
    """Tests for winner database operations."""

    @pytest.mark.asyncio
    async def test_add_winner(self, storage_service, sample_giveaway):
        """Test adding a winner.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)

        await storage_service.add_winner(created.id, 222222222)

        winners = await storage_service.get_winners(created.id)
        assert 222222222 in winners

    @pytest.mark.asyncio
    async def test_get_winners(self, storage_service, sample_giveaway):
        """Test getting winners for a giveaway.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        await storage_service.add_winner(created.id, 111111111)
        await storage_service.add_winner(created.id, 222222222)

        winners = await storage_service.get_winners(created.id)

        assert len(winners) == 2
        assert 111111111 in winners
        assert 222222222 in winners

    @pytest.mark.asyncio
    async def test_get_winners_none_id(self, storage_service):
        """Test getting winners with None giveaway ID.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        winners = await storage_service.get_winners(None)
        assert winners == []

    @pytest.mark.asyncio
    async def test_clear_winners(self, storage_service, sample_giveaway):
        """Test clearing winners for a giveaway.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        created = await storage_service.create_giveaway(sample_giveaway)
        await storage_service.add_winner(created.id, 111111111)
        await storage_service.add_winner(created.id, 222222222)

        await storage_service.clear_winners(created.id)

        winners = await storage_service.get_winners(created.id)
        assert len(winners) == 0


class TestGuildConfigOperations:
    """Tests for guild config database operations."""

    @pytest.mark.asyncio
    async def test_get_guild_config_creates_default(self, storage_service):
        """Test getting guild config creates default if not exists.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        config = await storage_service.get_guild_config(123456789)

        assert config is not None
        assert config.guild_id == 123456789
        assert config.admin_role_ids == []

    @pytest.mark.asyncio
    async def test_get_guild_config_existing(self, storage_service):
        """Test getting existing guild config.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        # Create a config first
        config = GuildConfig(
            guild_id=123456789,
            admin_role_ids=[111111111],
        )
        await storage_service.save_guild_config(config)

        # Retrieve it
        retrieved = await storage_service.get_guild_config(123456789)

        assert retrieved.guild_id == 123456789
        assert 111111111 in retrieved.admin_role_ids

    @pytest.mark.asyncio
    async def test_save_guild_config(self, storage_service):
        """Test saving guild config.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        config = GuildConfig(
            guild_id=123456789,
            admin_role_ids=[111111111, 222222222],
        )

        await storage_service.save_guild_config(config)

        retrieved = await storage_service.get_guild_config(123456789)
        assert len(retrieved.admin_role_ids) == 2

    @pytest.mark.asyncio
    async def test_save_guild_config_update(self, storage_service):
        """Test updating existing guild config.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
        """
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111])
        await storage_service.save_guild_config(config)

        config.admin_role_ids = [222222222, 333333333]
        await storage_service.save_guild_config(config)

        retrieved = await storage_service.get_guild_config(123456789)
        assert len(retrieved.admin_role_ids) == 2
        assert 222222222 in retrieved.admin_role_ids


class TestRuntimeErrors:
    """Tests for RuntimeError when database not initialized."""

    @pytest.mark.asyncio
    async def test_create_tables_not_initialized(self, tmp_path):
        """Test _create_tables raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage._create_tables()

    @pytest.mark.asyncio
    async def test_create_giveaway_not_initialized(self, tmp_path, sample_giveaway):
        """Test create_giveaway raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.create_giveaway(sample_giveaway)

    @pytest.mark.asyncio
    async def test_get_giveaway_not_initialized(self, tmp_path):
        """Test get_giveaway raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.get_giveaway(1)

    @pytest.mark.asyncio
    async def test_get_giveaway_by_message_not_initialized(self, tmp_path):
        """Test get_giveaway_by_message raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.get_giveaway_by_message(1)

    @pytest.mark.asyncio
    async def test_get_active_giveaways_not_initialized(self, tmp_path):
        """Test get_active_giveaways raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.get_active_giveaways()

    @pytest.mark.asyncio
    async def test_get_scheduled_giveaways_not_initialized(self, tmp_path):
        """Test get_scheduled_giveaways raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.get_scheduled_giveaways()

    @pytest.mark.asyncio
    async def test_update_giveaway_not_initialized(self, tmp_path, sample_giveaway):
        """Test update_giveaway raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.update_giveaway(sample_giveaway)

    @pytest.mark.asyncio
    async def test_delete_giveaway_not_initialized(self, tmp_path):
        """Test delete_giveaway raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.delete_giveaway(1)

    @pytest.mark.asyncio
    async def test_add_entry_not_initialized(self, tmp_path):
        """Test add_entry raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.add_entry(1, 123)

    @pytest.mark.asyncio
    async def test_remove_entry_not_initialized(self, tmp_path):
        """Test remove_entry raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.remove_entry(1, 123)

    @pytest.mark.asyncio
    async def test_get_entries_not_initialized(self, tmp_path):
        """Test get_entries raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.get_entries(1)

    @pytest.mark.asyncio
    async def test_has_entered_not_initialized(self, tmp_path):
        """Test has_entered raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.has_entered(1, 123)

    @pytest.mark.asyncio
    async def test_get_user_entries_not_initialized(self, tmp_path):
        """Test get_user_entries raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.get_user_entries(1, 123)

    @pytest.mark.asyncio
    async def test_add_winner_not_initialized(self, tmp_path):
        """Test add_winner raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.add_winner(1, 123)

    @pytest.mark.asyncio
    async def test_get_winners_not_initialized(self, tmp_path):
        """Test get_winners raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.get_winners(1)

    @pytest.mark.asyncio
    async def test_clear_winners_not_initialized(self, tmp_path):
        """Test clear_winners raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.clear_winners(1)

    @pytest.mark.asyncio
    async def test_get_guild_config_not_initialized(self, tmp_path):
        """Test get_guild_config raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.get_guild_config(123456789)

    @pytest.mark.asyncio
    async def test_save_guild_config_not_initialized(self, tmp_path):
        """Test save_guild_config raises when not initialized.

        Args:
            tmp_path: Pytest fixture providing a temporary directory path.
        """
        storage = StorageService(tmp_path / "test.db")
        config = GuildConfig(guild_id=123456789, admin_role_ids=[])
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            await storage.save_guild_config(config)


class TestDatabaseErrorHandling:
    """Tests for database error handling paths."""

    @pytest.mark.asyncio
    async def test_get_giveaway_db_error(self, storage_service, sample_giveaway, monkeypatch):
        """Test get_giveaway handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        created = await storage_service.create_giveaway(sample_giveaway)
        
        # Mock execute to raise an error
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.get_giveaway(created.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_giveaway_by_message_db_error(self, storage_service, monkeypatch):
        """Test get_giveaway_by_message handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.get_giveaway_by_message(123)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_giveaways_db_error(self, storage_service, monkeypatch):
        """Test get_active_giveaways handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.get_active_giveaways()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_scheduled_giveaways_db_error(self, storage_service, monkeypatch):
        """Test get_scheduled_giveaways handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.get_scheduled_giveaways()
        assert result == []

    @pytest.mark.asyncio
    async def test_update_giveaway_db_error(self, storage_service, sample_giveaway, monkeypatch):
        """Test update_giveaway raises database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        created = await storage_service.create_giveaway(sample_giveaway)
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        with pytest.raises(aiosqlite.Error):
            await storage_service.update_giveaway(created)

    @pytest.mark.asyncio
    async def test_remove_entry_db_error(self, storage_service, sample_giveaway, monkeypatch):
        """Test remove_entry handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        created = await storage_service.create_giveaway(sample_giveaway)
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.remove_entry(created.id, 123)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_entries_db_error(self, storage_service, sample_giveaway, monkeypatch):
        """Test get_entries handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        created = await storage_service.create_giveaway(sample_giveaway)
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.get_entries(created.id)
        assert result == []

    @pytest.mark.asyncio
    async def test_has_entered_db_error(self, storage_service, sample_giveaway, monkeypatch):
        """Test has_entered handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        created = await storage_service.create_giveaway(sample_giveaway)
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.has_entered(created.id, 123)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_entries_db_error(self, storage_service, monkeypatch):
        """Test get_user_entries handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.get_user_entries(123, 456)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_winners_db_error(self, storage_service, sample_giveaway, monkeypatch):
        """Test get_winners handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            sample_giveaway: Pytest fixture providing a sample Giveaway object.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        created = await storage_service.create_giveaway(sample_giveaway)
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.get_winners(created.id)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_guild_config_db_error(self, storage_service, monkeypatch):
        """Test get_guild_config handles database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        result = await storage_service.get_guild_config(123456789)
        # Should return default config on error
        assert result.guild_id == 123456789
        assert result.admin_role_ids == []

    @pytest.mark.asyncio
    async def test_save_guild_config_db_error(self, storage_service, monkeypatch):
        """Test save_guild_config raises database errors.

        Args:
            storage_service: Pytest fixture providing an initialized StorageService.
            monkeypatch: Pytest fixture for mocking.
        """
        import aiosqlite
        config = GuildConfig(guild_id=123456789, admin_role_ids=[])
        
        async def mock_execute(*args, **kwargs):
            raise aiosqlite.Error("Test error")
        
        monkeypatch.setattr(storage_service._connection, "execute", mock_execute)
        
        with pytest.raises(aiosqlite.Error):
            await storage_service.save_guild_config(config)
