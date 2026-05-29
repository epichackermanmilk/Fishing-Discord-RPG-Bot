# =============================================================
# OMEGA BOT — CULTIVATION COG
# Eternal River Sect
# /cultivate, /breakthrough, /titles, /title equip
# =============================================================
from __future__ import annotations

import logging
import random

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.data.title_data import ALL_TITLES, TITLE_BY_ID, general_titles_by_type
from bot.data.fish_data import FISH_BY_ID
from bot.cogs.shop import PILL_BASE_PRICES, PILL_NAMES
from bot.utils.formatters import (
    fmt_realm, fmt_stones, fmt_qi_bar, fmt_xp_bar,
    realm_emoji, base_embed, error_embed, success_embed,
    REALM_NAMES, STAGE_SUFFIXES, qi_for_stage, level_from_xp,
)

log = logging.getLogger(__name__)

# Breakthrough success probability:
#   base = 70% for realm 1, declining 5% per realm
#   +5% per previous failure
BREAKTHROUGH_BASE = {
    1: 0.70, 2: 0.65, 3: 0.60, 4: 0.55,
    5: 0.50, 6: 0.45, 7: 0.40, 8: 0.35, 9: 0.30,
}
FAILURE_BONUS = 0.05   # per failure
MAX_SUCCESS   = 0.95   # capped


