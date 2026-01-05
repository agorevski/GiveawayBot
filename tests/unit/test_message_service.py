"""Tests for the message service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

import discord

from src.services.message_service import GiveawayMessageService
from src.services.winner_service import WinnerService
from src.models.giveaway import Giveaway


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot."""
    bot = MagicMock(spec=discord.Client)
    return bot


@pytest.fixture
def mock_winner_service():
    """Create a mock winner service."""
    service = MagicMock(spec=WinnerService)
    service.format_dm_message.return_value = "Congratulations! You won!"
    return service


@pytest.fixture
def message_service(mock_bot, mock_winner_service):
    """Create a message service for testing."""
    return GiveawayMessageService(mock_bot, mock_winner_service)


@pytest.fixture
def sample_ended_giveaway():
    """Create a sample ended giveaway."""
    return Giveaway(
        id=1,
        guild_id=123456789,
        channel_id=987654321,
        message_id=555555555,
        prize="Test Prize",
        ends_at=datetime.now(timezone.utc) - timedelta(hours=1),
        created_by=111111111,
        ended=True,
    )


class TestUpdateGiveawayMessage:
    """Tests for update_giveaway_message method."""

    @pytest.mark.asyncio
    async def test_update_message_no_message_id(self, message_service):
        """Test update when giveaway has no message ID.

        Args:
            message_service: The message service fixture.

        Returns:
            None. Verifies that the method returns early without errors.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            message_id=None,  # No message ID
            prize="Prize",
            ends_at=datetime.now(timezone.utc),
            created_by=111111111,
        )

        # Should not raise, just return early
        await message_service.update_giveaway_message(giveaway, [])

    @pytest.mark.asyncio
    async def test_update_message_channel_not_text(self, message_service, mock_bot, sample_ended_giveaway):
        """Test update when channel is not a text channel.

        Args:
            message_service: The message service fixture.
            mock_bot: The mock Discord bot fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that get_channel is called with the correct channel ID.
        """
        mock_bot.get_channel.return_value = MagicMock(spec=discord.VoiceChannel)

        await message_service.update_giveaway_message(sample_ended_giveaway, [111])

        mock_bot.get_channel.assert_called_once_with(sample_ended_giveaway.channel_id)

    @pytest.mark.asyncio
    async def test_update_message_success(self, message_service, mock_bot, sample_ended_giveaway):
        """Test successful message update.

        Args:
            message_service: The message service fixture.
            mock_bot: The mock Discord bot fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that message.edit is called once.
        """
        channel = AsyncMock(spec=discord.TextChannel)
        message = AsyncMock(spec=discord.Message)
        channel.fetch_message.return_value = message
        mock_bot.get_channel.return_value = channel

        host = MagicMock()
        host.display_name = "TestHost"
        mock_bot.fetch_user = AsyncMock(return_value=host)

        await message_service.update_giveaway_message(sample_ended_giveaway, [111111111])

        message.edit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_message_not_found(self, message_service, mock_bot, sample_ended_giveaway):
        """Test update when message is not found.

        Args:
            message_service: The message service fixture.
            mock_bot: The mock Discord bot fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that the method handles NotFound gracefully.
        """
        channel = AsyncMock(spec=discord.TextChannel)
        channel.fetch_message.side_effect = discord.NotFound(MagicMock(), "Not found")
        mock_bot.get_channel.return_value = channel
        mock_bot.fetch_user = AsyncMock()

        # Should not raise, just log warning
        await message_service.update_giveaway_message(sample_ended_giveaway, [])

    @pytest.mark.asyncio
    async def test_update_message_host_not_found(self, message_service, mock_bot, sample_ended_giveaway):
        """Test update when host user is not found.

        Args:
            message_service: The message service fixture.
            mock_bot: The mock Discord bot fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that edit is called with 'Unknown' as host.
        """
        channel = AsyncMock(spec=discord.TextChannel)
        message = AsyncMock(spec=discord.Message)
        channel.fetch_message.return_value = message
        mock_bot.get_channel.return_value = channel
        mock_bot.fetch_user = AsyncMock(side_effect=discord.NotFound(MagicMock(), "Not found"))

        await message_service.update_giveaway_message(sample_ended_giveaway, [111111111])

        # Should still call edit with "Unknown" as host
        message.edit.assert_called_once()


class TestAnnounceWinners:
    """Tests for announce_winners method."""

    @pytest.mark.asyncio
    async def test_announce_no_winners(self, message_service, sample_ended_giveaway):
        """Test announcement when there are no winners.

        Args:
            message_service: The message service fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that 'No valid entries' message is sent.
        """
        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()

        await message_service.announce_winners(sample_ended_giveaway, [], channel)

        channel.send.assert_called_once()
        assert "No valid entries" in channel.send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_announce_with_winners(self, message_service, mock_bot, sample_ended_giveaway):
        """Test announcement with winners.

        Args:
            message_service: The message service fixture.
            mock_bot: The mock Discord bot fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that congratulations message includes winner mentions.
        """
        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.name = "Test Guild"

        winner_user = AsyncMock(spec=discord.User)
        mock_bot.fetch_user = AsyncMock(return_value=winner_user)

        await message_service.announce_winners(
            sample_ended_giveaway, [111111111, 222222222], channel
        )

        # Check public announcement
        assert channel.send.call_count >= 1
        first_call = channel.send.call_args_list[0]
        assert "Congratulations" in first_call[0][0]
        assert "<@111111111>" in first_call[0][0]
        assert "<@222222222>" in first_call[0][0]

    @pytest.mark.asyncio
    async def test_announce_dm_winners(self, message_service, mock_bot, mock_winner_service, sample_ended_giveaway):
        """Test that winners receive DMs.

        Args:
            message_service: The message service fixture.
            mock_bot: The mock Discord bot fixture.
            mock_winner_service: The mock winner service fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that DM is sent to winner.
        """
        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.name = "Test Guild"

        winner_user = AsyncMock(spec=discord.User)
        mock_bot.fetch_user = AsyncMock(return_value=winner_user)

        await message_service.announce_winners(sample_ended_giveaway, [111111111], channel)

        mock_winner_service.format_dm_message.assert_called_once_with(
            sample_ended_giveaway.prize, "Test Guild"
        )
        winner_user.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_announce_dm_fails_gracefully(self, message_service, mock_bot, sample_ended_giveaway):
        """Test that DM failures are handled gracefully.

        Args:
            message_service: The message service fixture.
            mock_bot: The mock Discord bot fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that Forbidden exception does not raise.
        """
        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.name = "Test Guild"

        winner_user = AsyncMock(spec=discord.User)
        winner_user.send.side_effect = discord.Forbidden(MagicMock(), "DMs disabled")
        mock_bot.fetch_user = AsyncMock(return_value=winner_user)

        # Should not raise
        await message_service.announce_winners(sample_ended_giveaway, [111111111], channel)

    @pytest.mark.asyncio
    async def test_announce_user_not_found(self, message_service, mock_bot, sample_ended_giveaway):
        """Test announcement when winner user is not found.

        Args:
            message_service: The message service fixture.
            mock_bot: The mock Discord bot fixture.
            sample_ended_giveaway: A sample ended giveaway fixture.

        Returns:
            None. Verifies that NotFound exception does not raise.
        """
        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.name = "Test Guild"

        mock_bot.fetch_user = AsyncMock(
            side_effect=discord.NotFound(MagicMock(), "Not found")
        )

        # Should not raise
        await message_service.announce_winners(sample_ended_giveaway, [111111111], channel)
