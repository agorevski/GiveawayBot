"""Tests for the GiveawayService."""

import pytest
from datetime import datetime, timedelta

from src.services.giveaway_service import GiveawayService

class TestParseDuration:
    """Tests for the parse_duration method."""

    def test_parse_seconds(self):
        """Test parsing seconds."""
        assert GiveawayService.parse_duration("30s") == 30
        assert GiveawayService.parse_duration("30sec") == 30
        assert GiveawayService.parse_duration("30 seconds") == 30
        assert GiveawayService.parse_duration("1 second") == 1

    def test_parse_minutes(self):
        """Test parsing minutes."""
        assert GiveawayService.parse_duration("5m") == 300
        assert GiveawayService.parse_duration("5min") == 300
        assert GiveawayService.parse_duration("5 minutes") == 300
        assert GiveawayService.parse_duration("1 minute") == 60

    def test_parse_hours(self):
        """Test parsing hours."""
        assert GiveawayService.parse_duration("2h") == 7200
        assert GiveawayService.parse_duration("2hr") == 7200
        assert GiveawayService.parse_duration("2 hours") == 7200
        assert GiveawayService.parse_duration("1 hour") == 3600

    def test_parse_days(self):
        """Test parsing days."""
        assert GiveawayService.parse_duration("1d") == 86400
        assert GiveawayService.parse_duration("1 day") == 86400
        assert GiveawayService.parse_duration("7 days") == 604800

    def test_parse_weeks(self):
        """Test parsing weeks."""
        assert GiveawayService.parse_duration("1w") == 604800
        assert GiveawayService.parse_duration("1 week") == 604800
        assert GiveawayService.parse_duration("2 weeks") == 1209600

    def test_parse_combined(self):
        """Test parsing combined durations."""
        assert GiveawayService.parse_duration("1d2h") == 86400 + 7200
        assert GiveawayService.parse_duration("1d 2h 30m") == 86400 + 7200 + 1800
        assert GiveawayService.parse_duration("1h30m") == 3600 + 1800

    def test_parse_number_only(self):
        """Test parsing plain numbers (assumed to be minutes)."""
        assert GiveawayService.parse_duration("30") == 1800  # 30 minutes
        assert GiveawayService.parse_duration("60") == 3600  # 60 minutes

    def test_parse_invalid(self):
        """Test parsing invalid duration strings."""
        assert GiveawayService.parse_duration("") is None
        assert GiveawayService.parse_duration("invalid") is None
        assert GiveawayService.parse_duration("abc123") is None

    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        assert GiveawayService.parse_duration("1H") == 3600
        assert GiveawayService.parse_duration("1D") == 86400
        assert GiveawayService.parse_duration("1 HOUR") == 3600

