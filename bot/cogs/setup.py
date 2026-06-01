# =============================================================
# OMEGA BOT — SERVER SETUP COG
# Eternal River Sect
# /omega_setup  (admin only)
# =============================================================
"""
Run /omega_setup to:
  1. DELETE every channel, category, and role (except @everyone & managed)
  2. Recreate them exactly as specified
  3. Apply all permission overwrites
  4. Register channels in DB
  5. Post all guide embeds
"""
from __future__ import annotations

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.utils.formatters import base_embed

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# STRUCTURE CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

CATEGORIES: list[dict] = [
    {"name": "📋 INFORMATION",                     "key": "info"},
    {"name": "🎭 ROLES",                           "key": "roles_cat"},
    {"name": "💬 GENERAL",                         "key": "general"},
    {"name": "🏯 DIVINATION HALL",                 "key": "divination"},
    {"name": "🏪 SPIRIT BAZAAR",                   "key": "bazaar"},
    {"name": "🎰 FORTUNE HOUSE",                   "key": "fortune"},
    {"name": "🌿 JADE WATERS  [Freshwater]",       "key": "fw"},
    {"name": "🌊 CRIMSON TIDES  [Saltwater]",      "key": "sw"},
    {"name": "🔒 LOCKED WATERS  [Quest Unlocked]", "key": "locked"},
    {"name": "🌑 THE PRIMORDIAL ABYSS  [Secret]",  "key": "abyss"},
    {"name": "🔊 VOICE",                           "key": "voice"},
    {"name": "🔧 MOD  [Staff Only]",               "key": "mod"},
]

# Each channel dict fields:
#   name     : displayed Discord channel name (emoji + │ + slug)
#   cat      : category key from CATEGORIES
#   type     : channel_config.channel_type stored in DB
#   biome    : biome_id (fishing channels only)
#   no_send  : @everyone cannot send messages (read-only)
#   mod_only : hidden from everyone, visible to master+elder only
#   locked   : hidden from everyone, visible to River Wayfarer + mods
#   secret   : hidden from everyone, visible to Eternal Sovereign + mods
CHANNELS: list[dict] = [
    # ── INFORMATION ──────────────────────────────────────────────────────────
    {"name": "✨│welcome",          "cat": "info",       "type": "welcome",           "no_send": True},
    {"name": "📜│rules",            "cat": "info",       "type": "rules",             "no_send": True},
    {"name": "📣│announcements",    "cat": "info",       "type": "announce",          "no_send": True},
    {"name": "📖│server-guide",     "cat": "info",       "type": "server_guide",      "no_send": True},
    {"name": "🎮│commands-guide",   "cat": "info",       "type": "commands_guide",    "no_send": True},
    {"name": "📝│patch-notes",      "cat": "info",       "type": "patch_notes",       "no_send": True},

    # ── ROLES ─────────────────────────────────────────────────────────────────
    {"name": "🎭│role-selection",   "cat": "roles_cat",  "type": "role_selection"},

    # ── GENERAL ───────────────────────────────────────────────────────────────
    {"name": "🌊│general",          "cat": "general",    "type": "general"},
    {"name": "🌸│introductions",    "cat": "general",    "type": "general"},
    {"name": "🖼️│media-lounge",    "cat": "general",    "type": "general"},
    {"name": "🗺️│adventure-grounds","cat": "general",   "type": "adventure"},

    # ── DIVINATION HALL ───────────────────────────────────────────────────────
    {"name": "🏆│breakthrough-hall",      "cat": "divination", "type": "breakthrough_hall", "no_send": True},
    {"name": "📢│heavenly-announcements", "cat": "divination", "type": "heavenly_announce", "no_send": True},

    # ── SPIRIT BAZAAR ─────────────────────────────────────────────────────────
    {"name": "💎│spirit-bazaar",    "cat": "bazaar",     "type": "shop"},

    # ── FORTUNE HOUSE ─────────────────────────────────────────────────────────
    {"name": "🎰│fortune-house",    "cat": "fortune",    "type": "gambling"},

    # ── JADE WATERS (Freshwater) ──────────────────────────────────────────────
    {"name": "🎣│jade-creek",              "cat": "fw", "type": "fishing", "biome": "freshwater1"},
    {"name": "🎣│misty-veil-river",        "cat": "fw", "type": "fishing", "biome": "freshwater2"},
    {"name": "🎣│dragons-spine-falls",     "cat": "fw", "type": "fishing", "biome": "freshwater3"},

    # ── CRIMSON TIDES (Saltwater) ─────────────────────────────────────────────
    {"name": "🎣│crimson-tide-shallows",   "cat": "sw", "type": "fishing", "biome": "saltwater1"},
    {"name": "🎣│heavens-brine-expanse",   "cat": "sw", "type": "fishing", "biome": "saltwater2"},
    {"name": "🎣│abyssal-sovereign-sea",   "cat": "sw", "type": "fishing", "biome": "saltwater3"},

    # ── LOCKED WATERS (Quest Unlocked) ───────────────────────────────────────
    {"name": "🔒│phantom-lotus-grotto",    "cat": "locked", "type": "fishing", "biome": "special1",  "locked": True},
    {"name": "🔒│celestial-peak-reservoir","cat": "locked", "type": "fishing", "biome": "special2",  "locked": True},
    {"name": "🔒│void-rift-depths",        "cat": "locked", "type": "fishing", "biome": "special3",  "locked": True},

    # ── THE PRIMORDIAL ABYSS (Secret) ─────────────────────────────────────────
    {"name": "🌑│primordial-abyss",        "cat": "abyss",  "type": "fishing", "biome": "secret",    "secret": True},

    # ── MOD (hidden from members) ─────────────────────────────────────────────
    {"name": "🔒│mod-log",          "cat": "mod",        "type": "mod_log",     "no_send": True, "mod_only": True},
    {"name": "🔒│mod-review",       "cat": "mod",        "type": "mod_review",               "mod_only": True},
    {"name": "🔒│mod-commands",     "cat": "mod",        "type": "mod_commands",              "mod_only": True},
]

