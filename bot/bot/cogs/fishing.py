# =============================================================
# OMEGA BOT — FISHING COG
# Eternal River Sect
# /reel command
# =============================================================
from __future__ import annotations

import asyncio
import logging
import math
import random
import time
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from bot.database import db
from bot.data.fish_data import (
    FISH, FISH_BY_ID, QUALITY_TIERS, QUALITY_MULTIPLIERS,
    get_fish_by_biome, get_size_multiplier,
    EVENTS,
)
from bot.data.bait_data import get_bait, get_max_stack
from bot.data.lure_data import get_lure
from bot.data.rod_data  import get_rod, effective_cooldown, effective_xp_bonus, effective_pouch_luck
from bot.data.title_data import get_species_title
from bot.utils.checks      import get_biome_for_channel, channel_is_fishing
from bot.utils.cooldowns   import reel_remaining, reel_ready, SPIRIT_POUCH_EVERY_N
from bot.utils.formatters  import (
    catch_value, build_catch_embed, build_junk_embed,
    fmt_stones, fmt_cooldown, fmt_realm, quality_color, fmt_quality,
    level_from_xp, xp_for_level, base_embed, error_embed,
    unix_to_discord_ts,
)

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

TIER_ANNOUNCE_THRESHOLD = 4   # Tier 4+ catches get public announcement
REEL_COUNTDOWN_SECONDS  = 3   # Animated countdown before reveal
BITE_BASE_CHANCE        = 0.85 # Base probability of a bite (not empty cast)

# Spirit Pouch quality outcome weights (0-100 rod_luck → shift towards better)
# Format: {quality: base_weight}
POUCH_BASE_WEIGHTS = {
    "dust":     50,
    "bronze":   25,
    "jade":     15,
    "gold":     7,
    "astral":   2,
    "immortal": 1,
}

# Qi gained per message (base, no multiplier applied here)
QI_PER_MESSAGE = 3

# Qi per fish catch (applied after realm multipliers in cultivation cog)
QI_PER_CATCH_BASE = 10


# ──────────────────────────────────────────────────────────────────────────────
# CATCH LOGIC HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _pick_quality(bait: dict | None, lure: dict | None, rod: dict | None,
                  fish: dict) -> str:
    """
    Weighted random quality selection.
    Base weights: dust=40, bronze=30, jade=18, gold=8, astral=3, immortal=1
    Biases from bait, lure, and rod are additive.
    """
    base = {"dust": 40, "bronze": 30, "jade": 18, "gold": 8, "astral": 3, "immortal": 1}

    for src in (bait, lure):
        if src and src.get("quality_bias"):
            for q, delta in src["quality_bias"].items():
                base[q.lower()] = base.get(q.lower(), 0) + delta * 10

    if rod:
        bonus = rod.get("quality_bonus", 0) * 10
        for q in base:
            base[q] += bonus

    population = list(base.keys())
    weights    = [max(0.1, base[q]) for q in population]
    return random.choices(population, weights=weights, k=1)[0]


def _pick_size(fish: dict, lure: dict | None) -> float:
    """
    Size is normally distributed around avg_size with ±60% std dev.
    Lure size_bias shifts the mean up ("large") or down ("small").
    """
    avg = fish["avg_size"]
    std = avg * 0.45

    bias = lure.get("size_bias") if lure else None
    if bias == "large":
        avg *= 1.25
    elif bias == "small":
        avg *= 0.75

    size = random.gauss(avg, std)
    # Clamp to reasonable bounds
    return max(avg * 0.05, size)


