# =============================================================
# OMEGA BOT — ROD DATA
# Eternal River Sect
# =============================================================
# Rods are permanent items purchased from the shop.
# Only one rod may be equipped at a time.
#
# Each rod has:
#   id              : str   — unique key, matches DB rod_id
#   name            : str   — display name
#   description     : str   — flavour text
#   tier            : int   — 1-5 prestige tier
#   price           : int   — shop cost in Spirit Stones
#   base_cooldown   : float — base /reel cooldown in seconds (before upgrade)
#   quality_bonus   : float — additive quality-weight bonus (flat across all qualities)
#   rare_bonus      : float — additive rare-fish bonus
#   xp_bonus        : float — XP multiplier (1.0 = neutral)
#   pouch_luck      : int   — additive bonus to Spirit Pouch luck roll (0-100 scale)
#   unlock_realm    : int   — minimum realm needed to purchase (0 = any)
#   flavor          : str   — short shop description line
#
# UPGRADE TIERS (rod_upgrades table, per user):
#   reel_speed_tier (0-5): reduces base_cooldown by REEL_SPEED_REDUCTION[tier] seconds
#   xp_bonus_tier   (0-9): XP multiplier += XP_BONUS_DELTA[tier]
#   rod_luck_tier   (0-5): pouch_luck  += ROD_LUCK_BONUS[tier]
#   max_bait_tier   (0-9): handled in bait_data.py
# =============================================================

RODS = [
    # ── Tier 1 — Starter ──────────────────────────────────────
    {
        "id":            "mortal_reed",
        "name":          "Mortal Reed Rod",
        "description":   "A simple bamboo rod cut from riverside reeds. It bends, it flexes, it catches fish. Eventually.",
        "tier":          1,
        "price":         0,          # free starter rod
        "base_cooldown": 10.0,
        "quality_bonus": 0.00,
        "rare_bonus":    0.00,
        "xp_bonus":      1.00,
        "pouch_luck":    0,
        "unlock_realm":  0,
        "flavor":        "Where every cultivator's fishing journey begins.",
    },
    # ── Tier 2 ────────────────────────────────────────────────
    {
        "id":            "spirit_willow_rod",
        "name":          "Spirit Willow Rod",
        "description":   "Crafted from willow that grew beside a spiritual spring. The wood hums with gentle Qi.",
        "tier":          2,
        "price":         3_500,
        "base_cooldown": 9.0,
        "quality_bonus": 0.02,
        "rare_bonus":    0.00,
        "xp_bonus":      1.08,
        "pouch_luck":    5,
        "unlock_realm":  0,
        "flavor":        "A smooth upgrade for disciples who've outgrown reeds.",
    },
    {
        "id":            "iron_bone_rod",
        "name":          "Iron Bone Rod",
        "description":   "Forged from the marrow of an iron-bone beast. Heavy but nearly unbreakable.",
        "tier":          2,
        "price":         4_200,
        "base_cooldown": 9.5,
        "quality_bonus": 0.00,
        "rare_bonus":    0.01,
        "xp_bonus":      1.05,
        "pouch_luck":    8,
        "unlock_realm":  0,
        "flavor":        "Popular among disciples who fish turbulent waters.",
    },
    # ── Tier 3 ────────────────────────────────────────────────
    {
        "id":            "jade_serpent_rod",
        "name":          "Jade Serpent Rod",
        "description":   "A sinuous rod carved from a single jade vein. The serpent at its tip seems to watch the water.",
        "tier":          3,
        "price":         15_000,
        "base_cooldown": 8.0,
        "quality_bonus": 0.05,
        "rare_bonus":    0.02,
        "xp_bonus":      1.18,
        "pouch_luck":    15,
        "unlock_realm":  2,
        "flavor":        "Foundation Establishment standard issue for serious fishers.",
    },
    {
        "id":            "thunder_cloud_pole",
        "name":          "Thunder Cloud Pole",
        "description":   "Infused with captured storm energy. Generates micro-lightning pulses that stun nearby fish.",
        "tier":          3,
        "price":         18_000,
        "base_cooldown": 7.5,
        "quality_bonus": 0.03,
        "rare_bonus":    0.03,
        "xp_bonus":      1.15,
        "pouch_luck":    12,
        "unlock_realm":  2,
        "flavor":        "High bite rate, moderate quality. Speed fishers love it.",
    },
    # ── Tier 4 ────────────────────────────────────────────────
    {
        "id":            "astral_bone_rod",
        "name":          "Astral Bone Rod",
        "description":   "Crafted from the rib of a fallen star beast. Channels astral currents to lure rare fish from the deep.",
        "tier":          4,
        "price":         65_000,
        "base_cooldown": 6.0,
        "quality_bonus": 0.08,
        "rare_bonus":    0.05,
        "xp_bonus":      1.30,
        "pouch_luck":    25,
        "unlock_realm":  4,
        "flavor":        "Core Formation grade. A rod worthy of the title 'Fisher of Heaven'.",
    },
    {
        "id":            "void_spine_rod",
        "name":          "Void Spine Rod",
        "description":   "A black rod etched with void runes. Fish cannot feel the line—until it is too late.",
        "tier":          4,
        "price":         80_000,
        "base_cooldown": 5.5,
        "quality_bonus": 0.06,
        "rare_bonus":    0.08,
        "xp_bonus":      1.25,
        "pouch_luck":    30,
        "unlock_realm":  4,
        "flavor":        "Rare fish hunters pay any price for this rod.",
    },
    # ── Tier 5 ────────────────────────────────────────────────
    {
        "id":            "nine_heaven_celestial_rod",
        "name":          "Nine Heaven Celestial Rod",
        "description":   "Formed at the peak of the ninth heaven from condensed celestial light. Those who hold it feel the river of fate itself.",
        "tier":          5,
        "price":         350_000,
        "base_cooldown": 4.0,
        "quality_bonus": 0.12,
        "rare_bonus":    0.12,
        "xp_bonus":      1.60,
        "pouch_luck":    50,
        "unlock_realm":  7,
        "flavor":        "The pinnacle of fishing equipment. Only Nascent Soul cultivators may wield it.",
    },
]

