"""Admin cog for giveaway management commands."""

import logging

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from src.models.giveaway import Giveaway
from src.services.giveaway_service import GiveawayService
from src.services.winner_service import WinnerService
from src.services.storage_service import StorageService
from src.services.message_service import GiveawayMessageService
from src.utils.permissions import check_giveaway_admin
from src.utils.validators import (
    validate_winner_count,
    validate_prize,
    validate_duration,
)
from src.ui.embeds import (
    create_giveaway_embed,
    create_cancelled_embed,
    create_list_embed,
)
from src.ui.buttons import GiveawayEntryView, EndedGiveawayView

logger = logging.getLogger(__name__)


class AdminCog(commands.Cog):
    """Cog for giveaway administration commands."""

    def __init__(
        self,
        bot: commands.Bot,
        giveaway_service: GiveawayService,
        winner_service: WinnerService,
        storage: StorageService,
        message_service: GiveawayMessageService,
    ):
        self.bot = bot
        self.giveaway_service = giveaway_service
        self.winner_service = winner_service
        self.storage = storage
        self.message_service = message_service

    async def _check_admin(self, interaction: discord.Interaction) -> bool:
        """Check if user has admin permissions."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return False

        member = interaction.user
        if not isinstance(member, discord.Member):
            return False

        guild_config = await self.storage.get_guild_config(interaction.guild.id)
        user_role_ids = [role.id for role in member.roles]
        has_admin = member.guild_permissions.administrator

        if not check_giveaway_admin(has_admin, user_role_ids, guild_config):
            await interaction.response.send_message(
                "❌ You don't have permission to manage giveaways.",
                ephemeral=True,
            )
            return False

        return True

    giveaway_group = app_commands.Group(
        name="giveaway",
        description="Giveaway management commands",
    )

    @giveaway_group.command(name="create", description="Create a new giveaway")
    @app_commands.describe(
        prize="The prize for the giveaway",
        duration="Duration (e.g., 1h, 30m, 1d, 1w)",
        winners="Number of winners (default: 1)",
        required_role="Role required to enter (optional)",
        channel="Channel to post in (default: current channel)",
    )
    async def create_giveaway(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        winners: int = 1,
        required_role: Optional[discord.Role] = None,
        channel: Optional[discord.TextChannel] = None,
    ) -> None:
        """Create a new giveaway."""
        if not await self._check_admin(interaction):
            return

        # Validate inputs
        valid, error = validate_prize(prize)
        if not valid:
            await interaction.response.send_message(f"❌ {error}", ephemeral=True)
            return

        valid, error = validate_winner_count(winners)
        if not valid:
            await interaction.response.send_message(f"❌ {error}", ephemeral=True)
            return

        duration_seconds = self.giveaway_service.parse_duration(duration)
        if duration_seconds is None:
            await interaction.response.send_message(
                "❌ Invalid duration format. Examples: 1h, 30m, 1d, 1w",
                ephemeral=True,
            )
            return

        valid, error = validate_duration(duration_seconds)
        if not valid:
            await interaction.response.send_message(f"❌ {error}", ephemeral=True)
            return

        # Use current channel if not specified
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Invalid channel.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Create the giveaway
        giveaway = await self.giveaway_service.create_giveaway(
            guild_id=interaction.guild.id,  # type: ignore
            channel_id=target_channel.id,
            prize=prize,
            duration_seconds=duration_seconds,
            created_by=interaction.user.id,
            winner_count=winners,
            required_role_id=required_role.id if required_role else None,
        )

        # Create and send the giveaway message
        embed = create_giveaway_embed(
            giveaway,
            host_name=interaction.user.display_name,
            role_name=required_role.name if required_role else None,
        )
        view = GiveawayEntryView(giveaway.id)  # type: ignore

        message = await target_channel.send(embed=embed, view=view)

        # Update giveaway with message ID
        await self.giveaway_service.set_message_id(giveaway, message.id)

        await interaction.followup.send(
            f"✅ Giveaway created! Check {target_channel.mention}",
            ephemeral=True,
        )

    @giveaway_group.command(name="end", description="End a giveaway early")
    @app_commands.describe(giveaway_id="The ID of the giveaway to end")
    async def end_giveaway(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
    ) -> None:
        """End a giveaway and select winners."""
        if not await self._check_admin(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        giveaway = await self.giveaway_service.get_giveaway(giveaway_id)
        if not giveaway:
            await interaction.followup.send("❌ Giveaway not found.", ephemeral=True)
            return

        if giveaway.guild_id != interaction.guild.id:  # type: ignore
            await interaction.followup.send("❌ Giveaway not found.", ephemeral=True)
            return

        if giveaway.is_ended:
            await interaction.followup.send(
                "❌ This giveaway has already ended.",
                ephemeral=True,
            )
            return

        # End the giveaway
        giveaway = await self.giveaway_service.end_giveaway(giveaway_id)
        if not giveaway:
            await interaction.followup.send(
                "❌ Failed to end giveaway.", ephemeral=True
            )
            return

        # Get valid members for winner selection
        guild = interaction.guild
        valid_user_ids = [member.id for member in guild.members] if guild else None

        # Select winners
        winners = await self.winner_service.select_winners(giveaway, valid_user_ids)

        # Update the original message
        await self.message_service.update_giveaway_message(giveaway, winners)

        # Announce winners
        channel = self.bot.get_channel(giveaway.channel_id)
        if isinstance(channel, discord.TextChannel):
            await self.message_service.announce_winners(giveaway, winners, channel)

        winner_text = (
            ", ".join(f"<@{uid}>" for uid in winners) if winners else "No winners"
        )
        await interaction.followup.send(
            f"✅ Giveaway ended! Winners: {winner_text}",
            ephemeral=True,
        )

    @giveaway_group.command(name="cancel", description="Cancel a giveaway")
    @app_commands.describe(giveaway_id="The ID of the giveaway to cancel")
    async def cancel_giveaway(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
    ) -> None:
        """Cancel a giveaway without selecting winners."""
        if not await self._check_admin(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        giveaway = await self.giveaway_service.get_giveaway(giveaway_id)
        if not giveaway:
            await interaction.followup.send("❌ Giveaway not found.", ephemeral=True)
            return

        if giveaway.guild_id != interaction.guild.id:  # type: ignore
            await interaction.followup.send("❌ Giveaway not found.", ephemeral=True)
            return

        success, message = await self.giveaway_service.cancel_giveaway(giveaway_id)
        if not success:
            await interaction.followup.send(f"❌ {message}", ephemeral=True)
            return

        # Update the original message
        giveaway = await self.giveaway_service.get_giveaway(giveaway_id)
        if giveaway and giveaway.message_id:
            try:
                channel = self.bot.get_channel(giveaway.channel_id)
                if isinstance(channel, discord.TextChannel):
                    msg = await channel.fetch_message(giveaway.message_id)
                    embed = create_cancelled_embed(
                        giveaway,
                        host_name=interaction.user.display_name,
                    )
                    await msg.edit(embed=embed, view=EndedGiveawayView())
            except discord.NotFound:
                logger.warning(f"Message {giveaway.message_id} not found - may have been deleted")

        await interaction.followup.send("✅ Giveaway cancelled.", ephemeral=True)

    @giveaway_group.command(name="reroll", description="Reroll winners for a giveaway")
    @app_commands.describe(
        giveaway_id="The ID of the giveaway to reroll",
        count="Number of new winners to select (default: 1)",
    )
    async def reroll_giveaway(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
        count: int = 1,
    ) -> None:
        """Reroll winners for an ended giveaway."""
        if not await self._check_admin(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        giveaway = await self.giveaway_service.get_giveaway(giveaway_id)
        if not giveaway:
            await interaction.followup.send("❌ Giveaway not found.", ephemeral=True)
            return

        if giveaway.guild_id != interaction.guild.id:  # type: ignore
            await interaction.followup.send("❌ Giveaway not found.", ephemeral=True)
            return

        if not giveaway.ended:
            await interaction.followup.send(
                "❌ Giveaway hasn't ended yet.",
                ephemeral=True,
            )
            return

        # Get valid members
        guild = interaction.guild
        valid_user_ids = [member.id for member in guild.members] if guild else None

        # Reroll winners
        new_winners, message = await self.winner_service.reroll_winners(
            giveaway,
            count=count,
            valid_user_ids=valid_user_ids,
        )

        if not new_winners:
            await interaction.followup.send(f"❌ {message}", ephemeral=True)
            return

        # Announce new winners
        channel = self.bot.get_channel(giveaway.channel_id)
        if isinstance(channel, discord.TextChannel):
            winner_mentions = ", ".join(f"<@{uid}>" for uid in new_winners)
            await channel.send(
                f"🎉 **Reroll!** New winner(s) for **{giveaway.prize}**: {winner_mentions}"
            )

        await interaction.followup.send(f"✅ {message}", ephemeral=True)

    @giveaway_group.command(name="list", description="List all active giveaways")
    async def list_giveaways(self, interaction: discord.Interaction) -> None:
        """List all active giveaways in the server."""
        if not await self._check_admin(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        giveaways = await self.giveaway_service.get_active_giveaways(
            interaction.guild.id  # type: ignore
        )

        embed = create_list_embed(
            giveaways,
            interaction.guild.name if interaction.guild else "Unknown",
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @giveaway_group.command(name="config", description="Configure giveaway admin roles")
    @app_commands.describe(
        action="Add or remove an admin role",
        role="The role to add or remove",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add admin role", value="add"),
            app_commands.Choice(name="Remove admin role", value="remove"),
            app_commands.Choice(name="List admin roles", value="list"),
        ]
    )
    async def config_giveaway(
        self,
        interaction: discord.Interaction,
        action: str,
        role: Optional[discord.Role] = None,
    ) -> None:
        """Configure giveaway admin roles."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        # Only Discord admins can configure
        member = interaction.user
        if not isinstance(member, discord.Member):
            return

        if not member.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Only server administrators can configure giveaway settings.",
                ephemeral=True,
            )
            return

        guild_config = await self.storage.get_guild_config(interaction.guild.id)

        if action == "list":
            if not guild_config.admin_role_ids:
                await interaction.response.send_message(
                    "No custom admin roles configured. Only Discord administrators can manage giveaways.",
                    ephemeral=True,
                )
            else:
                roles = [f"<@&{rid}>" for rid in guild_config.admin_role_ids]
                await interaction.response.send_message(
                    "**Giveaway Admin Roles:**\n" + "\n".join(roles),
                    ephemeral=True,
                )
            return

        if not role:
            await interaction.response.send_message(
                "❌ Please specify a role.",
                ephemeral=True,
            )
            return

        if action == "add":
            if guild_config.add_admin_role(role.id):
                await self.storage.save_guild_config(guild_config)
                await interaction.response.send_message(
                    f"✅ Added {role.mention} as a giveaway admin role.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"❌ {role.mention} is already a giveaway admin role.",
                    ephemeral=True,
                )
        elif action == "remove":
            if guild_config.remove_admin_role(role.id):
                await self.storage.save_guild_config(guild_config)
                await interaction.response.send_message(
                    f"✅ Removed {role.mention} from giveaway admin roles.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"❌ {role.mention} is not a giveaway admin role.",
                    ephemeral=True,
                )


async def setup(bot: commands.Bot) -> None:
    """Setup function for loading the cog."""
    # This will be called by the bot's load_extension
    # Services should be attached to the bot instance
    storage = getattr(bot, "storage", None)
    giveaway_service = getattr(bot, "giveaway_service", None)
    winner_service = getattr(bot, "winner_service", None)
    message_service = getattr(bot, "message_service", None)

    if storage and giveaway_service and winner_service and message_service:
        await bot.add_cog(
            AdminCog(
                bot, giveaway_service, winner_service, storage, message_service
            )
        )