class CultivationCog(commands.Cog, name="Cultivation"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /cultivate ────────────────────────────────────────────────────────────

    @app_commands.command(name="cultivate", description="View your Qi and cultivation progress.")
    async def cultivate(self, interaction: discord.Interaction) -> None:
        user_id  = interaction.user.id
        user_row = await db.get_or_create_user(user_id, str(interaction.user))

        realm = user_row["realm"]
        stage = user_row["stage"]
        qi    = user_row["qi"]

        embed = discord.Embed(
            title=f"{realm_emoji(realm)} Cultivation Status",
            color=0xA569BD,
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        embed.add_field(name="Realm",  value=fmt_realm(realm, stage), inline=True)
        embed.add_field(name="Stage",  value=STAGE_SUFFIXES[min(stage, len(STAGE_SUFFIXES)-1)] if realm > 0 else "N/A", inline=True)
        embed.add_field(name="​", value="​", inline=True)

        if realm < 9:
            stage_qi  = qi_for_stage(realm + 1 if realm == 0 else realm, max(stage, 1))
            qi_bar    = fmt_qi_bar(qi, realm + 1 if realm == 0 else realm, max(stage, 1))
            pill_cost = PILL_BASE_PRICES.get(realm + 1, "N/A")
            embed.add_field(name="Qi Progress", value=qi_bar, inline=False)
            embed.add_field(name="Next Realm Pill", value=f"{PILL_NAMES.get(realm+1,'—')} — {fmt_stones(pill_cost) if isinstance(pill_cost, int) else pill_cost}", inline=False)
        else:
            embed.add_field(name="Qi Progress", value="🏆 **ETERNAL SOVEREIGN** — Peak of cultivation!", inline=False)

        # Show tracker
        tracker = await db.get_cultivation_tracker(user_id)
        t = tracker.get(realm + 1, {})
        failures = t.get("failure_count", 0)
        if failures > 0:
            prob = min(MAX_SUCCESS, BREAKTHROUGH_BASE.get(realm+1, 0.30) + failures * FAILURE_BONUS)
            embed.add_field(
                name="Breakthrough Odds",
                value=f"{prob*100:.0f}% success ({failures} failure(s) — +{failures*5}% bonus)",
                inline=False,
            )

        embed.set_footer(text="Fill your Qi, buy a pill at /shop, then use /breakthrough")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /breakthrough ─────────────────────────────────────────────────────────

    @app_commands.command(name="breakthrough", description="Attempt to break through to the next realm.")
    async def breakthrough(self, interaction: discord.Interaction) -> None:
        user_id  = interaction.user.id
        user_row = await db.get_or_create_user(user_id, str(interaction.user))

        realm     = user_row["realm"]
        next_realm = realm + 1

        if next_realm > 9:
            await interaction.response.send_message(
                embed=error_embed("You have reached the pinnacle. There is nowhere higher to ascend."),
                ephemeral=True,
            )
            return

        # Check pill inventory
        pill_inv = await db.get_pill_inventory(user_id)
        if pill_inv.get(next_realm, 0) < 1:
            await interaction.response.send_message(
                embed=error_embed(
                    f"You need a **{PILL_NAMES[next_realm]}** to attempt this breakthrough.\n"
                    f"Buy one at the Spirit Stone Market with `/buy pill {next_realm}`."
                ),
                ephemeral=True,
            )
            return

        # Check Qi requirement — must have filled at least Stage 1 of current realm
        # Simplified: require at least qi_for_stage(realm, 1) Qi if realm > 0
        if realm > 0:
            min_qi = qi_for_stage(realm, 1)
            if user_row["qi"] < min_qi:
                await interaction.response.send_message(
                    embed=error_embed(
                        f"Your Qi is insufficient. You need at least **{min_qi:,} Qi** "
                        f"to attempt a breakthrough from this realm.\n"
                        f"Current Qi: **{user_row['qi']:,}**"
                    ),
                    ephemeral=True,
                )
                return

        # Consume pill
        await db.use_pill(user_id, next_realm)

        # Calculate success chance
        tracker  = await db.get_cultivation_tracker(user_id)
        t        = tracker.get(next_realm, {})
        failures = t.get("failure_count", 0)
        base_prob = BREAKTHROUGH_BASE.get(next_realm, 0.30)
        prob      = min(MAX_SUCCESS, base_prob + failures * FAILURE_BONUS)

        success = random.random() < prob

        if success:
            await db.record_breakthrough_success(user_id, next_realm)
            # Assign realm role
            await self._assign_realm_role(interaction, next_realm)
            # Check general title unlocks for realm
            await self._check_realm_titles(interaction, user_id, next_realm)
            # Announce in breakthrough hall
            await self._announce_breakthrough(interaction, next_realm)

            embed = discord.Embed(
                title=f"🎉 Breakthrough Success! {realm_emoji(next_realm)}",
                description=(
                    f"Your Qi coalesces into a new form.\n"
                    f"You have ascended to **{REALM_NAMES[next_realm]}**!\n\n"
                    f"*The river sings your name.*"
                ),
                color=0xFFD700,
            )
        else:
            await db.record_breakthrough_failure(user_id, next_realm)
            new_failures = failures + 1
            new_prob     = min(MAX_SUCCESS, base_prob + new_failures * FAILURE_BONUS)
            next_cost    = tracker.get(next_realm, {}).get("current_pill_cost", PILL_BASE_PRICES[next_realm]) * 2

            embed = discord.Embed(
                title="💥 Breakthrough Failed",
                description=(
                    f"The heavenly tribulation overwhelmed you.\n"
                    f"Your foundation held, but the pill was consumed.\n\n"
                    f"**Failure #{new_failures}** — next attempt: **{new_prob*100:.0f}%** success\n"
                    f"Next pill cost has increased to **{fmt_stones(next_cost)}**"
                ),
                color=0xE74C3C,
            )

        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /titles ───────────────────────────────────────────────────────────────

    @app_commands.command(name="titles", description="View all titles you have earned.")
    async def titles(self, interaction: discord.Interaction) -> None:
        user_id = interaction.user.id
        await db.get_or_create_user(user_id, str(interaction.user))
        earned = await db.get_earned_titles(user_id)   # list of title_ids

        if not earned:
            await interaction.response.send_message(
                embed=error_embed("You haven't earned any titles yet. Start fishing!"),
                ephemeral=True,
            )
            return

        user_row    = await db.get_user(user_id)
        active_id   = user_row.get("active_title_id")
        embed = discord.Embed(title=f"📜 {interaction.user.display_name}'s Titles", color=0xFFD700)

        lines = []
        for tid in earned:
            t = TITLE_BY_ID.get(tid)
            if not t:
                continue
            active_mark = "✅ " if tid == active_id else ""
            lines.append(f"{active_mark}**{t['name']}** — ×{t['xp_mult']:.2f} XP · ×{t['qi_mult']:.2f} Qi")

        # Chunk into fields
        chunk_size = 15
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i+chunk_size]
            embed.add_field(name=f"Titles {i+1}–{i+len(chunk)}", value="\n".join(chunk), inline=False)

        embed.set_footer(text=f"{len(earned)} title(s) earned  •  Equip with /title equip <name>")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /title equip ──────────────────────────────────────────────────────────

    title_group = app_commands.Group(name="title", description="Manage your active title.")

    @title_group.command(name="equip", description="Set your active title.")
    @app_commands.describe(name="Title name to equip")
    async def title_equip(self, interaction: discord.Interaction, name: str) -> None:
        user_id = interaction.user.id
        title   = next((t for t in ALL_TITLES if t["name"].lower() == name.lower()), None)
        if not title:
            await interaction.response.send_message(embed=error_embed(f"No title named **{name}**."), ephemeral=True)
            return
        earned = await db.get_earned_titles(user_id)
        if title["id"] not in earned:
            await interaction.response.send_message(embed=error_embed("You haven't earned this title."), ephemeral=True)
            return
        await db.set_active_title(user_id, title["id"])
        await interaction.response.send_message(
            embed=success_embed(
                f"Active title set to **{title['name']}**!\n"
                f"Bonuses: ×{title['xp_mult']:.2f} Fishing XP · ×{title['qi_mult']:.2f} Qi"
            ),
            ephemeral=True,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _assign_realm_role(self, interaction: discord.Interaction, realm: int) -> None:
        if not interaction.guild:
            return
        realm_role_names = {
            1: "Qi Condensation", 2: "Foundation Establishment", 3: "Golden Core",
            4: "Nascent Soul",    5: "Spirit Severing",          6: "Void Crossing",
            7: "Dao Manifestation",8:"Immortal Ascension",       9: "Eternal Sovereign",
        }
        # Remove old realm roles, add new
        old_names = set(realm_role_names.values())
        to_remove = [r for r in interaction.user.roles if r.name in old_names]
        new_role  = discord.utils.get(interaction.guild.roles, name=realm_role_names[realm])
        try:
            if to_remove:
                await interaction.user.remove_roles(*to_remove, reason="Realm advancement")
            if new_role:
                await interaction.user.add_roles(new_role, reason=f"Reached realm {realm}")
        except discord.Forbidden:
            pass

    async def _check_realm_titles(self, interaction: discord.Interaction,
                                  user_id: int, realm: int) -> None:
        """Award any realm-unlock general titles."""
        for t in general_titles_by_type("realm"):
            if t["unlock_value"] == realm:
                already = await db.has_title(user_id, t["id"])
                if not already:
                    await db.award_title(user_id, t["id"])
                    # Discord role
                    if interaction.guild:
                        role = discord.utils.get(interaction.guild.roles, name=t["name"])
                        if role:
                            try:
                                await interaction.user.add_roles(role, reason="Title awarded")
                            except discord.Forbidden:
                                pass

    async def _announce_breakthrough(self, interaction: discord.Interaction, realm: int) -> None:
        if not interaction.guild:
            return
        for ch in interaction.guild.text_channels:
            row = await db.get_channel_config(ch.id)
            if row and row["channel_type"] == "breakthrough_hall":
                embed = discord.Embed(
                    title=f"{realm_emoji(realm)} Breakthrough Achieved!",
                    description=(
                        f"{interaction.user.mention} has shattered their shackles and ascended to "
                        f"**{REALM_NAMES[realm]}**!\n\n"
                        f"*The river bears witness.*"
                    ),
                    color=0xFFD700,
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                await ch.send(embed=embed)
                return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CultivationCog(bot))
