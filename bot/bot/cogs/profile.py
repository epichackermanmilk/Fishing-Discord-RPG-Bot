# =============================================================
# OMEGA BOT — PROFILE COG
# Eternal River Sect
# /profile — full cultivation & fishing profile
# =============================================================
from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.data.fish_data import FISH
from bot.data.title_data import TITLE_BY_ID
from bot.data.rod_data   import get_rod, effective_cooldown
from bot.data.bait_data  import get_bait
from bot.data.lure_data  import get_lure
from bot.utils.formatters import (
    fmt_realm, fmt_stones, fmt_qi_bar, fmt_xp_bar,
    realm_emoji, level_from_xp, xp_for_level,
    qi_for_stage, REALM_NAMES, STAGE_SUFFIXES,
)

log = logging.getLogger(__name__)

TOTAL_SPECIES = len(FISH)


class ProfileCog(commands.Cog, name="Profile"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your cultivation and fishing profile.")
    @app_commands.describe(member="View another member's profile")
    async def profile(self, interaction: discord.Interaction,
                      member: discord.Member | None = None) -> None:
        target   = member or interaction.user
        user_row = await db.get_or_create_user(target.id, str(target))

        # Derived stats
        realm         = user_row["realm"]
        stage         = user_row["stage"]
        fishing_xp    = user_row["fishing_xp"]
        fishing_level = level_from_xp(fishing_xp)
        qi            = user_row["qi"]
        spirit_stones = user_row["spirit_stones"]
        total_fish    = user_row["total_fish_caught"]
        total_ss      = user_row["total_spirit_stones_earned"]
        total_adv     = user_row["total_adventures"]

        # Gear
        rod   = get_rod(user_row["rod_id"])
        bait  = get_bait(user_row["bait_id"])
        lure  = get_lure(user_row["lure_id"])
        upgr  = await db.get_rod_upgrades(target.id) or {}
        bait_stock = await db.get_bait_stock(target.id)

        # Codex
        codex_count = await db.get_codex_discovered_count(target.id)

        # Title
        active_title_id = user_row.get("active_title_id")
        active_title    = TITLE_BY_ID.get(active_title_id) if active_title_id else None

        # Titles earned count
        earned_titles = await db.get_earned_titles(target.id)

        # XP bar
        xp_bar    = fmt_xp_bar(fishing_xp, fishing_level)
        # Qi bar (for next realm)
        qi_bar    = fmt_qi_bar(qi, realm + 1 if realm < 9 else realm, max(stage, 1)) if realm < 9 else "🏆 Peak of Cultivation"

        # Build embed
        embed = discord.Embed(
            title=f"{realm_emoji(realm)} {target.display_name}'s Profile",
            color=0x9B59B6,
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        # ── Cultivation ───
        embed.add_field(
            name="⚡ Cultivation",
            value=(
                f"**Realm:** {fmt_realm(realm, stage)}\n"
                f"**Qi:** {qi_bar}"
            ),
            inline=True,
        )

        # ── Fishing ───
        embed.add_field(
            name="🎣 Fishing",
            value=(
                f"**Level:** {fishing_level}\n"
                f"{xp_bar}\n"
                f"**Total Caught:** {total_fish:,}"
            ),
            inline=True,
        )

        embed.add_field(name="​", value="​", inline=True)

        # ── Economy ───
        embed.add_field(
            name="💎 Economy",
            value=(
                f"**Spirit Stones:** {fmt_stones(spirit_stones)}\n"
                f"**Total Earned:** {fmt_stones(total_ss)}\n"
                f"**Adventures:** {total_adv:,}"
            ),
            inline=True,
        )

        # ── Gear ───
        bait_qty = bait_stock.get(user_row["bait_id"], 0) if bait else 0
        cd       = effective_cooldown(rod["id"], upgr.get("reel_speed_tier", 0)) if rod else 10
        embed.add_field(
            name="🎣 Equipped Gear",
            value=(
                f"**Rod:** {rod['name'] if rod else '—'} (cd: {cd:.0f}s)\n"
                f"**Bait:** {bait['name'] if bait else '—'} ×{bait_qty}\n"
                f"**Lure:** {lure['name'] if lure else '—'}"
            ),
            inline=True,
        )

        embed.add_field(name="​", value="​", inline=True)

        # ── Progression ───
        embed.add_field(
            name="📊 Progression",
            value=(
                f"**Codex:** {codex_count}/{TOTAL_SPECIES} species\n"
                f"**Titles Earned:** {len(earned_titles)}"
            ),
            inline=True,
        )

        # ── Active Title ───
        if active_title:
            embed.add_field(
                name=f"📜 Active Title — {active_title['name']}",
                value=(
                    f"*{active_title['description']}*\n"
                    f"XP ×{active_title['xp_mult']:.2f}  ·  Qi ×{active_title['qi_mult']:.2f}"
                ),
                inline=False,
            )

        embed.set_footer(text="Eternal River Sect  •  /titles to see all earned titles")
        await interaction.response.send_message(embed=embed, ephemeral=(member is None))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCog(bot))
