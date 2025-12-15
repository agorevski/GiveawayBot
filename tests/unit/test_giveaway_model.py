"""Tests for the Giveaway model."""

import pytest
from datetime import datetime, timedelta

from src.models.giveaway import Giveaway, GiveawayStatus


class TestGiveawayModel:
    """Tests for the Giveaway dataclass."""

    def test_create_giveaway(self):
        """Test creating a basic giveaway."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=1),
            created_by=111111111,
        )

        assert giveaway.guild_id == 123456789
        assert giveaway.channel_id == 987654321
        assert giveaway.prize == "Test Prize"
        assert giveaway.created_by == 111111111
        assert giveaway.winner_count == 1
        assert giveaway.id is None
        assert giveaway.message_id is None
        assert giveaway.required_role_id is None
        assert giveaway.ended is False
        assert giveaway.cancelled is False

    def test_giveaway_status_active(self):
        """Test that a new giveaway has active status."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=1),
            created_by=111111111,
        )

        assert giveaway.status == GiveawayStatus.ACTIVE
        assert giveaway.is_active is True
        assert giveaway.is_ended is False

    def test_giveaway_status_ended(self):
        """Test ended giveaway status."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=1),
            created_by=111111111,
            ended=True,
        )

        assert giveaway.status == GiveawayStatus.ENDED
        assert giveaway.is_active is False
        assert giveaway.is_ended is True

    def test_giveaway_status_cancelled(self):
        """Test cancelled giveaway status."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=1),
            created_by=111111111,
            cancelled=True,
        )

        assert giveaway.status == GiveawayStatus.CANCELLED
        assert giveaway.is_active is False
        assert giveaway.is_ended is True

    def test_giveaway_status_scheduled(self):
        """Test scheduled giveaway status."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=2),
            created_by=111111111,
            scheduled_start=datetime.utcnow() + timedelta(hours=1),
        )

        assert giveaway.status == GiveawayStatus.SCHEDULED
        assert giveaway.is_active is False
        assert giveaway.is_ended is False

    def test_should_end(self):
        """Test should_end property."""
        # Active giveaway past end time
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() - timedelta(hours=1),
            created_by=111111111,
        )

        assert giveaway.should_end is True

        # Active giveaway not past end time
        giveaway.ends_at = datetime.utcnow() + timedelta(hours=1)
        assert giveaway.should_end is False

    def test_should_start(self):
        """Test should_start property for scheduled giveaways."""
        # Scheduled giveaway past start time
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=2),
            created_by=111111111,
            scheduled_start=datetime.utcnow() - timedelta(minutes=5),
        )

        assert giveaway.should_start is True

        # Scheduled giveaway not past start time
        giveaway.scheduled_start = datetime.utcnow() + timedelta(hours=1)
        assert giveaway.should_start is False

    def test_time_remaining(self):
        """Test time_remaining property."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=1),
            created_by=111111111,
        )

        # Should be approximately 3600 seconds (1 hour)
        assert giveaway.time_remaining is not None
        assert 3590 <= giveaway.time_remaining <= 3610

        # Ended giveaway has no time remaining
        giveaway.ended = True
        assert giveaway.time_remaining is None

    def test_entry_count(self):
        """Test entry_count property."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=1),
            created_by=111111111,
        )

        assert giveaway.entry_count == 0

        giveaway.entries = [1, 2, 3, 4, 5]
        assert giveaway.entry_count == 5

    def test_to_dict(self):
        """Test to_dict method."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.utcnow() + timedelta(hours=1),
            created_by=111111111,
            winner_count=3,
        )

        data = giveaway.to_dict()

        assert data["id"] == 1
        assert data["guild_id"] == 123456789
        assert data["channel_id"] == 987654321
        assert data["prize"] == "Test Prize"
        assert data["winner_count"] == 3
        assert data["created_by"] == 111111111
        assert data["ended"] is False
        assert data["cancelled"] is False

    def test_from_dict(self):
        """Test from_dict classmethod."""
        data = {
            "id": 1,
            "guild_id": 123456789,
            "channel_id": 987654321,
            "prize": "Test Prize",
            "winner_count": 2,
            "created_by": 111111111,
            "ends_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "ended": False,
            "cancelled": False,
        }

        giveaway = Giveaway.from_dict(data)

        assert giveaway.id == 1
        assert giveaway.guild_id == 123456789
        assert giveaway.prize == "Test Prize"
        assert giveaway.winner_count == 2
