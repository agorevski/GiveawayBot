"""Giveaway data model."""

from dataclasses import dataclass, field
from datetime import datetime
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
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_start: Optional[datetime] = None
    ended: bool = False
    cancelled: bool = False

    # Runtime fields (not stored in DB)
    entries: List[int] = field(default_factory=list)
    winners: List[int] = field(default_factory=list)

    @property
    def status(self) -> GiveawayStatus:
        """Get the current status of the giveaway."""
        if self.cancelled:
            return GiveawayStatus.CANCELLED
        if self.ended:
            return GiveawayStatus.ENDED
        if self.scheduled_start and datetime.utcnow() < self.scheduled_start:
            return GiveawayStatus.SCHEDULED
        return GiveawayStatus.ACTIVE

    @property
    def is_active(self) -> bool:
        """Check if the giveaway is currently active."""
        return self.status == GiveawayStatus.ACTIVE

    @property
    def is_ended(self) -> bool:
        """Check if the giveaway has ended."""
        return self.status in (GiveawayStatus.ENDED, GiveawayStatus.CANCELLED)

    @property
    def should_end(self) -> bool:
        """Check if the giveaway should be ended (past end time)."""
        return self.is_active and datetime.utcnow() >= self.ends_at

    @property
    def should_start(self) -> bool:
        """Check if a scheduled giveaway should start."""
        if self.status != GiveawayStatus.SCHEDULED:
            return False
        if self.scheduled_start is None:
            return False
        return datetime.utcnow() >= self.scheduled_start

    @property
    def time_remaining(self) -> Optional[float]:
        """Get seconds remaining until giveaway ends. None if ended."""
        if self.is_ended:
            return None
        remaining = (self.ends_at - datetime.utcnow()).total_seconds()
        return max(0, remaining)

    @property
    def entry_count(self) -> int:
        """Get the number of entries."""
        return len(self.entries)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
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
        """Create a Giveaway from a dictionary."""
        return cls(
            id=data.get("id"),
            guild_id=data["guild_id"],
            channel_id=data["channel_id"],
            message_id=data.get("message_id"),
            prize=data["prize"],
            winner_count=data.get("winner_count", 1),
            required_role_id=data.get("required_role_id"),
            created_by=data["created_by"],
            created_at=_parse_datetime(data.get("created_at")) or datetime.utcnow(),
            scheduled_start=_parse_datetime(data.get("scheduled_start")),
            ends_at=_parse_datetime(data["ends_at"]) or datetime.utcnow(),
            ended=data.get("ended", False),
            cancelled=data.get("cancelled", False),
        )


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO format datetime string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)
