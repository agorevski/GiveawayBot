"""Tests for the AdminCog."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from src.cogs.admin import AdminCog, setup
from src.models.giveaway import Giveaway
from src.models.guild_config import GuildConfig


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot.

    Returns:
        MagicMock: A mock Discord bot with add_cog as an AsyncMock.
    """
    bot = MagicMock(spec=commands.Bot)
    bot.add_cog = AsyncMock()
    return bot


@pytest.fixture
def mock_storage():
    """Create a mock storage service.

    Returns:
        AsyncMock: A mock storage service with get_guild_config and
            save_guild_config methods.
    """
    storage = AsyncMock()
    storage.get_guild_config = AsyncMock(
        return_value=GuildConfig(guild_id=123456789, admin_role_ids=[])
    )
    storage.save_guild_config = AsyncMock()
    return storage


@pytest.fixture
def mock_giveaway_service():
    """Create a mock giveaway service.

    Returns:
        AsyncMock: A mock giveaway service with parse_duration returning 3600.
    """
    service = AsyncMock()
    service.parse_duration = MagicMock(return_value=3600)
    return service


@pytest.fixture
def mock_winner_service():
    """Create a mock winner service.

    Returns:
        AsyncMock: A mock winner service.
    """
    return AsyncMock()


@pytest.fixture
def mock_message_service():
    """Create a mock message service.

    Returns:
        AsyncMock: A mock message service.
    """
    return AsyncMock()


@pytest.fixture
def admin_cog(mock_bot, mock_giveaway_service, mock_winner_service, mock_storage, mock_message_service):
    """Create an AdminCog for testing.

    Args:
        mock_bot: Mock Discord bot fixture.
        mock_giveaway_service: Mock giveaway service fixture.
        mock_winner_service: Mock winner service fixture.
        mock_storage: Mock storage service fixture.
        mock_message_service: Mock message service fixture.

    Returns:
        AdminCog: An AdminCog instance configured with mock services.
    """
    return AdminCog(
        mock_bot,
        mock_giveaway_service,
        mock_winner_service,
        mock_storage,
        mock_message_service,
    )


def create_mock_interaction(
    guild_id=123456789,
    user_id=111111111,
    is_admin=True,
    user_roles=None,
):
    """Create a mock Discord interaction.

    Args:
        guild_id: The ID of the guild for the interaction. Defaults to 123456789.
        user_id: The ID of the user triggering the interaction. Defaults to 111111111.
        is_admin: Whether the user has administrator permissions. Defaults to True.
        user_roles: List of role IDs the user has. Defaults to None.

    Returns:
        MagicMock: A mock Discord interaction with configured guild, user, and channel.
    """
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()

    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.name = "Test Guild"
    guild.members = []
    interaction.guild = guild

    member = MagicMock(spec=discord.Member)
    member.id = user_id
    member.display_name = "TestUser"
    member.guild_permissions = MagicMock()
    member.guild_permissions.administrator = is_admin

    if user_roles:
        roles = []
        for role_id in user_roles:
            role = MagicMock(spec=discord.Role)
            role.id = role_id
            roles.append(role)
        member.roles = roles
    else:
        member.roles = []

    interaction.user = member
    interaction.channel = MagicMock(spec=discord.TextChannel)

    return interaction


