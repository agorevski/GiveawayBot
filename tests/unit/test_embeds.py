"""Tests for the embed builders."""

import pytest
from datetime import datetime, timedelta, timezone

import discord

from src.models.giveaway import Giveaway, GiveawayStatus
from src.ui.embeds import (
    create_giveaway_embed,
    create_ended_embed,
    create_cancelled_embed,
    create_list_embed,
    create_entries_embed,
)


class TestCreateGiveawayEmbed:
    """Tests for create_giveaway_embed function."""

    def test_active_giveaway_embed(self):
        """Test creating embed for active giveaway."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            winner_count=2,
        )

        embed = create_giveaway_embed(giveaway, host_name="TestHost")

        assert embed.title == "🎁 GIVEAWAY"
        assert "Test Prize" in embed.description
        assert embed.color == discord.Color.green()
        assert any(f.name == "Winners" and f.value == "2" for f in embed.fields)
        assert "TestHost" in embed.footer.text

    def test_scheduled_giveaway_embed(self):
        """Test creating embed for scheduled giveaway."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Scheduled Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        embed = create_giveaway_embed(giveaway)

        assert embed.color == discord.Color.blue()
        assert any("Scheduled" in f.value for f in embed.fields)

    def test_ended_status_embed(self):
        """Test creating embed for ended giveaway shows grey color."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Ended Prize",
            ends_at=datetime.now(timezone.utc) - timedelta(hours=1),
            created_by=111111111,
            ended=True,
        )

        embed = create_giveaway_embed(giveaway)

        assert embed.color == discord.Color.greyple()

    def test_giveaway_embed_with_role(self):
        """Test creating embed with required role."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="VIP Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            required_role_id=444444444,
        )

        embed = create_giveaway_embed(giveaway, role_name="VIP")

        assert any("VIP" in f.value for f in embed.fields)

    def test_giveaway_embed_entries(self):
        """Test embed shows correct entry count."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            entries=[111, 222, 333],
        )

        embed = create_giveaway_embed(giveaway)

        assert any(f.name == "Entries" and f.value == "3" for f in embed.fields)

    def test_giveaway_embed_time_remaining(self):
        """Test embed shows time remaining."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )

        embed = create_giveaway_embed(giveaway)

        assert any(f.name == "Time Remaining" for f in embed.fields)


class TestCreateEndedEmbed:
    """Tests for create_ended_embed function."""

    def test_ended_embed_with_winners(self):
        """Test creating ended embed with winners."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Won Prize",
            ends_at=datetime.now(timezone.utc) - timedelta(hours=1),
            created_by=111111111,
            ended=True,
            entries=[111, 222, 333],
        )
        winners = [111111111]

        embed = create_ended_embed(giveaway, winners, host_name="TestHost")

        assert embed.title == "🎁 GIVEAWAY ENDED"
        assert "Won Prize" in embed.description
        assert embed.color == discord.Color.dark_grey()
        assert any("Winner" in f.name for f in embed.fields)
        assert "<@111111111>" in embed.fields[0].value

    def test_ended_embed_multiple_winners(self):
        """Test creating ended embed with multiple winners."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc),
            created_by=111111111,
            ended=True,
        )
        winners = [111111111, 222222222, 333333333]

        embed = create_ended_embed(giveaway, winners)

        # Multiple winners should show as list
        winner_field = next(f for f in embed.fields if "Winner" in f.name)
        assert "<@111111111>" in winner_field.value
        assert "<@222222222>" in winner_field.value

    def test_ended_embed_no_winners(self):
        """Test creating ended embed with no winners."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc),
            created_by=111111111,
            ended=True,
        )
        winners = []

        embed = create_ended_embed(giveaway, winners)

        assert any("No valid entries" in f.value for f in embed.fields)

    def test_ended_embed_shows_entry_count(self):
        """Test ended embed shows total entries."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc),
            created_by=111111111,
            entries=[111, 222, 333],
        )

        embed = create_ended_embed(giveaway, [111])

        assert any(f.name == "Total Entries" for f in embed.fields)


