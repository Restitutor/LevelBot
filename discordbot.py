#!/usr/bin/env python3
"""Main entry point for the Discord xp bot.
Integrates all components and handles Discord events.
"""

import math
import string

import discord

import db
from config import TOKEN
from game import GameState
from utils import logger

# Bot setup
bot = discord.Bot(
    allowed_mentions=discord.AllowedMentions.none(),
    intents=discord.Intents.none()
    | discord.Intents.message_content
    | discord.Intents.guilds
    | discord.Intents.guild_messages,
)

lowercase_letters = set(string.ascii_lowercase)


def get_level(xp: int) -> int:
    return math.floor(max(xp, 0) ** (1 / 3))


@bot.event
async def on_ready() -> None:
    """Called when the bot is ready.
    Initializes database.
    """
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

    try:
        # Initialize game state and database
        await db.create_table()

        # Start random drop task
        await bot.wait_until_ready()
        logger.info("Bot is fully initialized and ready")
    except Exception as e:
        logger.error(f"Error during initialization: {e}")


@bot.listen("on_message")
async def on_text_message(message) -> None:
    """Processes incoming messages.

    Args:
        message: Discord message

    """
    # Ignore bot messages and DMs
    if message.author.bot or not isinstance(message.author, discord.member.Member):
        return

    # Skip meaningless messages
    if len(set(message.clean_content.lower()).intersection(lowercase_letters)) <= 1:
        return

    try:
        user = message.author.id
        if game_state.can_xp(user):
            await game_state.add_xp(user)

    except Exception as e:
        logger.error(f"Error processing message: {e}")


@bot.command()
async def exclude(ctx) -> None:
    """Slash command to exclude from game.

    Args:
        ctx: Command context

    """
    try:
        await ctx.respond(game_state.exclude.toggle(ctx.user.id))
    except Exception as e:
        logger.error(f"Error executing inventory command: {e}")
        await ctx.respond("An error occurred while retrieving the xp.")


@bot.command()
async def xp(ctx, user: discord.Option(discord.SlashCommandOptionType.user)) -> None:
    """Slash command to view a user's level and xp.

    Args:
        ctx: Command context
        user: User to view inventory for

    """
    try:
        if user.bot:
            await ctx.respond("That's a bot.")
        elif user.id in game_state.exclude.values:
            await ctx.respond(f"{user.display_name} opted out of the game.")
        else:
            xp = await db.get_xp(user.id)
            level = get_level(xp)
            await ctx.respond(f"<@{user.id}> is level {level} ({xp} xp).")
    except Exception as e:
        logger.error(f"Error executing inventory command: {e}")
        await ctx.respond("An error occurred while retrieving the xp.")


@bot.command()
async def leaderboard(ctx) -> None:
    """View the leaderboard!

    Args:
        ctx: Command context

    """
    try:
        result = await db.leaderboard()
        output = ""
        for user, xp in result.items():
            if user not in game_state.exclude.values:
                level = get_xp(xp)
                output += f"<@{user}>: {level}\n"

        if output:
            await ctx.respond(output.strip())
        else:
            await ctx.respond("No users found!")
    except Exception as e:
        logger.error(f"Error executing inventory command: {e}")
        await ctx.respond("An error occurred while retrieving the xp.")


if __name__ == "__main__":
    try:
        logger.info("Starting bot")
        game_state = GameState()
        bot.run(TOKEN)
        game_state.exclude.save()
    except Exception as e:
        logger.critical(f"Fatal error starting bot: {e}")
