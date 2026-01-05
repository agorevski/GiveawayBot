"""Tests for the Giveaway model."""

import pytest
from datetime import datetime, timedelta, timezone

from src.models.giveaway import Giveaway, GiveawayStatus


class TestGiveawayModel:
    """Tests for the Giveaway dataclass."""

    def test_create_giveaway(self):
        """Test creating a basic giveaway.

        Verifies that a Giveaway object is created with the correct default
        values and that all required fields are properly assigned.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
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
        """Test that a new giveaway has active status.

        Verifies that a newly created giveaway without scheduled_start
        has ACTIVE status and correct is_active/is_ended flags.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )

        assert giveaway.status == GiveawayStatus.ACTIVE
        assert giveaway.is_active is True
        assert giveaway.is_ended is False

    def test_giveaway_status_ended(self):
        """Test ended giveaway status.

        Verifies that a giveaway with ended=True has ENDED status
        and correct is_active/is_ended flags.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            ended=True,
        )

        assert giveaway.status == GiveawayStatus.ENDED
        assert giveaway.is_active is False
        assert giveaway.is_ended is True

    def test_giveaway_status_cancelled(self):
        """Test cancelled giveaway status.

        Verifies that a giveaway with cancelled=True has CANCELLED status
        and correct is_active/is_ended flags.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            cancelled=True,
        )

        assert giveaway.status == GiveawayStatus.CANCELLED
        assert giveaway.is_active is False
        assert giveaway.is_ended is True

    def test_giveaway_status_scheduled(self):
        """Test scheduled giveaway status.

        Verifies that a giveaway with a future scheduled_start time
        has SCHEDULED status and correct is_active/is_ended flags.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert giveaway.status == GiveawayStatus.SCHEDULED
        assert giveaway.is_active is False
        assert giveaway.is_ended is False

    def test_should_end(self):
        """Test should_end property.

        Verifies that should_end returns True when an active giveaway
        has passed its end time, and False otherwise.
        """
        # Active giveaway past end time
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) - timedelta(hours=1),
            created_by=111111111,
        )

        assert giveaway.should_end is True

        # Active giveaway not past end time
        giveaway.ends_at = datetime.now(timezone.utc) + timedelta(hours=1)
        assert giveaway.should_end is False

    def test_should_start(self):
        """Test should_start property for scheduled giveaways.

        Verifies the should_start property behavior for scheduled and
        active giveaways. A scheduled giveaway should_start only when
        the scheduled_start time has been reached.
        """
        # Scheduled giveaway that should start (scheduled_start is exactly now or just passed)
        # Note: should_start only returns True if status is SCHEDULED (scheduled_start > now)
        # and scheduled_start time has been reached. This is checked in the background task.
        # When scheduled_start passes, status becomes ACTIVE, so should_start returns False.
        
        # Giveaway scheduled for the future - should not start yet
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        
        assert giveaway.status == GiveawayStatus.SCHEDULED
        assert giveaway.should_start is False
        
        # Active giveaway (no scheduled_start) - should_start is not applicable
        active_giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            created_by=111111111,
        )
        assert active_giveaway.status == GiveawayStatus.ACTIVE
        assert active_giveaway.should_start is False

    def test_time_remaining(self):
        """Test time_remaining property.

        Verifies that time_remaining returns the correct number of seconds
        until the giveaway ends, and None for ended giveaways.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )

        # Should be approximately 3600 seconds (1 hour)
        assert giveaway.time_remaining is not None
        assert 3590 <= giveaway.time_remaining <= 3610

        # Ended giveaway has no time remaining
        giveaway.ended = True
        assert giveaway.time_remaining is None

    def test_entry_count(self):
        """Test entry_count property.

        Verifies that entry_count returns the correct number of entries
        in the giveaway's entries list.
        """
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )

        assert giveaway.entry_count == 0

        giveaway.entries = [1, 2, 3, 4, 5]
        assert giveaway.entry_count == 5

    def test_to_dict(self):
        """Test to_dict method.

        Verifies that to_dict returns a dictionary containing all
        giveaway attributes with correct values.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
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
        """Test from_dict classmethod.

        Verifies that from_dict correctly creates a Giveaway object
        from a dictionary representation.
        """
        data = {
            "id": 1,
            "guild_id": 123456789,
            "channel_id": 987654321,
            "prize": "Test Prize",
            "winner_count": 2,
            "created_by": 111111111,
            "ends_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "ended": False,
            "cancelled": False,
        }

        giveaway = Giveaway.from_dict(data)

        assert giveaway.id == 1
        assert giveaway.guild_id == 123456789
        assert giveaway.prize == "Test Prize"
        assert giveaway.winner_count == 2
