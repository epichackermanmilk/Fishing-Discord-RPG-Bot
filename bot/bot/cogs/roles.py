# =============================================================
# OMEGA BOT — ROLES COG
# Eternal River Sect
# /role location, /role interest
# Location roles are mutually exclusive.
# =============================================================
from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.utils.formatters import error_embed, success_embed

log = logging.getLogger(__name__)

LOCATION_ROLES = {
    "europe":        "🌍 Europe",
    "north america": "🌎 North America",
    "na":            "🌎 North America",
    "africa":        "🌍 Africa",
    "south america": "🌎 South America",
    "sa":            "🌎 South America",
    "asia":          "🌏 Asia",
    "oceania":       "🌐 Oceania",
}

INTEREST_ROLES = {
    "xianxia reader": "📚 Xianxia Reader",
    "xianxia":        "📚 Xianxia Reader",
    "action fan":     "⚔️ Action Fan",
    "action":         "⚔️ Action Fan",
    "gamer":          "🎮 Gamer",
    "artist":         "🎨 Artist",
    "music lover":    "🎵 Music Lover",
    "music":          "🎵 Music Lover",
    "avid fisher":    "🐟 Avid Fisher",
    "fisher":         "🐟 Avid Fisher",
    "story enjoyer":  "📖 Story Enjoyer",
    "story":          "📖 Story Enjoyer",
}

ALL_LOCATION_ROLE_NAMES = set(LOCATION_ROLES.values())
ALL_INTEREST_ROLE_NAMES = set(INTEREST_ROLES.values())


class RolesCog(commands.Cog, name="Roles"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    role_group = app_commands.Group(
        name="role",
        description="Assign or remove self-serve roles.",
        guild_only=True,
    )

    # ── /role location ────────────────────────────────────────────────────────

    @role_group.command(name="location", description="Set your region role (one at a time).")
    @app_commands.describe(region="Your region")
    @app_commands.choices(region=[
        app_commands.Choice(name="🌍 Europe",        value="europe"),
        app_commands.Choice(name="🌎 North America",  value="north america"),
        app_commands.Choice(name="🌍 Africa",         value="africa"),
        app_commands.Choice(name="🌎 South America",  value="south america"),
        app_commands.Choice(name="🌏 Asia",           value="asia"),
        app_commands.Choice(name="🌐 Oceania",        value="oceania"),
    ])
    async def role_location(self, interaction: discord.Interaction, region: str) -> None:
        guild  = interaction.guild
        member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("This command must be used inside the server."), ephemeral=True)
            return

        target_name = LOCATION_ROLES.get(region.lower())
        if not target_name:
            await interaction.response.send_message(
                embed=error_embed(f"Unknown region: {region}"), ephemeral=True)
            return

        target_role = discord.utils.get(guild.roles, name=target_name)
        if not target_role:
            await interaction.response.send_message(
                embed=error_embed(f"Role **{target_name}** not found. Run `/omega-setup`."),
                ephemeral=True,
            )
            return

        # Remove all existing location roles
        to_remove = [r for r in member.roles if r.name in ALL_LOCATION_ROLE_NAMES and r != target_role]
        if to_remove:
            await member.remove_roles(*to_remove, reason="Location role swap")

        # Toggle: if they already have it, remove it; otherwise add it
        if target_role in member.roles:
            await member.remove_roles(target_role, reason="Location role removed by user")
            await interaction.response.send_message(
                embed=success_embed(f"Removed **{target_name}** from your roles."),
                ephemeral=True,
            )
        else:
            await member.add_roles(target_role, reason="Location role assigned by user")
            await interaction.response.send_message(
                embed=success_embed(f"You now have the **{target_name}** role."),
                ephemeral=True,
            )

    # ── /role interest ────────────────────────────────────────────────────────

    @role_group.command(name="interest", description="Toggle an interest or genre role.")
    @app_commands.describe(interest="The interest to toggle")
    @app_commands.choices(interest=[
        app_commands.Choice(name="📚 Xianxia Reader", value="xianxia reader"),
        app_commands.Choice(name="⚔️ Action Fan",     value="action fan"),
        app_commands.Choice(name="🎮 Gamer",           value="gamer"),
        app_commands.Choice(name="🎨 Artist",          value="artist"),
        app_commands.Choice(name="🎵 Music Lover",     value="music lover"),
        app_commands.Choice(name="🐟 Avid Fisher",     value="avid fisher"),
        app_commands.Choice(name="📖 Story Enjoyer",   value="story enjoyer"),
    ])
    async def role_interest(self, interaction: discord.Interaction, interest: str) -> None:
        guild  = interaction.guild
        member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
        if not guild or not member:
            await interaction.response.send_message(embed=error_embed("This command must be used inside the server."), ephemeral=True)
            return

        target_name = INTEREST_ROLES.get(interest.lower())
        if not target_name:
            await interaction.response.send_message(
                embed=error_embed(f"Unknown interest: {interest}"), ephemeral=True)
            return

        target_role = discord.utils.get(guild.roles, name=target_name)
        if not target_role:
            await interaction.response.send_message(
                embed=error_embed(f"Role **{target_name}** not found. Run `/omega-setup`."),
                ephemeral=True,
            )
            return

        if target_role in member.roles:
            await member.remove_roles(target_role, reason="Interest role removed by user")
            await interaction.response.send_message(
                embed=success_embed(f"Removed **{target_name}**."), ephemeral=True)
        else:
            await member.add_roles(target_role, reason="Interest role assigned by user")
            await interaction.response.send_message(
                embed=success_embed(f"Added **{target_name}** to your roles."), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RolesCog(bot))
