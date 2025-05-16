"""Database operations for the Discord math catch bot.
Handles xp management and database interactions.
"""

import aiosqlite

from config import DATABASE
from utils import logger


async def create_table() -> None:
    """Creates the user_xp table if it doesn't exist."""
    try:
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_xp (
                    User INTEGER,
                    xp INTEGER,
                    PRIMARY KEY (User)
                )
                """,
            )
            await db.commit()
        logger.info(f"Successfully created/verified user_xp table in {DATABASE}")
    except Exception as e:
        logger.error(f"Error creating database table: {e}")
        raise


async def clear_xp(user: int) -> bool:
    """Removes all data about user from user_xp.

    Args:
        user: User ID

    Returns:
        Whether the user was removed.

    """
    try:
        async with (
            aiosqlite.connect(DATABASE) as db,
            db.execute(
                "delete from user_xp where User = ?",
                (user,),
            ) as cursor,
        ):
            await db.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error adding item to inventory: {e}")
        raise


async def add_xp(user: int, quantity: int) -> tuple[int, int]:
    """Adds xp to a user or increases if it already exists.

    Args:
        user: User ID
        quantity: xp to add

    """
    try:
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute(
                """
                INSERT INTO user_xp (User, xp)
                VALUES (?, ?)
                ON CONFLICT(User) DO UPDATE SET xp = xp + excluded.xp
                returning xp
                """,
                (user, quantity),
            ) as cursor:
                row = await cursor.fetchone()
                xp = row[0]
            await db.commit()
            logger.debug(f"Added {quantity} xp to user {user}")
            return xp - quantity, xp
    except Exception as e:
        logger.error(f"Error adding item to inventory: {e}")
        raise


async def get_xp(user: int) -> int:
    """Shows xp for user.

    Args:
        user: User ID

    """
    try:
        async with (
            aiosqlite.connect(DATABASE) as db,
            db.execute(
                "SELECT xp FROM user_xp WHERE User = ?",
                (user,),
            ) as cursor,
        ):
            return (await cursor.fetchall())[0][0]
    except Exception as e:
        logger.error(f"Error reading xp from user: {e}")
        raise


async def leaderboard(limit: int = 10) -> dict[str, int]:
    """Lists top 10 by xp.

    Returns:
        Dictionary mapping user IDs to quantities

    """
    try:
        async with (
            aiosqlite.connect(DATABASE) as db,
            db.execute(
                "SELECT User, xp FROM user_xp order by xp desc limit ?",
                (limit,),
            ) as cursor,
        ):
            rows = await cursor.fetchall()
            result = {row[0]: row[1] for row in rows}
        logger.debug(f"Retrieved {len(result)} results.")
        return result
    except Exception as e:
        logger.error(f"Error listing items from inventory: {e}")
        raise
