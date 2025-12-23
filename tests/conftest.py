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
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
async def storage_service(temp_db_path):
    """Create and initialize a storage service for testing."""
    storage = StorageService(temp_db_path)
    await storage.initialize()
    yield storage
    await storage.close()


@pytest.fixture
async def giveaway_service(storage_service):
    """Create a giveaway service for testing."""
    return GiveawayService(storage_service)


@pytest.fixture
async def winner_service(storage_service):
    """Create a winner service for testing."""
    return WinnerService(storage_service)


@pytest.fixture
def sample_giveaway():
    """Create a sample giveaway for testing."""
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
    """Create a sample giveaway dictionary for testing."""
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
    """Create a sample guild configuration for testing."""
    return GuildConfig(
        guild_id=123456789,
        admin_role_ids=[111111111, 222222222],
    )


@pytest.fixture
def sample_guild_config_dict():
    """Create a sample guild config dictionary for testing."""
    return {
        "guild_id": 123456789,
        "admin_role_ids": "[111111111, 222222222]",
        "created_at": datetime.utcnow().isoformat(),
    }
