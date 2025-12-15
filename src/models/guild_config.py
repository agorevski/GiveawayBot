"""Guild configuration model."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class GuildConfig:
    """Per-guild configuration for the giveaway bot."""

    guild_id: int
    admin_role_ids: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_admin_role(self, role_id: int) -> bool:
        """Add an admin role. Returns True if added, False if already exists."""
        if role_id not in self.admin_role_ids:
            self.admin_role_ids.append(role_id)
            return True
        return False

    def remove_admin_role(self, role_id: int) -> bool:
        """Remove an admin role. Returns True if removed, False if not found."""
        if role_id in self.admin_role_ids:
            self.admin_role_ids.remove(role_id)
            return True
        return False

    def is_admin_role(self, role_id: int) -> bool:
        """Check if a role is an admin role."""
        return role_id in self.admin_role_ids

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "guild_id": self.guild_id,
            "admin_role_ids": json.dumps(self.admin_role_ids),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GuildConfig":
        """Create a GuildConfig from a dictionary."""
        admin_role_ids = data.get("admin_role_ids", "[]")
        if isinstance(admin_role_ids, str):
            admin_role_ids = json.loads(admin_role_ids)

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.utcnow()

        return cls(
            guild_id=data["guild_id"],
            admin_role_ids=admin_role_ids,
            created_at=created_at,
        )

    @classmethod
    def default(cls, guild_id: int) -> "GuildConfig":
        """Create a default configuration for a guild."""
        return cls(guild_id=guild_id)
