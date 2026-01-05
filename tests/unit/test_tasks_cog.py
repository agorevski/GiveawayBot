"""Tests for the TasksCog."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from src.cogs.tasks import TasksCog, setup
from src.models.giveaway import Giveaway
from src.config import Config
from pathlib import Path


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot.

    Returns:
        MagicMock: A mock bot instance with add_cog and wait_until_ready
            configured as AsyncMock.
    """
    bot = MagicMock(spec=commands.Bot)
    bot.add_cog = AsyncMock()
    bot.wait_until_ready = AsyncMock()
    return bot


@pytest.fixture
def mock_giveaway_service():
    """Create a mock giveaway service.

    Returns:
        AsyncMock: A mock giveaway service instance.
    """
    return AsyncMock()


@pytest.fixture
def mock_winner_service():
    """Create a mock winner service.

    Returns:
        AsyncMock: A mock winner service instance.
    """
    return AsyncMock()


@pytest.fixture
def mock_message_service():
    """Create a mock message service.

    Returns:
        AsyncMock: A mock message service instance.
    """
    return AsyncMock()


@pytest.fixture
def mock_config():
    """Create a mock config.

    Returns:
        Config: A test configuration instance with default test values.
    """
    return Config(
        token="test-token",
        database_path=Path("data/test.db"),
        log_level="INFO",
        giveaway_check_interval=30,
    )


@pytest.fixture
def tasks_cog(mock_bot, mock_giveaway_service, mock_winner_service, mock_message_service, mock_config):
    """Create a TasksCog for testing.

    Args:
        mock_bot: Mock Discord bot fixture.
        mock_giveaway_service: Mock giveaway service fixture.
        mock_winner_service: Mock winner service fixture.
        mock_message_service: Mock message service fixture.
        mock_config: Mock config fixture.

    Returns:
        TasksCog: A TasksCog instance with cancelled background task.
    """
    cog = TasksCog(
        mock_bot,
        mock_giveaway_service,
        mock_winner_service,
        mock_message_service,
        mock_config,
    )
    # Stop the task from actually running
    cog.check_giveaways.cancel()
    return cog


class TestTasksCogInit:
    """Tests for TasksCog initialization."""

    def test_cog_initialization(self, tasks_cog, mock_config):
        """Test cog is initialized correctly.

        Args:
            tasks_cog: TasksCog fixture.
            mock_config: Mock config fixture.
        """
        assert tasks_cog.bot is not None
        assert tasks_cog.giveaway_service is not None
        assert tasks_cog.winner_service is not None
        assert tasks_cog.message_service is not None


class TestCogLoadUnload:
    """Tests for cog load/unload."""

    @pytest.mark.asyncio
    async def test_cog_load_starts_task(self, tasks_cog):
        """Test cog_load starts the background task.

        Args:
            tasks_cog: TasksCog fixture.
        """
        with patch.object(tasks_cog.check_giveaways, 'start') as mock_start:
            await tasks_cog.cog_load()
            mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_cog_unload_stops_task(self, tasks_cog):
        """Test cog_unload stops the background task.

        Args:
            tasks_cog: TasksCog fixture.
        """
        with patch.object(tasks_cog.check_giveaways, 'cancel') as mock_cancel:
            await tasks_cog.cog_unload()
            mock_cancel.assert_called_once()