VOICE_CHANNELS: list[dict] = [
    {"name": "☯️ Sect Assembly Hall",   "cat": "voice", "afk": False},
    {"name": "🎣 The Fishing Grounds",  "cat": "voice", "afk": False},
    {"name": "⚡ Cultivation Chamber",  "cat": "voice", "afk": False},
    {"name": "📖 Jade Library",         "cat": "voice", "afk": False},
    {"name": "💤 Ethereal Void",        "cat": "voice", "afk": True},
]

# ──────────────────────────────────────────────────────────────────────────────
# ROLES
# ──────────────────────────────────────────────────────────────────────────────

STANDARD_ROLES: list[dict] = [
    # ── Core server roles (displayed in sidebar, ordered top-to-bottom) ──────
    {"name": "Eternal River Sect Master",    "color": 0xFFD700, "hoist": True,  "mentionable": True,  "key": "master", "perms": "admin"},
    {"name": "Eternal River Sect Elder",     "color": 0xE67E22, "hoist": True,  "mentionable": True,  "key": "elder",  "perms": "mod"},
    {"name": "Eternal River Inner Disciple", "color": 0x2ECC71, "hoist": True,  "mentionable": False, "key": "inner"},
    {"name": "Eternal River Outer Disciple", "color": 0x5DADE2, "hoist": True,  "mentionable": False, "key": "outer"},

    # ── Special unlock roles ─────────────────────────────────────────────────
    {"name": "River Wayfarer",               "color": 0x9B59B6, "hoist": False, "mentionable": False, "key": "wayfarer"},
    {"name": "Qi Sealed",                    "color": 0x7F8C8D, "hoist": False, "mentionable": False, "key": "muted"},

    # ── Location roles (mutually exclusive) ──────────────────────────────────
    {"name": "🌍 Europe",        "color": 0x5DADE2, "hoist": False, "mentionable": False, "key": "loc_europe"},
    {"name": "🌎 North America", "color": 0x5DADE2, "hoist": False, "mentionable": False, "key": "loc_na"},
    {"name": "🌍 Africa",        "color": 0x5DADE2, "hoist": False, "mentionable": False, "key": "loc_africa"},
    {"name": "🌎 South America", "color": 0x5DADE2, "hoist": False, "mentionable": False, "key": "loc_sa"},
    {"name": "🌏 Asia",          "color": 0x5DADE2, "hoist": False, "mentionable": False, "key": "loc_asia"},
    {"name": "🌐 Oceania",       "color": 0x5DADE2, "hoist": False, "mentionable": False, "key": "loc_oceania"},

    # ── Interest / genre roles ────────────────────────────────────────────────
    {"name": "📚 Xianxia Reader", "color": 0x8E44AD, "hoist": False, "mentionable": False, "key": "genre_xianxia"},
    {"name": "⚔️ Action Fan",     "color": 0x8E44AD, "hoist": False, "mentionable": False, "key": "genre_action"},
    {"name": "🎮 Gamer",          "color": 0x8E44AD, "hoist": False, "mentionable": False, "key": "genre_gamer"},
    {"name": "🎨 Artist",         "color": 0x8E44AD, "hoist": False, "mentionable": False, "key": "genre_artist"},
    {"name": "🎵 Music Lover",    "color": 0x8E44AD, "hoist": False, "mentionable": False, "key": "genre_music"},
    {"name": "🐟 Avid Fisher",    "color": 0x8E44AD, "hoist": False, "mentionable": False, "key": "genre_fisher"},
    {"name": "📖 Story Enjoyer",  "color": 0x8E44AD, "hoist": False, "mentionable": False, "key": "genre_story"},

    # ── Realm progression roles (assigned by bot on breakthrough) ────────────
    {"name": "Mortal",                "color": 0x95A5A6, "hoist": False, "mentionable": False, "key": "realm_0"},
    {"name": "Qi Condensation",       "color": 0x7FB3D3, "hoist": False, "mentionable": False, "key": "realm_1"},
    {"name": "Foundation Establishment","color":0x82E0AA,"hoist": False, "mentionable": False, "key": "realm_2"},
    {"name": "Golden Core",           "color": 0xF7DC6F, "hoist": False, "mentionable": False, "key": "realm_3"},
    {"name": "Nascent Soul",          "color": 0xF0B27A, "hoist": False, "mentionable": False, "key": "realm_4"},
    {"name": "Spirit Severing",       "color": 0xE59866, "hoist": False, "mentionable": False, "key": "realm_5"},
    {"name": "Void Crossing",         "color": 0xA569BD, "hoist": False, "mentionable": False, "key": "realm_6"},
    {"name": "Dao Manifestation",     "color": 0x85C1E9, "hoist": False, "mentionable": False, "key": "realm_7"},
    {"name": "Immortal Ascension",    "color": 0xF8C471, "hoist": False, "mentionable": False, "key": "realm_8"},
    {"name": "Eternal Sovereign",     "color": 0xFF6B6B, "hoist": True,  "mentionable": True,  "key": "realm_9"},
]