class TestCheckAdmin:
    """Tests for _check_admin method."""

    @pytest.mark.asyncio
    async def test_check_admin_no_guild(self, admin_cog):
        """Test check admin with no guild.

        Args:
            admin_cog: The AdminCog fixture.
        """
        interaction = create_mock_interaction()
        interaction.guild = None

        result = await admin_cog._check_admin(interaction)

        assert result is False
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_admin_not_member(self, admin_cog):
        """Test check admin when user is not a member.

        Args:
            admin_cog: The AdminCog fixture.
        """
        interaction = create_mock_interaction()
        interaction.user = MagicMock(spec=discord.User)  # Not Member

        result = await admin_cog._check_admin(interaction)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_admin_with_admin_permissions(self, admin_cog, mock_storage):
        """Test check admin with Discord admin permissions.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[]
        )

        result = await admin_cog._check_admin(interaction)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_admin_without_permissions(self, admin_cog, mock_storage):
        """Test check admin without any permissions.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=False)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[]
        )

        result = await admin_cog._check_admin(interaction)

        assert result is False
        interaction.response.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_check_admin_with_admin_role(self, admin_cog, mock_storage):
        """Test check admin with giveaway admin role.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=False, user_roles=[444444444])
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[444444444]
        )

        result = await admin_cog._check_admin(interaction)

        assert result is True


class TestCreateGiveaway:
    """Tests for create_giveaway command."""

    @pytest.mark.asyncio
    async def test_create_giveaway_no_admin(self, admin_cog, mock_storage):
        """Test create giveaway without admin permissions.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=False)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[]
        )

        await admin_cog.create_giveaway.callback(
            admin_cog, interaction, prize="Test", duration="1h"
        )

        interaction.response.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_create_giveaway_invalid_prize(self, admin_cog, mock_storage):
        """Test create giveaway with invalid prize.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)

        await admin_cog.create_giveaway.callback(
            admin_cog, interaction, prize="", duration="1h"  # Empty prize
        )

        assert "❌" in str(interaction.response.send_message.call_args)

    @pytest.mark.asyncio
    async def test_create_giveaway_invalid_duration(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test create giveaway with invalid duration.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.parse_duration.return_value = None

        await admin_cog.create_giveaway.callback(
            admin_cog, interaction, prize="Test Prize", duration="invalid"
        )

        assert "Invalid duration" in str(interaction.response.send_message.call_args)

    @pytest.mark.asyncio
    async def test_create_giveaway_invalid_winner_count(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test create giveaway with invalid winner count.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.parse_duration.return_value = 3600

        await admin_cog.create_giveaway.callback(
            admin_cog, interaction, prize="Test Prize", duration="1h", winners=0
        )

        assert "❌" in str(interaction.response.send_message.call_args)

    @pytest.mark.asyncio
    async def test_create_giveaway_invalid_channel(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test create giveaway with invalid channel.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        interaction.channel = MagicMock(spec=discord.VoiceChannel)
        mock_giveaway_service.parse_duration.return_value = 3600

        await admin_cog.create_giveaway.callback(
            admin_cog, interaction, prize="Test Prize", duration="1h"
        )

        assert "Invalid channel" in str(interaction.response.send_message.call_args)

    @pytest.mark.asyncio
    async def test_create_giveaway_success(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test successful giveaway creation.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        channel = AsyncMock(spec=discord.TextChannel)
        channel.id = 987654321
        channel.mention = "#test"
        channel.send = AsyncMock(return_value=MagicMock(id=555555555))
        interaction.channel = channel

        mock_giveaway_service.parse_duration.return_value = 3600
        mock_giveaway_service.create_giveaway = AsyncMock(
            return_value=Giveaway(
                id=1,
                guild_id=123456789,
                channel_id=987654321,
                prize="Test Prize",
                ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
                created_by=111111111,
            )
        )
        mock_giveaway_service.set_message_id = AsyncMock()

        await admin_cog.create_giveaway.callback(
            admin_cog, interaction, prize="Test Prize", duration="1h"
        )

        mock_giveaway_service.create_giveaway.assert_called_once()
        interaction.followup.send.assert_called()


class TestEndGiveaway:
    """Tests for end_giveaway command."""

    @pytest.mark.asyncio
    async def test_end_giveaway_not_found(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test ending a non-existent giveaway.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=None)

        await admin_cog.end_giveaway.callback(admin_cog, interaction, giveaway_id=99999)

        assert "not found" in str(interaction.followup.send.call_args).lower()

    @pytest.mark.asyncio
    async def test_end_giveaway_wrong_guild(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test ending a giveaway from wrong guild.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_giveaway = AsyncMock(
            return_value=Giveaway(
                id=1,
                guild_id=999999999,  # Different guild
                channel_id=987654321,
                prize="Test",
                ends_at=datetime.now(timezone.utc),
                created_by=111111111,
            )
        )

        await admin_cog.end_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        assert "not found" in str(interaction.followup.send.call_args).lower()

    @pytest.mark.asyncio
    async def test_end_giveaway_already_ended(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test ending an already ended giveaway.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_giveaway = AsyncMock(
            return_value=Giveaway(
                id=1,
                guild_id=123456789,
                channel_id=987654321,
                prize="Test",
                ends_at=datetime.now(timezone.utc),
                created_by=111111111,
                ended=True,
            )
        )

        await admin_cog.end_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        assert "already ended" in str(interaction.followup.send.call_args).lower()

    @pytest.mark.asyncio
    async def test_end_giveaway_success(self, admin_cog, mock_storage, mock_giveaway_service, mock_winner_service, mock_message_service, mock_bot):
        """Test successful giveaway end.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
            mock_winner_service: The mock winner service fixture.
            mock_message_service: The mock message service fixture.
            mock_bot: The mock Discord bot fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
            entries=[111111111, 222222222],
        )
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=giveaway)
        mock_giveaway_service.end_giveaway = AsyncMock(return_value=giveaway)
        mock_winner_service.select_winners = AsyncMock(return_value=[111111111])

        channel = AsyncMock(spec=discord.TextChannel)
        mock_bot.get_channel.return_value = channel

        await admin_cog.end_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        mock_giveaway_service.end_giveaway.assert_called_once()
        mock_winner_service.select_winners.assert_called_once()
        mock_message_service.update_giveaway_message.assert_called_once()
        mock_message_service.announce_winners.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_giveaway_fails_to_end(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test when ending giveaway fails.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=giveaway)
        mock_giveaway_service.end_giveaway = AsyncMock(return_value=None)

        await admin_cog.end_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        assert "Failed" in str(interaction.followup.send.call_args)


