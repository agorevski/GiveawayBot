"""Permission checking utilities for the Giveaway Bot."""

from typing import List

from src.models.guild_config import GuildConfig


def check_giveaway_admin(
    user_permission_admin: bool,
    user_role_ids: List[int],
    guild_config: GuildConfig,
) -> bool:
    """Check if a user has giveaway admin permissions.

    A user is considered a giveaway admin if:
    1. They have Discord Administrator permission, OR
    2. They have one of the configured admin roles

    Args:
        user_permission_admin: Whether the user has Discord Administrator permission.
        user_role_ids: List of role IDs the user has.
        guild_config: The guild configuration containing admin role IDs.

    Returns:
        True if the user has giveaway admin permissions.
    """
    # Discord Administrator permission always grants access
    if user_permission_admin:
        return True

    # Check if user has any of the configured admin roles
    for role_id in user_role_ids:
        if guild_config.is_admin_role(role_id):
            return True

    return False


def has_required_role(user_role_ids: List[int], required_role_id: int) -> bool:
    """Check if a user has a required role.

    Args:
        user_role_ids: List of role IDs the user has.
        required_role_id: The required role ID.

    Returns:
        True if the user has the required role.
    """
    return required_role_id in user_role_ids