REALM_ROLE_KEYS = {f"realm_{i}" for i in range(10)}


# ──────────────────────────────────────────────────────────────────────────────
# PERMISSIONS HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _admin_permissions() -> discord.Permissions:
    return discord.Permissions(administrator=True)


def _mod_permissions() -> discord.Permissions:
    return discord.Permissions(
        manage_messages=True,
        kick_members=True,
        ban_members=True,
        mute_members=True,
        deafen_members=True,
        move_members=True,
        view_audit_log=True,
        manage_nicknames=True,
        mention_everyone=True,
        manage_channels=True,
    )


def _channel_overwrites(chdef: dict, role_map: dict) -> dict:
    """Build the permission overwrite dict for a text channel."""
    everyone  = role_map["__everyone__"]
    master    = role_map.get("master")
    elder     = role_map.get("elder")
    muted     = role_map.get("muted")
    wayfarer  = role_map.get("wayfarer")
    eternal_s = role_map.get("realm_9")   # Eternal Sovereign → Primordial Abyss

    ow: dict = {}

    if chdef.get("mod_only"):
        # Invisible to everyone, visible to Master + Elder only
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        if master: ow[master] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if elder:  ow[elder]  = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    elif chdef.get("secret"):
        # Invisible to everyone, unlocked for Eternal Sovereign + Master + Elder
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        if eternal_s: ow[eternal_s] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if master:    ow[master]    = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if elder:     ow[elder]     = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    elif chdef.get("locked"):
        # Invisible to everyone, unlocked for River Wayfarer + Master + Elder
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        if wayfarer: ow[wayfarer] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if master:   ow[master]   = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if elder:    ow[elder]    = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if muted:    ow[muted]    = discord.PermissionOverwrite(send_messages=False, add_reactions=False)

    elif chdef.get("no_send"):
        # Visible to all, only Master + Elder can send
        ow[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=False)
        if master: ow[master] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if elder:  ow[elder]  = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        # Qi Sealed already can't send; no extra overwrite needed

    else:
        # Normal open channel
        ow[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if muted: ow[muted] = discord.PermissionOverwrite(
            send_messages=False, add_reactions=False, use_application_commands=False
        )

    return ow


def _voice_overwrites(role_map: dict) -> dict:
    everyone = role_map["__everyone__"]
    muted    = role_map.get("muted")
    ow = {everyone: discord.PermissionOverwrite(view_channel=True, connect=True)}
    if muted:
        ow[muted] = discord.PermissionOverwrite(speak=False, connect=False)
    return ow


# ──────────────────────────────────────────────────────────────────────────────
# EMBED BUILDERS
# ──────────────────────────────────────────────────────────────────────────────

def _rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📜 Rules of the Eternal River Sect",
        color=0xE74C3C,
        description="All disciples who enter the Eternal River Sect agree to these sacred laws.\n​",
    )
    rules = [
        ("1. Respect All Members",       "Treat every disciple with dignity. Harassment, hate speech, and personal attacks are forbidden."),
        ("2. No NSFW Content",           "This sect is open to all realms of cultivation. Keep content appropriate for all ages."),
        ("3. No Spam or Flooding",       "One message at a time. Excessive repetition clogs the spiritual channels."),
        ("4. English in Main Channels",  "The common tongue keeps communication flowing. Use other languages in private."),
        ("5. No Self-Promotion",         "Do not advertise other servers, services, or social media without elder approval."),
        ("6. No Exploiting Bugs",        "Report bot bugs to moderators. Exploiting them results in immediate expulsion."),
        ("7. Follow Discord ToS",        "All members must comply with Discord's Terms of Service at all times."),
        ("8. Moderators Have Final Say", "Moderator decisions are final. Disputes go to the Sect Master privately."),
        ("9. Commands in Proper Channels","Use fishing commands in fishing channels, shop in Spirit Bazaar, etc."),
        ("10. Have Fun",                 "You are here to cultivate, fish, and grow. Enjoy the journey."),
    ]
    for name, value in rules:
        embed.add_field(name=name, value=value, inline=False)
    embed.set_footer(text="Eternal River Sect  •  May your Qi flow unobstructed.")
    return embed