class TestCheckScheduledGiveaways:
    """Tests for _check_scheduled_giveaways method."""

    @pytest.mark.asyncio
    async def test_no_scheduled_giveaways(self, tasks_cog, mock_giveaway_service):
        """Test when there are no scheduled giveaways.

        Args:
            tasks_cog: TasksCog fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        mock_giveaway_service.get_giveaways_to_start.return_value = []

        await tasks_cog._check_scheduled_giveaways()

        mock_giveaway_service.get_giveaways_to_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_scheduled_giveaway(self, tasks_cog, mock_bot, mock_giveaway_service):
        """Test starting a scheduled giveaway.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        mock_giveaway_service.get_giveaways_to_start.return_value = [giveaway]
        mock_giveaway_service.start_scheduled_giveaway = AsyncMock()
        mock_giveaway_service.set_message_id = AsyncMock()

        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.get_role.return_value = None
        message = MagicMock()
        message.id = 555555555
        channel.send.return_value = message
        mock_bot.get_channel.return_value = channel

        host = MagicMock()
        host.display_name = "Host"
        mock_bot.fetch_user = AsyncMock(return_value=host)

        await tasks_cog._check_scheduled_giveaways()

        mock_giveaway_service.start_scheduled_giveaway.assert_called_once()
        channel.send.assert_called()

    @pytest.mark.asyncio
    async def test_start_scheduled_invalid_channel(self, tasks_cog, mock_bot, mock_giveaway_service):
        """Test starting when channel is invalid.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        mock_giveaway_service.get_giveaways_to_start.return_value = [giveaway]
        mock_giveaway_service.start_scheduled_giveaway = AsyncMock()
        mock_bot.get_channel.return_value = MagicMock(spec=discord.VoiceChannel)

        await tasks_cog._check_scheduled_giveaways()

        mock_giveaway_service.start_scheduled_giveaway.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_scheduled_with_existing_message(self, tasks_cog, mock_bot, mock_giveaway_service):
        """Test starting a scheduled giveaway with existing message.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            message_id=555555555,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        mock_giveaway_service.get_giveaways_to_start.return_value = [giveaway]
        mock_giveaway_service.start_scheduled_giveaway = AsyncMock()

        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.get_role.return_value = None
        message = AsyncMock()
        channel.fetch_message.return_value = message
        mock_bot.get_channel.return_value = channel

        host = MagicMock()
        host.display_name = "Host"
        mock_bot.fetch_user = AsyncMock(return_value=host)

        await tasks_cog._check_scheduled_giveaways()

        message.edit.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_scheduled_message_deleted(self, tasks_cog, mock_bot, mock_giveaway_service):
        """Test starting when original message was deleted.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            message_id=555555555,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        mock_giveaway_service.get_giveaways_to_start.return_value = [giveaway]
        mock_giveaway_service.start_scheduled_giveaway = AsyncMock()
        mock_giveaway_service.set_message_id = AsyncMock()

        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.get_role.return_value = None
        channel.fetch_message.side_effect = discord.NotFound(MagicMock(), "Not found")
        new_message = MagicMock()
        new_message.id = 666666666
        channel.send.return_value = new_message
        mock_bot.get_channel.return_value = channel

        host = MagicMock()
        host.display_name = "Host"
        mock_bot.fetch_user = AsyncMock(return_value=host)

        await tasks_cog._check_scheduled_giveaways()

        mock_giveaway_service.set_message_id.assert_called()

    @pytest.mark.asyncio
    async def test_start_scheduled_with_role(self, tasks_cog, mock_bot, mock_giveaway_service):
        """Test starting a scheduled giveaway with required role.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) - timedelta(minutes=1),
            required_role_id=444444444,
        )
        mock_giveaway_service.get_giveaways_to_start.return_value = [giveaway]
        mock_giveaway_service.start_scheduled_giveaway = AsyncMock()
        mock_giveaway_service.set_message_id = AsyncMock()

        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        role = MagicMock()
        role.name = "VIP"
        channel.guild.get_role.return_value = role
        message = MagicMock()
        message.id = 555555555
        channel.send.return_value = message
        mock_bot.get_channel.return_value = channel

        host = MagicMock()
        host.display_name = "Host"
        mock_bot.fetch_user = AsyncMock(return_value=host)

        await tasks_cog._check_scheduled_giveaways()

        channel.send.assert_called()

    @pytest.mark.asyncio
    async def test_start_scheduled_host_not_found(self, tasks_cog, mock_bot, mock_giveaway_service):
        """Test starting when host user is not found.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            scheduled_start=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        mock_giveaway_service.get_giveaways_to_start.return_value = [giveaway]
        mock_giveaway_service.start_scheduled_giveaway = AsyncMock()
        mock_giveaway_service.set_message_id = AsyncMock()

        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.get_role.return_value = None
        message = MagicMock()
        message.id = 555555555
        channel.send.return_value = message
        mock_bot.get_channel.return_value = channel

        mock_bot.fetch_user = AsyncMock(
            side_effect=discord.NotFound(MagicMock(), "Not found")
        )

        await tasks_cog._check_scheduled_giveaways()

        # Should use "Unknown" as host name
        channel.send.assert_called()


class TestCheckEndingGiveaways:
    """Tests for _check_ending_giveaways method."""

    @pytest.mark.asyncio
    async def test_no_ending_giveaways(self, tasks_cog, mock_giveaway_service):
        """Test when there are no giveaways to end.

        Args:
            tasks_cog: TasksCog fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        mock_giveaway_service.get_giveaways_to_end.return_value = []

        await tasks_cog._check_ending_giveaways()

        mock_giveaway_service.get_giveaways_to_end.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_giveaway(self, tasks_cog, mock_bot, mock_giveaway_service, mock_winner_service, mock_message_service):
        """Test ending a giveaway.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
            mock_winner_service: Mock winner service fixture.
            mock_message_service: Mock message service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            created_by=111111111,
            entries=[111111111, 222222222],
        )
        mock_giveaway_service.get_giveaways_to_end.return_value = [giveaway]
        mock_giveaway_service.end_giveaway = AsyncMock(return_value=giveaway)
        mock_winner_service.select_winners = AsyncMock(return_value=[111111111])

        channel = AsyncMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.guild.members = [MagicMock(id=111111111), MagicMock(id=222222222)]
        mock_bot.get_channel.return_value = channel

        await tasks_cog._check_ending_giveaways()

        mock_giveaway_service.end_giveaway.assert_called_once()
        mock_winner_service.select_winners.assert_called_once()
        mock_message_service.update_giveaway_message.assert_called_once()
        mock_message_service.announce_winners.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_giveaway_invalid_channel(self, tasks_cog, mock_bot, mock_giveaway_service):
        """Test ending when channel is invalid.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            created_by=111111111,
        )
        mock_giveaway_service.get_giveaways_to_end.return_value = [giveaway]
        mock_giveaway_service.end_giveaway = AsyncMock(return_value=giveaway)
        mock_bot.get_channel.return_value = MagicMock(spec=discord.VoiceChannel)

        await tasks_cog._check_ending_giveaways()

        mock_giveaway_service.end_giveaway.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_giveaway_fails(self, tasks_cog, mock_bot, mock_giveaway_service):
        """Test when ending a giveaway fails.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
            mock_giveaway_service: Mock giveaway service fixture.
        """
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Prize",
            ends_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            created_by=111111111,
        )
        mock_giveaway_service.get_giveaways_to_end.return_value = [giveaway]
        mock_giveaway_service.end_giveaway = AsyncMock(return_value=None)

        await tasks_cog._check_ending_giveaways()

        mock_giveaway_service.end_giveaway.assert_called_once()


