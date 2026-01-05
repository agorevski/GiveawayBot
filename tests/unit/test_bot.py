"""Tests for the GiveawayBot main module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import discord
from discord.ext import commands

from src.bot import GiveawayBot, main
from src.config import Config


@pytest.fixture
def mock_config():
    """Create a mock config for testing.

    Returns:
        Config: A Config instance with test values for token,
            database_path, and log_level.
    """
    return Config(
        token="test-token",
        database_path=Path("data/test.db"),
        log_level="INFO",
    )


class TestGiveawayBot:
    """Tests for GiveawayBot class."""

    def test_bot_initialization(self, mock_config):
        """Test bot is initialized correctly.

        Args:
            mock_config: Pytest fixture providing a mock Config instance.
        """
        bot = GiveawayBot(mock_config)

        assert bot.config == mock_config
        assert bot.storage is not None
        assert bot.giveaway_service is not None
        assert bot.winner_service is not None
        assert bot.command_prefix == "!"

    def test_bot_intents(self, mock_config):
        """Test bot has correct intents.

        Args:
            mock_config: Pytest fixture providing a mock Config instance.
        """
        bot = GiveawayBot(mock_config)

        assert bot.intents.members is True
        assert bot.intents.guilds is True

    @pytest.mark.asyncio
    async def test_setup_hook(self, mock_config):
        """Test setup_hook initializes services and loads cogs.

        Args:
            mock_config: Pytest fixture providing a mock Config instance.
        """
        bot = GiveawayBot(mock_config)
        bot.storage.initialize = AsyncMock()
        bot.load_extension = AsyncMock()
        bot.tree.sync = AsyncMock()

        await bot.setup_hook()

        bot.storage.initialize.assert_called_once()
        assert bot.load_extension.call_count == 3
        bot.tree.sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_ready(self, mock_config):
        """Test on_ready sets presence.

        Args:
            mock_config: Pytest fixture providing a mock Config instance.
        """
        bot = GiveawayBot(mock_config)
        bot._connection = MagicMock()
        bot._connection.user = MagicMock()
        bot._connection.user.id = 123456789
        bot._connection._guilds = {}
        bot.change_presence = AsyncMock()

        await bot.on_ready()

        bot.change_presence.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_guild_join(self, mock_config):
        """Test on_guild_join syncs commands.

        Args:
            mock_config: Pytest fixture providing a mock Config instance.
        """
        bot = GiveawayBot(mock_config)
        bot.tree.sync = AsyncMock()

        guild = MagicMock(spec=discord.Guild)
        guild.id = 123456789
        guild.name = "Test Guild"

        await bot.on_guild_join(guild)

        bot.tree.sync.assert_called_once_with(guild=guild)

    @pytest.mark.asyncio
    async def test_close(self, mock_config):
        """Test close shuts down cleanly.

        Args:
            mock_config: Pytest fixture providing a mock Config instance.
        """
        bot = GiveawayBot(mock_config)
        bot.storage.close = AsyncMock()
        bot._closed = False
        bot._ready = MagicMock()

        # Mock parent close
        with patch.object(commands.Bot, 'close', new_callable=AsyncMock):
            await bot.close()

        bot.storage.close.assert_called_once()


class TestMain:
    """Tests for main function."""

    @pytest.mark.asyncio
    async def test_main_config_error(self):
        """Test main handles config errors.

        Verifies that the main function gracefully handles configuration
        errors without raising exceptions.
        """
        with patch('src.bot.get_config', side_effect=ValueError("Missing token")):
            await main()  # Should not raise

    @pytest.mark.asyncio
    async def test_main_success(self):
        """Test main starts the bot.

        Verifies that the main function correctly initializes and starts
        the bot with the provided configuration.
        """
        mock_config = Config(
            token="test-token",
            database_path=Path("data/test.db"),
            log_level="INFO",
        )

        with patch('src.bot.get_config', return_value=mock_config):
            with patch('src.bot.GiveawayBot') as MockBot:
                mock_bot = MagicMock()
                mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
                mock_bot.__aexit__ = AsyncMock(return_value=None)
                mock_bot.start = AsyncMock()
                MockBot.return_value = mock_bot

                await main()

                mock_bot.start.assert_called_once_with("test-token")
