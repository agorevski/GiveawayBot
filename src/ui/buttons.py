"""Button components for giveaway interactions."""

import discord
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.giveaway_service import GiveawayService


class GiveawayEntryButton(discord.ui.Button):
    """Button for entering a giveaway."""

    def __init__(self, giveaway_id: int):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="🎉 Enter Giveaway",
            custom_id=f"giveaway_enter:{giveaway_id}",
        )
        self.giveaway_id = giveaway_id

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle button click."""
        # Get the giveaway service from the bot
        giveaway_service: Optional["GiveawayService"] = getattr(
            interaction.client, "giveaway_service", None
        )

        if not giveaway_service:
            await interaction.response.send_message(
                "❌ Bot is not properly configured.",
                ephemeral=True,
            )
            return

        # Get user's role IDs
        if isinstance(interaction.user, discord.Member):
            user_role_ids = [role.id for role in interaction.user.roles]
        else:
            user_role_ids = []

        # Attempt to enter the giveaway
        success, message = await giveaway_service.enter_giveaway(
            self.giveaway_id,
            interaction.user.id,
            user_role_ids,
        )

        # Send response
        if success:
            await interaction.response.send_message(
                f"✅ {message}",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ {message}",
                ephemeral=True,
            )


class GiveawayLeaveButton(discord.ui.Button):
    """Button for leaving a giveaway."""

    def __init__(self, giveaway_id: int):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Leave Giveaway",
            custom_id=f"giveaway_leave:{giveaway_id}",
        )
        self.giveaway_id = giveaway_id

    async def callback(self, interaction: discord.Interaction) -> None:
        """Handle button click."""
        giveaway_service: Optional["GiveawayService"] = getattr(
            interaction.client, "giveaway_service", None
        )

        if not giveaway_service:
            await interaction.response.send_message(
                "❌ Bot is not properly configured.",
                ephemeral=True,
            )
            return

        success, message = await giveaway_service.leave_giveaway(
            self.giveaway_id,
            interaction.user.id,
        )

        if success:
            await interaction.response.send_message(
                f"✅ {message}",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ {message}",
                ephemeral=True,
            )


class GiveawayEntryView(discord.ui.View):
    """View containing giveaway entry buttons."""

    def __init__(self, giveaway_id: int, include_leave: bool = False):
        # Set timeout to None for persistent views
        super().__init__(timeout=None)

        self.add_item(GiveawayEntryButton(giveaway_id))
        if include_leave:
            self.add_item(GiveawayLeaveButton(giveaway_id))


class EndedGiveawayView(discord.ui.View):
    """View for ended giveaways (disabled buttons)."""

    def __init__(self):
        super().__init__(timeout=None)

        button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="🎉 Giveaway Ended",
            disabled=True,
        )
        self.add_item(button)