class TestCheckGiveaways:
    """Tests for check_giveaways task."""

    @pytest.mark.asyncio
    async def test_check_giveaways_calls_both(self, tasks_cog):
        """Test check_giveaways calls both check methods.

        Args:
            tasks_cog: TasksCog fixture.
        """
        tasks_cog._check_scheduled_giveaways = AsyncMock()
        tasks_cog._check_ending_giveaways = AsyncMock()

        await tasks_cog.check_giveaways()

        tasks_cog._check_scheduled_giveaways.assert_called_once()
        tasks_cog._check_ending_giveaways.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_giveaways_handles_errors(self, tasks_cog):
        """Test check_giveaways handles errors gracefully.

        Args:
            tasks_cog: TasksCog fixture.
        """
        tasks_cog._check_scheduled_giveaways = AsyncMock(
            side_effect=discord.DiscordException("Test error")
        )
        tasks_cog._check_ending_giveaways = AsyncMock()

        # Should not raise
        await tasks_cog.check_giveaways()


class TestBeforeCheckGiveaways:
    """Tests for before_check_giveaways method."""

    @pytest.mark.asyncio
    async def test_before_loop_waits_for_ready(self, tasks_cog, mock_bot):
        """Test before_loop waits for bot to be ready.

        Args:
            tasks_cog: TasksCog fixture.
            mock_bot: Mock bot fixture.
        """
        await tasks_cog.before_check_giveaways()

        mock_bot.wait_until_ready.assert_called_once()


class TestSetup:
    """Tests for setup function."""

    @pytest.mark.asyncio
    async def test_setup_with_all_services(self, mock_bot):
        """Test setup with all services available.

        Args:
            mock_bot: Mock bot fixture.
        """
        mock_bot.giveaway_service = MagicMock()
        mock_bot.winner_service = MagicMock()
        mock_bot.message_service = MagicMock()
        mock_bot.config = Config(
            token="test",
            database_path=Path("data/test.db"),
            log_level="INFO",
        )

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_missing_services(self, mock_bot):
        """Test setup with missing services.

        Args:
            mock_bot: Mock bot fixture.
        """
        # No services attached

        await setup(mock_bot)

        mock_bot.add_cog.assert_not_called()
