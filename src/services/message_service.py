"""Shared message service for giveaway message updates and announcements."""

import logging
from typing import List

import discord

from src.models.giveaway import Giveaway
from src.services.winner_service import WinnerService
from src.ui.embeds import create_ended_embed
from src.ui.buttons import EndedGiveawayView

logger = logging.getLogger(__name__)


class GiveawayMessageService:
    """Handles giveaway message updates and winner announcements."""

    def __init__(self, bot: discord.Client, winner_service: WinnerService):
        """Initialize the message service.

        Args:
            bot: Discord bot instance.
            winner_service: Winner service for DM formatting.
        """
        self.bot = bot
        self.winner_service = winner_service

    async def update_giveaway_message(
        self,
        giveaway: Giveaway,
        winners: List[int],
    ) -> None:
        """Update the giveaway message with ended status.

        Args:
            giveaway: The ended giveaway.
            winners: List of winner user IDs.
        """
        if not giveaway.message_id:
            return

        try:
            channel = self.bot.get_channel(giveaway.channel_id)
            if not isinstance(channel, discord.TextChannel):
                return

            message = await channel.fetch_message(giveaway.message_id)

            # Get host name
            try:
                host = await self.bot.fetch_user(giveaway.created_by)
                host_name = host.display_name
            except discord.NotFound:
                host_name = "Unknown"

            embed = create_ended_embed(giveaway, winners, host_name)
            await message.edit(embed=embed, view=EndedGiveawayView())
        except discord.NotFound:
            logger.warning(
                f"Message {giveaway.message_id} not found - may have been deleted"
            )

    async def announce_winners(
        self,
        giveaway: Giveaway,
        winners: List[int],
        channel: discord.TextChannel,
    ) -> None:
        """Announce winners and DM them.

        Args:
            giveaway: The ended giveaway.
            winners: List of winner user IDs.
            channel: The channel to announce in.
        """
        if not winners:
            await channel.send(
                f"🎉 The giveaway for **{giveaway.prize}** has ended!\n"
                "No valid entries - no winner could be selected."
            )
            return

        # Public announcement
        winner_mentions = ", ".join(f"<@{uid}>" for uid in winners)
        await channel.send(
            f"🎉 Congratulations {winner_mentions}! "
            f"You won the giveaway for **{giveaway.prize}**!"
        )

        # DM winners
        guild = channel.guild
        for winner_id in winners:
            try:
                user = await self.bot.fetch_user(winner_id)
                dm_message = self.winner_service.format_dm_message(
                    giveaway.prize,
                    guild.name,
                )
                await user.send(dm_message)
            except (discord.Forbidden, discord.NotFound):
                # User has DMs disabled or doesn't exist
                pass
