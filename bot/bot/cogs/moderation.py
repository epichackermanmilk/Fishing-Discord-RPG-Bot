# =============================================================
# OMEGA BOT — MODERATION COG
# Eternal River Sect
# Mute, unmute, kick, ban, warn, banned-words auto-mod
# =============================================================
from __future__ import annotations

import asyncio
import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.utils.formatters import error_embed, success_embed, base_embed

log = logging.getLogger(__name__)


def _mod_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            return False
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return False
        return (
            member.guild_permissions.manage_messages or
            member.guild_permissions.administrator or
            discord.utils.get(member.roles, name="Eternal River Sect Elder") is not None or
            discord.utils.get(member.roles, name="Eternal River Sect Master") is not None
        )
    return app_commands.check(predicate)


async def _get_mod_log(guild: discord.Guild) -> discord.TextChannel | None:
    for ch in guild.text_channels:
        row = await db.get_channel_config(ch.id)
        if row and row["channel_type"] == "mod_log":
            return ch
    return None


async def _log_action(guild: discord.Guild, action: str, target: discord.Member,
                      moderator: discord.Member, reason: str | None,
                      duration: int | None = None) -> None:
    await db.log_mod_action(
        action_type=action,
        target_id=target.id,
        target_name=str(target),
        moderator_id=moderator.id,
        moderator_name=str(moderator),
        reason=reason,
        duration_seconds=duration,
    )
    ch = await _get_mod_log(guild)
    if ch:
        color_map = {
            "mute": 0xF39C12, "unmute": 0x2ECC71, "kick": 0xE67E22,
            "ban": 0xE74C3C,  "warn": 0x3498DB,
        }
        embed = discord.Embed(
            title=f"🛡️ {action.upper()}",
            color=color_map.get(action, 0x7F8C8D),
        )
        embed.add_field(name="Target",    value=f"{target.mention} (`{target}`)", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention}",           inline=True)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        if duration:
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            embed.add_field(name="Duration", value=f"{h}h {m}m {s}s", inline=True)
        embed.set_footer(text=f"<t:{int(time.time())}:F>")
        await ch.send(embed=embed)


