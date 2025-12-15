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
        """Test valid winner counts."""
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
        """Test winner count below minimum."""
        valid, error = validate_winner_count(0)
        assert valid is False
        assert str(MIN_WINNER_COUNT) in error

    def test_winner_count_too_high(self):
        """Test winner count above maximum."""
        valid, error = validate_winner_count(MAX_WINNER_COUNT + 1)
        assert valid is False
        assert str(MAX_WINNER_COUNT) in error


class TestValidatePrize:
    """Tests for validate_prize function."""

    def test_valid_prize(self):
        """Test valid prize descriptions."""
        valid, error = validate_prize("Steam Game Key")
        assert valid is True
        assert error == ""

        valid, error = validate_prize("$100 Gift Card")
        assert valid is True
        assert error == ""

    def test_empty_prize(self):
        """Test empty prize description."""
        valid, error = validate_prize("")
        assert valid is False
        assert "empty" in error.lower()

        valid, error = validate_prize("   ")
        assert valid is False
        assert "empty" in error.lower()

    def test_prize_too_long(self):
        """Test prize description exceeding maximum length."""
        long_prize = "x" * 300
        valid, error = validate_prize(long_prize)
        assert valid is False
        assert "256" in error


class TestValidateDuration:
    """Tests for validate_duration function."""

    def test_valid_duration(self):
        """Test valid durations."""
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
        """Test duration below minimum."""
        valid, error = validate_duration(MIN_DURATION_SECONDS - 1)
        assert valid is False
        assert str(MIN_DURATION_SECONDS) in error

    def test_duration_too_long(self):
        """Test duration above maximum."""
        valid, error = validate_duration(MAX_DURATION_SECONDS + 1)
        assert valid is False
        assert "30" in error  # 30 days


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_format_seconds(self):
        """Test formatting seconds."""
        assert format_duration(1) == "1 second"
        assert format_duration(30) == "30 seconds"
        assert format_duration(59) == "59 seconds"

    def test_format_minutes(self):
        """Test formatting minutes."""
        assert format_duration(60) == "1 minute"
        assert format_duration(120) == "2 minutes"
        assert format_duration(300) == "5 minutes"

    def test_format_hours(self):
        """Test formatting hours."""
        assert format_duration(3600) == "1 hour"
        assert format_duration(7200) == "2 hours"
        assert format_duration(3660) == "1 hour 1 minute"
        assert format_duration(7320) == "2 hours 2 minutes"

    def test_format_days(self):
        """Test formatting days."""
        assert format_duration(86400) == "1 day"
        assert format_duration(172800) == "2 days"
        assert format_duration(90000) == "1 day 1 hour"


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_format_ended(self):
        """Test formatting when time is up."""
        assert format_timestamp(0) == "Ended"
        assert format_timestamp(-100) == "Ended"

    def test_format_remaining(self):
        """Test formatting remaining time."""
        assert "minute" in format_timestamp(120)
        assert "hour" in format_timestamp(3600)
