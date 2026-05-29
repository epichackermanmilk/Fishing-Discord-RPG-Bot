# =============================================================
# OMEGA BOT — UNLOCKS COG
# Eternal River Sect
# =============================================================
"""
Restores hidden-channel permission overwrites on bot startup.

When the bot restarts, all in-memory Discord permission overwrites are
still stored on the channels (Discord persists them), so technically no
restoration is needed for channels that still exist. However, if an
admin ran /omega_setup and recreated the channels, the channel IDs
changed. This cog re-applies overwrites from the user_biome_unlocks
DB table so no player loses their hard-earned access.
"""
from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from bot.database import db

log = logging.getLogger(__name__)


class UnlocksCog(commands.Cog, name="Unlocks"):
    """Restores locked-channel access on bot startup."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Re-apply channel permission overwrites from DB after startup."""
        await asyncio.sleep(2)  # Brief delay so guilds are fully populated
        await self._restore_all_unlocks()

    async def _restore_all_unlocks(self) -> None:
        """
        Iterate every stored biome unlock and ensure the matching Discord
        channel has view_channel=True for that user.
        """
        rows = await db.get_all_users_with_biome_unlocks()
        if not rows:
            return

        log.info("Restoring %d channel unlock(s) from DB…", len(rows))
        restored = 0
        skipped  = 0

        for row in rows:
            user_id  = row["user_id"]
            biome_id = row["biome_id"]

            for guild in self.bot.guilds:
                channel_id = await db.get_channel_id_by_biome(guild.id, biome_id)
                if not channel_id:
                    continue

                channel = guild.get_channel(channel_id)
                if not isinstance(channel, discord.TextChannel):
                    continue

                member = guild.get_member(user_id)
                if not member:
                    skipped += 1
                    continue  # User has left the server

                # Check if the overwrite is already there
                overwrite = channel.overwrites_for(member)
                if overwrite.view_channel is True:
                    continue  # Already set — nothing to do

                try:
                    await channel.set_permissions(
                        member,
                        view_channel=True,
                        reason="Unlock restore on bot startup",
                    )
                    restored += 1
                except discord.Forbidden:
                    log.warning(
                        "Missing perms to restore unlock %s for user %s", biome_id, user_id
                    )
                except Exception:
                    log.exception(
                        "Error restoring unlock %s for user %s", biome_id, user_id
                    )

        log.info(
            "Unlock restore complete: %d applied, %d skipped (user left server).",
            restored, skipped,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UnlocksCog(bot))