class ModerationCog(commands.Cog, name="Moderation"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /mute ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="mute", description="Qi Seal a member (mute).")
    @app_commands.describe(
        member="Member to mute",
        duration="Duration in minutes (0 = permanent)",
        reason="Reason for the mute",
    )
    @_mod_check()
    async def mute(self, interaction: discord.Interaction,
                   member: discord.Member,
                   duration: int = 0,
                   reason: str = "No reason provided") -> None:
        guild     = interaction.guild
        mute_role = discord.utils.get(guild.roles, name="Qi Sealed")
        if not mute_role:
            await interaction.response.send_message(embed=error_embed("Qi Sealed role not found. Run /omega-setup."), ephemeral=True)
            return
        if mute_role in member.roles:
            await interaction.response.send_message(embed=error_embed(f"{member.display_name} is already Qi Sealed."), ephemeral=True)
            return

        await member.add_roles(mute_role, reason=f"Muted by {interaction.user}: {reason}")

        expires_at = time.time() + duration * 60 if duration > 0 else None
        await db.set_active_mute(member.id, guild.id, expires_at or 0)
        dur_seconds = duration * 60 if duration > 0 else None

        await _log_action(guild, "mute", member, interaction.user, reason, dur_seconds)

        dur_str = f"{duration} min" if duration > 0 else "permanent"
        await interaction.response.send_message(
            embed=success_embed(f"🔇 {member.mention} has been Qi Sealed ({dur_str}).\nReason: {reason}"),
        )

        if expires_at:
            await asyncio.sleep(duration * 60)
            # Re-check they're still muted
            guild = self.bot.get_guild(guild.id)
            if guild:
                member = guild.get_member(member.id)
                if member and mute_role in member.roles:
                    await member.remove_roles(mute_role, reason="Mute expired")
                    await db.remove_active_mute(member.id)

    # ── /unmute ───────────────────────────────────────────────────────────────

    @app_commands.command(name="unmute", description="Unseal a Qi Sealed member.")
    @app_commands.describe(member="Member to unmute", reason="Reason")
    @_mod_check()
    async def unmute(self, interaction: discord.Interaction,
                     member: discord.Member, reason: str = "No reason provided") -> None:
        mute_role = discord.utils.get(interaction.guild.roles, name="Qi Sealed")
        if not mute_role or mute_role not in member.roles:
            await interaction.response.send_message(embed=error_embed(f"{member.display_name} is not Qi Sealed."), ephemeral=True)
            return
        await member.remove_roles(mute_role, reason=f"Unmuted by {interaction.user}: {reason}")
        await db.remove_active_mute(member.id)
        await _log_action(interaction.guild, "unmute", member, interaction.user, reason)
        await interaction.response.send_message(embed=success_embed(f"🔊 {member.mention} has been unsealed."))

    # ── /kick ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="kick", description="Expel a member from the sect.")
    @app_commands.describe(member="Member to kick", reason="Reason")
    @_mod_check()
    async def kick(self, interaction: discord.Interaction,
                   member: discord.Member, reason: str = "No reason provided") -> None:
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(embed=error_embed("Cannot kick this member — role hierarchy."), ephemeral=True)
            return
        await _log_action(interaction.guild, "kick", member, interaction.user, reason)
        await member.kick(reason=f"Kicked by {interaction.user}: {reason}")
        await interaction.response.send_message(embed=success_embed(f"👢 {member} has been expelled from the sect."))

    # ── /ban ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="ban", description="Banish a member from the sect.")
    @app_commands.describe(member="Member to ban", reason="Reason", delete_days="Days of messages to delete")
    @_mod_check()
    async def ban(self, interaction: discord.Interaction,
                  member: discord.Member,
                  reason: str = "No reason provided",
                  delete_days: int = 0) -> None:
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(embed=error_embed("Cannot ban this member — role hierarchy."), ephemeral=True)
            return
        await _log_action(interaction.guild, "ban", member, interaction.user, reason)
        await member.ban(reason=f"Banned by {interaction.user}: {reason}", delete_message_days=min(7, delete_days))
        await interaction.response.send_message(embed=success_embed(f"🔨 {member} has been banished from the sect."))

    # ── /warn ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="warn", description="Issue a formal warning to a member.")
    @app_commands.describe(member="Member to warn", reason="Reason for the warning")
    @_mod_check()
    async def warn(self, interaction: discord.Interaction,
                   member: discord.Member, reason: str) -> None:
        await _log_action(interaction.guild, "warn", member, interaction.user, reason)
        await interaction.response.send_message(embed=success_embed(f"⚠️ {member.mention} has been warned.\nReason: {reason}"))
        # DM the member
        try:
            embed = discord.Embed(
                title="⚠️ Warning — Eternal River Sect",
                description=(
                    f"You have received a formal warning from the sect moderators.\n\n"
                    f"**Reason:** {reason}\n\n"
                    f"Further violations may result in Qi Sealing or expulsion."
                ),
                color=0xF39C12,
            )
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

    # ── /modlog ───────────────────────────────────────────────────────────────

    @app_commands.command(name="modlog", description="View moderation history for a member.")
    @app_commands.describe(member="Member to look up")
    @_mod_check()
    async def modlog(self, interaction: discord.Interaction, member: discord.Member) -> None:
        actions = await db.get_mod_actions(member.id)
        if not actions:
            await interaction.response.send_message(
                embed=base_embed(f"Mod Log — {member}", "No recorded actions."),
                ephemeral=True,
            )
            return
        embed = discord.Embed(title=f"📋 Mod Log — {member}", color=0x3498DB)
        for a in actions[-10:]:
            dur = f" · {a['duration_seconds']//60}m" if a.get("duration_seconds") else ""
            embed.add_field(
                name=f"{a['action_type'].upper()}  <t:{int(a['created_at'])}:R>{dur}",
                value=f"By: <@{a['moderator_id']}>  Reason: {a.get('reason') or '—'}",
                inline=False,
            )
        embed.set_footer(text="Showing last 10 actions")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /bannedwords ──────────────────────────────────────────────────────────

    bannedwords_group = app_commands.Group(name="bannedwords", description="Manage the banned word list.")

    @bannedwords_group.command(name="add", description="Add a word to the auto-mod filter.")
    @app_commands.describe(word="Word to ban")
    @_mod_check()
    async def bw_add(self, interaction: discord.Interaction, word: str) -> None:
        await db.add_banned_word(word.lower(), interaction.user.id)
        await interaction.response.send_message(embed=success_embed(f"Word added to filter."), ephemeral=True)

    @bannedwords_group.command(name="remove", description="Remove a word from the auto-mod filter.")
    @app_commands.describe(word="Word to remove")
    @_mod_check()
    async def bw_remove(self, interaction: discord.Interaction, word: str) -> None:
        await db.remove_banned_word(word.lower())
        await interaction.response.send_message(embed=success_embed(f"Word removed from filter."), ephemeral=True)

    # ── Auto-mod: banned words listener ──────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        words = await db.get_banned_words()
        content_lower = message.content.lower()
        for word in words:
            if word in content_lower:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                try:
                    await message.channel.send(
                        f"{message.author.mention} Your message was removed for containing a banned word.",
                        delete_after=5,
                    )
                except discord.Forbidden:
                    pass
                await _log_action(
                    message.guild,
                    "auto_delete",
                    message.author,
                    message.guild.me,
                    f"Auto-mod: banned word detected",
                )
                break

    # ── Startup: restore active mutes ─────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        expired = await db.get_expired_mutes()
        for mute in expired:
            guild = self.bot.get_guild(mute["guild_id"])
            if not guild:
                continue
            member = guild.get_member(mute["user_id"])
            mute_role = discord.utils.get(guild.roles, name="Qi Sealed")
            if member and mute_role and mute_role in member.roles:
                try:
                    await member.remove_roles(mute_role, reason="Mute expired (bot restart)")
                    await db.remove_active_mute(member.id)
                except discord.Forbidden:
                    pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModerationCog(bot))
