# =============================================================
# OMEGA BOT — COOLDOWN HELPERS
# Eternal River Sect
# =============================================================
"""
All time-gate logic lives here.
DB stores UNIX timestamps (float). We compare against time.time().
No asyncio.sleep / background tasks here — just pure checks.
"""
from __future__ import annotations

import time

from bot.data.rod_data import effective_cooldown


# ──────────────────────────────────────────────────────────────────────────────
# Generic cooldown check
# ──────────────────────────────────────────────────────────────────────────────

def is_on_cooldown(last_used: float, cooldown_seconds: float) -> bool:
    """Return True if the action is still on cooldown."""
    return (time.time() - last_used) < cooldown_seconds


def remaining_cooldown(last_used: float, cooldown_seconds: float) -> float:
    """Return seconds remaining on a cooldown (0.0 if ready)."""
    remaining = cooldown_seconds - (time.time() - last_used)
    return max(0.0, remaining)


# ──────────────────────────────────────────────────────────────────────────────
# /reel cooldown
# ──────────────────────────────────────────────────────────────────────────────

def reel_remaining(last_reel: float, rod_id: str, reel_speed_tier: int) -> float:
    """
    Return seconds remaining on the /reel cooldown.
    0.0 means the user can fish again immediately.
    """
    cd = effective_cooldown(rod_id, reel_speed_tier)
    return remaining_cooldown(last_reel, cd)


def reel_ready(last_reel: float, rod_id: str, reel_speed_tier: int) -> bool:
    return reel_remaining(last_reel, rod_id, reel_speed_tier) <= 0.0


# ──────────────────────────────────────────────────────────────────────────────
# /adventure cooldown (fixed 1-hour base, no upgrades)
# ──────────────────────────────────────────────────────────────────────────────

ADVENTURE_COOLDOWN = 3_600  # 1 hour in seconds


def adventure_remaining(last_adventure: float) -> float:
    return remaining_cooldown(last_adventure, ADVENTURE_COOLDOWN)


def adventure_ready(last_adventure: float) -> bool:
    return adventure_remaining(last_adventure) <= 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Spirit Pouch (bonus drop on /reel, once per 10 casts — tracked externally)
# ──────────────────────────────────────────────────────────────────────────────

# The Spirit Pouch is not time-gated; it triggers every 10th cast.
# We track cast counts in memory (or a simple counter in users table is fine).
# This module just provides the threshold constant.
SPIRIT_POUCH_EVERY_N = 10


# ──────────────────────────────────────────────────────────────────────────────
# Utility: next available timestamp
# ──────────────────────────────────────────────────────────────────────────────

def next_available_ts(last_used: float, cooldown_seconds: float) -> float:
    """Return the Unix timestamp when the action next becomes available."""
    return last_used + cooldown_seconds


def next_reel_ts(last_reel: float, rod_id: str, reel_speed_tier: int) -> float:
    cd = effective_cooldown(rod_id, reel_speed_tier)
    return next_available_ts(last_reel, cd)


def next_adventure_ts(last_adventure: float) -> float:
    return next_available_ts(last_adventure, ADVENTURE_COOLDOWN)
