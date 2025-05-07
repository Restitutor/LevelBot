"""Handles exclusion list."""

import math
import pathlib
import time

import db
from config import MINUTE_TIME
from utils import logger


def get_raw_level(xp: int) -> int:
    return max(xp, 0) ** (1 / 2.5)


def get_level(xp: int) -> int:
    return math.floor(get_raw_level(xp))


def to_next_level(xp: int) -> int:
    next = math.ceil(get_raw_level(xp) + 1e-10)
    return round(next**2.5 - xp)


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

    async def xp_status(self, user: int) -> str:
        xp = await db.get_xp(user)
        level = get_level(xp)
        next = to_next_level(xp)
        return f"<@{user}> is level {level} ({xp} xp). Get {next} more xp to get level {level + 1}."

    async def on_message(self, user: int) -> str | None:
        if self.can_xp(user):
            old_xp, xp = await self.add_xp(user)
            level = get_level(xp)
            if level != get_level(old_xp):
                return f"You are now level {level}!"
        return None

    def exclude_user(self, user: int) -> str:
        try:
            return self.exclude.toggle(user)
        except Exception as e:
            logger.error(f"Error executing inventory command: {e}")
            return "An error occurred while retrieving the xp."

    async def get_leaderboard(self) -> str:
        result = await db.leaderboard()
        output = ""
        pos = 0
        for user, xp in result.items():
            if user not in self.exclude.values:
                pos += 1
                level = get_level(xp)
                output += f"**#{pos}** <@{user}>: {level}\n"

        if output:
            return output.strip()
        return "No users found!"

    async def leaderboard_info(self) -> str:
        try:
            return await self.get_leaderboard()
        except Exception as e:
            logger.error(f"Error executing inventory command: {e}")
            return "An error occurred while retrieving the xp."
