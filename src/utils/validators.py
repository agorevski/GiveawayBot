"""Input validation utilities for the Giveaway Bot."""

from typing import Tuple

# Constants for validation limits
MIN_WINNER_COUNT = 1
MAX_WINNER_COUNT = 20
MIN_PRIZE_LENGTH = 1
MAX_PRIZE_LENGTH = 256
MIN_DURATION_SECONDS = 10  # 10 seconds minimum
MAX_DURATION_SECONDS = 60 * 60 * 24 * 30  # 30 days maximum


def validate_winner_count(count: int) -> Tuple[bool, str]:
    """Validate the winner count.

    Args:
        count: Number of winners to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if count < MIN_WINNER_COUNT:
        return False, f"Winner count must be at least {MIN_WINNER_COUNT}."

    if count > MAX_WINNER_COUNT:
        return False, f"Winner count cannot exceed {MAX_WINNER_COUNT}."

    return True, ""


def validate_prize(prize: str) -> Tuple[bool, str]:
    """Validate the prize description.

    Args:
        prize: Prize description to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not prize or len(prize.strip()) < MIN_PRIZE_LENGTH:
        return False, "Prize description cannot be empty."

    if len(prize) > MAX_PRIZE_LENGTH:
        return False, f"Prize description cannot exceed {MAX_PRIZE_LENGTH} characters."

    return True, ""


def validate_duration(seconds: int) -> Tuple[bool, str]:
    """Validate the giveaway duration.

    Args:
        seconds: Duration in seconds to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if seconds < MIN_DURATION_SECONDS:
        return False, f"Duration must be at least {MIN_DURATION_SECONDS} seconds."

    if seconds > MAX_DURATION_SECONDS:
        days = MAX_DURATION_SECONDS // (60 * 60 * 24)
        return False, f"Duration cannot exceed {days} days."

    return True, ""


def format_duration(seconds: int) -> str:
    """Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Human-readable duration string.
    """
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    hours = minutes // 60
    if hours < 24:
        remaining_minutes = minutes % 60
        if remaining_minutes > 0:
            return f"{hours} hour{
                's' if hours != 1 else ''} {remaining_minutes} minute{
                's' if remaining_minutes != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''}"

    days = hours // 24
    remaining_hours = hours % 24
    if remaining_hours > 0:
        return f"{days} day{
            's' if days != 1 else ''} {remaining_hours} hour{
            's' if remaining_hours != 1 else ''}"
    return f"{days} day{'s' if days != 1 else ''}"


def format_timestamp(seconds_remaining: float) -> str:
    """Format remaining time for display.

    Args:
        seconds_remaining: Seconds remaining until end.

    Returns:
        Formatted time string.
    """
    if seconds_remaining <= 0:
        return "Ended"

    return format_duration(int(seconds_remaining))
