# =============================================================
# OMEGA BOT — CHANNEL UNLOCK CHECKER
# Eternal River Sect
# =============================================================
"""
Checks whether a user has met any hidden-channel unlock conditions
and, if so, grants them Discord channel access and records it in DB.

Call check_unlocks() as a fire-and-forget task after any event that
might satisfy a condition (fish caught, fish sold, etc.).

Conditions
----------
special1 — Phantom Lotus Grotto:
    Catch ≥1 fish in EACH of the 6 default biomes
    (freshwater1, freshwater2, freshwater3, saltwater1, saltwater2, saltwater3)

special2 — Celestial Peak Reservoir:
    Accumulate + sell ≥5,000 Spirit Stones total (total_spirit_stones_earned)

special3 — Void Rift Depths:
    Catch all 4 elemental fish (≥1 of each):
    terra_sovereign_koi, frost_eclipse_serpent,
    solar_inferno_drake, tempest_void_eel

secret — Primordial Chaos Abyss:
    Catch ≥1 of every non-junk species in the codex
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord.ext import commands

from bot.database import db

log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_BIOMES: frozenset[str] = frozenset({
    "freshwater1", "freshwater2", "freshwater3",
    "saltwater1",  "saltwater2",  "saltwater3",
})

ELEMENTAL_FISH_IDS: frozenset[str] = frozenset({
    "terra_sovereign_koi",
    "frost_eclipse_serpent",
    "solar_inferno_drake",
    "tempest_void_eel",
})

_CATCHABLE_SPECIES: frozenset[str] | None = None


def get_catchable_species() -> frozenset[str]:
    """Return the set of all species IDs that count toward the 'catch all' condition.
    Excludes junk items. Built lazily once on first call."""
    global _CATCHABLE_SPECIES
    if _CATCHABLE_SPECIES is None:
        from bot.data.fish_data import FISH
        _CATCHABLE_SPECIES = frozenset(
            f["id"] for f in FISH if f.get("category") not in ("junk",)
        )
    return _CATCHABLE_SPECIES


# ── Unlock messages ──────────────────────────────────────────────────────────

_UNLOCK_MESSAGES: dict[str, str] = {
    "special1": (
        "🌸 **Phantom Lotus Grotto Unlocked!**\n"
        "Your journey across every river and sea of the Eternal River Sect "
        "has awakened the hidden Grotto.\n"
        "The lotus blooms only for those who have walked every shore."
    ),
    "special2": (
        "⛰️ **Celestial Peak Reservoir Unlocked!**\n"
        "Your accumulated wealth has earned the respect of the heavens.\n"
        "The mountaintop waters now open to you."
    ),
    "special3": (
        "🌀 **Void Rift Depths Unlocked!**\n"
        "You have tamed all four elemental forces of nature.\n"
        "The rift between worlds splits open at your feet."
    ),
    "secret": (
        "👁️ **Primordial Chaos Abyss Unlocked!**\n"
        "You have witnessed every creature that swims beneath the heavens.\n"
        "The Primordial Abyss — the beginning and end of all — reveals itself to you."
    ),
}

# ── Individual condition checkers ─────────────────────────────────────────────

async def _check_phantom_lotus(user_id: int) -> bool:
    """Must have caught ≥1 fish in each of the 6 default biomes."""
    fished = await db.get_fished_biomes(user_id)
    return DEFAULT_BIOMES.issubset(fished)


async def _check_celestial_peak(user_id: int) -> bool:
    """Must have accumulated and sold ≥5,000 Spirit Stones total."""
    user = await db.get_user(user_id)
    if not user:
        return False
    return user.get("total_spirit_stones_earned", 0) >= 5_000


async def _check_void_rift(user_id: int) -> bool:
    """Must have caught all 4 elemental fish (≥1 of each)."""
    codex = await db.get_full_codex(user_id)  # {species_id: row}
    caught = {sid for sid, row in codex.items() if row.get("caught_count", 0) >= 1}
    return ELEMENTAL_FISH_IDS.issubset(caught)


async def _check_primordial_abyss(user_id: int) -> bool:
    """Must have caught ≥1 of every non-junk species."""
    codex = await db.get_full_codex(user_id)
    caught = {sid for sid, row in codex.items() if row.get("caught_count", 0) >= 1}
    return get_catchable_species().issubset(caught)


# ── Main entry point ─────────────────────────────────────────────────────────

async def check_unlocks(
    bot: commands.Bot,
    member: discord.Member,
    guild: discord.Guild,
) -> None:
    """
    Run all four unlock conditions for *member* in *guild*.
    Newly met conditions are recorded in the DB and the Discord channel
    permission overwrite is applied immediately.

    Safe to call as ``asyncio.create_task(check_unlocks(...))``.
    """
    user_id  = member.id
    guild_id = guild.id

    conditions = [
        ("special1", _check_phantom_lotus(user_id)),
        ("special2", _check_celestial_peak(user_id)),
        ("special3", _check_void_rift(user_id)),
        ("secret",   _check_primordial_abyss(user_id)),
    ]

    for biome_id, coro in conditions:
        try:
            # Skip if already unlocked
            if await db.is_biome_unlocked(user_id, biome_id):
                continue

            if not await coro:
                continue

            # ── Persist the unlock ──────────────────────────────────────────
            await db.grant_biome_unlock(user_id, biome_id)

            # ── Apply Discord permission overwrite ──────────────────────────
            channel_id = await db.get_channel_id_by_biome(guild_id, biome_id)
            if channel_id:
                channel = guild.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    try:
                        await channel.set_permissions(
                            member,
                            view_channel=True,
                            reason=f"Unlock: {biome_id}",
                        )
                    except discord.Forbidden:
                        log.warning(
                            "Missing permission to unlock %s for %s (%s)",
                            biome_id, member.display_name, user_id,
                        )
                    except Exception:
                        log.exception("Failed to set channel perms for %s / %s", biome_id, user_id)

            # ── Notify user via DM ──────────────────────────────────────────
            msg = _UNLOCK_MESSAGES.get(biome_id)
            if msg:
                try:
                    await member.send(msg)
                except (discord.Forbidden, discord.HTTPException):
                    pass  # DMs closed — silently ignore

            log.info("Unlock granted: %s → %s (%s)", member.display_name, biome_id, user_id)

        except Exception:
            log.exception(
                "Unexpected error in check_unlocks biome=%s user=%s", biome_id, user_id
            )
