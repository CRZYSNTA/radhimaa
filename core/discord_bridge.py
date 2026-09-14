"""
JARVIS V3.0 - Discord Remote Command Bridge
Enables secure remote interaction with JARVIS through a private Discord bot channel.
Routes user messages through core/router.py and returns formatted responses.
"""

from __future__ import annotations

import os
import asyncio
import logging
import threading
from typing import Optional

import config
from core.router import route_input

logger = logging.getLogger("JARVIS.Core.Discord")

_BOT_THREAD: Optional[threading.Thread] = None
_RUNNING = False


def _run_discord_bot(token: str, allowed_channel_ids: Optional[list] = None):
    try:
        import discord
        from discord.ext import commands

        intents = discord.Intents.default()
        intents.message_content = True

        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready():
            logger.info(f"[Discord Bridge] Logged in as {bot.user.name} ({bot.user.id})")
            print(f"[Discord Bridge] Connected successfully as {bot.user.name}")

        @bot.event
        async def on_message(message: discord.Message):
            if message.author == bot.user:
                return

            if allowed_channel_ids and message.channel.id not in allowed_channel_ids:
                return

            content = message.content.strip()
            if not content:
                return

            # Show typing while JARVIS processes
            async with message.channel.typing():
                try:
                    # Route directly through JARVIS core router
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(None, route_input, content)

                    # Discord message chunking (max 2000 chars)
                    if len(response) <= 1950:
                        await message.reply(response)
                    else:
                        chunks = [response[i:i + 1900] for i in range(0, len(response), 1900)]
                        for chunk in chunks:
                            await message.reply(chunk)
                except Exception as e:
                    await message.reply(f"JARVIS Error: {e}")

        bot.run(token)

    except ImportError:
        logger.warning("[Discord Bridge] 'discord.py' is not installed. Install with 'pip install discord.py'.")
    except Exception as e:
        logger.error(f"[Discord Bridge Error]: {e}")


def start_discord_bridge(token: Optional[str] = None, allowed_channel_ids: Optional[list] = None) -> str:
    """
    Starts the Discord bot bridge in a background daemon thread.
    """
    global _BOT_THREAD, _RUNNING

    bot_token = token or os.environ.get("DISCORD_BOT_TOKEN") or getattr(config, "DISCORD_BOT_TOKEN", None)
    if not bot_token:
        return "Discord bot token not configured. Set DISCORD_BOT_TOKEN in environment or config, sir."

    if _RUNNING:
        return "Discord bridge is already running, sir."

    _RUNNING = True
    _BOT_THREAD = threading.Thread(
        target=_run_discord_bot,
        args=(bot_token, allowed_channel_ids),
        daemon=True,
        name="JarvisDiscordBridge"
    )
    _BOT_THREAD.start()

    return "Discord remote bridge initialized and listening for commands, sir."
