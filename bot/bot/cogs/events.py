# =============================================================
# OMEGA BOT — EVENTS COG
# Eternal River Sect
# Random elemental event scheduler
# Announces events in #announcements and updates DB
# =============================================================
from __future__ import annotations

import asyncio
import logging
import random
import time

import discord
from discord.ext import commands, tasks

from bot.database import db
from bot.data.fish_data import EVENTS

log = logging.getLogger(__name__)


class EventsCog(commands.Cog, name="Events"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._event_tasks: dict[str, asyncio.Task] = {}

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Resume event scheduling after bot restart."""
        for event_id in EVENTS:
            if event_id not in self._event_tasks:
                self._event_tasks[event_id] = asyncio.create_task(
                    self._event_loop(event_id)
                )
        log.info("Event scheduler started for %d event(s).", len(EVENTS))

    async def cog_unload(self) -> None:
        for task in self._event_tasks.values():
            task.cancel()

    # ── Event loop (one per event type) ──────────────────────────────────────

    async def _event_loop(self, event_id: str) -> None:
        event = EVENTS[event_id]
        while True:
            # Check if there's an active event for this fish
            active = await db.get_active_event(event["fish_id"])
            now    = time.time()

            if active and active["end_time"] > now:
                # Event is running — wait for it to end
                sleep_for = active["end_time"] - now + 1
                log.info("Event %s still running; sleeping %.0fs", event_id, sleep_for)
                await asyncio.sleep(sleep_for)
                # Post end message
                await self._announce_event_end(event)
                await db.end_event(event["fish_id"])

            else:
                # Schedule next event
                cooldown_row = await db.get_event_cooldown(event["fish_id"])
                last_end     = cooldown_row["last_event_end"] if cooldown_row else 0
                gap          = random.uniform(event["min_gap"], event["max_gap"])
                next_start   = last_end + gap

                if next_start > now:
                    sleep_for = next_start - now
                    log.info("Event %s scheduled in %.0fs", event_id, sleep_for)
                    await asyncio.sleep(sleep_for)

                # Start event
                end_time = time.time() + event["duration"]
                await db.start_event(event["fish_id"], end_time)
                await self._announce_event_start(event, end_time)

                log.info("Event %s started; duration %ds", event_id, event["duration"])
                await asyncio.sleep(event["duration"])

                # End event
                await db.end_event(event["fish_id"])
                await self._announce_event_end(event)

    # ── Announcement helpers ──────────────────────────────────────────────────

    async def _get_announce_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        for ch in guild.text_channels:
            row = await db.get_channel_config(ch.id)
            if row and row["channel_type"] == "heavenly_announce":
                return ch
        return None

    async def _announce_event_start(self, event: dict, end_time: float) -> None:
        for guild in self.bot.guilds:
            ch = await self._get_announce_channel(guild)
            if ch:
                embed = discord.Embed(
                    title=f"🌩️ Event: {event['name']}",
                    description=event["message"],
                    color=0xFF4500,
                )
                embed.add_field(
                    name="Ends",
                    value=f"<t:{int(end_time)}:R>  (<t:{int(end_time)}:T>)",
                    inline=False,
                )
                embed.set_footer(text="Fish quickly — this window won't last!")
                try:
                    await ch.send(embed=embed)
                except discord.Forbidden:
                    pass

    async def _announce_event_end(self, event: dict) -> None:
        for guild in self.bot.guilds:
            ch = await self._get_announce_channel(guild)
            if ch:
                embed = discord.Embed(
                    title=f"🌤️ Event Ended: {event['name']}",
                    description=event["end_message"],
                    color=0x7F8C8D,
                )
                try:
                    await ch.send(embed=embed)
                except discord.Forbidden:
                    pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventsCog(bot))
