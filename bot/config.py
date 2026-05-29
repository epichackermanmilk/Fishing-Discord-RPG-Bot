# =============================================================
# OMEGA BOT — CONFIGURATION
# Eternal River Sect
# =============================================================
"""
All bot-wide configuration values.
Sensitive values (TOKEN) should live in a .env file and are
loaded automatically here via python-dotenv.

Create a .env file in the project root:
    DISCORD_TOKEN=your_bot_token_here
    OWNER_ID=your_discord_user_id
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ── Discord ───────────────────────────────────────────────────────────────────

TOKEN:    str = os.getenv("DISCORD_TOKEN", "")
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))

# ── Database ──────────────────────────────────────────────────────────────────

DB_PATH: Path = Path(__file__).parent / "database" / "omega.db"

# ── Bot behaviour ─────────────────────────────────────────────────────────────

COMMAND_PREFIX: str = "!"   # Legacy prefix commands (setup only)

# Cogs to load at startup (order matters — db must be implicit via imports)
COGS: list[str] = [
    "bot.cogs.admin",
    "bot.cogs.setup",
    "bot.cogs.fishing",
    "bot.cogs.shop",
    "bot.cogs.inventory",
    "bot.cogs.codex",
    "bot.cogs.cultivation",
    "bot.cogs.adventure",
    "bot.cogs.gambling",
    "bot.cogs.moderation",
    "bot.cogs.roles",
    "bot.cogs.events",
    "bot.cogs.quests",
    "bot.cogs.profile",
    "bot.cogs.unlocks",
]

# ── Feature flags ─────────────────────────────────────────────────────────────

DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# ── Intents ───────────────────────────────────────────────────────────────────
# These match what is enabled in the Discord Developer Portal.
# Required: members + message_content for Qi gain + auto-mod.

REQUIRED_INTENTS = {
    "guilds":          True,
    "members":         True,   # Must be enabled in Dev Portal
    "messages":        True,
    "message_content": True,   # Must be enabled in Dev Portal
    "voice_states":    True,
}
