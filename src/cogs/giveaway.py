"""Giveaway cog for user-facing commands."""

import discord
from discord import app_commands
from discord.ext import commands

from src.services.giveaway_service import GiveawayService
from src.services.storage_service import StorageService
from src.ui.embeds import create_list_embed, create_entries_embed
from src.ui.buttons import GiveawayEntryView


class GiveawayCog(commands.Cog):
    """Cog for user-facing giveaway commands."""

    def __init__(
        self,
        bot: commands.Bot,
        giveaway_service: GiveawayService,
        storage: StorageService,
    ):
        self.bot = bot
        self.giveaway_service = giveaway_service
        self.storage = storage

    @app_commands.command(
        name="giveaways",
        description="View all active giveaways in this server",
    )
    async def list_giveaways(self, interaction: discord.Interaction) -> None:
        """List all active giveaways in the server."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        giveaways = await self.giveaway_service.get_active_giveaways(
            interaction.guild.id
        )

        embed = create_list_embed(giveaways, interaction.guild.name)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="myentries",
        description="View your current giveaway entries",
    )
    async def my_entries(self, interaction: discord.Interaction) -> None:
        """Show the user's current giveaway entries."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        entries = await self.giveaway_service.get_user_entries(
            interaction.guild.id,
            interaction.user.id,
        )

        embed = create_entries_embed(entries, interaction.user.display_name)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Re-register persistent views when bot starts."""
        # Get all active giveaways and register their views
        giveaways = await self.giveaway_service.get_active_giveaways()

        for giveaway in giveaways:
            if giveaway.id is not None and giveaway.is_active:
                view = GiveawayEntryView(giveaway.id)
                self.bot.add_view(view)


async def setup(bot: commands.Bot) -> None:
    """Setup function for loading the cog."""
    storage = getattr(bot, "storage", None)
    giveaway_service = getattr(bot, "giveaway_service", None)

    if storage and giveaway_service:
        await bot.add_cog(GiveawayCog(bot, giveaway_service, storage))
