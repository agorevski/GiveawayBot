"""Tests for permission utilities."""

from src.utils.permissions import check_giveaway_admin, has_required_role
from src.models.guild_config import GuildConfig


class TestCheckGiveawayAdmin:
    """Tests for check_giveaway_admin function."""

    def test_discord_admin_always_allowed(self):
        """Test that Discord administrators always have access.

        Verifies that users with Discord administrator permissions are granted
        giveaway admin access regardless of configured admin roles.
        """
        config = GuildConfig(guild_id=123456789, admin_role_ids=[])

        result = check_giveaway_admin(
            user_permission_admin=True,
            user_role_ids=[],
            guild_config=config,
        )

        assert result is True

    def test_configured_admin_role(self):
        """Test that users with configured admin roles have access.

        Verifies that users who have one of the configured admin role IDs
        are granted giveaway admin access even without Discord admin permissions.
        """
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111, 222222222])

        # User has one of the admin roles
        result = check_giveaway_admin(
            user_permission_admin=False,
            user_role_ids=[111111111, 333333333],
            guild_config=config,
        )

        assert result is True

    def test_no_admin_permission(self):
        """Test that users without admin permissions are denied.

        Verifies that users without Discord admin permissions and without
        any of the configured admin roles are denied giveaway admin access.
        """
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111])

        # User doesn't have admin permission or admin role
        result = check_giveaway_admin(
            user_permission_admin=False,
            user_role_ids=[444444444, 555555555],
            guild_config=config,
        )

        assert result is False

    def test_empty_admin_roles(self):
        """Test with no configured admin roles.

        Verifies behavior when no admin roles are configured: non-admin users
        are denied but Discord administrators still have access.
        """
        config = GuildConfig(guild_id=123456789, admin_role_ids=[])

        # Non-admin user
        result = check_giveaway_admin(
            user_permission_admin=False,
            user_role_ids=[111111111],
            guild_config=config,
        )

        assert result is False

        # Discord admin still works
        result = check_giveaway_admin(
            user_permission_admin=True,
            user_role_ids=[111111111],
            guild_config=config,
        )

        assert result is True


class TestHasRequiredRole:
    """Tests for has_required_role function."""

    def test_user_has_role(self):
        """Test when user has the required role.

        Verifies that the function returns True when the user's role list
        contains the required role ID.
        """
        result = has_required_role(
            user_role_ids=[111111111, 222222222, 333333333],
            required_role_id=222222222,
        )

        assert result is True

    def test_user_missing_role(self):
        """Test when user doesn't have the required role.

        Verifies that the function returns False when the user's role list
        does not contain the required role ID.
        """
        result = has_required_role(
            user_role_ids=[111111111, 333333333],
            required_role_id=222222222,
        )

        assert result is False

    def test_empty_roles(self):
        """Test with empty role list.

        Verifies that the function returns False when the user has no roles.
        """
        result = has_required_role(
            user_role_ids=[],
            required_role_id=111111111,
        )

        assert result is False