def _welcome_embed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title="🌊 Welcome to the Eternal River Sect",
        color=0x2ECC71,
        description=(
            "The eternal river parts to welcome a new soul.\n\n"
            "You have found your way to **the Eternal River Sect** — a sanctuary of cultivation, "
            "fishing mastery, and the immortal path.\n\n"
            "Here, disciples fish sacred rivers, refine their Qi, and ascend through realms "
            "that mortals dare not dream of.\n\n"
            "**Your journey begins with a single cast.**\n​"
        ),
    )
    embed.add_field(
        name="🎣 Getting Started",
        value=(
            "• Head to any **🌿 JADE WATERS** or **🌊 CRIMSON TIDES** channel and use `/reel`\n"
            "• Sell fish at **💎│spirit-bazaar** with `/sell all`\n"
            "• Use Spirit Stones to upgrade your rod, bait, and lures at `/shop`\n"
            "• Gain **Qi** through fishing — then use `/breakthrough` to ascend realms\n"
            "• Check your progress with `/profile`"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎭 Assign Your Roles",
        value="Visit **🎭│role-selection** to pick your location and interest roles.",
        inline=False,
    )
    embed.add_field(
        name="📜 Read the Rules",
        value="Check **📜│rules** — violations result in the **Qi Sealed** penalty.",
        inline=False,
    )
    embed.set_footer(text=f"{guild.name}  •  May your catches be legendary.")
    return embed


def _commands_guide_embeds() -> list[discord.Embed]:
    embeds = []

    e1 = discord.Embed(title="🎣 Fishing Commands", color=0x2ECC71)
    e1.add_field(name="`/reel`",           value="Cast your line. Wait for the bite!", inline=False)
    e1.add_field(name="`/profile`",        value="View your cultivation profile and fishing stats.", inline=False)
    e1.add_field(name="`/inventory`",      value="Browse your fish inventory by category.", inline=False)
    e1.add_field(name="`/codex`",          value="Your fish discovery codex — all species you've found.", inline=False)
    e1.add_field(name="`/species <name>`", value="Detailed codex entry for a specific species.", inline=False)
    e1.add_field(name="📍 Where",          value="**Fishing channels only** (Jade Waters, Crimson Tides, Locked Waters, Primordial Abyss)", inline=False)
    embeds.append(e1)

    e2 = discord.Embed(title="🏪 Shop & Economy Commands", color=0xF7DC6F)
    e2.add_field(name="`/shop`",           value="Browse the Spirit Stone Market (rods, bait, lures, pills, upgrades).", inline=False)
    e2.add_field(name="`/buy rod`",        value="Purchase a rod.", inline=False)
    e2.add_field(name="`/buy bait`",       value="Purchase bait (license required for Tier 2+).", inline=False)
    e2.add_field(name="`/buy lure`",       value="Purchase a lure.", inline=False)
    e2.add_field(name="`/buy pill`",       value="Purchase a Breakthrough Pill.", inline=False)
    e2.add_field(name="`/equip rod/bait/lure`", value="Equip owned gear.", inline=False)
    e2.add_field(name="`/sell all`",       value="Sell every fish in your inventory.", inline=False)
    e2.add_field(name="`/sell fish`",      value="Sell a specific fish by inventory ID.", inline=False)
    e2.add_field(name="`/upgrade`",        value="Upgrade your rod's stats (reel speed, XP, luck, bait capacity).", inline=False)
    e2.add_field(name="📍 Where",          value="**💎│spirit-bazaar only**", inline=False)
    embeds.append(e2)

    e3 = discord.Embed(title="⚡ Cultivation Commands", color=0xA569BD)
    e3.add_field(name="`/cultivate`",      value="View your Qi bar and realm progress.", inline=False)
    e3.add_field(name="`/breakthrough`",   value="Attempt a realm breakthrough (requires a Breakthrough Pill).", inline=False)
    e3.add_field(name="`/titles`",         value="View all titles you have earned.", inline=False)
    e3.add_field(name="`/title equip`",    value="Set your active title (boosts XP and Qi gain).", inline=False)
    e3.add_field(name="`/quests`",         value="Check your quest progress and rewards.", inline=False)
    e3.add_field(name="`/quest_claim`",    value="Claim a completed quest reward.", inline=False)
    e3.add_field(name="📍 Where",          value="Anywhere.", inline=False)
    embeds.append(e3)

    e4 = discord.Embed(title="⚔️ Adventure & Fortune Commands", color=0xE74C3C)
    e4.add_field(name="`/adventure`",      value="Embark on a 1-hour-cooldown expedition. Win Spirit Stones, XP, bait, or pills.", inline=False)
    e4.add_field(name="`/gamble buy`",     value="Buy a scratch ticket (Qi Slip / Spirit Scroll / Heavenly Decree).", inline=False)
    e4.add_field(name="`/gamble use`",     value="Scratch a ticket — 20 spots to reveal your prize.", inline=False)
    e4.add_field(name="`/gamble tickets`", value="View your unscratched ticket inventory.", inline=False)
    e4.add_field(name="📍 Where",
                 value="**`/adventure` → 🗺️│adventure-grounds only**\n**`/gamble` → 🎰│fortune-house only**",
                 inline=False)
    embeds.append(e4)

    e5 = discord.Embed(title="🌍 Role Commands", color=0x5DADE2)
    e5.add_field(name="`/role location`",  value="Assign your region role. Only one allowed at a time.", inline=False)
    e5.add_field(name="`/role interest`",  value="Toggle an interest or genre role.", inline=False)
    e5.add_field(name="📍 Where",          value="Anywhere.", inline=False)
    embeds.append(e5)

    e6 = discord.Embed(
        title="💎 NovelCodex Supporter Commands",
        color=0xF0B429,
        description="Exclusive commands for **NovelCodex.org** supporters. Requires a supporter role.",
    )
    e6.add_field(
        name="🎨 `/myrole` — Custom Role *(Seeker / Sage / Immortal Sage)*",
        value=(
            "`/myrole create [name] [#hex]` — Create a custom colour role\n"
            "`/myrole edit` — Edit your role's name or colour\n"
            "`/myrole delete` — Delete your custom role"
        ),
        inline=False,
    )
    e6.add_field(
        name="🔊 `/mychannel` — Private Voice Channel *(Reader / Scholar)*",
        value=(
            "`/mychannel create [name]` — Create a private voice channel\n"
            "`/mychannel rename [name]` — Rename it\n"
            "`/mychannel limit [0–99]` — Set a user cap\n"
            "`/mychannel add @user` — Allow someone in\n"
            "`/mychannel remove @user` — Remove someone's access\n"
            "`/mychannel delete` — Delete the channel"
        ),
        inline=False,
    )
    e6.set_footer(text="Visit NovelCodex.org to become a supporter.")
    embeds.append(e6)

    return embeds


def _server_guide_embeds() -> list[discord.Embed]:
    embeds = []

    e1 = discord.Embed(
        title="🗺️ Server Guide — Eternal River Sect",
        color=0x3498DB,
        description="A complete guide to channels, systems, and progression.\n​",
    )
    e1.add_field(
        name="📋 INFORMATION Channels",
        value=(
            "**✨│welcome** — Bot greets new disciples here\n"
            "**📜│rules** — Sacred laws of the sect\n"
            "**📣│announcements** — Official updates\n"
            "**📖│server-guide** — You are here\n"
            "**🎮│commands-guide** — Every command explained\n"
            "**📝│patch-notes** — Changelogs from the elders"
        ),
        inline=False,
    )
    e1.add_field(
        name="🎣 Fishing Channels",
        value=(
            "Each channel is a **biome** with unique fish.\n\n"
            "**🌿 JADE WATERS** (Freshwater):\n"
            "🎣│jade-creek  ·  🎣│misty-veil-river  ·  🎣│dragons-spine-falls\n\n"
            "**🌊 CRIMSON TIDES** (Saltwater):\n"
            "🎣│crimson-tide-shallows  ·  🎣│heavens-brine-expanse  ·  🎣│abyssal-sovereign-sea\n\n"
            "**🔒 LOCKED WATERS** *(individually unlocked — see below)*:\n"
            "🔒│phantom-lotus-grotto  ·  🔒│celestial-peak-reservoir  ·  🔒│void-rift-depths\n\n"
            "**🌑 THE PRIMORDIAL ABYSS** *(ultimate unlock — see below)*:\n"
            "🌑│primordial-abyss"
        ),
        inline=False,
    )
    embeds.append(e1)

    e2 = discord.Embed(title="📈 Progression Systems", color=0x2ECC71)
    e2.add_field(
        name="🎣 Fishing Level",
        value="Catch fish to earn **Fishing XP**. Higher levels unlock shop items and title milestones.",
        inline=False,
    )
    e2.add_field(
        name="⚡ Qi & Realms",
        value=(
            "Fishing fills your **Qi bar**. When full, buy a **Breakthrough Pill** and use `/breakthrough`.\n"
            "Failure raises your next chance by 5% but doubles the pill cost.\n\n"
            "**9 Realms:** Qi Condensation → Foundation → Golden Core → Nascent Soul\n"
            "→ Spirit Severing → Void Crossing → Dao Manifestation → Immortal Ascension → **Eternal Sovereign**"
        ),
        inline=False,
    )
    e2.add_field(
        name="📜 Titles",
        value="Earned by milestones. Each title adds **XP** and **Qi multipliers**. Equip with `/title equip`.",
        inline=False,
    )
    embeds.append(e2)

    e3 = discord.Embed(title="🔒 Unlocking the Hidden Waters", color=0x8E44AD)
    e3.add_field(
        name="🌸 Phantom Lotus Grotto",
        value=(
            "Catch at least **1 fish in each of the 6 default channels**.\n"
            "*(All 3 Jade Waters + all 3 Crimson Tides channels)*"
        ),
        inline=False,
    )
    e3.add_field(
        name="⛰️ Celestial Peak Reservoir",
        value=(
            "Accumulate and sell a total of **5,000 Spirit Stones** worth of fish.\n"
            "*(Tracks your all-time earnings — keep selling!)*"
        ),
        inline=False,
    )
    e3.add_field(
        name="🌀 Void Rift Depths",
        value=(
            "Catch **all 4 Elemental Fish** — one of each:\n"
            "Terra Sovereign Koi · Frost Eclipse Serpent · Solar Inferno Drake · Tempest Void Eel\n"
            "*(These appear during elemental events in any channel)*"
        ),
        inline=False,
    )
    e3.add_field(
        name="👁️ Primordial Chaos Abyss",
        value=(
            "Catch **at least 1 of every fish species** in the codex.\n"
            "*(The ultimate challenge — complete your entire Codex to enter the Abyss)*"
        ),
        inline=False,
    )
    e3.set_footer(text="Unlocks are permanent and survive server resets. You'll receive a DM when you unlock a channel.")
    embeds.append(e3)

    e4 = discord.Embed(title="🛒 Economy & Gear", color=0xF7DC6F)
    e4.add_field(name="💎 Spirit Stones", value="Earned by selling fish, quests, and adventures.", inline=False)
    e4.add_field(name="🎣 Rods",          value="Higher-tier rods reduce cooldown and boost XP. Upgrade with `/upgrade`.", inline=False)
    e4.add_field(name="🪱 Bait",          value="Consumed per cast. Better bait raises quality and rare-fish chances.", inline=False)
    e4.add_field(name="🪝 Lures",         value="Permanent accessories that modify what you catch.", inline=False)
    e4.add_field(name="💊 Breakthrough Pills", value="Required for realm ascension. Buy at **💎│spirit-bazaar**.", inline=False)
    embeds.append(e4)

    e5 = discord.Embed(title="🎰 Events & Fortune", color=0xE74C3C)
    e5.add_field(
        name="🌩️ Elemental Events",
        value="Rare events spawn special fish in ALL channels. Announced in **📢│heavenly-announcements**.",
        inline=False,
    )
    e5.add_field(
        name="🎰 Scratch Tickets",
        value=(
            "Three tiers: **Qi Slip** (150 SS) · **Spirit Scroll** (600 SS) · **Heavenly Decree** (2,500 SS)\n"
            "Scratch 20 spots to find matching numbers — jackpots up to **350,000 Spirit Stones**!\n"
            "Even a single match on a Qi Slip pays back more than the ticket costs.\n"
            "Use in **🎰│fortune-house** only."
        ),
        inline=False,
    )
    e5.add_field(
        name="⚔️ Adventures",
        value="Use `/adventure` in **🗺️│adventure-grounds** once per hour. Earn Spirit Stones, XP, bait, or pills.",
        inline=False,
    )
    embeds.append(e5)

    e6 = discord.Embed(
        title="💎 NovelCodex.org — Discord Perks",
        color=0xF0B429,
        description=(
            "Supporters of **[NovelCodex.org](https://novelcodex.org)** unlock exclusive Discord perks "
            "based on their tier. Perks are granted automatically when your supporter role is assigned.\n​"
        ),
    )
    e6.add_field(
        name="🎨 Custom Role — `/myrole`",
        value=(
            "Available to: **Seeker, Sage, Immortal Sage** and any subscriber role *(any $5+ supporter)*\n\n"
            "`/myrole create [name] [#hex]` — Create your own uniquely coloured role\n"
            "`/myrole edit` — Change your role's name or colour\n"
            "`/myrole delete` — Remove your custom role"
        ),
        inline=False,
    )
    e6.add_field(
        name="🔊 Private Voice Channel — `/mychannel`",
        value=(
            "Available to: **active subscribers (Reader, Scholar)**\n\n"
            "`/mychannel create [name]` — Spawn a private voice channel just for you\n"
            "`/mychannel rename [name]` — Rename your channel\n"
            "`/mychannel limit [0–99]` — Set a user cap (0 = unlimited)\n"
            "`/mychannel add @user` — Grant someone access\n"
            "`/mychannel remove @user` — Revoke someone's access\n"
            "`/mychannel delete` — Delete your channel"
        ),
        inline=False,
    )
    e6.set_footer(text="Visit NovelCodex.org to support the project and unlock your perks.")
    embeds.append(e6)

    return embeds


def _breakthrough_hall_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏆 Breakthrough Hall — Eternal River Sect",
        color=0xFFD700,
        description=(
            "This sacred hall records every disciple who has shattered the shackles of their realm.\n\n"
            "When a disciple successfully breaks through, their achievement is announced here.\n​"
        ),
    )
    embed.add_field(
        name="How Breakthroughs Work",
        value=(
            "1. Fish to fill your **Qi bar**\n"
            "2. Buy a **Breakthrough Pill** at **💎│spirit-bazaar**\n"
            "3. Use `/breakthrough` — success brings glory, failure raises your next chance by **+5%**\n"
            "4. Each failure **doubles** the pill cost for that realm\n"
            "5. Your realm role updates automatically on success"
        ),
        inline=False,
    )
    embed.set_footer(text="May your Dao-heart be unshakeable.")
    return embed