class TestCancelGiveaway:
    """Tests for cancel_giveaway command."""

    @pytest.mark.asyncio
    async def test_cancel_giveaway_not_found(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test cancelling a non-existent giveaway.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=None)

        await admin_cog.cancel_giveaway.callback(admin_cog, interaction, giveaway_id=99999)

        assert "not found" in str(interaction.followup.send.call_args).lower()

    @pytest.mark.asyncio
    async def test_cancel_giveaway_wrong_guild(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test cancelling a giveaway from wrong guild.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_giveaway = AsyncMock(
            return_value=Giveaway(
                id=1,
                guild_id=999999999,  # Different guild
                channel_id=987654321,
                prize="Test",
                ends_at=datetime.now(timezone.utc),
                created_by=111111111,
            )
        )

        await admin_cog.cancel_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        assert "not found" in str(interaction.followup.send.call_args).lower()

    @pytest.mark.asyncio
    async def test_cancel_giveaway_failed(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test cancel failure.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=giveaway)
        mock_giveaway_service.cancel_giveaway = AsyncMock(return_value=(False, "Already ended"))

        await admin_cog.cancel_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        assert "❌" in str(interaction.followup.send.call_args)

    @pytest.mark.asyncio
    async def test_cancel_giveaway_success(self, admin_cog, mock_storage, mock_giveaway_service, mock_bot):
        """Test successful giveaway cancellation.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
            mock_bot: The mock Discord bot fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            message_id=555555555,
            prize="Test",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=giveaway)
        mock_giveaway_service.cancel_giveaway = AsyncMock(return_value=(True, "Cancelled"))

        channel = AsyncMock(spec=discord.TextChannel)
        message = AsyncMock()
        channel.fetch_message = AsyncMock(return_value=message)
        mock_bot.get_channel.return_value = channel

        await admin_cog.cancel_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        mock_giveaway_service.cancel_giveaway.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_cancel_giveaway_message_not_found(self, admin_cog, mock_storage, mock_giveaway_service, mock_bot):
        """Test cancel when message was deleted.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
            mock_bot: The mock Discord bot fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            message_id=555555555,
            prize="Test",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=giveaway)
        mock_giveaway_service.cancel_giveaway = AsyncMock(return_value=(True, "Cancelled"))

        channel = AsyncMock(spec=discord.TextChannel)
        channel.fetch_message = AsyncMock(side_effect=discord.NotFound(MagicMock(), "Not found"))
        mock_bot.get_channel.return_value = channel

        # Should not raise
        await admin_cog.cancel_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        interaction.followup.send.assert_called()

    @pytest.mark.asyncio
    async def test_cancel_giveaway_add_admin_role_already_exists(self, admin_cog, mock_storage):
        """Test adding an admin role that already exists.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[444444444]
        )

        role = MagicMock(spec=discord.Role)
        role.id = 444444444
        role.mention = "@Role"

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="add", role=role)

        # Should indicate role is already an admin role
        assert "already" in str(interaction.response.send_message.call_args).lower()

    @pytest.mark.asyncio
    async def test_cancel_giveaway_remove_nonexistent_role(self, admin_cog, mock_storage):
        """Test removing a role that isn't an admin role.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[]  # No roles
        )

        role = MagicMock(spec=discord.Role)
        role.id = 444444444
        role.mention = "@Role"

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="remove", role=role)

        assert "not a giveaway admin role" in str(interaction.response.send_message.call_args).lower()