class TestGiveawayServiceAsync:
    """Async tests for the GiveawayService."""

    @pytest.mark.asyncio
    async def test_create_giveaway(self, giveaway_service):
        """Test creating a giveaway."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
            winner_count=2,
        )

        assert giveaway.id is not None
        assert giveaway.guild_id == 123456789
        assert giveaway.channel_id == 987654321
        assert giveaway.prize == "Test Prize"
        assert giveaway.winner_count == 2
        assert giveaway.is_active is True

    @pytest.mark.asyncio
    async def test_get_giveaway(self, giveaway_service):
        """Test retrieving a giveaway."""
        created = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        retrieved = await giveaway_service.get_giveaway(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.prize == "Test Prize"

    @pytest.mark.asyncio
    async def test_get_nonexistent_giveaway(self, giveaway_service):
        """Test retrieving a non-existent giveaway."""
        result = await giveaway_service.get_giveaway(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_enter_giveaway(self, giveaway_service):
        """Test entering a giveaway."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        success, message = await giveaway_service.enter_giveaway(
            giveaway.id,
            user_id=222222222,
            user_role_ids=[],
        )

        assert success is True
        assert "entered" in message.lower()

    @pytest.mark.asyncio
    async def test_enter_giveaway_twice(self, giveaway_service):
        """Test that a user can't enter twice."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        # First entry
        await giveaway_service.enter_giveaway(
            giveaway.id,
            user_id=222222222,
            user_role_ids=[],
        )

        # Second entry should fail
        success, message = await giveaway_service.enter_giveaway(
            giveaway.id,
            user_id=222222222,
            user_role_ids=[],
        )

        assert success is False
        assert "already" in message.lower()

    @pytest.mark.asyncio
    async def test_enter_giveaway_role_requirement(self, giveaway_service):
        """Test role requirement for giveaway entry."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
            required_role_id=444444444,
        )

        # User without required role
        success, message = await giveaway_service.enter_giveaway(
            giveaway.id,
            user_id=222222222,
            user_role_ids=[555555555],
        )

        assert success is False
        assert "role" in message.lower()

        # User with required role
        success, message = await giveaway_service.enter_giveaway(
            giveaway.id,
            user_id=333333333,
            user_role_ids=[444444444],
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_end_giveaway(self, giveaway_service):
        """Test ending a giveaway."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        ended = await giveaway_service.end_giveaway(giveaway.id)

        assert ended is not None
        assert ended.ended is True

    @pytest.mark.asyncio
    async def test_cancel_giveaway(self, giveaway_service):
        """Test cancelling a giveaway."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        success, message = await giveaway_service.cancel_giveaway(giveaway.id)

        assert success is True

        cancelled = await giveaway_service.get_giveaway(giveaway.id)
        assert cancelled.cancelled is True

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_giveaway(self, giveaway_service):
        """Test cancelling a non-existent giveaway."""
        success, message = await giveaway_service.cancel_giveaway(99999)

        assert success is False
        assert "not found" in message.lower()

    @pytest.mark.asyncio
    async def test_cancel_already_ended_giveaway(self, giveaway_service):
        """Test cancelling an already ended giveaway."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        await giveaway_service.end_giveaway(giveaway.id)

        success, message = await giveaway_service.cancel_giveaway(giveaway.id)

        assert success is False
        assert "already ended" in message.lower()

    @pytest.mark.asyncio
    async def test_leave_giveaway(self, giveaway_service):
        """Test leaving a giveaway."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        await giveaway_service.enter_giveaway(giveaway.id, 222222222, [])

        success, message = await giveaway_service.leave_giveaway(giveaway.id, 222222222)

        assert success is True
        assert "removed" in message.lower()

    @pytest.mark.asyncio
    async def test_leave_giveaway_not_entered(self, giveaway_service):
        """Test leaving a giveaway when not entered."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        success, message = await giveaway_service.leave_giveaway(giveaway.id, 222222222)

        assert success is False

    @pytest.mark.asyncio
    async def test_leave_nonexistent_giveaway(self, giveaway_service):
        """Test leaving a non-existent giveaway."""
        success, message = await giveaway_service.leave_giveaway(99999, 222222222)

        assert success is False
        assert "not found" in message.lower()

    @pytest.mark.asyncio
    async def test_enter_nonexistent_giveaway(self, giveaway_service):
        """Test entering a non-existent giveaway."""
        success, message = await giveaway_service.enter_giveaway(99999, 222222222, [])

        assert success is False
        assert "not found" in message.lower()

    @pytest.mark.asyncio
    async def test_enter_ended_giveaway(self, giveaway_service):
        """Test entering an ended giveaway."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        await giveaway_service.end_giveaway(giveaway.id)

        success, message = await giveaway_service.enter_giveaway(giveaway.id, 222222222, [])

        assert success is False
        assert "ended" in message.lower()

    @pytest.mark.asyncio
    async def test_end_nonexistent_giveaway(self, giveaway_service):
        """Test ending a non-existent giveaway."""
        result = await giveaway_service.end_giveaway(99999)

        assert result is None

    @pytest.mark.asyncio
    async def test_set_message_id(self, giveaway_service):
        """Test setting message ID on a giveaway."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        await giveaway_service.set_message_id(giveaway, 555555555)

        retrieved = await giveaway_service.get_giveaway(giveaway.id)
        assert retrieved.message_id == 555555555

    @pytest.mark.asyncio
    async def test_get_active_giveaways(self, giveaway_service):
        """Test getting active giveaways."""
        guild_id = 123456789

        await giveaway_service.create_giveaway(
            guild_id=guild_id,
            channel_id=987654321,
            prize="Active 1",
            duration_seconds=3600,
            created_by=111111111,
        )
        await giveaway_service.create_giveaway(
            guild_id=guild_id,
            channel_id=987654321,
            prize="Active 2",
            duration_seconds=3600,
            created_by=111111111,
        )

        active = await giveaway_service.get_active_giveaways(guild_id)

        assert len(active) >= 2

    @pytest.mark.asyncio
    async def test_get_giveaway_by_message(self, giveaway_service):
        """Test getting a giveaway by message ID."""
        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
        )

        await giveaway_service.set_message_id(giveaway, 555555555)

        retrieved = await giveaway_service.get_giveaway_by_message(555555555)

        assert retrieved is not None
        assert retrieved.id == giveaway.id

    @pytest.mark.asyncio
    async def test_start_scheduled_giveaway(self, giveaway_service):
        """Test starting a scheduled giveaway."""
        from datetime import datetime, timedelta, timezone

        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert giveaway.scheduled_start is not None

        await giveaway_service.start_scheduled_giveaway(giveaway)

        retrieved = await giveaway_service.get_giveaway(giveaway.id)
        assert retrieved.scheduled_start is None

    @pytest.mark.asyncio
    async def test_create_giveaway_with_scheduled_start(self, giveaway_service):
        """Test creating a giveaway with scheduled start."""
        from datetime import datetime, timedelta, timezone

        scheduled = datetime.now(timezone.utc) + timedelta(hours=2)

        giveaway = await giveaway_service.create_giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            duration_seconds=3600,
            created_by=111111111,
            scheduled_start=scheduled,
        )

        assert giveaway.scheduled_start is not None
        # ends_at should be scheduled_start + duration
        expected_end = scheduled + timedelta(seconds=3600)
        assert abs((giveaway.ends_at - expected_end).total_seconds()) < 1
