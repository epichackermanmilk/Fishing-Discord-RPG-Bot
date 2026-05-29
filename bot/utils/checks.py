# =============================================================
# OMEGA BOT — CHANNEL & PERMISSION CHECKS
# Eternal River Sect
# =============================================================
"""
discord.ext.commands check factories and helper predicates used
across all cogs to enforce channel-type restrictions.
"""
from __future__ import annotations

import discord
from discord.ext import commands

from bot.database import db


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _get_channel_type(channel_id: int) -> str | None:
    """Return the channel_type string from DB, or None if unconfigured."""
    row = await db.get_channel_config(channel_id)
    return row["channel_type"] if row else None


# ──────────────────────────────────────────────────────────────────────────────
# Check factories
# ──────────────────────────────────────────────────────────────────────────────

def is_fishing_channel():
    """Command can only be used in channels configured as 'fishing'."""
    async def predicate(ctx: commands.Context) -> bool:
        ctype = await _get_channel_type(ctx.channel.id)
        if ctype == "fishing":
            return True
        raise NotFishingChannel()
    return commands.check(predicate)


def is_shop_channel():
    """Command can only be used in channels configured as 'shop'."""
    async def predicate(ctx: commands.Context) -> bool:
        ctype = await _get_channel_type(ctx.channel.id)
        if ctype == "shop":
            return True
        raise NotShopChannel()
    return commands.check(predicate)


def is_fishing_or_shop_channel():
    """Command can be used in fishing OR shop channels."""
    async def predicate(ctx: commands.Context) -> bool:
        ctype = await _get_channel_type(ctx.channel.id)
        if ctype in ("fishing", "shop"):
            return True
        raise WrongChannel("You can only use that command in a fishing or shop channel.")
    return commands.check(predicate)


def is_configured_channel(*types: str):
    """Generic: channel must be one of the given type strings."""
    async def predicate(ctx: commands.Context) -> bool:
        ctype = await _get_channel_type(ctx.channel.id)
        if ctype in types:
            return True
        raise WrongChannel(f"This command can only be used in: {', '.join(types)}")
    return commands.check(predicate)


# ──────────────────────────────────────────────────────────────────────────────
# Slash-command (app command) equivalents (discord.app_commands style)
# ──────────────────────────────────────────────────────────────────────────────

def app_is_fishing_channel():
    """app_commands interaction check: must be a fishing channel."""
    async def predicate(interaction: discord.Interaction) -> bool:
        ctype = await _get_channel_type(interaction.channel_id)
        if ctype == "fishing":
            return True
        await interaction.response.send_message(
            "⛔ You can only use fishing commands in designated fishing channels.",
            ephemeral=True,
        )
        return False
    return discord.app_commands.check(predicate)


def app_is_shop_channel():
    """app_commands interaction check: must be a shop channel."""
    async def predicate(interaction: discord.Interaction) -> bool:
        ctype = await _get_channel_type(interaction.channel_id)
        if ctype == "shop":
            return True
        await interaction.response.send_message(
            "⛔ You can only use shop commands in the designated shop channel.",
            ephemeral=True,
        )
        return False
    return discord.app_commands.check(predicate)


def app_is_configured_channel(*types: str):
    """app_commands interaction check: channel must be one of the given types."""
    async def predicate(interaction: discord.Interaction) -> bool:
        ctype = await _get_channel_type(interaction.channel_id)
        if ctype in types:
            return True
        await interaction.response.send_message(
            f"⛔ This command can only be used in: {', '.join(types)} channels.",
            ephemeral=True,
        )
        return False
    return discord.app_commands.check(predicate)


# ──────────────────────────────────────────────────────────────────────────────
# Fishing-channel access helper (for views / callbacks outside check wrappers)
# ──────────────────────────────────────────────────────────────────────────────

async def channel_is_fishing(channel_id: int) -> bool:
    ctype = await _get_channel_type(channel_id)
    return ctype == "fishing"


async def channel_is_shop(channel_id: int) -> bool:
    ctype = await _get_channel_type(channel_id)
    return ctype == "shop"


async def get_biome_for_channel(channel_id: int) -> str | None:
    """Return the biome_id for a fishing channel, or None."""
    row = await db.get_channel_config(channel_id)
    if row and row["channel_type"] == "fishing":
        return row["biome_id"]
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Custom exceptions
# ──────────────────────────────────────────────────────────────────────────────

class NotFishingChannel(commands.CheckFailure):
    def __init__(self):
        super().__init__("⛔ You can only use fishing commands in designated fishing channels.")


class NotShopChannel(commands.CheckFailure):
    def __init__(self):
        super().__init__("⛔ You can only use shop commands in the designated shop channel.")


class WrongChannel(commands.CheckFailure):
    pass
