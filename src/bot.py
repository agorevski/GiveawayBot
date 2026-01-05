"""Main bot entry point for the Giveaway Bot."""

import asyncio
import logging
import discord
from discord.ext import commands

from src.config import get_config, Config
from src.services.storage_service import StorageService
from src.services.giveaway_service import GiveawayService
from src.services.winner_service import WinnerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GiveawayBot(commands.Bot):
    """Custom bot class with giveaway services."""

    def __init__(self, config: Config):
        """Initialize the GiveawayBot with configuration.

        Args:
            config: Configuration object containing bot settings and credentials.
        """
        intents = discord.Intents.default()
        intents.members = True  # Required for winner selection
        intents.guilds = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        self.config = config
        self.storage: StorageService = StorageService(config.database_path)
        self.giveaway_service: GiveawayService = GiveawayService(self.storage)
        self.winner_service: WinnerService = WinnerService(self.storage)

    async def setup_hook(self) -> None:
        """Initialize services and load cogs.

        This method is called automatically by discord.py during bot setup.
        It initializes the database, loads all cogs, and syncs slash commands.
        """
        # Initialize database
        logger.info("Initializing database...")
        await self.storage.initialize()

        # Load cogs
        logger.info("Loading cogs...")
        await self.load_extension("src.cogs.admin")
        await self.load_extension("src.cogs.giveaway")
        await self.load_extension("src.cogs.tasks")

        # Sync commands
        logger.info("Syncing commands...")
        await self.tree.sync()

        logger.info("Bot setup complete!")

    async def on_ready(self) -> None:
        """Handle the bot ready event.

        Called when the bot has successfully connected to Discord and is ready
        to receive events. Sets the bot's presence status.
        """
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")  # type: ignore
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        # Set presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for giveaways 🎁",
        )
        await self.change_presence(activity=activity)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Handle the bot joining a new guild.

        Syncs slash commands to the newly joined guild.

        Args:
            guild: The Discord guild that the bot joined.
        """
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")

        # Sync commands for the new guild
        await self.tree.sync(guild=guild)

    async def close(self) -> None:
        """Clean up resources when the bot is shutting down.

        Closes the storage connection and performs graceful shutdown.
        """
        logger.info("Shutting down...")
        await self.storage.close()
        await super().close()


async def main() -> None:
    """Main entry point for the Giveaway Bot.

    Loads configuration, initializes the bot, and starts the connection
    to Discord. Handles configuration errors gracefully.
    """
    try:
        config = get_config()
        config.ensure_data_directory()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return

    bot = GiveawayBot(config)

    async with bot:
        await bot.start(config.token)


if __name__ == "__main__":
    asyncio.run(main())
