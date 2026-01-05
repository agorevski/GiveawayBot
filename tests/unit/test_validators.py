"""Tests for validator utilities."""

from src.utils.validators import (
    validate_winner_count,
    validate_prize,
    validate_duration,
    format_duration,
    format_timestamp,
    MIN_WINNER_COUNT,
    MAX_WINNER_COUNT,
    MIN_DURATION_SECONDS,
    MAX_DURATION_SECONDS,
)


class TestValidateWinnerCount:
    """Tests for validate_winner_count function."""

    def test_valid_winner_count(self):
        """Test valid winner counts.

        Verifies that winner counts within the valid range (1, 5, and
        MAX_WINNER_COUNT) return True with an empty error message.
        """
        valid, error = validate_winner_count(1)
        assert valid is True
        assert error == ""

        valid, error = validate_winner_count(5)
        assert valid is True
        assert error == ""

        valid, error = validate_winner_count(MAX_WINNER_COUNT)
        assert valid is True
        assert error == ""

    def test_winner_count_too_low(self):
        """Test winner count below minimum.

        Verifies that a winner count of 0 returns False and an error
        message containing the minimum allowed count.
        """
        valid, error = validate_winner_count(0)
        assert valid is False
        assert str(MIN_WINNER_COUNT) in error

    def test_winner_count_too_high(self):
        """Test winner count above maximum.

        Verifies that a winner count exceeding MAX_WINNER_COUNT returns
        False and an error message containing the maximum allowed count.
        """
        valid, error = validate_winner_count(MAX_WINNER_COUNT + 1)
        assert valid is False
        assert str(MAX_WINNER_COUNT) in error


class TestValidatePrize:
    """Tests for validate_prize function."""

    def test_valid_prize(self):
        """Test valid prize descriptions.

        Verifies that typical prize descriptions like "Steam Game Key"
        and "$100 Gift Card" return True with an empty error message.
        """
        valid, error = validate_prize("Steam Game Key")
        assert valid is True
        assert error == ""

        valid, error = validate_prize("$100 Gift Card")
        assert valid is True
        assert error == ""

    def test_empty_prize(self):
        """Test empty prize description.

        Verifies that empty strings and whitespace-only strings return
        False with an error message containing "empty".
        """
        valid, error = validate_prize("")
        assert valid is False
        assert "empty" in error.lower()

        valid, error = validate_prize("   ")
        assert valid is False
        assert "empty" in error.lower()

    def test_prize_too_long(self):
        """Test prize description exceeding maximum length.

        Verifies that a 300-character prize description returns False
        with an error message referencing the 256-character limit.
        """
        long_prize = "x" * 300
        valid, error = validate_prize(long_prize)
        assert valid is False
        assert "256" in error


class TestValidateDuration:
    """Tests for validate_duration function."""

    def test_valid_duration(self):
        """Test valid durations.

        Verifies that durations of 1 minute (60s), 1 hour (3600s), and
        1 day (86400s) all return True with an empty error message.
        """
        valid, error = validate_duration(60)  # 1 minute
        assert valid is True
        assert error == ""

        valid, error = validate_duration(3600)  # 1 hour
        assert valid is True
        assert error == ""

        valid, error = validate_duration(86400)  # 1 day
        assert valid is True
        assert error == ""

    def test_duration_too_short(self):
        """Test duration below minimum.

        Verifies that a duration one second below MIN_DURATION_SECONDS
        returns False with an error containing the minimum value.
        """
        valid, error = validate_duration(MIN_DURATION_SECONDS - 1)
        assert valid is False
        assert str(MIN_DURATION_SECONDS) in error

    def test_duration_too_long(self):
        """Test duration above maximum.

        Verifies that a duration exceeding MAX_DURATION_SECONDS returns
        False with an error referencing the 30-day limit.
        """
        valid, error = validate_duration(MAX_DURATION_SECONDS + 1)
        assert valid is False
        assert "30" in error  # 30 days


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_format_seconds(self):
        """Test formatting seconds.

        Verifies that durations under 60 seconds are formatted as
        singular or plural seconds (e.g., "1 second", "30 seconds").
        """
        assert format_duration(1) == "1 second"
        assert format_duration(30) == "30 seconds"
        assert format_duration(59) == "59 seconds"

    def test_format_minutes(self):
        """Test formatting minutes.

        Verifies that durations of exact minutes are formatted as
        singular or plural minutes (e.g., "1 minute", "5 minutes").
        """
        assert format_duration(60) == "1 minute"
        assert format_duration(120) == "2 minutes"
        assert format_duration(300) == "5 minutes"

    def test_format_hours(self):
        """Test formatting hours.

        Verifies that hour durations are formatted correctly, including
        combined hour and minute formats (e.g., "1 hour 1 minute").
        """
        assert format_duration(3600) == "1 hour"
        assert format_duration(7200) == "2 hours"
        assert format_duration(3660) == "1 hour 1 minute"
        assert format_duration(7320) == "2 hours 2 minutes"

    def test_format_days(self):
        """Test formatting days.

        Verifies that day durations are formatted correctly, including
        combined day and hour formats (e.g., "1 day 1 hour").
        """
        assert format_duration(86400) == "1 day"
        assert format_duration(172800) == "2 days"
        assert format_duration(90000) == "1 day 1 hour"


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_format_ended(self):
        """Test formatting when time is up.

        Verifies that zero or negative timestamps return "Ended" to
        indicate the giveaway has concluded.
        """
        assert format_timestamp(0) == "Ended"
        assert format_timestamp(-100) == "Ended"

    def test_format_remaining(self):
        """Test formatting remaining time.

        Verifies that positive timestamps are formatted to show
        remaining time with appropriate units (minutes, hours).
        """
        assert "minute" in format_timestamp(120)
        assert "hour" in format_timestamp(3600)
