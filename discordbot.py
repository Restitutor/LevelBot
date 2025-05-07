#!/usr/bin/env python3
"""Main entry point for the Discord xp bot.
Integrates all components and handles Discord events.
"""

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

    if "!leaderboard" in message.clean_content:
        await message.reply(await game_state.leaderboard_info())
        return

    if "!xp" in message.clean_content:
        await message.reply(await xp_info(message.author))
        return

    try:
        msg = await game_state.on_message(message.author.id)
        if msg is not None:
            await message.reply(msg)

    except Exception as e:
        logger.exception(f"Error processing message: {e}")


@bot.command()
async def exclude(ctx) -> None:
    """Slash command to exclude from game.

    Args:
        ctx: Command context

    """
    await ctx.respond(game_state.exclude_user(ctx.user.id))


@bot.command()
async def clearxp(ctx) -> None:
    """Slash command to purge user xp.

    Args:
        ctx: Command context

    """
    try:
        xp = await db.get_xp(ctx.user.id)
        if xp is None:
            await ctx.respond("You had no xp.")
        else:
            await db.clear_xp(ctx.user.id)
            await ctx.respond(f"Cleared {xp} xp.")
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
    await ctx.respond(await xp_info(user))


async def xp_info(user: discord.User) -> str:
    try:
        if user.bot:
            return "That's a bot."
        if user.id in game_state.exclude.values:
            return f"{user.display_name} opted out of the game."
        return await game_state.xp_status(user.id)
    except Exception as e:
        logger.error(f"Error executing inventory command: {e}")
        return "An error occurred while retrieving the xp."


@bot.command()
async def leaderboard(ctx) -> None:
    """View the leaderboard!

    Args:
        ctx: Command context

    """
    await ctx.respond(await leaderboard_info())


if __name__ == "__main__":
    try:
        logger.info("Starting bot")
        game_state = GameState()
        bot.run(TOKEN)
        game_state.exclude.save()
    except Exception as e:
        logger.critical(f"Fatal error starting bot: {e}")