# ── Rod upgrade scaling tables ─────────────────────────────────────────────────

# reel_speed_tier 0-5: seconds subtracted from rod's base_cooldown
REEL_SPEED_REDUCTION = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]

# xp_bonus_tier 0-9: added to rod's xp_bonus multiplier
XP_BONUS_DELTA = [0.00, 0.03, 0.06, 0.10, 0.15, 0.20, 0.27, 0.35, 0.44, 0.55]

# rod_luck_tier 0-5: added to rod's pouch_luck (0-100 scale)
ROD_LUCK_BONUS = [0, 5, 12, 22, 35, 50]

# Minimum cooldown floor regardless of upgrades/rod combo
MIN_COOLDOWN = 3.0

# ── Helpers ───────────────────────────────────────────────────────────────────

ROD_BY_ID: dict = {r["id"]: r for r in RODS}
ROD_ORDER  = [r["id"] for r in RODS]


def get_rod(rod_id: str) -> dict | None:
    """Return rod dict or None if not found."""
    return ROD_BY_ID.get(rod_id)


def effective_cooldown(rod_id: str, reel_speed_tier: int) -> float:
    """Return the effective /reel cooldown in seconds, floored at MIN_COOLDOWN."""
    rod = ROD_BY_ID.get(rod_id)
    if rod is None:
        return 10.0
    reduction = REEL_SPEED_REDUCTION[min(reel_speed_tier, len(REEL_SPEED_REDUCTION) - 1)]
    return max(MIN_COOLDOWN, rod["base_cooldown"] - reduction)


def effective_xp_bonus(rod_id: str, xp_bonus_tier: int) -> float:
    """Return the effective XP multiplier for a rod + upgrade combo."""
    rod = ROD_BY_ID.get(rod_id)
    if rod is None:
        return 1.0
    delta = XP_BONUS_DELTA[min(xp_bonus_tier, len(XP_BONUS_DELTA) - 1)]
    return rod["xp_bonus"] + delta


def effective_pouch_luck(rod_id: str, rod_luck_tier: int) -> int:
    """Return total pouch_luck score (0-100 capped) for a rod + upgrade combo."""
    rod = ROD_BY_ID.get(rod_id)
    if rod is None:
        return 0
    bonus = ROD_LUCK_BONUS[min(rod_luck_tier, len(ROD_LUCK_BONUS) - 1)]
    return min(100, rod["pouch_luck"] + bonus)
