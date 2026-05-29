"""
database/db.py
Omega Bot — Async database access layer (aiosqlite)
All interaction with SQLite goes through these async functions.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import aiosqlite

DB_PATH     = Path(__file__).parent / "omega.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _dict_row_factory(cursor, row):
    """Return every DB row as a plain dict so .get() works everywhere."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

QUALITY_ORDER = ["dust", "bronze", "jade", "gold", "astral", "immortal"]


# ──────────────────────────────────────────────────────────────────────────────
# INIT
# ──────────────────────────────────────────────────────────────────────────────

async def init() -> None:
    """Create all tables from schema.sql."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        await db.executescript(schema)
        await db.commit()


async def _db() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = _dict_row_factory
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ──────────────────────────────────────────────────────────────────────────────
# USERS
# ──────────────────────────────────────────────────────────────────────────────

async def get_user(discord_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        return await cur.fetchone()


async def get_or_create_user(discord_id: int, username: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute(
            "INSERT OR IGNORE INTO users (discord_id, username) VALUES (?, ?)",
            (discord_id, username),
        )
        await db.execute(
            "INSERT OR IGNORE INTO rod_upgrades (user_id) VALUES (?)", (discord_id,))
        await db.execute(
            "INSERT OR IGNORE INTO bait_stock (user_id, bait_id, quantity) VALUES (?, 'spirit_worm', 5)",
            (discord_id,),
        )
        await db.execute(
            "INSERT OR IGNORE INTO rods_owned (user_id, rod_id) VALUES (?, 'mortal_reed')",
            (discord_id,),
        )
        await db.execute(
            "INSERT OR IGNORE INTO lures_owned (user_id, lure_id) VALUES (?, 'mortal_hook')",
            (discord_id,),
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        return await cur.fetchone()


async def update_user(discord_id: int, **kwargs: Any) -> None:
    if not kwargs:
        return
    cols = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [discord_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {cols} WHERE discord_id = ?", vals)
        await db.commit()


async def add_fishing_xp(user_id: int, xp: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET fishing_xp = fishing_xp + ? WHERE discord_id = ?",
            (xp, user_id),
        )
        await db.commit()


async def set_fishing_level(user_id: int, level: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET fishing_level = ? WHERE discord_id = ?", (level, user_id))
        await db.commit()


async def increment_fish_caught(user_id: int, value: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_fish_caught = total_fish_caught + 1, "
            "total_spirit_stones_earned = total_spirit_stones_earned + ? "
            "WHERE discord_id = ?",
            (0, user_id),  # value earned tracked separately via sell
        )
        await db.commit()


async def increment_total_adventures(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_adventures = total_adventures + 1 WHERE discord_id = ?",
            (user_id,),
        )
        await db.commit()


async def add_total_ss_earned(user_id: int, amount: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_spirit_stones_earned = total_spirit_stones_earned + ? "
            "WHERE discord_id = ?",
            (amount, user_id),
        )
        await db.commit()


async def add_spirit_stones(user_id: int, amount: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET spirit_stones = spirit_stones + ? WHERE discord_id = ?",
            (amount, user_id),
        )
        await db.commit()


async def spend_spirit_stones(user_id: int, amount: int) -> bool:
    """Deduct spirit stones if user has enough. Returns True on success."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT spirit_stones FROM users WHERE discord_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row or row["spirit_stones"] < amount:
            return False
        await db.execute(
            "UPDATE users SET spirit_stones = spirit_stones - ? WHERE discord_id = ?",
            (amount, user_id),
        )
        await db.commit()
        return True


