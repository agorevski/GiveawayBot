"""Tests for the GiveawayCog."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from src.cogs.giveaway import GiveawayCog, setup
from src.models.giveaway import Giveaway


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot.

    Returns:
        MagicMock: A mock bot object with spec of commands.Bot,
            including mocked add_cog and add_view methods.
    """
    bot = MagicMock(spec=commands.Bot)
    bot.add_cog = AsyncMock()
    bot.add_view = MagicMock()
    return bot


@pytest.fixture
def mock_storage():
    """Create a mock storage service.

    Returns:
        AsyncMock: A mock storage service object for testing.
    """
    return AsyncMock()


@pytest.fixture
def mock_giveaway_service():
    """Create a mock giveaway service.

    Returns:
        AsyncMock: A mock giveaway service object for testing.
    """
    return AsyncMock()


@pytest.fixture
def giveaway_cog(mock_bot, mock_giveaway_service, mock_storage):
    """Create a GiveawayCog for testing.

    Args:
        mock_bot: The mock Discord bot fixture.
        mock_giveaway_service: The mock giveaway service fixture.
        mock_storage: The mock storage service fixture.

    Returns:
        GiveawayCog: A configured GiveawayCog instance for testing.
    """
    return GiveawayCog(mock_bot, mock_giveaway_service, mock_storage)


def create_mock_interaction(guild_id=123456789, user_id=111111111):
    """Create a mock Discord interaction.

    Args:
        guild_id: The ID for the mock guild. Defaults to 123456789.
        user_id: The ID for the mock user. Defaults to 111111111.

    Returns:
        MagicMock: A mock Discord interaction with configured guild and user.
    """
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = AsyncMock()

    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.name = "Test Guild"
    interaction.guild = guild

    user = MagicMock(spec=discord.Member)
    user.id = user_id
    user.display_name = "TestUser"
    interaction.user = user

    return interaction


class TestListGiveaways:
    """Tests for list_giveaways command."""

    @pytest.mark.asyncio
    async def test_list_giveaways_no_guild(self, giveaway_cog):
        """Test list giveaways with no guild.

        Args:
            giveaway_cog: The GiveawayCog fixture.

        Verifies that an appropriate error message is sent when the
        command is used outside of a server context.
        """
        interaction = create_mock_interaction()
        interaction.guild = None

        await giveaway_cog.list_giveaways.callback(giveaway_cog, interaction)

        interaction.response.send_message.assert_called_once()
        assert "only be used in a server" in str(
            interaction.response.send_message.call_args
        )

    @pytest.mark.asyncio
    async def test_list_giveaways_success(self, giveaway_cog, mock_giveaway_service):
        """Test successful list giveaways.

        Args:
            giveaway_cog: The GiveawayCog fixture.
            mock_giveaway_service: The mock giveaway service fixture.

        Verifies that active giveaways are fetched and a response is sent.
        """
        interaction = create_mock_interaction()
        mock_giveaway_service.get_active_giveaways = AsyncMock(
            return_value=[
                Giveaway(
                    id=1,
                    guild_id=123456789,
                    channel_id=987654321,
                    prize="Prize 1",
                    ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
                    created_by=111111111,
                ),
            ]
        )

        await giveaway_cog.list_giveaways.callback(giveaway_cog, interaction)

        mock_giveaway_service.get_active_giveaways.assert_called_once_with(123456789)
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_giveaways_empty(self, giveaway_cog, mock_giveaway_service):
        """Test list giveaways when none exist.

        Args:
            giveaway_cog: The GiveawayCog fixture.
            mock_giveaway_service: The mock giveaway service fixture.

        Verifies that an appropriate response is sent when no giveaways exist.
        """
        interaction = create_mock_interaction()
        mock_giveaway_service.get_active_giveaways = AsyncMock(return_value=[])

        await giveaway_cog.list_giveaways.callback(giveaway_cog, interaction)

        interaction.response.send_message.assert_called_once()


