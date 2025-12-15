"""Winner service for selecting and notifying giveaway winners."""

import random
from typing import List, Optional, Tuple

from src.models.giveaway import Giveaway
from src.services.storage_service import StorageService


class WinnerService:
    """Handles winner selection and notification logic."""

    def __init__(self, storage: StorageService):
        """Initialize the winner service.

        Args:
            storage: Storage service for database operations.
        """
        self.storage = storage

    async def select_winners(
        self,
        giveaway: Giveaway,
        valid_user_ids: Optional[List[int]] = None,
    ) -> List[int]:
        """Select random winners for a giveaway.

        Args:
            giveaway: The giveaway to select winners for.
            valid_user_ids: Optional list of valid user IDs (users still in server).
                           If None, all entries are considered valid.

        Returns:
            List of winner user IDs.
        """
        if giveaway.id is None:
            return []

        # Get all entries
        entries = await self.storage.get_entries(giveaway.id)

        if not entries:
            return []

        # Filter to valid users if provided
        if valid_user_ids is not None:
            entries = [uid for uid in entries if uid in valid_user_ids]

        if not entries:
            return []

        # Select winners
        winner_count = min(giveaway.winner_count, len(entries))
        winners = random.sample(entries, winner_count)

        # Store winners
        for winner_id in winners:
            await self.storage.add_winner(giveaway.id, winner_id)

        return winners

    async def reroll_winners(
        self,
        giveaway: Giveaway,
        count: int = 1,
        valid_user_ids: Optional[List[int]] = None,
        exclude_previous: bool = True,
    ) -> Tuple[List[int], str]:
        """Reroll winners for a giveaway.

        Args:
            giveaway: The giveaway to reroll winners for.
            count: Number of new winners to select.
            valid_user_ids: Optional list of valid user IDs (users still in server).
            exclude_previous: Whether to exclude previous winners from the reroll.

        Returns:
            Tuple of (new winner IDs, message).
        """
        if giveaway.id is None:
            return [], "Invalid giveaway."

        # Get all entries
        entries = await self.storage.get_entries(giveaway.id)

        if not entries:
            return [], "No entries found for this giveaway."

        # Filter to valid users if provided
        if valid_user_ids is not None:
            entries = [uid for uid in entries if uid in valid_user_ids]

        if not entries:
            return [], "No valid entries found (users may have left the server)."

        # Exclude previous winners if requested
        if exclude_previous:
            previous_winners = await self.storage.get_winners(giveaway.id)
            entries = [uid for uid in entries if uid not in previous_winners]

        if not entries:
            return [], "No eligible entries remaining for reroll."

        # Select new winners
        winner_count = min(count, len(entries))
        new_winners = random.sample(entries, winner_count)

        # Store new winners
        for winner_id in new_winners:
            await self.storage.add_winner(giveaway.id, winner_id)

        return (
            new_winners,
            f"Successfully rerolled {
            len(new_winners)} winner(s)!",
        )

    async def get_winners(self, giveaway_id: int) -> List[int]:
        """Get all winners for a giveaway."""
        return await self.storage.get_winners(giveaway_id)

    async def clear_winners(self, giveaway_id: int) -> None:
        """Clear all winners for a giveaway."""
        await self.storage.clear_winners(giveaway_id)

    def format_winners_message(
        self,
        winners: List[int],
        prize: str,
    ) -> str:
        """Format a message announcing the winners.

        Args:
            winners: List of winner user IDs.
            prize: The prize description.

        Returns:
            Formatted winner announcement message.
        """
        if not winners:
            return f"🎉 **Giveaway Ended!**\n\nPrize: **{prize}**\n\nNo valid entries - no winner could be selected."

        if len(winners) == 1:
            winner_mentions = f"<@{winners[0]}>"
            return (
                f"🎉 **Giveaway Ended!**\n\n"
                f"Prize: **{prize}**\n\n"
                f"Winner: {winner_mentions}\n\n"
                f"Congratulations! 🎊"
            )

        winner_mentions = ", ".join(f"<@{uid}>" for uid in winners)
        return (
            f"🎉 **Giveaway Ended!**\n\n"
            f"Prize: **{prize}**\n\n"
            f"Winners: {winner_mentions}\n\n"
            f"Congratulations to all winners! 🎊"
        )

    def format_dm_message(self, prize: str, guild_name: str) -> str:
        """Format a DM message for winners.

        Args:
            prize: The prize description.
            guild_name: Name of the Discord server.

        Returns:
            Formatted DM message.
        """
        return (
            f"🎉 **Congratulations!**\n\n"
            f"You won the giveaway in **{guild_name}**!\n\n"
            f"Prize: **{prize}**\n\n"
            f"Please contact a server administrator to claim your prize."
        )
