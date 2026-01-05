"""Configuration management for the Giveaway Bot."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Bot configuration settings."""

    # Discord bot token
    token: str

    # Database path
    database_path: Path

    # Logging level
    log_level: str

    # Task intervals (in seconds)
    giveaway_check_interval: int = 30

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables.

        Returns:
            Config: A new Config instance populated with values from
                environment variables.

        Raises:
            ValueError: If DISCORD_TOKEN environment variable is not set.
        """
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN environment variable is required")

        database_path = Path(os.getenv("DATABASE_PATH", "data/giveaway.db"))
        log_level = os.getenv("LOG_LEVEL", "INFO")

        return cls(
            token=token,
            database_path=database_path,
            log_level=log_level,
        )

    def ensure_data_directory(self) -> None:
        """Ensure the data directory exists.

        Creates the parent directory of the database path if it does not
        already exist, including any necessary intermediate directories.
        """
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """Get the bot configuration.

    Returns:
        Config: The bot configuration loaded from environment variables.

    Raises:
        ValueError: If required environment variables are not set.
    """
    return Config.from_env()
