"""Tests for the button components."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

import discord

from src.ui.buttons import (
    GiveawayEntryButton,
    GiveawayLeaveButton,
    GiveawayEntryView,
    EndedGiveawayView,
)
from src.models.giveaway import Giveaway


class TestGiveawayEntryButton:
    """Tests for GiveawayEntryButton."""

    def test_button_initialization(self):
        """Test button is initialized correctly."""
        button = GiveawayEntryButton(giveaway_id=123)

        assert button.giveaway_id == 123
        assert button.style == discord.ButtonStyle.primary
        assert "Enter" in button.label
        assert button.custom_id == "giveaway_enter:123"

    @pytest.mark.asyncio
    async def test_callback_no_service(self):
        """Test callback when giveaway service is not available."""
        button = GiveawayEntryButton(giveaway_id=123)
        
        interaction = MagicMock(spec=discord.Interaction)
        interaction.client = MagicMock()
        interaction.client.giveaway_service = None
        interaction.response = AsyncMock()

        await button.callback(interaction)

        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "not properly configured" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_callback_successful_entry(self):
        """Test callback for successful entry."""
        button = GiveawayEntryButton(giveaway_id=123)

        # Mock interaction
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 111111111
        interaction.user.roles = []
        interaction.response = AsyncMock()
        interaction.message = AsyncMock()
        interaction.guild = MagicMock()
        interaction.guild.get_member.return_value = None

        # Mock giveaway service
        giveaway_service = AsyncMock()
        giveaway_service.enter_giveaway.return_value = (True, "You've been entered!")
        giveaway_service.get_giveaway.return_value = Giveaway(
            id=123,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        interaction.client = MagicMock()
        interaction.client.giveaway_service = giveaway_service

        await button.callback(interaction)

        giveaway_service.enter_giveaway.assert_called_once()
        interaction.response.send_message.assert_called_once()
        assert "✅" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_callback_failed_entry(self):
        """Test callback for failed entry."""
        button = GiveawayEntryButton(giveaway_id=123)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 111111111
        interaction.user.roles = []
        interaction.response = AsyncMock()

        giveaway_service = AsyncMock()
        giveaway_service.enter_giveaway.return_value = (False, "Already entered!")
        interaction.client = MagicMock()
        interaction.client.giveaway_service = giveaway_service

        await button.callback(interaction)

        assert "❌" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_callback_with_member_roles(self):
        """Test callback extracts roles from member."""
        button = GiveawayEntryButton(giveaway_id=123)

        role1 = MagicMock()
        role1.id = 111
        role2 = MagicMock()
        role2.id = 222

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 111111111
        interaction.user.roles = [role1, role2]
        interaction.response = AsyncMock()

        giveaway_service = AsyncMock()
        giveaway_service.enter_giveaway.return_value = (False, "test")
        interaction.client = MagicMock()
        interaction.client.giveaway_service = giveaway_service

        await button.callback(interaction)

        call_args = giveaway_service.enter_giveaway.call_args
        assert call_args[0][2] == [111, 222]  # user_role_ids

    @pytest.mark.asyncio
    async def test_callback_non_member_user(self):
        """Test callback with non-member user."""
        button = GiveawayEntryButton(giveaway_id=123)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.User)  # Not Member
        interaction.user.id = 111111111
        # User doesn't have roles attribute
        del interaction.user.roles
        interaction.response = AsyncMock()

        giveaway_service = AsyncMock()
        giveaway_service.enter_giveaway.return_value = (False, "test")
        interaction.client = MagicMock()
        interaction.client.giveaway_service = giveaway_service

        await button.callback(interaction)

        call_args = giveaway_service.enter_giveaway.call_args
        assert call_args[0][2] == []  # empty role list


class TestGiveawayLeaveButton:
    """Tests for GiveawayLeaveButton."""

    def test_button_initialization(self):
        """Test button is initialized correctly."""
        button = GiveawayLeaveButton(giveaway_id=456)

        assert button.giveaway_id == 456
        assert button.style == discord.ButtonStyle.secondary
        assert "Leave" in button.label
        assert button.custom_id == "giveaway_leave:456"

    @pytest.mark.asyncio
    async def test_callback_no_service(self):
        """Test callback when giveaway service is not available."""
        button = GiveawayLeaveButton(giveaway_id=123)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.client = MagicMock()
        interaction.client.giveaway_service = None
        interaction.response = AsyncMock()

        await button.callback(interaction)

        assert "not properly configured" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_callback_successful_leave(self):
        """Test callback for successful leave."""
        button = GiveawayLeaveButton(giveaway_id=123)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock()
        interaction.user.id = 111111111
        interaction.response = AsyncMock()
        interaction.message = AsyncMock()
        interaction.guild = MagicMock()
        interaction.guild.get_member.return_value = None

        giveaway_service = AsyncMock()
        giveaway_service.leave_giveaway.return_value = (True, "Removed!")
        giveaway_service.get_giveaway.return_value = Giveaway(
            id=123,
            guild_id=123456789,
            channel_id=987654321,
            prize="Test",
            ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by=111111111,
        )
        interaction.client = MagicMock()
        interaction.client.giveaway_service = giveaway_service

        await button.callback(interaction)

        giveaway_service.leave_giveaway.assert_called_once_with(123, 111111111)
        assert "✅" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_callback_failed_leave(self):
        """Test callback for failed leave."""
        button = GiveawayLeaveButton(giveaway_id=123)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock()
        interaction.user.id = 111111111
        interaction.response = AsyncMock()

        giveaway_service = AsyncMock()
        giveaway_service.leave_giveaway.return_value = (False, "Not entered!")
        interaction.client = MagicMock()
        interaction.client.giveaway_service = giveaway_service

        await button.callback(interaction)

        assert "❌" in interaction.response.send_message.call_args[0][0]


class TestGiveawayEntryView:
    """Tests for GiveawayEntryView."""

    @pytest.mark.asyncio
    async def test_view_with_enter_only(self):
        """Test view with just enter button."""
        view = GiveawayEntryView(giveaway_id=123)

        assert view.timeout is None  # Persistent view
        assert len(view.children) == 1
        assert isinstance(view.children[0], GiveawayEntryButton)

    @pytest.mark.asyncio
    async def test_view_with_leave_button(self):
        """Test view with both enter and leave buttons."""
        view = GiveawayEntryView(giveaway_id=123, include_leave=True)

        assert len(view.children) == 2
        assert any(isinstance(c, GiveawayEntryButton) for c in view.children)
        assert any(isinstance(c, GiveawayLeaveButton) for c in view.children)


class TestEndedGiveawayView:
    """Tests for EndedGiveawayView."""

    @pytest.mark.asyncio
    async def test_view_initialization(self):
        """Test ended view is initialized correctly."""
        view = EndedGiveawayView()

        assert view.timeout is None
        assert len(view.children) == 1
        
        button = view.children[0]
        assert button.disabled is True
        assert "Ended" in button.label
