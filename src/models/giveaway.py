"""Giveaway data model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List


class GiveawayStatus(Enum):
    """Status of a giveaway."""

    SCHEDULED = "scheduled"  # Waiting for scheduled start time
    ACTIVE = "active"  # Currently accepting entries
    ENDED = "ended"  # Ended and winners selected
    CANCELLED = "cancelled"  # Cancelled by admin


@dataclass
class Giveaway:
    """Represents a giveaway."""

    # Required fields
    guild_id: int
    channel_id: int
    prize: str
    ends_at: datetime
    created_by: int

    # Optional fields with defaults
    id: Optional[int] = None
    message_id: Optional[int] = None
    winner_count: int = 1
    required_role_id: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_start: Optional[datetime] = None
    ended: bool = False
    cancelled: bool = False

    # Runtime fields (not stored in DB)
    entries: List[int] = field(default_factory=list)
    winners: List[int] = field(default_factory=list)

    @property
    def status(self) -> GiveawayStatus:
        """Get the current status of the giveaway.

        Returns:
            GiveawayStatus: The current status (SCHEDULED, ACTIVE, ENDED, or CANCELLED).
        """
        if self.cancelled:
            return GiveawayStatus.CANCELLED
        if self.ended:
            return GiveawayStatus.ENDED
        if self.scheduled_start and datetime.now(timezone.utc) < self.scheduled_start:
            return GiveawayStatus.SCHEDULED
        return GiveawayStatus.ACTIVE

    @property
    def is_active(self) -> bool:
        """Check if the giveaway is currently active.

        Returns:
            bool: True if the giveaway status is ACTIVE, False otherwise.
        """
        return self.status == GiveawayStatus.ACTIVE

    @property
    def is_ended(self) -> bool:
        """Check if the giveaway has ended.

        Returns:
            bool: True if the giveaway status is ENDED or CANCELLED, False otherwise.
        """
        return self.status in (GiveawayStatus.ENDED, GiveawayStatus.CANCELLED)

    @property
    def should_end(self) -> bool:
        """Check if the giveaway should be ended (past end time).

        Returns:
            bool: True if the giveaway is active and past its end time.
        """
        return self.is_active and datetime.now(timezone.utc) >= self.ends_at

    @property
    def should_start(self) -> bool:
        """Check if a scheduled giveaway should start.

        Returns:
            bool: True if the giveaway is scheduled and past its start time.
        """
        if self.status != GiveawayStatus.SCHEDULED:
            return False
        if self.scheduled_start is None:
            return False
        return datetime.now(timezone.utc) >= self.scheduled_start

    @property
    def time_remaining(self) -> Optional[float]:
        """Get seconds remaining until giveaway ends.

        Returns:
            Optional[float]: Seconds remaining, or None if the giveaway has ended.
        """
        if self.is_ended:
            return None
        remaining = (self.ends_at - datetime.now(timezone.utc)).total_seconds()
        return max(0, remaining)

    @property
    def entry_count(self) -> int:
        """Get the number of entries.

        Returns:
            int: The total number of entries in the giveaway.
        """
        return len(self.entries)

    def to_dict(self) -> dict:
        """Convert the giveaway to a dictionary for storage.

        Returns:
            dict: A dictionary representation of the giveaway with all fields
                serialized for database storage.
        """
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "message_id": self.message_id,
            "prize": self.prize,
            "winner_count": self.winner_count,
            "required_role_id": self.required_role_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "scheduled_start": (
                self.scheduled_start.isoformat() if self.scheduled_start else None
            ),
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
            "ended": self.ended,
            "cancelled": self.cancelled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Giveaway":
        """Create a Giveaway instance from a dictionary.

        Args:
            data: A dictionary containing giveaway data, typically from database storage.

        Returns:
            Giveaway: A new Giveaway instance populated with the provided data.
        """
        return cls(
            id=data.get("id"),
            guild_id=data["guild_id"],
            channel_id=data["channel_id"],
            message_id=data.get("message_id"),
            prize=data["prize"],
            winner_count=data.get("winner_count", 1),
            required_role_id=data.get("required_role_id"),
            created_by=data["created_by"],
            created_at=_parse_datetime(data.get("created_at")) or datetime.now(timezone.utc),
            scheduled_start=_parse_datetime(data.get("scheduled_start")),
            ends_at=_parse_datetime(data["ends_at"]) or datetime.now(timezone.utc),
            ended=bool(data.get("ended", False)),
            cancelled=bool(data.get("cancelled", False)),
        )


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO format datetime string.

    Args:
        value: An ISO format datetime string, a datetime object, or None.

    Returns:
        Optional[datetime]: The parsed datetime object, or None if value is None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)
