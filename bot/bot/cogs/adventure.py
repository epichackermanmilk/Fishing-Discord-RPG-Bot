# =============================================================
# OMEGA BOT — ADVENTURE COG
# Eternal River Sect
# /adventure — 1-hour cooldown expedition
# =============================================================
from __future__ import annotations

import logging
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.utils.cooldowns import adventure_remaining, adventure_ready, next_adventure_ts
from bot.utils.formatters import fmt_stones, error_embed, unix_to_discord_ts

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# ADVENTURE OUTCOMES
# Each outcome dict:
#   weight      : int   — relative probability
#   type        : str   — "stones" | "xp" | "bait" | "pill" | "empty"
#   title       : str   — embed title
#   icon        : str   — emoji prefix
#   color       : int   — embed color
#   stone_range : tuple — (min, max) Spirit Stones (for type "stones")
#   xp_range    : tuple — (min, max) fishing XP
#   bait_id     : str   — bait id (for type "bait")
#   bait_qty    : tuple — (min, max) bait quantity
#   pill_realm  : None  — dynamically set to user realm +1
# ──────────────────────────────────────────────────────────────────────────────

ADVENTURE_OUTCOMES = [
    {
        "weight": 5, "type": "empty",
        "title": "The road was long and the reward was silence.",
        "icon": "🌑", "color": 0x7F8C8D,
        "description": "You returned empty-handed, but wiser for the journey.",
    },
    {
        "weight": 25, "type": "stones",
        "title": "Spirit Stone Cache Discovered!",
        "icon": "💎", "color": 0x3498DB,
        "stone_range": (50, 300),
        "description": "Buried beneath an ancient tree — a cache of Spirit Stones.",
    },
    {
        "weight": 20, "type": "stones",
        "title": "Bandit Tribute Collected",
        "icon": "⚔️", "color": 0xE74C3C,
        "stone_range": (100, 500),
        "description": "A group of rogue cultivators underestimated you. Their loss.",
    },
    {
        "weight": 18, "type": "xp",
        "title": "Ancient Fishing Scroll Found",
        "icon": "📜", "color": 0x9B59B6,
        "xp_range": (80, 250),
        "description": "The scroll contained forgotten fishing techniques. You absorbed them instantly.",
    },
    {
        "weight": 15, "type": "stones",
        "title": "Merchant Escort Reward",
        "icon": "🧳", "color": 0x2ECC71,
        "stone_range": (200, 800),
        "description": "A grateful merchant paid handsomely for your protection.",
    },
    {
        "weight": 10, "type": "bait",
        "title": "Rare Bait Found in the Wild",
        "icon": "🪱", "color": 0x1ABC9C,
        "bait_id": "jade_grub",
        "bait_qty": (3, 10),
        "description": "Glowing grubs clung to a spirit-stone formation. You collected them.",
    },
    {
        "weight": 8, "type": "stones",
        "title": "Collapsed Sect Treasury Raided",
        "icon": "🏛️", "color": 0xF7DC6F,
        "stone_range": (500, 2_000),
        "description": "The ruins of a fallen sect held treasures no one had claimed for centuries.",
    },
    {
        "weight": 5, "type": "bait",
        "title": "Golden Cricket Nest!",
        "icon": "🦗", "color": 0xFFD700,
        "bait_id": "golden_cricket",
        "bait_qty": (2, 6),
        "description": "A nest of golden crickets, singing at a spirit nexus.",
    },
    {
        "weight": 3, "type": "stones",
        "title": "Demonic Beast Defeated",
        "icon": "🐉", "color": 0xC0392B,
        "stone_range": (1_000, 5_000),
        "description": "You slew a demonic beast terrorising a village. The elders rewarded you generously.",
    },
    {
        "weight": 2, "type": "pill",
        "title": "Mysterious Pill Pavilion",
        "icon": "💊", "color": 0xA569BD,
        "description": "An abandoned pill pavilion. A single breakthrough pill rested on its altar.",
    },
    {
        "weight": 1, "type": "stones",
        "title": "Immortal Ruins Plundered!",
        "icon": "✨", "color": 0xFFFF00,
        "stone_range": (5_000, 20_000),
        "description": "The ruins of an immortal's private cultivation ground — untouched until today.",
    },
]


def _pick_outcome() -> dict:
    weights   = [o["weight"] for o in ADVENTURE_OUTCOMES]
    return random.choices(ADVENTURE_OUTCOMES, weights=weights, k=1)[0]


class AdventureCog(commands.Cog, name="Adventure"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="adventure", description="Embark on an adventure (1-hour cooldown).")
    async def adventure(self, interaction: discord.Interaction) -> None:
        user_id  = interaction.user.id
        user_row = await db.get_or_create_user(user_id, str(interaction.user))

        remaining = adventure_remaining(user_row["last_adventure"])
        if remaining > 0:
            ready_ts = int(time.time() + remaining)
            await interaction.response.send_message(
                f"⏳ You are still recovering from your last adventure. Ready {unix_to_discord_ts(ready_ts, 'R')}.",
                ephemeral=True,
            )
            return

        await db.update_last_adventure(user_id)
        await db.increment_total_adventures(user_id)

        outcome = _pick_outcome()
        stones_earned = 0
        xp_earned     = 0
        bait_gained   = None

        otype = outcome["type"]

        if otype == "stones":
            lo, hi = outcome["stone_range"]
            stones_earned = random.randint(lo, hi)
            await db.add_spirit_stones(user_id, stones_earned)
            await db.add_total_ss_earned(user_id, stones_earned)

        elif otype == "xp":
            lo, hi = outcome["xp_range"]
            xp_earned = random.randint(lo, hi)
            await db.add_fishing_xp(user_id, xp_earned)

        elif otype == "bait":
            bait_qty   = random.randint(*outcome["bait_qty"])
            bait_id    = outcome["bait_id"]
            bait_gained = (bait_id, bait_qty)
            await db.add_bait_stock(user_id, bait_id, bait_qty)

        elif otype == "pill":
            realm = user_row["realm"]
            if realm < 9:
                await db.add_pill(user_id, realm + 1, 1)

        # Update quest progress
        await db.increment_quest_progress(user_id, "adventurer", 1)

        # Build embed
        embed = discord.Embed(
            title=f"{outcome['icon']} {outcome['title']}",
            description=outcome["description"],
            color=outcome["color"],
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        if stones_earned:
            embed.add_field(name="Reward", value=fmt_stones(stones_earned), inline=True)
        if xp_earned:
            embed.add_field(name="XP Gained", value=f"+{xp_earned:,} Fishing XP", inline=True)
        if bait_gained:
            from bot.data.bait_data import get_bait
            b = get_bait(bait_gained[0])
            bname = b["name"] if b else bait_gained[0]
            embed.add_field(name="Bait Found", value=f"{bait_gained[1]}× {bname}", inline=True)
        if otype == "pill":
            from bot.cogs.shop import PILL_NAMES
            pill_name = PILL_NAMES.get(user_row["realm"] + 1, "Breakthrough Pill")
            embed.add_field(name="Item Found", value=f"1× {pill_name}", inline=True)

        next_ts = next_adventure_ts(time.time())
        embed.set_footer(text=f"Next adventure available {unix_to_discord_ts(next_ts, 'R')}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdventureCog(bot))
