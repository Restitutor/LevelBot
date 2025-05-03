"""Handles exclusion list."""

import pathlib
import time

import db
from config import MINUTE_TIME
from utils import logger


class PersistentExclude:
    path = pathlib.Path("excluded_users.txt")
    values: set[int]

    def __init__(self) -> None:
        self.values = self.load()

    def load(self) -> set[int]:
        try:
            return {int(i) for i in self.path.read_text().split("\n") if i}
        except Exception:
            logger.exception("Could not read %s", self.path)

            # Initialize
            self.values = set()
            self.save()
            return set()

    def save(self) -> None:
        self.path.write_text("\n".join(sorted(str(i) for i in self.values)))

    def toggle(self, user: int) -> str:
        if user in self.values:
            self.values.remove(user)
            msg = "You are no longer excluded."
        else:
            self.values.add(user)
            msg = "You are now excluded."

        self.save()
        return msg


class GameState:
    """Encapsulates game state and mechanics."""

    def __init__(self) -> None:
        self.exclude = PersistentExclude()
        self.last_msg: dict[int, int] = {}
        logger.info("Initialized game state.")

    def can_xp(self, user_id: int) -> bool:
        """Checks if a user can get xp.

        Args:
            user_id: Discord user ID

        Returns:
            True if the user can get xp, False otherwise

        """
        if user_id in self.exclude.values:
            return False

        if self.last_msg.get(user_id, 0) < time.time() - MINUTE_TIME * 60:
            self.last_msg[user_id] = round(time.time())
            return True

        return False

    async def add_xp(self, user_id: int, quantity: int = 1) -> tuple[int, int]:
        """Gives user more xp.

        Args:
            user_id: User snowflake
            quantity: Amount to give

        Returns:
            Int of new xp

        """
        return await db.add_xp(user_id, quantity)