async def add_qi(user_id: int, amount: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET qi = qi + ? WHERE discord_id = ?", (amount, user_id))
        await db.commit()


async def update_last_reel(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_reel = ? WHERE discord_id = ?", (time.time(), user_id))
        await db.commit()


async def update_last_adventure(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_adventure = ? WHERE discord_id = ?", (time.time(), user_id))
        await db.commit()


async def set_active_title(user_id: int, title_id: str | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET active_title_id = ? WHERE discord_id = ?", (title_id, user_id))
        await db.commit()


async def set_user_rod(user_id: int, rod_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET rod_id = ? WHERE discord_id = ?", (rod_id, user_id))
        await db.commit()


async def set_user_bait(user_id: int, bait_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET bait_id = ? WHERE discord_id = ?", (bait_id, user_id))
        await db.commit()


async def set_user_lure(user_id: int, lure_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET lure_id = ? WHERE discord_id = ?", (lure_id, user_id))
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# ROD UPGRADES
# ──────────────────────────────────────────────────────────────────────────────

async def get_rod_upgrades(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT * FROM rod_upgrades WHERE user_id = ?", (user_id,))
        return await cur.fetchone()


async def set_rod_upgrade_tier(user_id: int, column: str, tier: int) -> None:
    allowed = {"reel_speed_tier", "xp_bonus_tier", "rod_luck_tier", "max_bait_tier"}
    if column not in allowed:
        raise ValueError(f"Invalid upgrade column: {column}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE rod_upgrades SET {column} = ? WHERE user_id = ?", (tier, user_id))
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# BAIT
# ──────────────────────────────────────────────────────────────────────────────

async def get_bait_stock(user_id: int) -> dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT bait_id, quantity FROM bait_stock WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return {r["bait_id"]: r["quantity"] for r in rows}


async def consume_bait(user_id: int, bait_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT quantity FROM bait_stock WHERE user_id = ? AND bait_id = ?",
            (user_id, bait_id),
        )
        row = await cur.fetchone()
        if not row or row["quantity"] < 1:
            return False
        await db.execute(
            "UPDATE bait_stock SET quantity = quantity - 1 WHERE user_id = ? AND bait_id = ?",
            (user_id, bait_id),
        )
        await db.commit()
        return True


async def add_bait_stock(user_id: int, bait_id: str, qty: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bait_stock (user_id, bait_id, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, bait_id) DO UPDATE SET quantity = quantity + excluded.quantity",
            (user_id, bait_id, qty),
        )
        await db.commit()


async def get_bait_licenses(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT bait_id FROM bait_licenses WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return [r["bait_id"] for r in rows]


async def add_bait_license(user_id: int, bait_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO bait_licenses (user_id, bait_id) VALUES (?, ?)",
            (user_id, bait_id),
        )
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# LURES & RODS OWNED
# ──────────────────────────────────────────────────────────────────────────────

async def get_owned_rod_ids(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT rod_id FROM rods_owned WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return [r["rod_id"] for r in rows]


async def add_owned_rod(user_id: int, rod_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO rods_owned (user_id, rod_id) VALUES (?, ?)",
            (user_id, rod_id),
        )
        await db.commit()


async def get_owned_lure_ids(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT lure_id FROM lures_owned WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return [r["lure_id"] for r in rows]


async def add_owned_lure(user_id: int, lure_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO lures_owned (user_id, lure_id) VALUES (?, ?)",
            (user_id, lure_id),
        )
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# FISH INVENTORY
# ──────────────────────────────────────────────────────────────────────────────

async def add_fish(user_id: int, species_id: str, quality: str,
                   size: float, value: int) -> int:
    """Insert a caught fish; return its new row id."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO fish_inventory (user_id, species_id, quality, size, value) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, species_id, quality, size, value),
        )
        await db.commit()
        return cur.lastrowid


async def get_fish_by_id(fish_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            """SELECT fi.*, f.name FROM fish_inventory fi
               LEFT JOIN (SELECT id as species_id, name FROM fish_inventory) sub
               ON fi.species_id = sub.species_id
               WHERE fi.id = ? AND fi.user_id = ?""",
            (fish_id, user_id),
        )
        # Simpler join using fish data in Python
        row = await cur.fetchone()
        if row:
            # Attach display name from fish_data
            from bot.data.fish_data import FISH_BY_ID
            f = FISH_BY_ID.get(row["species_id"], {})
            # Return as dict for easier access
            d = dict(row)
            d["name"] = f.get("name", row["species_id"])
            d["avg_size"] = f.get("avg_size", row["size"])
            return d
        return None


async def get_fish_inventory(user_id: int, category: str | None = None) -> list[dict]:
    """Return all fish for a user, optionally filtered by category."""
    from bot.data.fish_data import FISH_BY_ID
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM fish_inventory WHERE user_id = ? ORDER BY caught_at DESC",
            (user_id,),
        )
        rows = await cur.fetchall()
    result = []
    for row in rows:
        f = FISH_BY_ID.get(row["species_id"], {})
        if category and f.get("category") != category:
            continue
        d = dict(row)
        d["name"]     = f.get("name", row["species_id"])
        d["avg_size"] = f.get("avg_size", row["size"])
        result.append(d)
    return result


async def fish_inventory_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM fish_inventory WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else 0


async def fish_count_by_species(user_id: int, species_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM fish_inventory WHERE user_id = ? AND species_id = ?",
            (user_id, species_id),
        )
        row = await cur.fetchone()
        return row[0] if row else 0


async def sell_all_fish(user_id: int) -> tuple[int, int]:
    """Sell all fish; return (total_value, count)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT SUM(value), COUNT(*) FROM fish_inventory WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        total, count = (row[0] or 0), (row[1] or 0)
        if count > 0:
            await db.execute("DELETE FROM fish_inventory WHERE user_id = ?", (user_id,))
            await db.execute(
                "UPDATE users SET spirit_stones = spirit_stones + ?, "
                "total_spirit_stones_earned = total_spirit_stones_earned + ? "
                "WHERE discord_id = ?",
                (total, total, user_id),
            )
            await db.commit()
        return total, count


async def sell_fish_by_id(user_id: int, fish_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT value FROM fish_inventory WHERE id = ? AND user_id = ?",
            (fish_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            return False
        await db.execute("DELETE FROM fish_inventory WHERE id = ?", (fish_id,))
        await db.execute(
            "UPDATE users SET spirit_stones = spirit_stones + ?, "
            "total_spirit_stones_earned = total_spirit_stones_earned + ? "
            "WHERE discord_id = ?",
            (row["value"], row["value"], user_id),
        )
        await db.commit()
        return True


async def sell_fish_by_species(user_id: int, species_id: str) -> tuple[int, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT SUM(value), COUNT(*) FROM fish_inventory "
            "WHERE user_id = ? AND species_id = ?",
            (user_id, species_id),
        )
        row = await cur.fetchone()
        total, count = (row[0] or 0), (row[1] or 0)
        if count > 0:
            await db.execute(
                "DELETE FROM fish_inventory WHERE user_id = ? AND species_id = ?",
                (user_id, species_id),
            )
            await db.execute(
                "UPDATE users SET spirit_stones = spirit_stones + ?, "
                "total_spirit_stones_earned = total_spirit_stones_earned + ? "
                "WHERE discord_id = ?",
                (total, total, user_id),
            )
            await db.commit()
        return total, count


# ──────────────────────────────────────────────────────────────────────────────
# CODEX
# ──────────────────────────────────────────────────────────────────────────────

async def get_codex_entry(user_id: int, species_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM codex WHERE user_id = ? AND species_id = ?",
            (user_id, species_id),
        )
        return await cur.fetchone()


async def get_full_codex(user_id: int) -> dict[str, dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT * FROM codex WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return {r["species_id"]: dict(r) for r in rows}


async def get_codex_discovered_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM codex WHERE user_id = ? AND caught_count > 0", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else 0


async def update_codex(user_id: int, species_id: str, quality: str,
                        size: float, value: int) -> None:
    qi = QUALITY_ORDER.index(quality) if quality in QUALITY_ORDER else 0
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM codex WHERE user_id = ? AND species_id = ?",
            (user_id, species_id),
        )
        row = await cur.fetchone()
        if not row:
            await db.execute(
                """INSERT INTO codex
                   (user_id, species_id, caught_count, best_quality,
                    largest_size, smallest_size, largest_value, smallest_value, first_caught_at)
                   VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)""",
                (user_id, species_id, quality, size, size, value, value, now),
            )
        else:
            best_qi  = QUALITY_ORDER.index(row["best_quality"]) if row["best_quality"] in QUALITY_ORDER else 0
            new_best = quality if qi > best_qi else row["best_quality"]
            await db.execute(
                """UPDATE codex SET
                   caught_count   = caught_count + 1,
                   best_quality   = ?,
                   largest_size   = MAX(largest_size, ?),
                   smallest_size  = MIN(smallest_size, ?),
                   largest_value  = MAX(largest_value, ?),
                   smallest_value = MIN(smallest_value, ?)
                   WHERE user_id = ? AND species_id = ?""",
                (new_best, size, size, value, value, user_id, species_id),
            )
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# TITLES
# ──────────────────────────────────────────────────────────────────────────────

async def has_title(user_id: int, title_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM user_titles WHERE user_id = ? AND title_id = ?",
            (user_id, title_id),
        )
        return bool(await cur.fetchone())


async def award_title(user_id: int, title_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_titles (user_id, title_id) VALUES (?, ?)",
            (user_id, title_id),
        )
        await db.commit()


async def get_earned_titles(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT title_id FROM user_titles WHERE user_id = ? ORDER BY earned_at",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [r["title_id"] for r in rows]


async def get_title(title_id: str) -> dict | None:
    """Return title dict from data layer (not DB)."""
    from bot.data.title_data import TITLE_BY_ID
    return TITLE_BY_ID.get(title_id)


# ──────────────────────────────────────────────────────────────────────────────
# CULTIVATION
# ──────────────────────────────────────────────────────────────────────────────

async def get_cultivation_tracker(user_id: int) -> dict[int, dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM cultivation_tracker WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return {r["realm"]: dict(r) for r in rows}


async def record_breakthrough_failure(user_id: int, realm: int) -> None:
    from bot.cogs.shop import PILL_BASE_PRICES
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM cultivation_tracker WHERE user_id = ? AND realm = ?",
            (user_id, realm),
        )
        row = await cur.fetchone()
        if not row:
            base = PILL_BASE_PRICES.get(realm, 500)
            await db.execute(
                "INSERT INTO cultivation_tracker (user_id, realm, failure_count, current_pill_cost) "
                "VALUES (?, ?, 1, ?)",
                (user_id, realm, base * 2),
            )
        else:
            new_cost = row["current_pill_cost"] * 2
            await db.execute(
                "UPDATE cultivation_tracker SET failure_count = failure_count + 1, "
                "current_pill_cost = ? WHERE user_id = ? AND realm = ?",
                (new_cost, user_id, realm),
            )
        await db.commit()


async def record_breakthrough_success(user_id: int, new_realm: int) -> None:
    from bot.cogs.shop import PILL_BASE_PRICES
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET realm = ?, qi = 0, stage = 0 WHERE discord_id = ?",
            (new_realm, user_id),
        )
        # Reset tracker for this realm
        base = PILL_BASE_PRICES.get(new_realm + 1, 500) if new_realm < 9 else 0
        await db.execute(
            "INSERT OR REPLACE INTO cultivation_tracker (user_id, realm, failure_count, current_pill_cost) "
            "VALUES (?, ?, 0, ?)",
            (user_id, new_realm, base),
        )
        await db.commit()


async def get_pill_inventory(user_id: int) -> dict[int, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT realm, quantity FROM pill_inventory WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return {r["realm"]: r["quantity"] for r in rows}


async def add_pill(user_id: int, realm: int, qty: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO pill_inventory (user_id, realm, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, realm) DO UPDATE SET quantity = quantity + excluded.quantity",
            (user_id, realm, qty),
        )
        await db.commit()


async def use_pill(user_id: int, realm: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT quantity FROM pill_inventory WHERE user_id = ? AND realm = ?",
            (user_id, realm),
        )
        row = await cur.fetchone()
        if not row or row["quantity"] < 1:
            return False
        await db.execute(
            "UPDATE pill_inventory SET quantity = quantity - 1 WHERE user_id = ? AND realm = ?",
            (user_id, realm),
        )
        await db.commit()
        return True


# ──────────────────────────────────────────────────────────────────────────────
# QUESTS
# ──────────────────────────────────────────────────────────────────────────────

async def get_quest_progress(user_id: int, quest_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM quests WHERE user_id = ? AND quest_id = ?",
            (user_id, quest_id),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_all_quest_progress(user_id: int) -> dict[str, dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT * FROM quests WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return {r["quest_id"]: dict(r) for r in rows}


async def increment_quest_progress(user_id: int, quest_id: str, amount: int = 1) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO quests (user_id, quest_id, current_progress)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, quest_id)
               DO UPDATE SET current_progress = current_progress + excluded.current_progress,
                             last_updated = unixepoch()""",
            (user_id, quest_id, amount),
        )
        await db.commit()


async def advance_quest_level(user_id: int, quest_id: str, new_level: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE quests SET level_reached = ?, last_updated = unixepoch() "
            "WHERE user_id = ? AND quest_id = ?",
            (new_level, user_id, quest_id),
        )
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# SCRATCH TICKETS
# ──────────────────────────────────────────────────────────────────────────────

async def create_scratch_ticket(user_id: int, tier: str,
                                 win_numbers: list[int],
                                 scratch_numbers: list[int]) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO scratch_tickets
               (user_id, tier, win_numbers, scratch_numbers, revealed_spots)
               VALUES (?, ?, ?, ?, '[]')""",
            (user_id, tier, json.dumps(win_numbers), json.dumps(scratch_numbers)),
        )
        await db.commit()
        return cur.lastrowid


async def get_scratch_ticket(ticket_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM scratch_tickets WHERE id = ? AND user_id = ?",
            (ticket_id, user_id),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_unscratched_tickets(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM scratch_tickets WHERE user_id = ? AND opened = 0 "
            "ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def update_ticket_revealed(ticket_id: int, revealed: list[int]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scratch_tickets SET revealed_spots = ? WHERE id = ?",
            (json.dumps(revealed), ticket_id),
        )
        await db.commit()


async def mark_ticket_opened(ticket_id: int, prize: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scratch_tickets SET opened = 1, prize_amount = ?, opened_at = unixepoch() "
            "WHERE id = ?",
            (prize, ticket_id),
        )
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# EVENTS
# ──────────────────────────────────────────────────────────────────────────────

async def get_active_event(fish_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM active_events WHERE fish_id = ? AND end_time > ?",
            (fish_id, time.time()),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_active_event_fish(biome_id: str) -> str | None:
    """Return species_id of any currently active event fish, or None."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT fish_id FROM active_events WHERE end_time > ?", (time.time(),))
        row = await cur.fetchone()
        return row["fish_id"] if row else None


async def start_event(fish_id: str, end_time: float) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO active_events (fish_id, start_time, end_time, announced) "
            "VALUES (?, ?, ?, 1)",
            (fish_id, time.time(), end_time),
        )
        await db.execute(
            "INSERT OR REPLACE INTO event_cooldowns (fish_id, last_event_end) VALUES (?, ?)",
            (fish_id, end_time),
        )
        await db.commit()


async def end_event(fish_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM active_events WHERE fish_id = ?", (fish_id,))
        await db.commit()


async def get_event_cooldown(fish_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM event_cooldowns WHERE fish_id = ?", (fish_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


# ──────────────────────────────────────────────────────────────────────────────
# CHANNEL CONFIG
# ──────────────────────────────────────────────────────────────────────────────

async def get_channel_config(channel_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM channel_config WHERE channel_id = ?", (channel_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_channel_config(channel_id: int, channel_type: str,
                              biome_id: str | None, guild_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO channel_config (channel_id, channel_type, biome_id, guild_id)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(channel_id) DO UPDATE SET
               channel_type = excluded.channel_type,
               biome_id     = excluded.biome_id,
               guild_id     = excluded.guild_id""",
            (channel_id, channel_type, biome_id, guild_id),
        )
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# CHANNEL UNLOCKS (locked fishing channels)
# ──────────────────────────────────────────────────────────────────────────────

async def user_has_channel_access(user_id: int, channel_id: int) -> bool:
    """Return True if the channel is not locked, or user has been unlocked."""
    row = await get_channel_config(channel_id)
    if not row:
        return True
    if not row.get("unlock_condition"):
        return True  # Not locked
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM channel_unlocks WHERE user_id = ? AND channel_id = ?",
            (user_id, channel_id),
        )
        return bool(await cur.fetchone())


async def unlock_channel_for_user(user_id: int, channel_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO channel_unlocks (user_id, channel_id) VALUES (?, ?)",
            (user_id, channel_id),
        )
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# BIOME FISHED TRACKING (for Phantom Lotus Grotto unlock)
# ──────────────────────────────────────────────────────────────────────────────

async def mark_biome_fished(user_id: int, biome_id: str) -> None:
    """Record that user has caught at least one fish in this biome."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_biomes_fished (user_id, biome_id) VALUES (?, ?)",
            (user_id, biome_id),
        )
        await db.commit()


async def get_fished_biomes(user_id: int) -> frozenset[str]:
    """Return the set of biome_ids the user has fished in."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT biome_id FROM user_biomes_fished WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return frozenset(r[0] for r in rows)


# ──────────────────────────────────────────────────────────────────────────────
# BIOME UNLOCK TRACKING (survival across /omega_setup channel recreation)
# ──────────────────────────────────────────────────────────────────────────────

async def is_biome_unlocked(user_id: int, biome_id: str) -> bool:
    """Return True if the user has already earned the unlock for this biome."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM user_biome_unlocks WHERE user_id = ? AND biome_id = ?",
            (user_id, biome_id),
        )
        return bool(await cur.fetchone())


async def grant_biome_unlock(user_id: int, biome_id: str) -> None:
    """Record that a user has earned access to a locked biome."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_biome_unlocks (user_id, biome_id) VALUES (?, ?)",
            (user_id, biome_id),
        )
        await db.commit()


async def get_biome_unlocks(user_id: int) -> list[str]:
    """Return all biome_ids the user has unlocked."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT biome_id FROM user_biome_unlocks WHERE user_id = ?", (user_id,))
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def get_channel_id_by_biome(guild_id: int, biome_id: str) -> int | None:
    """Look up the current Discord channel_id for a given biome in a guild."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT channel_id FROM channel_config WHERE guild_id = ? AND biome_id = ?",
            (guild_id, biome_id),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def get_all_users_with_biome_unlocks() -> list[dict]:
    """Return all rows from user_biome_unlocks (used to restore permissions on startup)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT user_id, biome_id FROM user_biome_unlocks")
        return await cur.fetchall()


# ──────────────────────────────────────────────────────────────────────────────
# MODERATION
# ──────────────────────────────────────────────────────────────────────────────

async def log_mod_action(action_type: str, target_id: int, target_name: str,
                          moderator_id: int, moderator_name: str,
                          reason: str | None = None,
                          duration_seconds: int | None = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO mod_actions
               (action_type, target_id, target_name, moderator_id, moderator_name,
                reason, duration_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (action_type, target_id, target_name, moderator_id, moderator_name,
             reason, duration_seconds),
        )
        await db.commit()


async def get_mod_actions(target_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM mod_actions WHERE target_id = ? ORDER BY created_at DESC",
            (target_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def set_active_mute(user_id: int, guild_id: int, expires_at: float) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO active_mutes (user_id, guild_id, expires_at) "
            "VALUES (?, ?, ?)",
            (user_id, guild_id, expires_at),
        )
        await db.commit()


async def remove_active_mute(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM active_mutes WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_expired_mutes() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT * FROM active_mutes WHERE expires_at > 0 AND expires_at <= ?",
            (time.time(),),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def add_banned_word(word: str, added_by: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO banned_words (word, added_by) VALUES (?, ?)",
            (word, added_by),
        )
        await db.commit()


async def remove_banned_word(word: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM banned_words WHERE word = ?", (word,))
        await db.commit()


async def get_banned_words() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute("SELECT word FROM banned_words")
        rows = await cur.fetchall()
        return [r["word"] for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# SERVER RECORDS
# ──────────────────────────────────────────────────────────────────────────────

async def clear_all_channel_configs() -> None:
    """Wipe every row from channel_config (called before omega_setup rebuilds)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channel_config")
        await db.commit()


async def update_server_record(record_type: str, value: float,
                                user_id: int, username: str,
                                species_id: str | None = None,
                                extra_data: dict | None = None) -> bool:
    """
    Update a server record if this value beats the current one.
    For 'smallest_fish': lower is better. For everything else: higher is better.
    Returns True if the record was broken.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_row_factory
        cur = await db.execute(
            "SELECT value FROM server_records WHERE record_type = ?", (record_type,))
        row = await cur.fetchone()
        current = row["value"] if row and row["value"] is not None else None

        if record_type == "smallest_fish":
            is_better = current is None or value < current
        else:
            is_better = current is None or value > current

        if is_better:
            await db.execute(
                """UPDATE server_records SET
                   species_id = ?, value = ?, user_id = ?, username = ?,
                   extra_data = ?, set_at = ?
                   WHERE record_type = ?""",
                (species_id, value, user_id, username,
                 json.dumps(extra_data) if extra_data else None,
                 time.time(), record_type),
            )
            await db.commit()
            return True
        return False