class TestMyEntries:
    """Tests for my_entries command."""

    @pytest.mark.asyncio
    async def test_my_entries_no_guild(self, giveaway_cog):
        """Test my entries with no guild.

        Args:
            giveaway_cog: The GiveawayCog fixture.

        Verifies that an appropriate error message is sent when the
        command is used outside of a server context.
        """
        interaction = create_mock_interaction()
        interaction.guild = None

        await giveaway_cog.my_entries.callback(giveaway_cog, interaction)

        interaction.response.send_message.assert_called_once()
        assert "only be used in a server" in str(
            interaction.response.send_message.call_args
        )

    @pytest.mark.asyncio
    async def test_my_entries_success(self, giveaway_cog, mock_giveaway_service):
        """Test successful my entries.

        Args:
            giveaway_cog: The GiveawayCog fixture.
            mock_giveaway_service: The mock giveaway service fixture.

        Verifies that user entries are fetched and a response is sent.
        """
        interaction = create_mock_interaction()
        mock_giveaway_service.get_user_entries = AsyncMock(
            return_value=[
                Giveaway(
                    id=1,
                    guild_id=123456789,
                    channel_id=987654321,
                    prize="Prize 1",
                    ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
                    created_by=111111111,
                ),
            ]
        )

        await giveaway_cog.my_entries.callback(giveaway_cog, interaction)

        mock_giveaway_service.get_user_entries.assert_called_once_with(
            123456789, 111111111
        )
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_my_entries_empty(self, giveaway_cog, mock_giveaway_service):
        """Test my entries when user has no entries.

        Args:
            giveaway_cog: The GiveawayCog fixture.
            mock_giveaway_service: The mock giveaway service fixture.

        Verifies that an appropriate response is sent when user has no entries.
        """
        interaction = create_mock_interaction()
        mock_giveaway_service.get_user_entries = AsyncMock(return_value=[])

        await giveaway_cog.my_entries.callback(giveaway_cog, interaction)

        interaction.response.send_message.assert_called_once()


class TestOnReady:
    """Tests for on_ready listener."""

    @pytest.mark.asyncio
    async def test_on_ready_registers_views(self, giveaway_cog, mock_bot, mock_giveaway_service):
        """Test on_ready registers persistent views.

        Args:
            giveaway_cog: The GiveawayCog fixture.
            mock_bot: The mock Discord bot fixture.
            mock_giveaway_service: The mock giveaway service fixture.

        Verifies that persistent views are registered for each active giveaway.
        """
        mock_giveaway_service.get_active_giveaways = AsyncMock(
            return_value=[
                Giveaway(
                    id=1,
                    guild_id=123456789,
                    channel_id=987654321,
                    prize="Prize",
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
        )

        await giveaway_cog.on_ready()

        assert mock_bot.add_view.call_count == 2

    @pytest.mark.asyncio
    async def test_on_ready_skips_inactive_giveaways(self, giveaway_cog, mock_bot, mock_giveaway_service):
        """Test on_ready skips inactive giveaways.

        Args:
            giveaway_cog: The GiveawayCog fixture.
            mock_bot: The mock Discord bot fixture.
            mock_giveaway_service: The mock giveaway service fixture.

        Verifies that ended giveaways do not have views registered.
        """
        mock_giveaway_service.get_active_giveaways = AsyncMock(
            return_value=[
                Giveaway(
                    id=1,
                    guild_id=123456789,
                    channel_id=987654321,
                    prize="Prize",
                    ends_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Ended
                    created_by=111111111,
                    ended=True,
                ),
            ]
        )

        await giveaway_cog.on_ready()

        mock_bot.add_view.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_ready_skips_none_id(self, giveaway_cog, mock_bot, mock_giveaway_service):
        """Test on_ready skips giveaways with None ID.

        Args:
            giveaway_cog: The GiveawayCog fixture.
            mock_bot: The mock Discord bot fixture.
            mock_giveaway_service: The mock giveaway service fixture.

        Verifies that giveaways without an ID do not have views registered.
        """
        mock_giveaway_service.get_active_giveaways = AsyncMock(
            return_value=[
                Giveaway(
                    id=None,  # No ID
                    guild_id=123456789,
                    channel_id=987654321,
                    prize="Prize",
                    ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
                    created_by=111111111,
                ),
            ]
        )

        await giveaway_cog.on_ready()

        mock_bot.add_view.assert_not_called()


class TestSetup:
    """Tests for setup function."""

    @pytest.mark.asyncio
    async def test_setup_with_services(self, mock_bot):
        """Test setup with services available.

        Args:
            mock_bot: The mock Discord bot fixture.

        Verifies that the cog is added when all required services are present.
        """
        mock_bot.storage = MagicMock()
        mock_bot.giveaway_service = MagicMock()

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_missing_storage(self, mock_bot):
        """Test setup with missing storage.

        Args:
            mock_bot: The mock Discord bot fixture.

        Verifies that the cog is not added when storage service is missing.
        """
        mock_bot.giveaway_service = MagicMock()
        # storage not set

        await setup(mock_bot)

        mock_bot.add_cog.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_missing_giveaway_service(self, mock_bot):
        """Test setup with missing giveaway service.

        Args:
            mock_bot: The mock Discord bot fixture.

        Verifies that the cog is not added when giveaway service is missing.
        """
        mock_bot.storage = MagicMock()
        # giveaway_service not set

        await setup(mock_bot)

        mock_bot.add_cog.assert_not_called()
