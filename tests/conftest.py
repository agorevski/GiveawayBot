"""Pytest fixtures for the Giveaway Bot tests."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone

from src.models.giveaway import Giveaway
from src.models.guild_config import GuildConfig
from src.services.storage_service import StorageService
from src.services.giveaway_service import GiveawayService
from src.services.winner_service import WinnerService


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing.

    Yields:
        Path: A path to a temporary SQLite database file that will be
            cleaned up after the test completes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
async def storage_service(temp_db_path):
    """Create and initialize a storage service for testing.

    Args:
        temp_db_path: Path to the temporary database file.

    Yields:
        StorageService: An initialized storage service instance that will be
            closed after the test completes.
    """
    storage = StorageService(temp_db_path)
    await storage.initialize()
    yield storage
    await storage.close()


@pytest.fixture
async def giveaway_service(storage_service):
    """Create a giveaway service for testing.

    Args:
        storage_service: The storage service fixture to use for persistence.

    Returns:
        GiveawayService: A giveaway service instance configured with the
            test storage service.
    """
    return GiveawayService(storage_service)


@pytest.fixture
async def winner_service(storage_service):
    """Create a winner service for testing.

    Args:
        storage_service: The storage service fixture to use for persistence.

    Returns:
        WinnerService: A winner service instance configured with the
            test storage service.
    """
    return WinnerService(storage_service)


@pytest.fixture
def sample_giveaway():
    """Create a sample giveaway for testing.

    Returns:
        Giveaway: A giveaway instance with predefined test values including
            a guild ID, channel ID, prize name, and end time set to 1 hour
            from creation.
    """
    return Giveaway(
        guild_id=123456789,
        channel_id=987654321,
        prize="Test Prize",
        ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_by=111111111,
        winner_count=1,
    )


@pytest.fixture
def sample_giveaway_dict():
    """Create a sample giveaway dictionary for testing.

    Returns:
        dict: A dictionary representing a giveaway with all fields populated,
            including an ID, message ID, required role, and end time set to
            1 hour from creation.
    """
    ends_at = datetime.now(timezone.utc) + timedelta(hours=1)
    return {
        "id": 1,
        "guild_id": 123456789,
        "channel_id": 987654321,
        "message_id": 555555555,
        "prize": "Test Prize",
        "winner_count": 2,
        "required_role_id": 444444444,
        "created_by": 111111111,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scheduled_start": None,
        "ends_at": ends_at.isoformat(),
        "ended": False,
        "cancelled": False,
    }


@pytest.fixture
def sample_guild_config():
    """Create a sample guild configuration for testing.

    Returns:
        GuildConfig: A guild configuration instance with predefined test values
            including a guild ID and two admin role IDs.
    """
    return GuildConfig(
        guild_id=123456789,
        admin_role_ids=[111111111, 222222222],
    )


@pytest.fixture
def sample_guild_config_dict():
    """Create a sample guild config dictionary for testing.

    Returns:
        dict: A dictionary representing a guild configuration with guild ID,
            JSON-encoded admin role IDs, and creation timestamp.
    """
    return {
        "guild_id": 123456789,
        "admin_role_ids": "[111111111, 222222222]",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
