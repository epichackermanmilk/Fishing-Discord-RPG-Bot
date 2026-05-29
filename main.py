#!/usr/bin/env python3
# =============================================================
# OMEGA BOT — MAIN ENTRY POINT
# Eternal River Sect
# Run with:  python main.py
# =============================================================
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from bot.config import TOKEN, COMMAND_PREFIX, COGS, DEBUG, OWNER_ID
from bot.database import db

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────

log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("omega")


# ──────────────────────────────────────────────────────────────────────────────
# BOT CLASS
# ──────────────────────────────────────────────────────────────────────────────

class OmegaBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.members          = True
        intents.message_content  = True
        intents.voice_states     = True

        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            owner_id=OWNER_ID,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        """Called once before the bot connects. Load cogs and init DB."""
        log.info("Initialising database...")
        await db.init()

        log.info("Loading cogs...")
        failed = []
        for cog_path in COGS:
            try:
                await self.load_extension(cog_path)
                log.info("  ✓ %s", cog_path)
            except Exception as exc:
                log.exception("  ✗ Failed to load %s: %s", cog_path, exc)
                failed.append(cog_path)

        if failed:
            log.warning("⚠️  %d cog(s) failed to load: %s", len(failed), ", ".join(failed))
        else:
            log.info("All cogs loaded successfully.")

    async def on_ready(self) -> None:
        log.info("=" * 50)
        log.info("Omega Bot — Eternal River Sect")
        log.info("Logged in as: %s (ID: %d)", self.user, self.user.id)
        log.info("Guilds: %d", len(self.guilds))
        log.info("=" * 50)

        # ── Step 1: snapshot every global command (includes Group commands from Cogs).
        # copy_global_to + guild sync gives instant propagation instead of the 1-hour
        # global CDN delay.  We snapshot first so we can restore the local tree after
        # clearing the global namespace (step 3), keeping !sync working across the
        # lifetime of this process.
        global_cmds = list(self.tree.get_commands(guild=None))

        # ── Step 2: push all commands as guild-specific to every guild.
        log.info("Syncing slash commands to %d guild(s)...", len(self.guilds))
        synced_total = 0
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                log.info("  ✓ Synced %d command(s) to guild: %s", len(synced), guild.name)
                synced_total += len(synced)
            except discord.Forbidden:
                log.warning("  ✗ Missing 'applications.commands' scope in guild: %s", guild.name)
            except Exception as exc:
                log.error("  ✗ Sync failed for guild %s: %s", guild.name, exc)

        # ── Step 3: wipe Discord's global command namespace so players don't see
        # duplicate entries (one guild-specific + one global copy of every command).
        self.tree.clear_commands(guild=None)
        try:
            await self.tree.sync()   # pushes an empty list → removes all global cmds
            log.info("Global command namespace cleared (prevents duplicate slash commands).")
        except Exception as exc:
            log.warning("Could not clear global commands: %s", exc)

        # ── Step 4: restore commands to the local tree so !sync (and future
        # copy_global_to calls within this process) still works correctly.
        for cmd in global_cmds:
            self.tree.add_command(cmd)

        log.info("Slash command sync complete. Total: %d command(s).", synced_total)

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the eternal river flow 🎣",
            )
        )

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context) -> None:
        """Owner-only: force re-sync slash commands to this guild."""
        await ctx.message.add_reaction("⏳")
        try:
            self.tree.copy_global_to(guild=ctx.guild)
            synced = await self.tree.sync(guild=ctx.guild)
            await ctx.message.add_reaction("✅")
            await ctx.send(f"✅ Synced **{len(synced)}** slash command(s) to **{ctx.guild.name}**.")
            log.info("Manual sync: %d commands synced to %s by %s", len(synced), ctx.guild.name, ctx.author)
        except Exception as exc:
            await ctx.message.add_reaction("❌")
            await ctx.send(f"❌ Sync failed: `{exc}`")
            log.error("Manual sync failed: %s", exc)

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("⛔ You lack the permissions to use this command.", delete_after=5)
        elif isinstance(error, commands.CommandNotFound):
            pass  # Silently ignore unknown prefix commands
        else:
            log.error("Unhandled command error: %s", error, exc_info=True)

    async def on_app_command_error(self, interaction: discord.Interaction,
                                   error: discord.app_commands.AppCommandError) -> None:
        msg = str(error)
        if isinstance(error, discord.app_commands.CheckFailure):
            msg = "⛔ You don't have permission to use this command."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ {msg}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        except Exception:
            pass
        log.error("App command error in /%s: %s", interaction.command.name if interaction.command else "?", error)


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    if not TOKEN:
        log.critical("DISCORD_TOKEN is not set. Create a .env file with DISCORD_TOKEN=your_token.")
        sys.exit(1)

    bot = OmegaBot()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Omega Bot shutting down — 再见.")
