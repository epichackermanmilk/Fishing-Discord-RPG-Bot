# =============================================================
# OMEGA BOT — DISPLAY FORMATTERS
# Eternal River Sect
# =============================================================
"""
Pure functions for turning raw game data into human-readable
strings and Discord embed objects.
No DB calls here — all data passed in.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

import discord

from bot.data.fish_data import (
    QUALITY_DISPLAY, QUALITY_MULTIPLIERS, QUALITY_TIERS,
    get_size_multiplier,
)

# ──────────────────────────────────────────────────────────────────────────────
# Realm / Stage names
# ──────────────────────────────────────────────────────────────────────────────

REALM_NAMES = {
    0: "Mortal",
    1: "Qi Condensation",
    2: "Foundation Establishment",
    3: "Golden Core",
    4: "Nascent Soul",
    5: "Spirit Severing",
    6: "Void Crossing",
    7: "Dao Manifestation",
    8: "Immortal Ascension",
    9: "Eternal Sovereign",
}

STAGE_SUFFIXES = [
    "Initial Stage",
    "Early Stage",
    "Mid Stage",
    "Late Stage",
    "Peak Stage",
    "Minor Perfection",
    "Major Perfection",
    "Pinnacle",
    "Peak Pinnacle",
]

REALM_EMOJIS = {
    0: "🌿", 1: "💧", 2: "🪨", 3: "🔥",
    4: "🌀", 5: "⚔️",  6: "🌌", 7: "☯️",
    8: "✨", 9: "👑",
}


def fmt_realm(realm: int, stage: int) -> str:
    """e.g. 'Golden Core — Mid Stage'"""
    rname = REALM_NAMES.get(realm, f"Realm {realm}")
    if realm == 0:
        return rname
    sname = STAGE_SUFFIXES[min(stage, len(STAGE_SUFFIXES) - 1)]
    return f"{rname} — {sname}"


def realm_emoji(realm: int) -> str:
    return REALM_EMOJIS.get(realm, "🌿")


# ──────────────────────────────────────────────────────────────────────────────
# Number formatting
# ──────────────────────────────────────────────────────────────────────────────

def fmt_stones(amount: int) -> str:
    """'12,345 Spirit Stones'"""
    return f"{amount:,} Spirit Stones"


def fmt_number(n: int | float) -> str:
    """'1,234,567'"""
    return f"{n:,}"


def fmt_size(size_cm: float) -> str:
    """'45.3 cm'"""
    return f"{size_cm:.1f} cm"


def fmt_pct(value: float) -> str:
    """'42.5%'"""
    return f"{value * 100:.1f}%"


def fmt_duration(seconds: float) -> str:
    """Human-readable duration: '1h 23m 45s'"""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    parts  = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s or not parts: parts.append(f"{s}s")
    return " ".join(parts)


def fmt_cooldown(remaining: float) -> str:
    """'Ready!' or 'XX:XX remaining'"""
    if remaining <= 0:
        return "✅ Ready!"
    m, s = divmod(int(remaining), 60)
    return f"⏳ {m:02d}:{s:02d} remaining"


# ──────────────────────────────────────────────────────────────────────────────
# Fish / Catch formatting
# ──────────────────────────────────────────────────────────────────────────────

QUALITY_COLORS = {
    "dust":     0x8B8B8B,
    "bronze":   0xCD7F32,
    "jade":     0x00A86B,
    "gold":     0xFFD700,
    "astral":   0x9B59B6,
    "immortal": 0xF7DC6F,
}


def quality_color(quality: str) -> int:
    return QUALITY_COLORS.get(quality, 0x8B8B8B)


def fmt_quality(quality: str) -> str:
    return QUALITY_DISPLAY.get(quality, quality.capitalize())


def catch_value(fish: dict, quality: str, size: float) -> int:
    """
    Compute Spirit Stone value for a caught fish.
    Fish with base_value (junk/misc) use flat pricing with quality mult.
    Regular fish use the formula:
        value = ceil( (5 × (1 + 0.25×(tier-1)))^(2.5 - w) × q_mult × s_mult )
    where w = quality_weight index 0-5 mapped to 0.0-1.0
    """
    tier = fish.get("tier", 1)
    qm   = QUALITY_MULTIPLIERS.get(quality, 1.0)
    sm, _ = get_size_multiplier(size, fish["avg_size"])

    if fish.get("base_value") is not None:
        return max(1, math.ceil(fish["base_value"] * qm * sm))

    qi = QUALITY_TIERS.index(quality) if quality in QUALITY_TIERS else 0
    w  = qi / (len(QUALITY_TIERS) - 1)   # 0.0 (dust) → 1.0 (immortal)
    base = (5 * (1 + 0.25 * (tier - 1))) ** (2.5 - w)
    return max(1, math.ceil(base * qm * sm))


def build_catch_embed(fish: dict, quality: str, size: float, value: int,
                      xp_gained: int, user: discord.User | discord.Member,
                      is_rare: bool = False) -> discord.Embed:
    """
    Construct the embed shown after a successful /reel catch.
    Tier 4+ triggers a public announcement; this same embed is used.
    """
    _, size_label = get_size_multiplier(size, fish["avg_size"])
    qual_str      = fmt_quality(quality)
    color         = quality_color(quality)

    title = f"🎣 {'⭐ Rare Catch! ' if is_rare else ''}{fish['name']}"
    embed = discord.Embed(title=title, color=color)
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

    embed.add_field(name="Quality",       value=qual_str,          inline=True)
    embed.add_field(name="Size",          value=f"{size_label} ({fmt_size(size)})", inline=True)
    embed.add_field(name="Value",         value=fmt_stones(value),  inline=True)
    embed.add_field(name="XP Gained",     value=f"+{xp_gained} XP", inline=True)

    tier_stars = "⭐" * fish["tier"] if fish["tier"] > 0 else "🗑️"
    embed.set_footer(text=f"Tier {fish['tier']} {tier_stars}  •  {fish['category'].capitalize()}")
    return embed


def build_junk_embed(fish: dict, value: int, xp_gained: int,
                     user: discord.User | discord.Member) -> discord.Embed:
    """Embed for catching junk / misc items."""
    embed = discord.Embed(
        title=f"🪣 {fish['name']}",
        description=f"*Hmm. Not exactly a fish.*",
        color=0x8B8B8B,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.add_field(name="Value",     value=fmt_stones(value),   inline=True)
    embed.add_field(name="XP Gained", value=f"+{xp_gained} XP", inline=True)
    return embed


# ──────────────────────────────────────────────────────────────────────────────
# Inventory / Fish listing
# ──────────────────────────────────────────────────────────────────────────────

def fmt_fish_row(row: dict, index: int) -> str:
    """
    Format a single fish_inventory row as a compact list line.
    row must have: id, species_id, quality, size, value, name (joined from fish_data).
    """
    qual = fmt_quality(row["quality"])
    _, size_label = get_size_multiplier(row["size"], row.get("avg_size", row["size"]))
    return (
        f"`#{index:>3}` **{row['name']}** — {qual} · {size_label} ({fmt_size(row['size'])}) "
        f"· {fmt_stones(row['value'])}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# XP / Level
# ──────────────────────────────────────────────────────────────────────────────

# XP needed per fishing level (quadratic scaling)
def xp_for_level(level: int) -> int:
    """Total XP needed to *reach* this level from level 1."""
    if level <= 1:
        return 0
    return int(100 * (level - 1) ** 1.6)


def xp_to_next_level(current_xp: int, current_level: int) -> int:
    """XP still needed to reach current_level + 1."""
    needed = xp_for_level(current_level + 1) - xp_for_level(current_level)
    progress = current_xp - xp_for_level(current_level)
    return max(0, needed - progress)


def level_from_xp(total_xp: int) -> int:
    """Compute what level a given total XP amount corresponds to."""
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    return level


def fmt_xp_bar(current_xp: int, level: int, bar_len: int = 12) -> str:
    """
    Return a visual XP progress bar like:
    ▓▓▓▓▓▓░░░░░░  1,250 / 2,000 XP
    """
    base      = xp_for_level(level)
    next_base = xp_for_level(level + 1)
    span      = next_base - base
    progress  = current_xp - base
    ratio     = min(1.0, progress / span) if span > 0 else 1.0
    filled    = int(ratio * bar_len)
    bar       = "▓" * filled + "░" * (bar_len - filled)
    return f"{bar}  {progress:,} / {span:,} XP"


# ──────────────────────────────────────────────────────────────────────────────
# Qi / Cultivation
# ──────────────────────────────────────────────────────────────────────────────

def qi_for_stage(realm: int, stage: int) -> int:
    """Qi required to fill the given stage of a realm."""
    if realm == 0:
        return 0
    return int(100 * stage * (1.5 ** (realm - 1)))


def total_qi_for_realm(realm: int) -> int:
    """Total Qi to fill all 9 stages in a realm."""
    return sum(qi_for_stage(realm, s) for s in range(1, 10))


def fmt_qi_bar(current_qi: int, realm: int, stage: int, bar_len: int = 12) -> str:
    needed = qi_for_stage(realm, stage)
    if needed == 0:
        return "∞ (Mortal Realm)"
    ratio  = min(1.0, current_qi / needed)
    filled = int(ratio * bar_len)
    bar    = "▓" * filled + "░" * (bar_len - filled)
    return f"{bar}  {current_qi:,} / {needed:,} Qi"


# ──────────────────────────────────────────────────────────────────────────────
# Timestamps
# ──────────────────────────────────────────────────────────────────────────────

def unix_to_discord_ts(ts: float, style: str = "R") -> str:
    """Return a Discord timestamp string like <t:123456789:R>."""
    return f"<t:{int(ts)}:{style}>"


def now_unix() -> float:
    return datetime.now(timezone.utc).timestamp()


# ──────────────────────────────────────────────────────────────────────────────
# Generic embed builder
# ──────────────────────────────────────────────────────────────────────────────

def base_embed(title: str, description: str = "", color: int = 0x2ECC71) -> discord.Embed:
    """Return a styled base embed with the sect footer."""
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Eternal River Sect  •  Omega Bot")
    return embed


def error_embed(message: str) -> discord.Embed:
    return discord.Embed(title="⛔ Error", description=message, color=0xE74C3C)


def success_embed(message: str) -> discord.Embed:
    return discord.Embed(title="✅ Success", description=message, color=0x2ECC71)


def info_embed(title: str, message: str) -> discord.Embed:
    return discord.Embed(title=f"ℹ️ {title}", description=message, color=0x3498DB)
