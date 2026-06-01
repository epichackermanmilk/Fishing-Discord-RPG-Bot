# =============================================================
# OMEGA BOT — NOVELCODEX SUPPORTER PERKS
# Eternal River Sect
#
# Perks unlocked by NovelCodex spend (roles synced by the website):
#   • Spent >= $5 total  → /myrole  : create a personal colored role
#   • Active subscriber  → /mychannel : create + manage a private voice channel
#
# Entitlement is read from the member's NovelCodex roles, which the
# NovelCodex website assigns/removes automatically based on Stripe data.
# =============================================================
from __future__ import annotations

import logging
import re

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from bot.config import DB_PATH
from bot.utils.formatters import error_embed, success_embed

log = logging.getLogger(__name__)

# ── NovelCodex entitlement role IDs (synced by the website) ───────────────────
NC_MEMBER     = 1510606615290843136   # linked account
READER        = 1510606693388648649   # Reader subscriber
SCHOLAR       = 1510606690758951093   # Scholar subscriber
SEEKER        = 1510606687269158943   # >= $5 cumulative spend
SAGE          = 1510606684173635644   # >= $25 cumulative spend
IMMORTAL_SAGE = 1510606680696688764   # >= $100 cumulative spend

# Any of these means the member has spent at least $5 (or is a subscriber)
SPEND_5_ROLES    = {SEEKER, SAGE, IMMORTAL_SAGE, READER, SCHOLAR}
# Active subscribers (channel perk)
SUBSCRIBER_ROLES = {READER, SCHOLAR}

# Category that holds members' private channels
CUSTOM_CHANNEL_CATEGORY = 1510804387616788551

HEX_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")


def parse_hex(value: str) -> discord.Colour | None:
    value = (value or "").strip()
    if not HEX_RE.match(value):
        return None
    return discord.Colour(int(value.lstrip("#"), 16))


def has_any_role(member: discord.Member, role_ids: set[int]) -> bool:
    return any(r.id in role_ids for r in member.roles)