def _pick_fish(biome_id: str, bait: dict | None, lure: dict | None,
               event_fish_id: str | None) -> dict | None:
    """
    Weighted random fish selection for the given biome.
    Applies rare bonuses from bait and lure.
    """
    pool = get_fish_by_biome(biome_id, include_event=bool(event_fish_id))
    if not pool:
        return None

    # If there's an active event, include the event fish and filter to only
    # fish that belong to this biome or belong to the active event
    if event_fish_id:
        pool = [f for f in pool if not f["is_event"] or f["id"] == event_fish_id]
    else:
        pool = [f for f in pool if not f["is_event"]]

    if not pool:
        return None

    rare_bonus = 0.0
    if bait:
        rare_bonus += bait.get("rare_bonus", 0.0)
    if lure:
        rare_bonus += lure.get("rare_bonus", 0.0)

    def weight(f: dict) -> float:
        w = f["loot_weight"]
        if f.get("is_rare") and rare_bonus > 0:
            w *= (1 + rare_bonus * 5)
        return w

    weights = [weight(f) for f in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def _compute_xp(fish: dict, quality: str, rod: dict, rod_upgrade: dict,
                active_title: dict | None, bait: dict | None) -> int:
    """
    base_xp × rod_xp_mult × bait_xp_mult × title_xp_mult
    """
    base    = fish["obtain_xp"]
    rod_m   = effective_xp_bonus(rod["id"], rod_upgrade.get("xp_bonus_tier", 0))
    bait_m  = bait.get("xp_bonus", 1.0) if bait else 1.0
    title_m = active_title.get("xp_mult", 1.0) if active_title else 1.0
    return max(1, int(base * rod_m * bait_m * title_m))


def _spirit_pouch_quality(pouch_luck: int) -> str:
    """
    pouch_luck (0-100) shifts weight toward higher quality.
    """
    weights = {}
    for q, w in POUCH_BASE_WEIGHTS.items():
        idx = list(POUCH_BASE_WEIGHTS.keys()).index(q)
        weights[q] = max(0.1, w + (pouch_luck * idx * 0.5))
    pop     = list(weights.keys())
    wts     = [weights[q] for q in pop]
    return random.choices(pop, weights=wts, k=1)[0]


# ──────────────────────────────────────────────────────────────────────────────
# BUTTON VIEWS
# ──────────────────────────────────────────────────────────────────────────────

class CatchActionView(discord.ui.View):
    """Buttons shown after a catch: Keep / Sell Immediately / Reel Again."""

    def __init__(self, fish_db_id: int, fish: dict, value: int,
                 user_id: int, cog: "FishingCog", *, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.fish_db_id = fish_db_id
        self.fish       = fish
        self.value      = value
        self.user_id    = user_id
        self.cog        = cog
        self.done       = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your catch!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🎒 Keep", style=discord.ButtonStyle.secondary)
    async def keep(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.done = True
        self.stop()
        await interaction.response.edit_message(
            content="✅ Added to inventory.",
            embed=None,
            view=None,
        )

    @discord.ui.button(label="💰 Sell Now", style=discord.ButtonStyle.success)
    async def sell_now(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.done = True
        self.stop()
        sold = await db.sell_fish_by_id(self.user_id, self.fish_db_id)
        if sold:
            await interaction.response.edit_message(
                content=f"💰 Sold for **{fmt_stones(self.value)}**!",
                embed=None,
                view=None,
            )
            # Trigger channel unlock checks (Celestial Peak condition)
            if interaction.guild and isinstance(interaction.user, discord.Member):
                from bot.utils.unlock_checker import check_unlocks
                asyncio.create_task(check_unlocks(self.cog.bot, interaction.user, interaction.guild))
        else:
            await interaction.response.edit_message(
                content="⚠️ Could not sell — fish may have already been sold.",
                embed=None,
                view=None,
            )

    @discord.ui.button(label="🎣 Reel Again", style=discord.ButtonStyle.primary)
    async def reel_again(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.done = True
        self.stop()

        user    = interaction.user
        channel = interaction.channel

        # ── Re-validate everything before consuming the interaction response ──

        if not await channel_is_fishing(channel.id):
            await interaction.response.send_message(
                "⛔ You can only fish in designated fishing channels.", ephemeral=True)
            return

        biome_id = await get_biome_for_channel(channel.id)
        if not biome_id:
            await interaction.response.send_message(
                "⛔ This channel has no biome configured.", ephemeral=True)
            return

        user_row = await db.get_or_create_user(user.id, str(user))

        if not await db.user_has_channel_access(user.id, channel.id):
            row = await db.get_channel_config(channel.id)
            if row and row.get("unlock_condition"):
                await interaction.response.send_message(
                    "🔒 You have not unlocked access to this fishing channel yet.", ephemeral=True)
                return

        rod_id          = user_row["rod_id"]
        rod_upgrade_row = await db.get_rod_upgrades(user.id)
        reel_spd_tier   = rod_upgrade_row["reel_speed_tier"] if rod_upgrade_row else 0
        remaining       = reel_remaining(user_row["last_reel"], rod_id, reel_spd_tier)

        if remaining > 0:
            ready_ts = int(time.time() + remaining)
            await interaction.response.send_message(
                f"⏳ Your line is still soaking. Ready {unix_to_discord_ts(ready_ts, 'R')}.",
                ephemeral=True,
            )
            return

        bait_id  = user_row["bait_id"]
        has_bait = await db.consume_bait(user.id, bait_id)
        if not has_bait:
            if bait_id != "spirit_worm":
                fallback = await db.consume_bait(user.id, "spirit_worm")
                if fallback:
                    bait_id = "spirit_worm"
                    await db.set_user_bait(user.id, "spirit_worm")
                else:
                    await interaction.response.send_message(
                        "🪱 You're out of bait! Buy more at the **Spirit Stone Market** with `/shop`.",
                        ephemeral=True,
                    )
                    return
            else:
                await interaction.response.send_message(
                    "🪱 You're out of bait! Buy more at the **Spirit Stone Market** with `/shop`.",
                    ephemeral=True,
                )
                return

        bait = get_bait(bait_id)
        lure = get_lure(user_row["lure_id"])
        rod  = get_rod(rod_id)

        await db.update_last_reel(user.id)

        # ── Transform the catch embed into the new cast message ───────────────
        await interaction.response.edit_message(
            content="🎣 Casting your line...", embed=None, view=None)
        msg = await interaction.original_response()

        await self.cog._reel_core(
            interaction, msg, user, biome_id, user_row,
            bait, lure, rod, rod_upgrade_row,
        )

    async def on_timeout(self):
        # Fish stays in inventory on timeout — buttons just go stale
        self.stop()


# ──────────────────────────────────────────────────────────────────────────────
# FISHING COG
# ──────────────────────────────────────────────────────────────────────────────

class FishingCog(commands.Cog, name="Fishing"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # In-memory cast counter {user_id: cast_count}
        self._cast_counts: dict[int, int] = {}

    # ── /reel ─────────────────────────────────────────────────────────────────

    @discord.app_commands.command(name="reel", description="Cast your line and see what bites!")
    async def reel(self, interaction: discord.Interaction) -> None:
        user    = interaction.user
        channel = interaction.channel

        # 1. Channel check
        if not await channel_is_fishing(channel.id):
            await interaction.response.send_message(
                "⛔ You can only fish in designated fishing channels.",
                ephemeral=True,
            )
            return

        biome_id = await get_biome_for_channel(channel.id)
        if not biome_id:
            await interaction.response.send_message(
                "⛔ This channel has no biome configured. Contact an administrator.",
                ephemeral=True,
            )
            return

        # 2. Load user
        user_row = await db.get_or_create_user(user.id, str(user))

        # 3. Locked channel check
        if not await db.user_has_channel_access(user.id, channel.id):
            row = await db.get_channel_config(channel.id)
            if row and row.get("unlock_condition"):
                await interaction.response.send_message(
                    "🔒 You have not unlocked access to this fishing channel yet.",
                    ephemeral=True,
                )
                return

        # 4. Cooldown check
        rod_id          = user_row["rod_id"]
        rod_upgrade_row = await db.get_rod_upgrades(user.id)
        reel_spd_tier   = rod_upgrade_row["reel_speed_tier"] if rod_upgrade_row else 0
        remaining       = reel_remaining(user_row["last_reel"], rod_id, reel_spd_tier)

        if remaining > 0:
            ready_ts = int(time.time() + remaining)
            await interaction.response.send_message(
                f"⏳ Your line is still soaking. Ready {unix_to_discord_ts(ready_ts, 'R')}.",
                ephemeral=True,
            )
            return

        # 5. Bait check
        bait_id  = user_row["bait_id"]
        has_bait = await db.consume_bait(user.id, bait_id)
        if not has_bait:
            # Try to fall back to spirit_worm if equipped bait is empty
            if bait_id != "spirit_worm":
                fallback = await db.consume_bait(user.id, "spirit_worm")
                if fallback:
                    bait_id = "spirit_worm"
                    await db.set_user_bait(user.id, "spirit_worm")
                else:
                    await interaction.response.send_message(
                        "🪱 You're out of bait! Buy more at the **Spirit Stone Market** with `/shop`.",
                        ephemeral=True,
                    )
                    return
            else:
                await interaction.response.send_message(
                    "🪱 You're out of bait! Buy more at the **Spirit Stone Market** with `/shop`.",
                    ephemeral=True,
                )
                return

        # 6. Load gear
        bait   = get_bait(bait_id)
        lure   = get_lure(user_row["lure_id"])
        rod    = get_rod(rod_id)

        # 7. Update last_reel timestamp
        await db.update_last_reel(user.id)

        # 8. Animated countdown
        await interaction.response.send_message("🎣 Casting your line...")
        msg = await interaction.original_response()

        await self._reel_core(
            interaction, msg, user, biome_id, user_row,
            bait, lure, rod, rod_upgrade_row,
        )

    # ── Core reel logic (shared between /reel and Reel Again button) ──────────

    async def _reel_core(
        self,
        interaction: discord.Interaction,
        msg: discord.Message,
        user: discord.Member,
        biome_id: str,
        user_row: dict,
        bait: dict | None,
        lure: dict | None,
        rod: dict | None,
        rod_upgrade_row: dict | None,
    ) -> None:
        """Run the countdown + catch sequence using *msg* as the editable message."""

        # 9. Animated countdown (msg already shows "🎣 Casting your line...")
        for i in range(REEL_COUNTDOWN_SECONDS, 0, -1):
            await asyncio.sleep(1)
            dots = "." * (REEL_COUNTDOWN_SECONDS - i + 1)
            await msg.edit(content=f"🎣 Waiting for a bite{dots} `{i}s`")

        await asyncio.sleep(1)

        # 10. Empty cast check (bite chance)
        bite_chance = BITE_BASE_CHANCE
        if bait:
            bite_chance += bait.get("bite_bonus", 0.0)
        if lure:
            bite_chance += lure.get("bite_bonus", 0.0)
        bite_chance = min(0.97, bite_chance)

        if random.random() > bite_chance:
            await msg.edit(content="🌊 Nothing bit... The river is silent. Better luck next cast.")
            return

        # 11. Check for active event
        event_fish_id = await db.get_active_event_fish(biome_id)

        # 12. Pick fish
        fish = _pick_fish(biome_id, bait, lure, event_fish_id)
        if not fish:
            await msg.edit(content="🌊 The waters are empty here. Strange.")
            return

        # 13. Quality & size
        quality = _pick_quality(bait, lure, rod, fish)
        size    = _pick_size(fish, lure)
        value   = catch_value(fish, quality, size)

        # 14. XP
        active_title_id  = user_row.get("active_title_id")
        active_title_row = await db.get_title(active_title_id) if active_title_id else None
        xp_gained = _compute_xp(fish, quality, rod, rod_upgrade_row or {}, active_title_row, bait)

        # 15. Store fish in DB
        fish_db_id = await db.add_fish(
            user_id=user.id,
            species_id=fish["id"],
            quality=quality,
            size=round(size, 1),
            value=value,
        )

        # 16. Update user stats
        await db.add_fishing_xp(user.id, xp_gained)
        await db.increment_fish_caught(user.id, value)

        # 17. Codex update
        await db.update_codex(
            user_id=user.id,
            species_id=fish["id"],
            quality=quality,
            size=round(size, 1),
            value=value,
        )

        # 18. Quest progress
        await self._update_quests(user.id, fish)

        # 18a. Mark biome as fished + trigger channel unlock checks
        if fish["category"] not in ("junk",):
            await db.mark_biome_fished(user.id, biome_id)
        if interaction.guild and isinstance(interaction.user, discord.Member):
            from bot.utils.unlock_checker import check_unlocks
            asyncio.create_task(check_unlocks(self.bot, interaction.user, interaction.guild))

        # 19. Title unlock check
        await self._check_title_unlock(interaction, user.id, fish)

        # 20. Level-up check
        await self._check_level_up(interaction, user.id, xp_gained)

        # 21. Spirit Pouch (every N-th cast)
        self._cast_counts[user.id] = self._cast_counts.get(user.id, 0) + 1
        pouch_embed = None
        if self._cast_counts[user.id] % SPIRIT_POUCH_EVERY_N == 0:
            pouch_embed = await self._award_spirit_pouch(user.id, rod, rod_upgrade_row or {})

        # 22. Build catch embed
        is_junk = fish["category"] in ("junk",)
        is_rare = fish.get("is_rare", False)

        if is_junk:
            embed = build_junk_embed(fish, value, xp_gained, user)
        else:
            embed = build_catch_embed(fish, quality, round(size, 1), value, xp_gained, user, is_rare)

        # 23. View (with Reel Again)
        view = CatchActionView(fish_db_id, fish, value, user.id, self)

        await msg.edit(content=None, embed=embed, view=view)

        # 24. Tier 4+ public announcement
        if fish["tier"] >= TIER_ANNOUNCE_THRESHOLD and not is_junk:
            await self._send_announcement(interaction, fish, quality, size, value, user)

        # 25. Spirit Pouch follow-up
        if pouch_embed:
            await interaction.followup.send(embed=pouch_embed, ephemeral=False)

    # ── Quest progress update ─────────────────────────────────────────────────

    async def _update_quests(self, user_id: int, fish: dict) -> None:
        from bot.data.quest_data import QUESTS, QUESTS_BY_TAG
        tags = fish.get("quest_tags", [])
        quest_ids_to_update = {"total_fish_caught"}
        for tag in tags:
            for q in QUESTS_BY_TAG.get(tag, []):
                quest_ids_to_update.add(q["id"])
        for qid in quest_ids_to_update:
            await db.increment_quest_progress(user_id, qid, 1)

    # ── Title unlock check ────────────────────────────────────────────────────

    async def _check_title_unlock(self, interaction: discord.Interaction,
                                  user_id: int, fish: dict) -> None:
        for level in (1, 2):
            title_id = fish.get(f"title_l{'1' if level == 1 else '2'}")
            if not title_id:
                continue
            threshold = 1 if level == 1 else 5
            codex_row = await db.get_codex_entry(user_id, fish["id"])
            if not codex_row:
                continue
            if codex_row["caught_count"] == threshold:
                # First time reaching threshold — award title
                already = await db.has_title(user_id, title_id)
                if not already:
                    await db.award_title(user_id, title_id)
                    # Try to assign Discord role
                    from bot.data.title_data import get_title
                    t = get_title(title_id)
                    if t and interaction.guild:
                        role = discord.utils.get(interaction.guild.roles, name=t["name"])
                        if role:
                            try:
                                await interaction.user.add_roles(role, reason="Title unlocked")
                            except discord.Forbidden:
                                pass
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="📜 New Title Unlocked!",
                            description=(
                                f"**{t['name']}**\n"
                                f"*{t['description']}*\n\n"
                                f"Equip it with `/title equip`!"
                            ),
                            color=0xFFD700,
                        ),
                        ephemeral=True,
                    )

    # ── Level-up check ────────────────────────────────────────────────────────

    async def _check_level_up(self, interaction: discord.Interaction,
                              user_id: int, xp_just_gained: int) -> None:
        user_row = await db.get_user(user_id)
        if not user_row:
            return
        new_level = level_from_xp(user_row["fishing_xp"])
        if new_level > user_row["fishing_level"]:
            await db.set_fishing_level(user_id, new_level)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⬆️ Fishing Level Up!",
                    description=(
                        f"🎣 You are now **Fishing Level {new_level}**!\n"
                        f"New gear and titles may now be available."
                    ),
                    color=0x2ECC71,
                ),
                ephemeral=True,
            )

    # ── Spirit Pouch award ────────────────────────────────────────────────────

    async def _award_spirit_pouch(self, user_id: int, rod: dict,
                                  rod_upgrade: dict) -> discord.Embed | None:
        """Award a Spirit Pouch bonus — either SS or a bait refund."""
        pouch_luck = effective_pouch_luck(rod["id"], rod_upgrade.get("rod_luck_tier", 0))
        quality    = _spirit_pouch_quality(pouch_luck)

        # Pouch gives spirit stones scaled by quality
        stone_amounts = {
            "dust": (5, 25),
            "bronze": (20, 80),
            "jade": (60, 200),
            "gold": (150, 500),
            "astral": (400, 1_200),
            "immortal": (1_000, 4_000),
        }
        lo, hi = stone_amounts.get(quality, (5, 25))
        stones = random.randint(lo, hi)

        await db.add_spirit_stones(user_id, stones)

        embed = discord.Embed(
            title="👜 Spirit Pouch Found!",
            description=(
                f"Hidden beneath the waves, your {SPIRIT_POUCH_EVERY_N}th cast revealed a **{fmt_quality(quality)}** Spirit Pouch!\n"
                f"You found **{fmt_stones(stones)}** inside."
            ),
            color=quality_color(quality),
        )
        return embed

    # ── Tier 4+ announcement ──────────────────────────────────────────────────

    async def _send_announcement(self, interaction: discord.Interaction,
                                 fish: dict, quality: str, size: float,
                                 value: int, user: discord.User | discord.Member) -> None:
        if not interaction.guild:
            return
        # Find announce channel from DB
        for ch in interaction.guild.text_channels:
            row = await db.get_channel_config(ch.id)
            if row and row["channel_type"] == "announce":
                from bot.utils.formatters import fmt_size
                _, size_label = get_size_multiplier(size, fish["avg_size"])
                embed = discord.Embed(
                    title=f"🌟 Remarkable Catch — {fish['name']}!",
                    description=(
                        f"{user.mention} has pulled a **{fmt_quality(quality)}** "
                        f"**{fish['name']}** from the waters!\n"
                        f"Size: {size_label} ({fmt_size(size)})  •  "
                        f"Value: {fmt_stones(value)}"
                    ),
                    color=quality_color(quality),
                )
                embed.set_thumbnail(url=user.display_avatar.url)
                await ch.send(embed=embed)
                return

    # ── Message listener — Qi gain ────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Award Qi for every message (no cooldown)."""
        if message.author.bot:
            return
        if not message.guild:
            return

        user_id = message.author.id
        user_row = await db.get_user(user_id)
        if not user_row:
            return  # User hasn't registered via /reel yet

        # Apply title Qi multiplier
        active_title_id = user_row.get("active_title_id")
        qi_mult = 1.0
        if active_title_id:
            t = await db.get_title(active_title_id)
            if t:
                qi_mult = t.get("qi_mult", 1.0)

        qi_gained = max(1, int(QI_PER_MESSAGE * qi_mult))
        await db.add_qi(user_id, qi_gained)


# ──────────────────────────────────────────────────────────────────────────────
# COG SETUP
# ──────────────────────────────────────────────────────────────────────────────

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FishingCog(bot))
