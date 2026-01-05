"""Guild configuration model."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class GuildConfig:
    """Per-guild configuration for the giveaway bot."""

    guild_id: int
    admin_role_ids: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_admin_role(self, role_id: int) -> bool:
        """Add an admin role to the guild configuration.

        Args:
            role_id: The Discord role ID to add as an admin role.

        Returns:
            True if the role was added, False if it already exists.
        """
        if role_id not in self.admin_role_ids:
            self.admin_role_ids.append(role_id)
            return True
        return False

    def remove_admin_role(self, role_id: int) -> bool:
        """Remove an admin role from the guild configuration.

        Args:
            role_id: The Discord role ID to remove from admin roles.

        Returns:
            True if the role was removed, False if it was not found.
        """
        if role_id in self.admin_role_ids:
            self.admin_role_ids.remove(role_id)
            return True
        return False

    def is_admin_role(self, role_id: int) -> bool:
        """Check if a role is an admin role.

        Args:
            role_id: The Discord role ID to check.

        Returns:
            True if the role is an admin role, False otherwise.
        """
        return role_id in self.admin_role_ids

    def to_dict(self) -> dict:
        """Convert the guild configuration to a dictionary for storage.

        Returns:
            A dictionary representation of the guild configuration.
        """
        return {
            "guild_id": self.guild_id,
            "admin_role_ids": json.dumps(self.admin_role_ids),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GuildConfig":
        """Create a GuildConfig instance from a dictionary.

        Args:
            data: A dictionary containing guild configuration data.

        Returns:
            A new GuildConfig instance populated with the provided data.
        """
        admin_role_ids = data.get("admin_role_ids", "[]")
        if isinstance(admin_role_ids, str):
            admin_role_ids = json.loads(admin_role_ids)

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        return cls(
            guild_id=data["guild_id"],
            admin_role_ids=admin_role_ids,
            created_at=created_at,
        )

    @classmethod
    def default(cls, guild_id: int) -> "GuildConfig":
        """Create a default configuration for a guild.

        Args:
            guild_id: The Discord guild ID to create the configuration for.

        Returns:
            A new GuildConfig instance with default settings.
        """
        return cls(guild_id=guild_id)
