"""Background tasks cog for automated giveaway management."""

import discord
from discord.ext import commands, tasks
import logging

from src.services.giveaway_service import GiveawayService
from src.services.winner_service import WinnerService
from src.ui.embeds import create_ended_embed, create_giveaway_embed
from src.ui.buttons import GiveawayEntryView, EndedGiveawayView

logger = logging.getLogger(__name__)


class TasksCog(commands.Cog):
    """Cog for background tasks like auto-ending giveaways."""

    def __init__(
        self,
        bot: commands.Bot,
        giveaway_service: GiveawayService,
        winner_service: WinnerService,
    ):
        self.bot = bot
        self.giveaway_service = giveaway_service
        self.winner_service = winner_service

    async def cog_load(self) -> None:
        """Start background tasks when cog is loaded."""
        self.check_giveaways.start()

    async def cog_unload(self) -> None:
        """Stop background tasks when cog is unloaded."""
        self.check_giveaways.cancel()

    @tasks.loop(seconds=30)
    async def check_giveaways(self) -> None:
        """Check for giveaways that need to start or end."""
        try:
            # Check for scheduled giveaways that should start
            await self._check_scheduled_giveaways()

            # Check for giveaways that should end
            await self._check_ending_giveaways()
        except Exception as e:
            logger.error(f"Error in check_giveaways task: {e}")

    @check_giveaways.before_loop
    async def before_check_giveaways(self) -> None:
        """Wait for bot to be ready before starting task."""
        await self.bot.wait_until_ready()

    async def _check_scheduled_giveaways(self) -> None:
        """Check for and start scheduled giveaways."""
        giveaways_to_start = await self.giveaway_service.get_giveaways_to_start()

        for giveaway in giveaways_to_start:
            try:
                # Clear scheduled_start to mark as started
                giveaway.scheduled_start = None
                await self.giveaway_service.storage.update_giveaway(giveaway)

                # Get channel and send/update message
                channel = self.bot.get_channel(giveaway.channel_id)
                if not isinstance(channel, discord.TextChannel):
                    continue

                # Get host name
                try:
                    host = await self.bot.fetch_user(giveaway.created_by)
                    host_name = host.display_name
                except discord.NotFound:
                    host_name = "Unknown"

                # Get role name if required
                role_name = None
                if giveaway.required_role_id:
                    guild = channel.guild
                    role = guild.get_role(giveaway.required_role_id)
                    if role:
                        role_name = role.name

                embed = create_giveaway_embed(giveaway, host_name, role_name)
                view = GiveawayEntryView(giveaway.id)  # type: ignore

                if giveaway.message_id:
                    # Update existing message
                    try:
                        message = await channel.fetch_message(giveaway.message_id)
                        await message.edit(embed=embed, view=view)
                    except discord.NotFound:
                        # Message was deleted, send new one
                        message = await channel.send(embed=embed, view=view)
                        await self.giveaway_service.set_message_id(
                            giveaway, message.id
                        )
                else:
                    # Send new message
                    message = await channel.send(embed=embed, view=view)
                    await self.giveaway_service.set_message_id(giveaway, message.id)

                # Announce start
                await channel.send(
                    f"🎉 A giveaway for **{giveaway.prize}** has started! "
                    "Click the button above to enter!"
                )

                logger.info(f"Started scheduled giveaway {giveaway.id}")
            except Exception as e:
                logger.error(f"Error starting giveaway {giveaway.id}: {e}")

    async def _check_ending_giveaways(self) -> None:
        """Check for and end giveaways past their end time."""
        giveaways_to_end = await self.giveaway_service.get_giveaways_to_end()

        for giveaway in giveaways_to_end:
            try:
                # End the giveaway
                ended_giveaway = await self.giveaway_service.end_giveaway(
                    giveaway.id  # type: ignore
                )
                if not ended_giveaway:
                    continue

                # Get channel
                channel = self.bot.get_channel(giveaway.channel_id)
                if not isinstance(channel, discord.TextChannel):
                    continue

                # Get valid members
                guild = channel.guild
                valid_user_ids = [member.id for member in guild.members]

                # Select winners
                winners = await self.winner_service.select_winners(
                    ended_giveaway, valid_user_ids
                )

                # Update the giveaway message
                await self._update_ended_message(ended_giveaway, winners, channel)

                # Announce winners
                await self._announce_winners(ended_giveaway, winners, channel)

                logger.info(
                    f"Ended giveaway {giveaway.id} with {len(winners)} winner(s)"
                )
            except Exception as e:
                logger.error(f"Error ending giveaway {giveaway.id}: {e}")

    async def _update_ended_message(
        self,
        giveaway,
        winners: list,
        channel: discord.TextChannel,
    ) -> None:
        """Update the giveaway message to show it has ended."""
        if not giveaway.message_id:
            return

        try:
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
            pass

    async def _announce_winners(
        self,
        giveaway,
        winners: list,
        channel: discord.TextChannel,
    ) -> None:
        """Announce winners and DM them."""
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


async def setup(bot: commands.Bot) -> None:
    """Setup function for loading the cog."""
    giveaway_service = getattr(bot, "giveaway_service", None)
    winner_service = getattr(bot, "winner_service", None)

    if giveaway_service and winner_service:
        await bot.add_cog(TasksCog(bot, giveaway_service, winner_service))
