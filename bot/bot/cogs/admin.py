# =============================================================
# OMEGA BOT — ADMIN COG
# Eternal River Sect
# /shutdown  /restart  /botstatus
# Owner-only bot lifecycle controls.
# =============================================================
from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import sys

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger(__name__)

# systemd service name — matches /etc/systemd/system/omega-bot.service
SERVICE_NAME = "omega-bot"


def _is_systemd() -> bool:
    """Return True if the bot is running under systemd (i.e. on the VPS)."""
    return os.getenv("INVOCATION_ID") is not None or _service_exists()


def _service_exists() -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "status", SERVICE_NAME],
            capture_output=True, timeout=5,
        )
        return result.returncode in (0, 3)  # 0=running, 3=stopped but exists
    except Exception:
        return False


class AdminCog(commands.Cog, name="Admin"):
    """Owner-only bot lifecycle commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _owner_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.bot.owner_id

    # ── /shutdown ─────────────────────────────────────────────────────────────

    @app_commands.command(
        name="shutdown",
        description="[Owner] Shut the bot down completely.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def shutdown(self, interaction: discord.Interaction) -> None:
        if not self._owner_check(interaction):
            await interaction.response.send_message(
                "⛔ Only the bot owner can use this command.", ephemeral=True)
            return

        await interaction.response.send_message(
            "⛔ **Omega Bot is shutting down.** The bot will go offline now.\n"
            "*(To bring it back, restart the VPS service or ask Claude.)*",
            ephemeral=False,
        )

        log.warning("Shutdown requested by %s (%d)", interaction.user, interaction.user.id)
        await asyncio.sleep(1)   # Let Discord deliver the message

        if _is_systemd():
            # Tell systemd to stop the service — Restart=on-failure means it
            # will NOT auto-restart on a clean stop.
            subprocess.Popen(["systemctl", "stop", SERVICE_NAME])
        else:
            # Running locally — just exit the process
            await self.bot.close()

    # ── /restart ──────────────────────────────────────────────────────────────

    @app_commands.command(
        name="restart",
        description="[Owner] Restart the bot (re-loads all code from disk).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def restart(self, interaction: discord.Interaction) -> None:
        if not self._owner_check(interaction):
            await interaction.response.send_message(
                "⛔ Only the bot owner can use this command.", ephemeral=True)
            return

        await interaction.response.send_message(
            "🔄 **Restarting Omega Bot…** Back in a few seconds.",
            ephemeral=False,
        )

        log.warning("Restart requested by %s (%d)", interaction.user, interaction.user.id)
        await asyncio.sleep(1)

        if _is_systemd():
            subprocess.Popen(["systemctl", "restart", SERVICE_NAME])
        else:
            # Running locally — re-exec the current Python process
            os.execv(sys.executable, [sys.executable] + sys.argv)

    # ── /botstatus ────────────────────────────────────────────────────────────

    @app_commands.command(
        name="botstatus",
        description="[Owner] Show bot uptime, latency, and service status.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def botstatus(self, interaction: discord.Interaction) -> None:
        if not self._owner_check(interaction):
            await interaction.response.send_message(
                "⛔ Only the bot owner can use this command.", ephemeral=True)
            return

        latency_ms = round(self.bot.latency * 1000)
        guilds     = len(self.bot.guilds)
        on_systemd = _is_systemd()

        # Try to get systemd uptime
        systemd_info = ""
        if on_systemd:
            try:
                result = subprocess.run(
                    ["systemctl", "show", SERVICE_NAME,
                     "--property=ActiveEnterTimestamp,ActiveState"],
                    capture_output=True, text=True, timeout=5,
                )
                systemd_info = f"\n```{result.stdout.strip()}```"
            except Exception:
                pass

        embed = discord.Embed(
            title="🤖 Omega Bot Status",
            color=0x2ECC71,
        )
        embed.add_field(name="🏓 Latency",    value=f"{latency_ms} ms",      inline=True)
        embed.add_field(name="🏰 Guilds",     value=str(guilds),              inline=True)
        embed.add_field(name="⚙️ Running on", value="VPS (systemd)" if on_systemd else "Local process", inline=True)
        if systemd_info:
            embed.add_field(name="📋 Service info", value=systemd_info, inline=False)
        embed.set_footer(text="Use /shutdown to stop · /restart to reload")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
