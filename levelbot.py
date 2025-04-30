#!/usr/bin/env python3
"""Main entry point for the Discord xp bot.
Integrates all components and handles Discord events.
"""

import asyncio
import random
import string

import discord
from discord.ext import bridge

import db
from config import TOKEN, TRACKED_GUILD
from game import GameState
from utils import logger

# Bot setup
bot = bridge.Bot(
    allowed_mentions=discord.AllowedMentions(
        everyone=False, users=False, roles=False, replied_user=True
    ),
    command_prefix="!",
    intents=discord.Intents.none()
    | discord.Intents.message_content
    | discord.Intents.guilds
    | discord.Intents.guild_messages,
)

lowercase_letters = set(string.ascii_lowercase)
IGNORE_CATEGORIES = {
    "776214031782379560",  # Text games
    "812135020109889536",  # Info announcements
    "749994585648005210",  # Bot & Logs
    "411554086346031105",  # Restricted Access
}
IGNORE_CHANNELS = {
    "1166541781563871312",
    "1351172404331937902",
    "1202081495469002882",
}
IGNORE_CHANNEL_NAMES = {
    "announcements",
    "polls",
    "quotes",
    "updates",
    "memes",
    "venting",
    "therapy",
    "vent",
    "ticket",
    "count",
    "members",
    "testing",
    "level",
    "roles",
    "rules",
}


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
        await bot.sync_commands()
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

    # Skip threads
    if not isinstance(message.channel, discord.TextChannel):
        return

    # Skip meaningless messages
    if len(set(message.clean_content.lower()).intersection(lowercase_letters)) <= 1:
        return

    try:
        msg = await game_state.on_message(message.author.id)
        if msg is None:
            return
        if (
            message.channel.category_id in IGNORE_CATEGORIES
            or message.channel.id in IGNORE_CHANNELS
        ):
            logger.info("Silence message in %s", message.channel.name)
            return

        for n in IGNORE_CHANNEL_NAMES:
            if n in message.channel.name.lower():
                logger.info("Silence message in %s", message.channel.name)
                return

        emoji = random.choice(("🎉", "<:PanParty:1139976695684796527>", "🎊", "🚀)"))
        m = await message.reply(
            f"## {message.author.display_name} leveled up! {emoji}\n{msg}"
        )
        print(m)
        await asyncio.sleep(100)
        m.delete()

    except Exception as e:
        logger.exception(f"Error processing message: {e}")


@bot.bridge_command(
    description="Exclude user from the game.", guild_ids=[TRACKED_GUILD]
)
async def exclude(ctx) -> None:
    """Slash command to exclude from game.

    Args:
        ctx: Command context

    """
    await ctx.respond(game_state.exclude_user(ctx.user.id))


@bot.bridge_command(description="Clears all user xp data.", guild_ids=[TRACKED_GUILD])
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


@bot.bridge_command(description="Shows user level and xp.", guild_ids=[TRACKED_GUILD])
@discord.option("user", type=discord.SlashCommandOptionType.user, required=False)
async def xp(ctx: bridge.BridgeContext, user: discord.User | None) -> None:
    """Slash command to view a user's level and xp.

    Args:
        ctx: Command context
        user: User to view inventory for

    """
    if user is None:
        user = ctx.author

    try:
        await ctx.respond(await xp_info(user))
    except Exception:
        logger.exception("Error getting xp.")
        await ctx.respond("Error getting xp.")


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


@bot.bridge_command(description="Shows the leaderboard.", guild_ids=[TRACKED_GUILD])
async def leaderboard(ctx: bridge.BridgeContext) -> None:
    """View the leaderboard!

    Args:
        ctx: Command context

    """
    await ctx.respond(await game_state.leaderboard_info())


if __name__ == "__main__":
    try:
        logger.info("Starting bot")
        game_state = GameState()
        bot.run(TOKEN)
        game_state.exclude.save()
    except Exception as e:
        logger.critical(f"Fatal error starting bot: {e}")
