"""Storage service for database operations."""

import aiosqlite
import logging
from pathlib import Path
from typing import List, Optional

from src.models.giveaway import Giveaway
from src.models.guild_config import GuildConfig

logger = logging.getLogger(__name__)

class StorageService:
    """Handles all database operations for giveaways and guild configurations."""

    def __init__(self, database_path: Path):
        """Initialize the storage service.

        Args:
            database_path: Path to the SQLite database file.
        """
        self.database_path = database_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initialize the database connection and create tables.

        Creates the database directory if it doesn't exist, establishes
        the connection, and creates all required tables.

        Raises:
            aiosqlite.Error: If database connection fails.
        """
        # Ensure the directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.database_path)
        self._connection.row_factory = aiosqlite.Row

        await self._create_tables()

    async def close(self) -> None:
        """Close the database connection.

        Safely closes the database connection if one exists.
        Sets the connection to None after closing.
        """
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist.

        Creates the giveaways, entries, winners, and guild_config tables
        along with necessary indexes.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        await self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER,
                prize TEXT NOT NULL,
                winner_count INTEGER DEFAULT 1,
                required_role_id INTEGER,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_start TIMESTAMP,
                ends_at TIMESTAMP NOT NULL,
                ended BOOLEAN DEFAULT FALSE,
                cancelled BOOLEAN DEFAULT FALSE
            );

            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giveaway_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (giveaway_id) REFERENCES giveaways(id),
                UNIQUE(giveaway_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giveaway_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                notified BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (giveaway_id) REFERENCES giveaways(id)
            );

            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                admin_role_ids TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_giveaways_guild ON giveaways(guild_id);
            CREATE INDEX IF NOT EXISTS idx_giveaways_active ON giveaways(ended, cancelled);
            CREATE INDEX IF NOT EXISTS idx_entries_giveaway ON entries(giveaway_id);
            CREATE INDEX IF NOT EXISTS idx_entries_user ON entries(user_id);
        """
        )
        await self._connection.commit()

    # Giveaway operations

    async def create_giveaway(self, giveaway: Giveaway) -> Giveaway:
        """Create a new giveaway and return it with the assigned ID.

        Args:
            giveaway: The Giveaway object to persist.

        Returns:
            The same Giveaway object with its ID populated from the database.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        cursor = await self._connection.execute(
            """
            INSERT INTO giveaways
            (guild_id, channel_id, message_id, prize, winner_count, required_role_id,
             created_by, created_at, scheduled_start, ends_at, ended, cancelled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                giveaway.guild_id,
                giveaway.channel_id,
                giveaway.message_id,
                giveaway.prize,
                giveaway.winner_count,
                giveaway.required_role_id,
                giveaway.created_by,
                giveaway.created_at.isoformat(),
                (
                    giveaway.scheduled_start.isoformat()
                    if giveaway.scheduled_start
                    else None
                ),
                giveaway.ends_at.isoformat(),
                giveaway.ended,
                giveaway.cancelled,
            ),
        )
        await self._connection.commit()

        giveaway.id = cursor.lastrowid
        return giveaway

    async def get_giveaway(self, giveaway_id: int) -> Optional[Giveaway]:
        """Get a giveaway by ID.

        Args:
            giveaway_id: The unique identifier of the giveaway.

        Returns:
            The Giveaway object with entries and winners populated,
            or None if not found.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            cursor = await self._connection.execute(
                "SELECT * FROM giveaways WHERE id = ?", (giveaway_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            giveaway = Giveaway.from_dict(dict(row))
            giveaway.entries = await self.get_entries(giveaway_id)
            giveaway.winners = await self.get_winners(giveaway_id)

            return giveaway
        except aiosqlite.Error as e:
            logger.error(f"Database error in get_giveaway: {e}")
            return None

    async def get_giveaway_by_message(self, message_id: int) -> Optional[Giveaway]:
        """Get a giveaway by its Discord message ID.

        Args:
            message_id: The Discord message ID associated with the giveaway.

        Returns:
            The Giveaway object with entries and winners populated,
            or None if not found.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            cursor = await self._connection.execute(
                "SELECT * FROM giveaways WHERE message_id = ?", (message_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            giveaway = Giveaway.from_dict(dict(row))
            giveaway.entries = await self.get_entries(giveaway.id)
            giveaway.winners = await self.get_winners(giveaway.id)

            return giveaway
        except aiosqlite.Error as e:
            logger.error(f"Database error in get_giveaway_by_message: {e}")
            return None

    async def get_active_giveaways(
        self, guild_id: Optional[int] = None
    ) -> List[Giveaway]:
        """Get all active giveaways, optionally filtered by guild.

        Args:
            guild_id: Optional Discord guild ID to filter by.

        Returns:
            List of active Giveaway objects with entries populated.
            Returns empty list on database error.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            if guild_id:
                cursor = await self._connection.execute(
                    "SELECT * FROM giveaways WHERE guild_id = ? AND ended = FALSE AND cancelled = FALSE",
                    (guild_id,),
                )
            else:
                cursor = await self._connection.execute(
                    "SELECT * FROM giveaways WHERE ended = FALSE AND cancelled = FALSE"
                )

            rows = await cursor.fetchall()
            giveaways = []

            for row in rows:
                giveaway = Giveaway.from_dict(dict(row))
                giveaway.entries = await self.get_entries(giveaway.id)
                giveaways.append(giveaway)

            return giveaways
        except aiosqlite.Error as e:
            logger.error(f"Database error in get_active_giveaways: {e}")
            return []

    async def get_scheduled_giveaways(self) -> List[Giveaway]:
        """Get all scheduled giveaways that haven't started yet.

        Returns:
            List of Giveaway objects that have a scheduled_start time,
            are not ended, and are not cancelled.
            Returns empty list on database error.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            cursor = await self._connection.execute(
                """
                SELECT * FROM giveaways
                WHERE scheduled_start IS NOT NULL
                AND ended = FALSE
                AND cancelled = FALSE
                """
            )
            rows = await cursor.fetchall()

            return [Giveaway.from_dict(dict(row)) for row in rows]
        except aiosqlite.Error as e:
            logger.error(f"Database error in get_scheduled_giveaways: {e}")
            return []

    async def update_giveaway(self, giveaway: Giveaway) -> None:
        """Update an existing giveaway.

        Args:
            giveaway: The Giveaway object with updated values.

        Raises:
            RuntimeError: If database is not initialized.
            aiosqlite.Error: If database update fails.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            await self._connection.execute(
                """
                UPDATE giveaways SET
                    message_id = ?,
                    prize = ?,
                    winner_count = ?,
                    required_role_id = ?,
                    scheduled_start = ?,
                    ends_at = ?,
                    ended = ?,
                    cancelled = ?
                WHERE id = ?
                """,
                (
                    giveaway.message_id,
                    giveaway.prize,
                    giveaway.winner_count,
                    giveaway.required_role_id,
                    (
                        giveaway.scheduled_start.isoformat()
                        if giveaway.scheduled_start
                        else None
                    ),
                    giveaway.ends_at.isoformat(),
                    giveaway.ended,
                    giveaway.cancelled,
                    giveaway.id,
                ),
            )
            await self._connection.commit()
        except aiosqlite.Error as e:
            logger.error(f"Database error in update_giveaway: {e}")
            raise

    async def delete_giveaway(self, giveaway_id: int) -> None:
        """Delete a giveaway and all related data.

        Removes the giveaway along with all associated entries and winners.

        Args:
            giveaway_id: The unique identifier of the giveaway to delete.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        await self._connection.execute(
            "DELETE FROM entries WHERE giveaway_id = ?", (giveaway_id,)
        )
        await self._connection.execute(
            "DELETE FROM winners WHERE giveaway_id = ?", (giveaway_id,)
        )
        await self._connection.execute(
            "DELETE FROM giveaways WHERE id = ?", (giveaway_id,)
        )
        await self._connection.commit()

    # Entry operations

    async def add_entry(self, giveaway_id: int, user_id: int) -> bool:
        """Add an entry to a giveaway.

        Args:
            giveaway_id: The unique identifier of the giveaway.
            user_id: The Discord user ID entering the giveaway.

        Returns:
            True if the entry was added, False if user already entered.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            await self._connection.execute(
                "INSERT INTO entries (giveaway_id, user_id) VALUES (?, ?)",
                (giveaway_id, user_id),
            )
            await self._connection.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def remove_entry(self, giveaway_id: int, user_id: int) -> bool:
        """Remove an entry from a giveaway.

        Args:
            giveaway_id: The unique identifier of the giveaway.
            user_id: The Discord user ID to remove from the giveaway.

        Returns:
            True if the entry was removed, False if entry didn't exist
            or on database error.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            cursor = await self._connection.execute(
                "DELETE FROM entries WHERE giveaway_id = ? AND user_id = ?",
                (giveaway_id, user_id),
            )
            await self._connection.commit()
            return cursor.rowcount > 0
        except aiosqlite.Error as e:
            logger.error(f"Database error in remove_entry: {e}")
            return False

    async def get_entries(self, giveaway_id: Optional[int]) -> List[int]:
        """Get all user IDs who entered a giveaway.

        Args:
            giveaway_id: The unique identifier of the giveaway.

        Returns:
            List of Discord user IDs who entered the giveaway.
            Returns empty list if giveaway_id is None or on error.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        if giveaway_id is None:
            return []

        try:
            cursor = await self._connection.execute(
                "SELECT user_id FROM entries WHERE giveaway_id = ?", (giveaway_id,)
            )
            rows = await cursor.fetchall()
            return [row["user_id"] for row in rows]
        except aiosqlite.Error as e:
            logger.error(f"Database error in get_entries: {e}")
            return []

    async def has_entered(self, giveaway_id: int, user_id: int) -> bool:
        """Check if a user has entered a giveaway.

        Args:
            giveaway_id: The unique identifier of the giveaway.
            user_id: The Discord user ID to check.

        Returns:
            True if the user has entered, False otherwise or on error.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            cursor = await self._connection.execute(
                "SELECT 1 FROM entries WHERE giveaway_id = ? AND user_id = ?",
                (giveaway_id, user_id),
            )
            return await cursor.fetchone() is not None
        except aiosqlite.Error as e:
            logger.error(f"Database error in has_entered: {e}")
            return False

    async def get_user_entries(self, guild_id: int, user_id: int) -> List[Giveaway]:
        """Get all active giveaways a user has entered in a guild.

        Args:
            guild_id: The Discord guild ID to filter by.
            user_id: The Discord user ID to look up entries for.

        Returns:
            List of active Giveaway objects the user has entered.
            Returns empty list on database error.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            cursor = await self._connection.execute(
                """
                SELECT g.* FROM giveaways g
                INNER JOIN entries e ON g.id = e.giveaway_id
                WHERE g.guild_id = ? AND e.user_id = ? AND g.ended = FALSE AND g.cancelled = FALSE
                """,
                (guild_id, user_id),
            )
            rows = await cursor.fetchall()
            return [Giveaway.from_dict(dict(row)) for row in rows]
        except aiosqlite.Error as e:
            logger.error(f"Database error in get_user_entries: {e}")
            return []

    # Winner operations

    async def add_winner(self, giveaway_id: int, user_id: int) -> None:
        """Add a winner to a giveaway.

        Args:
            giveaway_id: The unique identifier of the giveaway.
            user_id: The Discord user ID of the winner.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        await self._connection.execute(
            "INSERT INTO winners (giveaway_id, user_id) VALUES (?, ?)",
            (giveaway_id, user_id),
        )
        await self._connection.commit()

    async def get_winners(self, giveaway_id: Optional[int]) -> List[int]:
        """Get all winner user IDs for a giveaway.

        Args:
            giveaway_id: The unique identifier of the giveaway.

        Returns:
            List of Discord user IDs who won the giveaway.
            Returns empty list if giveaway_id is None or on error.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        if giveaway_id is None:
            return []

        try:
            cursor = await self._connection.execute(
                "SELECT user_id FROM winners WHERE giveaway_id = ?", (giveaway_id,)
            )
            rows = await cursor.fetchall()
            return [row["user_id"] for row in rows]
        except aiosqlite.Error as e:
            logger.error(f"Database error in get_winners: {e}")
            return []

    async def clear_winners(self, giveaway_id: int) -> None:
        """Clear all winners for a giveaway (for rerolling).

        Args:
            giveaway_id: The unique identifier of the giveaway.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        await self._connection.execute(
            "DELETE FROM winners WHERE giveaway_id = ?", (giveaway_id,)
        )
        await self._connection.commit()

    # Guild config operations

    async def get_guild_config(self, guild_id: int) -> GuildConfig:
        """Get guild configuration, creating a default if it doesn't exist.

        Args:
            guild_id: The Discord guild ID to get configuration for.

        Returns:
            The GuildConfig object for the guild. Creates and returns
            a default configuration if one doesn't exist.

        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            cursor = await self._connection.execute(
                "SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)
            )
            row = await cursor.fetchone()

            if row:
                return GuildConfig.from_dict(dict(row))

            # Create default config
            config = GuildConfig.default(guild_id)
            await self.save_guild_config(config)
            return config
        except aiosqlite.Error as e:
            logger.error(f"Database error in get_guild_config: {e}")
            return GuildConfig.default(guild_id)

    async def save_guild_config(self, config: GuildConfig) -> None:
        """Save or update guild configuration.

        Args:
            config: The GuildConfig object to persist.

        Raises:
            RuntimeError: If database is not initialized.
            aiosqlite.Error: If database operation fails.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        try:
            await self._connection.execute(
                """
                INSERT OR REPLACE INTO guild_config (guild_id, admin_role_ids, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    config.guild_id,
                    config.to_dict()["admin_role_ids"],
                    config.created_at.isoformat(),
                ),
            )
            await self._connection.commit()
        except aiosqlite.Error as e:
            logger.error(f"Database error in save_guild_config: {e}")
            raise