class TestCreateCancelledEmbed:
    """Tests for create_cancelled_embed function."""

    def test_cancelled_embed(self):
        """Test creating cancelled embed."""
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Cancelled Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            cancelled=True,
        )

        embed = create_cancelled_embed(giveaway, host_name="TestHost")

        assert embed.title == "🎁 GIVEAWAY CANCELLED"
        assert "~~Cancelled Prize~~" in embed.description
        assert embed.color == discord.Color.red()
        assert any("Cancelled" in f.value for f in embed.fields)
        assert "TestHost" in embed.footer.text


class TestCreateListEmbed:
    """Tests for create_list_embed function."""

    def test_list_embed_with_giveaways(self):
        """Test creating list embed with giveaways."""
        giveaways = [
            Giveaway(
                id=1,
                guild_id=123456789,
                channel_id=987654321,
                prize="Prize 1",
                ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
                created_by=111111111,
            ),
            Giveaway(
                id=2,
                guild_id=123456789,
                channel_id=987654321,
                prize="Prize 2",
                ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
                created_by=111111111,
            ),
        ]

        embed = create_list_embed(giveaways, "Test Guild")

        assert "Test Guild" in embed.title
        assert len(embed.fields) == 2

    def test_list_embed_empty(self):
        """Test creating list embed with no giveaways."""
        embed = create_list_embed([], "Test Guild")

        assert "No active giveaways" in embed.description

    def test_list_embed_scheduled_status(self):
        """Test list embed shows scheduled status."""
        giveaways = [
            Giveaway(
                id=1,
                guild_id=123456789,
                channel_id=987654321,
                prize="Scheduled",
                ends_at=datetime.now(timezone.utc) + timedelta(hours=2),
                created_by=111111111,
                scheduled_start=datetime.now(timezone.utc) + timedelta(hours=1),
            ),
        ]

        embed = create_list_embed(giveaways, "Guild")

        assert "Scheduled" in embed.fields[0].name

    def test_list_embed_truncates_at_10(self):
        """Test list embed truncates at 10 giveaways."""
        giveaways = [
            Giveaway(
                id=i,
                guild_id=123456789,
                channel_id=987654321,
                prize=f"Prize {i}",
                ends_at=datetime.now(timezone.utc) + timedelta(hours=i),
                created_by=111111111,
            )
            for i in range(15)
        ]

        embed = create_list_embed(giveaways, "Guild")

        assert len(embed.fields) == 10
        assert "5 more" in embed.footer.text


class TestCreateEntriesEmbed:
    """Tests for create_entries_embed function."""

    def test_entries_embed_with_entries(self):
        """Test creating entries embed with entries."""
        giveaways = [
            Giveaway(
                id=1,
                guild_id=123456789,
                channel_id=987654321,
                prize="Prize 1",
                ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
                created_by=111111111,
            ),
        ]

        embed = create_entries_embed(giveaways, "TestUser")

        assert "TestUser" in embed.title
        assert embed.color == discord.Color.purple()
        assert len(embed.fields) == 1

    def test_entries_embed_empty(self):
        """Test creating entries embed with no entries."""
        embed = create_entries_embed([], "TestUser")

        assert "haven't entered" in embed.description

    def test_entries_embed_truncates_at_10(self):
        """Test entries embed truncates at 10 entries."""
        giveaways = [
            Giveaway(
                id=i,
                guild_id=123456789,
                channel_id=987654321,
                prize=f"Prize {i}",
                ends_at=datetime.now(timezone.utc) + timedelta(hours=i),
                created_by=111111111,
            )
            for i in range(15)
        ]

        embed = create_entries_embed(giveaways, "User")

        assert len(embed.fields) == 10
        assert "5 more" in embed.footer.text
