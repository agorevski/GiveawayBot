"""Tests for permission utilities."""

from src.utils.permissions import check_giveaway_admin, has_required_role
from src.models.guild_config import GuildConfig


class TestCheckGiveawayAdmin:
    """Tests for check_giveaway_admin function."""

    def test_discord_admin_always_allowed(self):
        """Test that Discord administrators always have access."""
        config = GuildConfig(guild_id=123456789, admin_role_ids=[])

        result = check_giveaway_admin(
            user_permission_admin=True,
            user_role_ids=[],
            guild_config=config,
        )

        assert result is True

    def test_configured_admin_role(self):
        """Test that users with configured admin roles have access."""
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111, 222222222])

        # User has one of the admin roles
        result = check_giveaway_admin(
            user_permission_admin=False,
            user_role_ids=[111111111, 333333333],
            guild_config=config,
        )

        assert result is True

    def test_no_admin_permission(self):
        """Test that users without admin permissions are denied."""
        config = GuildConfig(guild_id=123456789, admin_role_ids=[111111111])

        # User doesn't have admin permission or admin role
        result = check_giveaway_admin(
            user_permission_admin=False,
            user_role_ids=[444444444, 555555555],
            guild_config=config,
        )

        assert result is False

    def test_empty_admin_roles(self):
        """Test with no configured admin roles."""
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
        """Test when user has the required role."""
        result = has_required_role(
            user_role_ids=[111111111, 222222222, 333333333],
            required_role_id=222222222,
        )

        assert result is True

    def test_user_missing_role(self):
        """Test when user doesn't have the required role."""
        result = has_required_role(
            user_role_ids=[111111111, 333333333],
            required_role_id=222222222,
        )

        assert result is False

    def test_empty_roles(self):
        """Test with empty role list."""
        result = has_required_role(
            user_role_ids=[],
            required_role_id=111111111,
        )

        assert result is False