class TestRerollGiveaway:
    """Tests for reroll_giveaway command."""

    @pytest.mark.asyncio
    async def test_reroll_giveaway_not_ended(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test rerolling a non-ended giveaway.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_giveaway = AsyncMock(
            return_value=Giveaway(
                id=1,
                guild_id=123456789,
                channel_id=987654321,
                prize="Test",
                ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
                created_by=111111111,
                ended=False,
            )
        )

        await admin_cog.reroll_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        assert "hasn't ended" in str(interaction.followup.send.call_args).lower()

    @pytest.mark.asyncio
    async def test_reroll_giveaway_not_found(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test rerolling a non-existent giveaway.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=None)

        await admin_cog.reroll_giveaway.callback(admin_cog, interaction, giveaway_id=99999)

        assert "not found" in str(interaction.followup.send.call_args).lower()

    @pytest.mark.asyncio
    async def test_reroll_giveaway_wrong_guild(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test rerolling a giveaway from wrong guild.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_giveaway = AsyncMock(
            return_value=Giveaway(
                id=1,
                guild_id=999999999,  # Different guild
                channel_id=987654321,
                prize="Test",
                ends_at=datetime.now(timezone.utc),
                created_by=111111111,
                ended=True,
            )
        )

        await admin_cog.reroll_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        assert "not found" in str(interaction.followup.send.call_args).lower()

    @pytest.mark.asyncio
    async def test_reroll_giveaway_success(self, admin_cog, mock_storage, mock_giveaway_service, mock_winner_service, mock_bot):
        """Test successful reroll.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
            mock_winner_service: The mock winner service fixture.
            mock_bot: The mock Discord bot fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) - timedelta(hours=1),
            created_by=111111111,
            ended=True,
            entries=[111111111, 222222222],
        )
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=giveaway)
        mock_winner_service.reroll_winners = AsyncMock(return_value=([333333333], "New winner selected"))

        channel = AsyncMock(spec=discord.TextChannel)
        mock_bot.get_channel.return_value = channel

        await admin_cog.reroll_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        mock_winner_service.reroll_winners.assert_called_once()
        interaction.followup.send.assert_called()

    @pytest.mark.asyncio
    async def test_reroll_giveaway_no_winners(self, admin_cog, mock_storage, mock_giveaway_service, mock_winner_service):
        """Test reroll with no valid winners.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
            mock_winner_service: The mock winner service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        giveaway = Giveaway(
            id=1,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test Prize",
            ends_at=datetime.now(timezone.utc) - timedelta(hours=1),
            created_by=111111111,
            ended=True,
        )
        mock_giveaway_service.get_giveaway = AsyncMock(return_value=giveaway)
        mock_winner_service.reroll_winners = AsyncMock(return_value=([], "No valid entries"))

        await admin_cog.reroll_giveaway.callback(admin_cog, interaction, giveaway_id=1)

        assert "❌" in str(interaction.followup.send.call_args)


class TestListGiveaways:
    """Tests for list_giveaways command."""

    @pytest.mark.asyncio
    async def test_list_giveaways(self, admin_cog, mock_storage, mock_giveaway_service):
        """Test listing giveaways.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
            mock_giveaway_service: The mock giveaway service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_giveaway_service.get_active_giveaways = AsyncMock(return_value=[])

        await admin_cog.list_giveaways.callback(admin_cog, interaction)

        mock_giveaway_service.get_active_giveaways.assert_called_once()
        interaction.followup.send.assert_called()


class TestConfigGiveaway:
    """Tests for config_giveaway command."""

    @pytest.mark.asyncio
    async def test_config_no_guild(self, admin_cog):
        """Test config command with no guild.

        Args:
            admin_cog: The AdminCog fixture.
        """
        interaction = create_mock_interaction()
        interaction.guild = None

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="list")

        interaction.response.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_config_not_admin(self, admin_cog):
        """Test config command without admin permissions.

        Args:
            admin_cog: The AdminCog fixture.
        """
        interaction = create_mock_interaction(is_admin=False)

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="list")

        assert "administrators" in str(interaction.response.send_message.call_args).lower()

    @pytest.mark.asyncio
    async def test_config_list_empty(self, admin_cog, mock_storage):
        """Test listing empty admin roles.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[]
        )

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="list")

        assert "No custom admin roles" in str(interaction.response.send_message.call_args)

    @pytest.mark.asyncio
    async def test_config_list_with_roles(self, admin_cog, mock_storage):
        """Test listing admin roles.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[111111111]
        )

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="list")

        assert "Admin Roles" in str(interaction.response.send_message.call_args)

    @pytest.mark.asyncio
    async def test_config_add_no_role(self, admin_cog, mock_storage):
        """Test adding without specifying role.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="add", role=None)

        assert "specify a role" in str(interaction.response.send_message.call_args).lower()

    @pytest.mark.asyncio
    async def test_config_add_role(self, admin_cog, mock_storage):
        """Test adding an admin role.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[]
        )
        
        role = MagicMock(spec=discord.Role)
        role.id = 444444444
        role.mention = "@Role"

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="add", role=role)

        mock_storage.save_guild_config.assert_called()
        assert "Added" in str(interaction.response.send_message.call_args)

    @pytest.mark.asyncio
    async def test_config_remove_role(self, admin_cog, mock_storage):
        """Test removing an admin role.

        Args:
            admin_cog: The AdminCog fixture.
            mock_storage: The mock storage service fixture.
        """
        interaction = create_mock_interaction(is_admin=True)
        mock_storage.get_guild_config.return_value = GuildConfig(
            guild_id=123456789, admin_role_ids=[444444444]
        )

        role = MagicMock(spec=discord.Role)
        role.id = 444444444
        role.mention = "@Role"

        await admin_cog.config_giveaway.callback(admin_cog, interaction, action="remove", role=role)

        mock_storage.save_guild_config.assert_called()
        assert "Removed" in str(interaction.response.send_message.call_args)


class TestSetup:
    """Tests for setup function."""

    @pytest.mark.asyncio
    async def test_setup_with_all_services(self, mock_bot):
        """Test setup with all services available.

        Args:
            mock_bot: The mock Discord bot fixture.
        """
        mock_bot.storage = MagicMock()
        mock_bot.giveaway_service = MagicMock()
        mock_bot.winner_service = MagicMock()
        mock_bot.message_service = MagicMock()

        await setup(mock_bot)

        mock_bot.add_cog.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_missing_services(self, mock_bot):
        """Test setup with missing services.

        Args:
            mock_bot: The mock Discord bot fixture.
        """
        # No services attached
        delattr(mock_bot, 'storage') if hasattr(mock_bot, 'storage') else None

        await setup(mock_bot)

        mock_bot.add_cog.assert_not_called()