class NovelCodexCog(commands.Cog, name="NovelCodex Perks"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS nc_custom_roles ("
                "user_id INTEGER PRIMARY KEY, role_id INTEGER NOT NULL)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS nc_custom_channels ("
                "user_id INTEGER PRIMARY KEY, channel_id INTEGER NOT NULL)"
            )
            await db.commit()
        log.info("NovelCodex perks cog loaded.")

    # ── small DB helpers ──────────────────────────────────────────────────────
    async def _get_role_id(self, user_id: int) -> int | None:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT role_id FROM nc_custom_roles WHERE user_id = ?", (user_id,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def _set_role_id(self, user_id: int, role_id: int) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO nc_custom_roles (user_id, role_id) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET role_id = excluded.role_id",
                (user_id, role_id),
            )
            await db.commit()

    async def _clear_role(self, user_id: int) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM nc_custom_roles WHERE user_id = ?", (user_id,))
            await db.commit()

    async def _get_channel_id(self, user_id: int) -> int | None:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT channel_id FROM nc_custom_channels WHERE user_id = ?", (user_id,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def _set_channel_id(self, user_id: int, channel_id: int) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO nc_custom_channels (user_id, channel_id) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET channel_id = excluded.channel_id",
                (user_id, channel_id),
            )
            await db.commit()

    async def _clear_channel(self, user_id: int) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM nc_custom_channels WHERE user_id = ?", (user_id,))
            await db.commit()

    # ══════════════════════════════════════════════════════════════════════════
    # /myrole — personal colored role (>= $5 spend)
    # ══════════════════════════════════════════════════════════════════════════
    myrole = app_commands.Group(
        name="myrole",
        description="Create and manage your personal NovelCodex supporter role.",
        guild_only=True,
    )

    @myrole.command(name="create", description="Create your personal colored role (NovelCodex supporters, $5+).")
    @app_commands.describe(name="Role name", color="Hex color, e.g. #8b5cf6")
    async def myrole_create(self, interaction: discord.Interaction, name: str, color: str) -> None:
        guild  = interaction.guild
        member = guild.get_member(interaction.user.id) if guild else None
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return

        if not has_any_role(member, SPEND_5_ROLES):
            await interaction.response.send_message(
                embed=error_embed(
                    "Custom roles are for NovelCodex supporters who've spent **$5 or more**.\n"
                    "Link your Discord at **novelcodex.org/profile** and grab some tokens to unlock this."),
                ephemeral=True)
            return

        colour = parse_hex(color)
        if colour is None:
            await interaction.response.send_message(
                embed=error_embed("Invalid color. Use a hex code like `#8b5cf6` or `8b5cf6`."), ephemeral=True)
            return

        name = name.strip()[:90]
        if not name:
            await interaction.response.send_message(embed=error_embed("Please provide a role name."), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Already have one? Update it instead of creating a duplicate.
        existing_id = await self._get_role_id(member.id)
        if existing_id:
            role = guild.get_role(existing_id)
            if role:
                await role.edit(name=name, colour=colour, reason="NovelCodex custom role update")
                if role not in member.roles:
                    await member.add_roles(role, reason="Re-assign custom role")
                await interaction.followup.send(
                    embed=success_embed(f"Updated your role → **{name}**."), ephemeral=True)
                return
            await self._clear_role(member.id)  # stale — fall through to recreate

        try:
            role = await guild.create_role(
                name=name, colour=colour, reason=f"NovelCodex custom role for {member}")
            # Try to lift it just under the bot's top role so the color shows.
            try:
                top = guild.me.top_role
                if top and top.position > 1:
                    await role.edit(position=max(1, top.position - 1))
            except discord.HTTPException:
                pass
            await member.add_roles(role, reason="NovelCodex custom role")
            await self._set_role_id(member.id, role.id)
        except discord.Forbidden:
            await interaction.followup.send(
                embed=error_embed("I don't have permission to manage roles. Ask an admin to check my role position."),
                ephemeral=True)
            return

        await interaction.followup.send(
            embed=success_embed(f"Created your role **{name}** with color `{color}`. Wear it with pride."),
            ephemeral=True)

    @myrole.command(name="edit", description="Rename or recolor your custom role.")
    @app_commands.describe(name="New name (optional)", color="New hex color (optional)")
    async def myrole_edit(self, interaction: discord.Interaction, name: str | None = None, color: str | None = None) -> None:
        guild  = interaction.guild
        member = guild.get_member(interaction.user.id) if guild else None
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return

        role_id = await self._get_role_id(member.id)
        role = guild.get_role(role_id) if role_id else None
        if not role:
            await interaction.response.send_message(
                embed=error_embed("You don't have a custom role yet. Use `/myrole create` first."), ephemeral=True)
            return

        kwargs = {}
        if name:
            kwargs["name"] = name.strip()[:90]
        if color:
            colour = parse_hex(color)
            if colour is None:
                await interaction.response.send_message(
                    embed=error_embed("Invalid color. Use a hex code like `#8b5cf6`."), ephemeral=True)
                return
            kwargs["colour"] = colour
        if not kwargs:
            await interaction.response.send_message(
                embed=error_embed("Provide a new name and/or color."), ephemeral=True)
            return

        await role.edit(reason="NovelCodex custom role edit", **kwargs)
        await interaction.response.send_message(embed=success_embed("Your role has been updated."), ephemeral=True)

    @myrole.command(name="delete", description="Delete your custom role.")
    async def myrole_delete(self, interaction: discord.Interaction) -> None:
        guild  = interaction.guild
        member = guild.get_member(interaction.user.id) if guild else None
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return
        role_id = await self._get_role_id(member.id)
        role = guild.get_role(role_id) if role_id else None
        if role:
            try:
                await role.delete(reason="NovelCodex custom role deleted by owner")
            except discord.HTTPException:
                pass
        await self._clear_role(member.id)
        await interaction.response.send_message(embed=success_embed("Your custom role was removed."), ephemeral=True)

    # ══════════════════════════════════════════════════════════════════════════
    # /mychannel — private voice channel (active subscribers)
    # ══════════════════════════════════════════════════════════════════════════
    mychannel = app_commands.Group(
        name="mychannel",
        description="Create and manage your private channel (NovelCodex subscribers).",
        guild_only=True,
    )

    def _is_subscriber(self, member: discord.Member) -> bool:
        return has_any_role(member, SUBSCRIBER_ROLES)

    async def _owned_channel(self, guild: discord.Guild, user_id: int) -> discord.VoiceChannel | None:
        cid = await self._get_channel_id(user_id)
        if not cid:
            return None
        ch = guild.get_channel(cid)
        if ch is None:
            await self._clear_channel(user_id)
            return None
        return ch  # type: ignore[return-value]

    @mychannel.command(name="create", description="Create your private voice channel (subscribers only).")
    @app_commands.describe(name="Channel name")
    async def channel_create(self, interaction: discord.Interaction, name: str) -> None:
        guild  = interaction.guild
        member = guild.get_member(interaction.user.id) if guild else None
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return

        if not self._is_subscriber(member):
            await interaction.response.send_message(
                embed=error_embed(
                    "Private channels are a **NovelCodex subscriber** perk.\n"
                    "Subscribe at **novelcodex.org/shop** and link your Discord to unlock this."),
                ephemeral=True)
            return

        existing = await self._owned_channel(guild, member.id)
        if existing:
            await interaction.response.send_message(
                embed=error_embed(f"You already have a channel: **{existing.name}**. Use `/mychannel` commands to manage it."),
                ephemeral=True)
            return

        category = guild.get_channel(CUSTOM_CHANNEL_CATEGORY)
        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message(
                embed=error_embed("The custom-channels category is missing. Ask an admin."), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
            member: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True, move_members=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True),
        }
        try:
            channel = await guild.create_voice_channel(
                name=name.strip()[:90] or f"{member.display_name}'s channel",
                category=category,
                overwrites=overwrites,
                reason=f"NovelCodex subscriber channel for {member}",
            )
            await self._set_channel_id(member.id, channel.id)
        except discord.Forbidden:
            await interaction.followup.send(
                embed=error_embed("I don't have permission to create channels here. Ask an admin."), ephemeral=True)
            return

        await interaction.followup.send(
            embed=success_embed(
                f"Created your private voice channel **{channel.name}**.\n"
                f"Manage it with `/mychannel rename`, `/mychannel limit`, `/mychannel add`, `/mychannel remove`."),
            ephemeral=True)

    @mychannel.command(name="rename", description="Rename your private channel.")
    @app_commands.describe(name="New channel name")
    async def channel_rename(self, interaction: discord.Interaction, name: str) -> None:
        guild, member = interaction.guild, interaction.guild.get_member(interaction.user.id) if interaction.guild else (None, None)
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return
        ch = await self._owned_channel(guild, member.id)
        if not ch:
            await interaction.response.send_message(embed=error_embed("You don't have a channel. Use `/mychannel create`."), ephemeral=True)
            return
        await ch.edit(name=name.strip()[:90], reason="Owner renamed channel")
        await interaction.response.send_message(embed=success_embed(f"Renamed to **{ch.name}**."), ephemeral=True)

    @mychannel.command(name="limit", description="Set how many people your channel holds (0 = unlimited).")
    @app_commands.describe(capacity="Max people (0–99, 0 = unlimited)")
    async def channel_limit(self, interaction: discord.Interaction, capacity: app_commands.Range[int, 0, 99]) -> None:
        guild, member = interaction.guild, interaction.guild.get_member(interaction.user.id) if interaction.guild else (None, None)
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return
        ch = await self._owned_channel(guild, member.id)
        if not ch:
            await interaction.response.send_message(embed=error_embed("You don't have a channel. Use `/mychannel create`."), ephemeral=True)
            return
        await ch.edit(user_limit=capacity, reason="Owner set capacity")
        nice = "unlimited" if capacity == 0 else str(capacity)
        await interaction.response.send_message(embed=success_embed(f"Capacity set to **{nice}**."), ephemeral=True)

    @mychannel.command(name="add", description="Allow someone into your private channel.")
    @app_commands.describe(user="Member to allow")
    async def channel_add(self, interaction: discord.Interaction, user: discord.Member) -> None:
        guild, member = interaction.guild, interaction.guild.get_member(interaction.user.id) if interaction.guild else (None, None)
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return
        ch = await self._owned_channel(guild, member.id)
        if not ch:
            await interaction.response.send_message(embed=error_embed("You don't have a channel. Use `/mychannel create`."), ephemeral=True)
            return
        await ch.set_permissions(user, view_channel=True, connect=True, reason="Owner allowed member")
        await interaction.response.send_message(embed=success_embed(f"Allowed **{user.display_name}** into your channel."), ephemeral=True)

    @mychannel.command(name="remove", description="Remove someone from your private channel.")
    @app_commands.describe(user="Member to remove")
    async def channel_remove(self, interaction: discord.Interaction, user: discord.Member) -> None:
        guild, member = interaction.guild, interaction.guild.get_member(interaction.user.id) if interaction.guild else (None, None)
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return
        ch = await self._owned_channel(guild, member.id)
        if not ch:
            await interaction.response.send_message(embed=error_embed("You don't have a channel. Use `/mychannel create`."), ephemeral=True)
            return
        await ch.set_permissions(user, overwrite=None, reason="Owner removed member")
        # Kick them from the voice channel if currently connected
        if user.voice and user.voice.channel and user.voice.channel.id == ch.id:
            try:
                await user.move_to(None, reason="Removed from private channel")
            except discord.HTTPException:
                pass
        await interaction.response.send_message(embed=success_embed(f"Removed **{user.display_name}** from your channel."), ephemeral=True)

    @mychannel.command(name="delete", description="Delete your private channel.")
    async def channel_delete(self, interaction: discord.Interaction) -> None:
        guild, member = interaction.guild, interaction.guild.get_member(interaction.user.id) if interaction.guild else (None, None)
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("Use this inside the server."), ephemeral=True)
            return
        ch = await self._owned_channel(guild, member.id)
        if ch:
            try:
                await ch.delete(reason="Owner deleted channel")
            except discord.HTTPException:
                pass
        await self._clear_channel(member.id)
        await interaction.response.send_message(embed=success_embed("Your private channel was deleted."), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NovelCodexCog(bot))
