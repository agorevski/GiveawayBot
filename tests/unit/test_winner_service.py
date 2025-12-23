"""Tests for the WinnerService."""

import pytest
from datetime import datetime, timedelta, timezone

from src.models.giveaway import Giveaway


class TestWinnerService:
    """Tests for the WinnerService."""

    @pytest.mark.asyncio
    async def test_select_winners_basic(self, winner_service, storage_service):
        """Test selecting winners from entries."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            winner_count=1,
        )
        saved = await storage_service.create_giveaway(giveaway)

        # Add entries
        await storage_service.add_entry(saved.id, 222222222)
        await storage_service.add_entry(saved.id, 333333333)
        await storage_service.add_entry(saved.id, 444444444)

        winners = await winner_service.select_winners(saved)

        assert len(winners) == 1
        assert winners[0] in [222222222, 333333333, 444444444]

    @pytest.mark.asyncio
    async def test_select_multiple_winners(self, winner_service, storage_service):
        """Test selecting multiple winners."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            winner_count=3,
        )
        saved = await storage_service.create_giveaway(giveaway)

        # Add entries
        await storage_service.add_entry(saved.id, 222222222)
        await storage_service.add_entry(saved.id, 333333333)
        await storage_service.add_entry(saved.id, 444444444)
        await storage_service.add_entry(saved.id, 555555555)

        winners = await winner_service.select_winners(saved)

        assert len(winners) == 3
        assert len(set(winners)) == 3  # All unique

    @pytest.mark.asyncio
    async def test_select_winners_no_entries(self, winner_service, storage_service):
        """Test selecting winners when there are no entries."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            winner_count=1,
        )
        saved = await storage_service.create_giveaway(giveaway)

        winners = await winner_service.select_winners(saved)

        assert len(winners) == 0

    @pytest.mark.asyncio
    async def test_select_winners_fewer_entries_than_winners(
        self, winner_service, storage_service
    ):
        """Test selecting winners when there are fewer entries than winners requested."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            winner_count=5,
        )
        saved = await storage_service.create_giveaway(giveaway)

        # Only 2 entries
        await storage_service.add_entry(saved.id, 222222222)
        await storage_service.add_entry(saved.id, 333333333)

        winners = await winner_service.select_winners(saved)

        assert len(winners) == 2

    @pytest.mark.asyncio
    async def test_select_winners_with_valid_user_filter(
        self, winner_service, storage_service
    ):
        """Test selecting winners filtering by valid users."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            winner_count=1,
        )
        saved = await storage_service.create_giveaway(giveaway)

        # Add entries
        await storage_service.add_entry(saved.id, 222222222)
        await storage_service.add_entry(saved.id, 333333333)
        await storage_service.add_entry(saved.id, 444444444)

        # Only 222222222 is valid
        winners = await winner_service.select_winners(
            saved, valid_user_ids=[222222222]
        )

        assert len(winners) == 1
        assert winners[0] == 222222222

    @pytest.mark.asyncio
    async def test_select_winners_no_valid_users(
        self, winner_service, storage_service
    ):
        """Test selecting winners when no entries are valid users."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            winner_count=1,
        )
        saved = await storage_service.create_giveaway(giveaway)

        await storage_service.add_entry(saved.id, 222222222)
        await storage_service.add_entry(saved.id, 333333333)

        # No entries are valid
        winners = await winner_service.select_winners(
            saved, valid_user_ids=[999999999]
        )

        assert len(winners) == 0

    @pytest.mark.asyncio
    async def test_select_winners_null_giveaway_id(self, winner_service):
        """Test selecting winners for a giveaway with no ID."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        # giveaway.id is None

        winners = await winner_service.select_winners(giveaway)

        assert len(winners) == 0

    @pytest.mark.asyncio
    async def test_reroll_winners(self, winner_service, storage_service):
        """Test rerolling winners."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            winner_count=1,
        )
        saved = await storage_service.create_giveaway(giveaway)

        # Add entries
        await storage_service.add_entry(saved.id, 222222222)
        await storage_service.add_entry(saved.id, 333333333)
        await storage_service.add_entry(saved.id, 444444444)

        # First selection
        first_winners = await winner_service.select_winners(saved)

        # Reroll
        new_winners, message = await winner_service.reroll_winners(saved)

        assert len(new_winners) == 1
        assert "rerolled" in message.lower() or "success" in message.lower()
        # New winner should be different from first if possible
        assert new_winners[0] not in first_winners

    @pytest.mark.asyncio
    async def test_reroll_winners_no_entries(self, winner_service, storage_service):
        """Test rerolling when there are no entries."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        saved = await storage_service.create_giveaway(giveaway)

        new_winners, message = await winner_service.reroll_winners(saved)

        assert len(new_winners) == 0
        assert "no" in message.lower()

    @pytest.mark.asyncio
    async def test_reroll_winners_null_id(self, winner_service):
        """Test rerolling for a giveaway with no ID."""
        giveaway = Giveaway(
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )

        new_winners, message = await winner_service.reroll_winners(giveaway)

        assert len(new_winners) == 0
        assert "invalid" in message.lower()

    @pytest.mark.asyncio
    async def test_get_winners(self, winner_service, storage_service):
        """Test getting winners for a giveaway."""
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

        winners = await winner_service.get_winners(saved.id)

        assert len(winners) == 2
        assert 222222222 in winners
        assert 333333333 in winners

    @pytest.mark.asyncio
    async def test_clear_winners(self, winner_service, storage_service):
        """Test clearing winners for a giveaway."""
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

        await winner_service.clear_winners(saved.id)

        winners = await winner_service.get_winners(saved.id)
        assert len(winners) == 0


class TestWinnerServiceFormatting:
    """Tests for WinnerService formatting methods."""

    def test_format_winners_message_no_winners(self, winner_service):
        """Test formatting message when there are no winners."""
        message = winner_service.format_winners_message([], "Test Prize")

        assert "no valid entries" in message.lower() or "no winner" in message.lower()
        assert "Test Prize" in message

    def test_format_winners_message_single_winner(self, winner_service):
        """Test formatting message for a single winner."""
        message = winner_service.format_winners_message([222222222], "Test Prize")

        assert "<@222222222>" in message
        assert "Test Prize" in message
        assert "congratulations" in message.lower()

    def test_format_winners_message_multiple_winners(self, winner_service):
        """Test formatting message for multiple winners."""
        message = winner_service.format_winners_message(
            [222222222, 333333333, 444444444], "Test Prize"
        )

        assert "<@222222222>" in message
        assert "<@333333333>" in message
        assert "<@444444444>" in message
        assert "Test Prize" in message

    def test_format_dm_message(self, winner_service):
        """Test formatting DM message for winners."""
        message = winner_service.format_dm_message("Test Prize", "Test Server")

        assert "congratulations" in message.lower()
        assert "Test Prize" in message
        assert "Test Server" in message
