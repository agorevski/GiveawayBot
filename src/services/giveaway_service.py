"""Giveaway service for business logic."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from src.models.giveaway import Giveaway, GiveawayStatus
from src.services.storage_service import StorageService


class GiveawayService:
    """Handles giveaway business logic."""

    def __init__(self, storage: StorageService):
        """Initialize the giveaway service.

        Args:
            storage: Storage service for database operations.
        """
        self.storage = storage

    async def create_giveaway(
        self,
        guild_id: int,
        channel_id: int,
        prize: str,
        duration_seconds: int,
        created_by: int,
        winner_count: int = 1,
        required_role_id: Optional[int] = None,
        scheduled_start: Optional[datetime] = None,
    ) -> Giveaway:
        """Create a new giveaway.

        Args:
            guild_id: Discord guild ID.
            channel_id: Discord channel ID.
            prize: Prize description.
            duration_seconds: Duration in seconds from start to end.
            created_by: User ID who created the giveaway.
            winner_count: Number of winners to select.
            required_role_id: Optional role ID required to enter.
            scheduled_start: Optional scheduled start time.

        Returns:
            The created giveaway.
        """
        # Calculate end time
        if scheduled_start:
            ends_at = scheduled_start + timedelta(seconds=duration_seconds)
        else:
            ends_at = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)

        giveaway = Giveaway(
            guild_id=guild_id,
            channel_id=channel_id,
            prize=prize,
            ends_at=ends_at,
            created_by=created_by,
            winner_count=winner_count,
            required_role_id=required_role_id,
            scheduled_start=scheduled_start,
        )

        return await self.storage.create_giveaway(giveaway)

    async def get_giveaway(self, giveaway_id: int) -> Optional[Giveaway]:
        """Get a giveaway by ID.

        Args:
            giveaway_id: The unique identifier of the giveaway.

        Returns:
            The giveaway if found, None otherwise.
        """
        return await self.storage.get_giveaway(giveaway_id)

    async def get_giveaway_by_message(self, message_id: int) -> Optional[Giveaway]:
        """Get a giveaway by its Discord message ID.

        Args:
            message_id: The Discord message ID associated with the giveaway.

        Returns:
            The giveaway if found, None otherwise.
        """
        return await self.storage.get_giveaway_by_message(message_id)

    async def get_active_giveaways(
        self, guild_id: Optional[int] = None
    ) -> List[Giveaway]:
        """Get all active giveaways, optionally filtered by guild.

        Args:
            guild_id: Optional Discord guild ID to filter by.

        Returns:
            List of active giveaways.
        """
        return await self.storage.get_active_giveaways(guild_id)

    async def set_message_id(self, giveaway: Giveaway, message_id: int) -> None:
        """Set the Discord message ID for a giveaway.

        Args:
            giveaway: The giveaway to update.
            message_id: The Discord message ID to associate with the giveaway.
        """
        giveaway.message_id = message_id
        await self.storage.update_giveaway(giveaway)

    async def enter_giveaway(
        self,
        giveaway_id: int,
        user_id: int,
        user_role_ids: List[int],
    ) -> Tuple[bool, str]:
        """Attempt to enter a user into a giveaway.

        Args:
            giveaway_id: The giveaway to enter.
            user_id: The user attempting to enter.
            user_role_ids: List of role IDs the user has.

        Returns:
            Tuple of (success, message).
        """
        giveaway = await self.storage.get_giveaway(giveaway_id)

        if not giveaway:
            return False, "Giveaway not found."

        if not giveaway.is_active:
            if giveaway.status == GiveawayStatus.SCHEDULED:
                return False, "This giveaway hasn't started yet."
            return False, "This giveaway has ended."

        # Check role requirement
        if giveaway.required_role_id:
            if giveaway.required_role_id not in user_role_ids:
                return False, "You don't have the required role to enter this giveaway."

        # Check if already entered
        if await self.storage.has_entered(giveaway_id, user_id):
            return False, "You've already entered this giveaway!"

        # Add entry
        success = await self.storage.add_entry(giveaway_id, user_id)
        if success:
            return True, "You've been entered into the giveaway! 🎉"
        return False, "Failed to enter the giveaway."

    async def leave_giveaway(self, giveaway_id: int, user_id: int) -> Tuple[bool, str]:
        """Remove a user from a giveaway.

        Args:
            giveaway_id: The giveaway to leave.
            user_id: The user attempting to leave.

        Returns:
            Tuple of (success, message).
        """
        giveaway = await self.storage.get_giveaway(giveaway_id)

        if not giveaway:
            return False, "Giveaway not found."

        if not giveaway.is_active:
            return False, "This giveaway has ended."

        success = await self.storage.remove_entry(giveaway_id, user_id)
        if success:
            return True, "You've been removed from the giveaway."
        return False, "You weren't entered in this giveaway."

    async def end_giveaway(self, giveaway_id: int) -> Optional[Giveaway]:
        """End a giveaway and mark it as ended.

        Args:
            giveaway_id: The unique identifier of the giveaway to end.

        Returns:
            The updated giveaway, or None if not found.
        """
        giveaway = await self.storage.get_giveaway(giveaway_id)

        if not giveaway:
            return None

        giveaway.ended = True
        await self.storage.update_giveaway(giveaway)

        return giveaway

    async def cancel_giveaway(self, giveaway_id: int) -> Tuple[bool, str]:
        """Cancel a giveaway.

        Args:
            giveaway_id: The unique identifier of the giveaway to cancel.

        Returns:
            Tuple of (success, message).
        """
        giveaway = await self.storage.get_giveaway(giveaway_id)

        if not giveaway:
            return False, "Giveaway not found."

        if giveaway.is_ended:
            return False, "This giveaway has already ended."

        giveaway.cancelled = True
        await self.storage.update_giveaway(giveaway)

        return True, "Giveaway cancelled."

    async def get_giveaways_to_end(self) -> List[Giveaway]:
        """Get all giveaways that should be ended now.

        Returns:
            List of giveaways that have passed their end time.
        """
        active_giveaways = await self.storage.get_active_giveaways()
        return [g for g in active_giveaways if g.should_end]

    async def get_giveaways_to_start(self) -> List[Giveaway]:
        """Get all scheduled giveaways that should start now.

        Returns:
            List of scheduled giveaways that have passed their start time.
        """
        scheduled = await self.storage.get_scheduled_giveaways()
        return [g for g in scheduled if g.should_start]

    async def get_user_entries(self, guild_id: int, user_id: int) -> List[Giveaway]:
        """Get all active giveaways a user has entered in a guild.

        Args:
            guild_id: The Discord guild ID.
            user_id: The user ID to check entries for.

        Returns:
            List of active giveaways the user has entered.
        """
        return await self.storage.get_user_entries(guild_id, user_id)

    async def start_scheduled_giveaway(self, giveaway: Giveaway) -> None:
        """Start a scheduled giveaway by clearing its scheduled_start time.

        Args:
            giveaway: The scheduled giveaway to start.
        """
        giveaway.scheduled_start = None
        await self.storage.update_giveaway(giveaway)

    @staticmethod
    def parse_duration(duration_str: str) -> Optional[int]:
        """Parse a duration string into seconds.

        Supports formats like:
        - "30s", "30sec", "30 seconds"
        - "5m", "5min", "5 minutes"
        - "2h", "2hr", "2 hours"
        - "1d", "1 day", "1 days"
        - "1w", "1 week", "1 weeks"
        - Combinations: "1d 2h 30m", "1d2h30m"

        Args:
            duration_str: The duration string to parse.

        Returns:
            Total seconds, or None if parsing failed.
        """
        duration_str = duration_str.lower().strip()

        if not duration_str:
            return None

        # Try to parse as just a number (assume minutes)
        try:
            return int(duration_str) * 60
        except ValueError:
            pass

        total_seconds = 0
        current_number = ""

        # Define unit multipliers
        units = {
            "s": 1,
            "sec": 1,
            "second": 1,
            "seconds": 1,
            "m": 60,
            "min": 60,
            "minute": 60,
            "minutes": 60,
            "h": 3600,
            "hr": 3600,
            "hour": 3600,
            "hours": 3600,
            "d": 86400,
            "day": 86400,
            "days": 86400,
            "w": 604800,
            "week": 604800,
            "weeks": 604800,
        }

        i = 0
        while i < len(duration_str):
            char = duration_str[i]

            if char.isdigit():
                current_number += char
            elif char.isalpha():
                # Find the full unit
                unit = ""
                while i < len(duration_str) and duration_str[i].isalpha():
                    unit += duration_str[i]
                    i += 1
                i -= 1  # Back up one since the loop will increment

                if current_number and unit in units:
                    total_seconds += int(current_number) * units[unit]
                    current_number = ""
                elif unit not in units:
                    return None  # Unknown unit
            elif char in " \t":
                pass  # Skip whitespace
            else:
                return None  # Unknown character

            i += 1

        return total_seconds if total_seconds > 0 else None
