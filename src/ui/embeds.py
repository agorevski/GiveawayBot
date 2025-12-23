"""Embed builders for giveaway displays."""

import discord
from datetime import datetime, timezone
from typing import Optional, List

from src.models.giveaway import Giveaway, GiveawayStatus
from src.utils.validators import format_duration


def create_giveaway_embed(
    giveaway: Giveaway,
    host_name: str = "Unknown",
    role_name: Optional[str] = None,
) -> discord.Embed:
    """Create an embed for an active giveaway.

    Args:
        giveaway: The giveaway to display.
        host_name: Name of the user who created the giveaway.
        role_name: Name of the required role, if any.

    Returns:
        Discord embed for the giveaway.
    """
    # Determine color based on status
    if giveaway.status == GiveawayStatus.SCHEDULED:
        color = discord.Color.blue()
        status_text = "🕐 Scheduled"
    elif giveaway.status == GiveawayStatus.ACTIVE:
        color = discord.Color.green()
        status_text = "🎉 Active"
    else:
        color = discord.Color.greyple()
        status_text = "Ended"

    embed = discord.Embed(
        title="🎁 GIVEAWAY",
        description=f"**{giveaway.prize}**",
        color=color,
    )

    # Add fields
    embed.add_field(
        name="Status",
        value=status_text,
        inline=True,
    )

    embed.add_field(
        name="Winners",
        value=str(giveaway.winner_count),
        inline=True,
    )

    embed.add_field(
        name="Entries",
        value=str(giveaway.entry_count),
        inline=True,
    )

    # Time remaining
    if giveaway.status == GiveawayStatus.SCHEDULED and giveaway.scheduled_start:
        time_until_start = (
            giveaway.scheduled_start - datetime.now(timezone.utc)
        ).total_seconds()
        embed.add_field(
            name="Starts In",
            value=format_duration(int(max(0, time_until_start))),
            inline=True,
        )
    elif giveaway.time_remaining is not None:
        embed.add_field(
            name="Time Remaining",
            value=format_duration(int(giveaway.time_remaining)),
            inline=True,
        )

    # End time as timestamp
    embed.add_field(
        name="Ends At",
        value=f"<t:{int(giveaway.ends_at.timestamp())}:R>",
        inline=True,
    )

    # Role requirement
    if role_name:
        embed.add_field(
            name="Required Role",
            value=f"@{role_name}",
            inline=True,
        )

    # Footer
    embed.set_footer(text=f"Hosted by {host_name} • ID: {giveaway.id}")
    embed.timestamp = giveaway.ends_at

    return embed


def create_ended_embed(
    giveaway: Giveaway,
    winners: List[int],
    host_name: str = "Unknown",
) -> discord.Embed:
    """Create an embed for an ended giveaway.

    Args:
        giveaway: The ended giveaway.
        winners: List of winner user IDs.
        host_name: Name of the user who created the giveaway.

    Returns:
        Discord embed for the ended giveaway.
    """
    embed = discord.Embed(
        title="🎁 GIVEAWAY ENDED",
        description=f"**{giveaway.prize}**",
        color=discord.Color.dark_grey(),
    )

    # Winners field
    if winners:
        if len(winners) == 1:
            winner_text = f"<@{winners[0]}>"
        else:
            winner_text = "\n".join(f"• <@{uid}>" for uid in winners)
        embed.add_field(
            name="🏆 Winner(s)",
            value=winner_text,
            inline=False,
        )
    else:
        embed.add_field(
            name="Winner(s)",
            value="No valid entries",
            inline=False,
        )

    embed.add_field(
        name="Total Entries",
        value=str(giveaway.entry_count),
        inline=True,
    )

    embed.set_footer(text=f"Hosted by {host_name} • ID: {giveaway.id}")
    embed.timestamp = datetime.now(timezone.utc)

    return embed


def create_cancelled_embed(
    giveaway: Giveaway,
    host_name: str = "Unknown",
) -> discord.Embed:
    """Create an embed for a cancelled giveaway.

    Args:
        giveaway: The cancelled giveaway.
        host_name: Name of the user who created the giveaway.

    Returns:
        Discord embed for the cancelled giveaway.
    """
    embed = discord.Embed(
        title="🎁 GIVEAWAY CANCELLED",
        description=f"~~{giveaway.prize}~~",
        color=discord.Color.red(),
    )

    embed.add_field(
        name="Status",
        value="❌ Cancelled",
        inline=True,
    )

    embed.set_footer(text=f"Hosted by {host_name} • ID: {giveaway.id}")
    embed.timestamp = datetime.now(timezone.utc)

    return embed


def create_list_embed(
    giveaways: List[Giveaway],
    guild_name: str,
) -> discord.Embed:
    """Create an embed listing multiple giveaways.

    Args:
        giveaways: List of giveaways to display.
        guild_name: Name of the guild.

    Returns:
        Discord embed with giveaway list.
    """
    embed = discord.Embed(
        title=f"🎁 Active Giveaways in {guild_name}",
        color=discord.Color.blue(),
    )

    if not giveaways:
        embed.description = "No active giveaways at the moment."
        return embed

    for giveaway in giveaways[:10]:  # Limit to 10
        status = (
            "🕐 Scheduled"
            if giveaway.status == GiveawayStatus.SCHEDULED
            else "🎉 Active"
        )
        time_left = format_duration(int(giveaway.time_remaining or 0))

        embed.add_field(
            name=f"{status} {giveaway.prize}",
            value=(
                f"ID: `{giveaway.id}` | "
                f"Winners: {giveaway.winner_count} | "
                f"Entries: {giveaway.entry_count} | "
                f"Ends: {time_left}"
            ),
            inline=False,
        )

    if len(giveaways) > 10:
        embed.set_footer(text=f"And {len(giveaways) - 10} more...")

    return embed


def create_entries_embed(
    giveaways: List[Giveaway],
    user_name: str,
) -> discord.Embed:
    """Create an embed showing a user's giveaway entries.

    Args:
        giveaways: List of giveaways the user has entered.
        user_name: Name of the user.

    Returns:
        Discord embed with user's entries.
    """
    embed = discord.Embed(
        title=f"🎟️ {user_name}'s Giveaway Entries",
        color=discord.Color.purple(),
    )

    if not giveaways:
        embed.description = "You haven't entered any active giveaways."
        return embed

    for giveaway in giveaways[:10]:
        time_left = format_duration(int(giveaway.time_remaining or 0))

        embed.add_field(
            name=giveaway.prize,
            value=f"Ends in: {time_left} | Winners: {giveaway.winner_count}",
            inline=False,
        )

    if len(giveaways) > 10:
        embed.set_footer(text=f"And {len(giveaways) - 10} more entries...")

    return embed