def _role_selection_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎭 Role Selection",
        color=0x5DADE2,
        description=(
            "Use the slash commands below to personalise your profile.\n"
            "**Location roles are mutually exclusive** — you may only hold one.\n​"
        ),
    )
    embed.add_field(
        name="🌍 Location Roles",
        value=(
            "`/role location europe`\n"
            "`/role location north america`\n"
            "`/role location africa`\n"
            "`/role location south america`\n"
            "`/role location asia`\n"
            "`/role location oceania`"
        ),
        inline=True,
    )
    embed.add_field(
        name="🎨 Interest / Genre Roles",
        value=(
            "`/role interest xianxia reader`\n"
            "`/role interest action fan`\n"
            "`/role interest gamer`\n"
            "`/role interest artist`\n"
            "`/role interest music lover`\n"
            "`/role interest avid fisher`\n"
            "`/role interest story enjoyer`"
        ),
        inline=True,
    )
    embed.set_footer(text="Using a location command while you have one replaces the old one automatically.")
    return embed


# ──────────────────────────────────────────────────────────────────────────────
# SETUP COG
# ──────────────────────────────────────────────────────────────────────────────

class SetupCog(commands.Cog, name="Setup"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /omega_setup ──────────────────────────────────────────────────────────

    @app_commands.command(
        name="omega_setup",
        description="[Admin] Wipe and rebuild the entire Eternal River Sect server structure.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def omega_setup(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild

        # Ephemeral so the status message is delivered through the interaction
        # webhook — NOT stored in the channel — meaning it survives channel deletion.
        await interaction.response.defer(ephemeral=True)
        status = await interaction.followup.send(
            "⏳ **Eternal River Sect Setup** — beginning now...\n"
            "🗑️ Deleting all channels, categories, and roles...",
            ephemeral=True,
        )

        async def _update(msg: str) -> None:
            """Edit the ephemeral status message, ignoring any Discord errors."""
            try:
                await status.edit(content=msg)
            except Exception:
                pass

        try:
            await self._delete_everything(guild)

            await _update("🔧 Creating roles...")
            role_map = await self._create_roles(guild)

            await _update("🔧 Creating categories and channels...")
            cat_map, channel_map, channel_pairs = await self._create_channels(guild, role_map)

            await _update("🔧 Creating voice channels...")
            await self._create_voice_channels(guild, cat_map, role_map)

            await _update("🔧 Registering channels in database...")
            await db.clear_all_channel_configs()
            await self._register_channels(channel_pairs, guild.id)

            await _update("🔧 Posting guide embeds...")
            await self._post_embeds(guild, channel_map)

            await _update("🔧 Assigning default roles to existing members...")
            await self._assign_default_roles(guild, role_map)

            await _update(
                "✅ **Setup complete!** The Eternal River Sect is ready.\n\n"
                "**Channels created** · **Roles assigned** · **Guides posted**\n"
                "*Restart or use `!sync` if slash commands do not appear immediately.*"
            )
            log.info("omega_setup completed for %s (%d)", guild.name, guild.id)

        except Exception as exc:
            log.exception("omega_setup failed: %s", exc)
            await _update(f"❌ Setup failed: `{exc}`\nCheck the bot logs for details.")
            raise

    # ── /update_guide ─────────────────────────────────────────────────────────

    @app_commands.command(
        name="update_guide",
        description="[Admin] Refresh the server-guide and commands-guide embeds without a full reset.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def update_guide(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        guide_targets = {
            "server_guide":   _server_guide_embeds,
            "commands_guide": _commands_guide_embeds,
        }

        updated_mentions: list[str] = []

        for ch_type, embed_fn in guide_targets.items():
            # Find the matching channel from DB
            guide_ch: discord.TextChannel | None = None
            for ch in guild.text_channels:
                row = await db.get_channel_config(ch.id)
                if row and row["channel_type"] == ch_type:
                    guide_ch = ch
                    break

            if not guide_ch:
                continue

            # Delete the bot's existing messages in that channel (up to 20)
            try:
                async for old_msg in guide_ch.history(limit=20):
                    if old_msg.author == guild.me:
                        try:
                            await old_msg.delete()
                            await asyncio.sleep(0.3)
                        except discord.NotFound:
                            pass
            except discord.Forbidden:
                pass

            # Post the fresh embeds
            for embed in embed_fn():
                await guide_ch.send(embed=embed)
                await asyncio.sleep(0.3)

            updated_mentions.append(guide_ch.mention)

        if updated_mentions:
            await interaction.followup.send(
                f"✅ Guide embeds refreshed in: {', '.join(updated_mentions)}",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "⚠️ No guide channels found. Run `/omega_setup` first to create them.",
                ephemeral=True,
            )

    # ── Step 1: Delete everything ─────────────────────────────────────────────

    async def _delete_everything(self, guild: discord.Guild) -> None:
        bot_top = guild.me.top_role

        # Delete text + voice channels first (must remove from categories before deleting cat)
        for ch in list(guild.channels):
            if isinstance(ch, discord.CategoryChannel):
                continue
            try:
                await ch.delete(reason="omega_setup reset")
                await asyncio.sleep(0.25)
            except Exception:
                pass

        # Delete categories
        for cat in list(guild.categories):
            try:
                await cat.delete(reason="omega_setup reset")
                await asyncio.sleep(0.25)
            except Exception:
                pass

        # Delete roles (protect @everyone and managed/integration roles)
        for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
            if role.is_default() or role.managed:
                continue
            if role >= bot_top:
                continue  # can't delete roles at/above bot's own position
            try:
                await role.delete(reason="omega_setup reset")
                await asyncio.sleep(0.3)
            except Exception:
                pass

    # ── Step 2: Create roles ──────────────────────────────────────────────────

    async def _create_roles(self, guild: discord.Guild) -> dict[str, discord.Role]:
        from bot.data.title_data import ALL_TITLES

        role_map: dict[str, discord.Role] = {}
        role_map["__everyone__"] = guild.default_role

        for rdef in STANDARD_ROLES:
            perms_key = rdef.get("perms")
            if perms_key == "admin":
                perms = _admin_permissions()
            elif perms_key == "mod":
                perms = _mod_permissions()
            else:
                perms = discord.Permissions.none()

            role = await guild.create_role(
                name=rdef["name"],
                color=discord.Color(rdef["color"]),
                hoist=rdef.get("hoist", False),
                mentionable=rdef.get("mentionable", False),
                permissions=perms,
                reason="omega_setup",
            )
            role_map[rdef["key"]] = role
            await asyncio.sleep(0.3)

        # Title roles (no special colour; just name)
        for t in ALL_TITLES:
            role = await guild.create_role(
                name=t["name"],
                color=discord.Color(0x95A5A6),
                reason="omega_setup title role",
            )
            role_map[f"title_{t['id']}"] = role
            await asyncio.sleep(0.3)

        return role_map

    # ── Step 3: Create categories + text channels ─────────────────────────────

    async def _create_channels(
        self, guild: discord.Guild, role_map: dict
    ) -> tuple[dict, dict, list]:
        cat_map: dict[str, discord.CategoryChannel] = {}

        for cdef in CATEGORIES:
            cat = await guild.create_category(cdef["name"], reason="omega_setup")
            cat_map[cdef["key"]] = cat
            await asyncio.sleep(0.3)

        channel_map: dict[str, discord.TextChannel] = {}
        # Full list of (chdef, channel) for correct per-channel DB registration
        channel_pairs: list[tuple[dict, discord.TextChannel]] = []

        for chdef in CHANNELS:
            cat = cat_map.get(chdef["cat"])
            ow  = _channel_overwrites(chdef, role_map)

            ch = await guild.create_text_channel(
                name=chdef["name"],
                category=cat,
                overwrites=ow,
                topic=_channel_topic(chdef),
                reason="omega_setup",
            )

            # channel_pairs tracks every channel individually for DB registration
            channel_pairs.append((chdef, ch))

            # channel_map stores by type (first wins) and biome — used for embed posting
            ctype = chdef["type"]
            if ctype not in channel_map:
                channel_map[ctype] = ch
            biome = chdef.get("biome")
            if biome:
                channel_map[f"biome_{biome}"] = ch

            await asyncio.sleep(0.3)

        return cat_map, channel_map, channel_pairs

    # ── Step 4: Create voice channels ─────────────────────────────────────────

    async def _create_voice_channels(
        self, guild: discord.Guild,
        cat_map: dict[str, discord.CategoryChannel],
        role_map: dict,
    ) -> None:
        afk_ch = None
        voice_cat = cat_map.get("voice")

        for vdef in VOICE_CHANNELS:
            ow = _voice_overwrites(role_map)
            vc = await guild.create_voice_channel(
                name=vdef["name"],
                category=voice_cat,
                overwrites=ow,
                reason="omega_setup",
            )
            if vdef.get("afk"):
                afk_ch = vc
            await asyncio.sleep(0.3)

        if afk_ch:
            try:
                await guild.edit(afk_channel=afk_ch, afk_timeout=300, reason="omega_setup afk")
            except Exception:
                pass

    # ── Step 5: Register channels in DB ──────────────────────────────────────

    async def _register_channels(
        self, channel_pairs: list[tuple[dict, discord.TextChannel]], guild_id: int
    ) -> None:
        """Register every channel individually — one row per Discord channel."""
        for chdef, ch in channel_pairs:
            await db.set_channel_config(
                channel_id=ch.id,
                channel_type=chdef["type"],
                biome_id=chdef.get("biome"),
                guild_id=guild_id,
            )

    # ── Step 6: Post guide embeds ─────────────────────────────────────────────

    async def _post_embeds(self, guild: discord.Guild, channel_map: dict) -> None:
        async def _post(ch: discord.TextChannel | None, embeds: list[discord.Embed]) -> None:
            if not ch:
                return
            try:
                await ch.purge(limit=20, check=lambda m: m.author == self.bot.user)
            except discord.Forbidden:
                pass
            for e in embeds:
                await ch.send(embed=e)
                await asyncio.sleep(0.4)

        await _post(channel_map.get("welcome"),       [_welcome_embed(guild)])
        await _post(channel_map.get("rules"),         [_rules_embed()])
        await _post(channel_map.get("commands_guide"), _commands_guide_embeds())
        await _post(channel_map.get("server_guide"),  _server_guide_embeds())
        await _post(channel_map.get("breakthrough_hall"), [_breakthrough_hall_embed()])
        await _post(channel_map.get("role_selection"), [_role_selection_embed()])

    # ── Step 7: Assign default roles ──────────────────────────────────────────

    async def _assign_default_roles(
        self, guild: discord.Guild, role_map: dict
    ) -> None:
        outer    = role_map.get("outer")    # Eternal River Outer Disciple
        mortal   = role_map.get("realm_0")  # Mortal realm
        realm_rs = {role_map[k] for k in REALM_ROLE_KEYS if k in role_map}

        for member in guild.members:
            if member.bot:
                continue
            to_add = []
            if outer  and outer  not in member.roles:
                to_add.append(outer)
            if mortal and mortal not in member.roles:
                if not any(r in member.roles for r in realm_rs):
                    to_add.append(mortal)
            if to_add:
                try:
                    await member.add_roles(*to_add, reason="omega_setup defaults")
                    await asyncio.sleep(0.2)
                except discord.Forbidden:
                    pass

    # ── New-member welcome ────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild

        # Assign default roles
        for role_name in ("Eternal River Outer Disciple", "Mortal"):
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                try:
                    await member.add_roles(role, reason="New member default roles")
                except discord.Forbidden:
                    pass

        # Post welcome message in welcome channel
        welcome_ch = None
        for ch in guild.text_channels:
            row = await db.get_channel_config(ch.id)
            if row and row["channel_type"] == "welcome":
                welcome_ch = ch
                break

        if welcome_ch:
            embed = discord.Embed(
                title="🌊 A New Disciple Arrives",
                description=(
                    f"The eternal river parts to welcome {member.mention}!\n\n"
                    f"You have entered **the Eternal River Sect** — where mortals become immortals "
                    f"through patience, fishing, and the cultivation of Qi.\n\n"
                    f"Cast your first line with `/reel` in any **🎣 fishing channel**.\n"
                    f"Your journey begins now."
                ),
                color=0x2ECC71,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Eternal River Sect  •  Member #{guild.member_count}")
            try:
                await welcome_ch.send(embed=embed)
            except discord.Forbidden:
                pass


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _channel_topic(chdef: dict) -> str:
    topics = {
        "fishing":          f"🎣 Use /reel here. Biome: {chdef.get('biome', '?')}",
        "shop":             "🏪 /shop /buy /sell /equip /upgrade — Spirit Stone Market.",
        "gambling":         "🎰 /gamble buy | use | tickets — Fortune House only.",
        "adventure":        "🗺️ /adventure — 1-hour cooldown expedition.",
        "announce":         "📣 Official sect announcements and rare catch alerts.",
        "welcome":          "🌸 New disciple welcome channel.",
        "rules":            "📜 Sect rules — read before doing anything.",
        "commands_guide":   "🎮 All commands and where to use them.",
        "server_guide":     "📖 How everything in the sect works.",
        "patch_notes":      "📝 Changelogs from the sect elders.",
        "breakthrough_hall":"🏆 Cultivation breakthrough announcements.",
        "role_selection":   "🎭 Use /role location and /role interest to assign your roles.",
        "general":          "💬 General conversation.",
        "mod_log":          "📋 Moderation action log (staff only).",
        "mod_review":       "🔍 Mod review queue (staff only).",
        "mod_commands":     "🔧 Staff command usage (staff only).",
        "heavenly_announce":"📢 Bot announcements for events and rare catches.",
    }
    return topics.get(chdef["type"], "")


# ──────────────────────────────────────────────────────────────────────────────
# COG SETUP
# ──────────────────────────────────────────────────────────────────────────────

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))
