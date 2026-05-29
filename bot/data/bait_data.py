# =============================================================
# OMEGA BOT — BAIT DATA
# Eternal River Sect
# =============================================================
# Each bait has:
#   id           : str  — unique key, matches DB bait_id
#   name         : str  — display name
#   description  : str  — flavour text
#   tier         : int  — 1-5 (shop unlock tier / quality)
#   price        : int  — cost in Spirit Stones per unit
#   max_stack    : int  — base carry limit (upgraded via rod_upgrades.max_bait_tier)
#   bite_bonus   : float— additive bonus to bite chance (0.0 = no effect)
#   quality_bias : dict — quality tier → additive weight modifier (positive = more likely)
#   rare_bonus   : float— additive bonus to rare-fish chance
#   xp_bonus     : float— multiplier on catch XP (1.0 = no effect)
#   license_cost : int  — one-time Spirit Stone cost to unlock in shop (0 = always available)
#   flavor       : str  — short item description shown in shop
# =============================================================

BAITS = [
    {
        "id":           "spirit_worm",
        "name":         "Spirit Worm",
        "description":  "A luminous earthworm infused with ambient Qi. Standard bait for novice cultivators.",
        "tier":         1,
        "price":        10,
        "max_stack":    50,
        "bite_bonus":   0.00,
        "quality_bias": {},
        "rare_bonus":   0.00,
        "xp_bonus":     1.00,
        "license_cost": 0,
        "flavor":       "The backbone of any fisherman's pouch.",
    },
    {
        "id":           "jade_grub",
        "name":         "Jade Grub",
        "description":  "A fat grub preserved in jade essence. Fish find the scent irresistible.",
        "tier":         2,
        "price":        45,
        "max_stack":    40,
        "bite_bonus":   0.05,
        "quality_bias": {"bronze": 0.10, "jade": 0.05},
        "rare_bonus":   0.01,
        "xp_bonus":     1.10,
        "license_cost": 500,
        "flavor":       "Slightly better odds, noticeably better fish.",
    },
    {
        "id":           "golden_cricket",
        "name":         "Golden Cricket",
        "description":  "A cricket gilded in liquid gold essence. Draws fish of higher quality.",
        "tier":         3,
        "price":        120,
        "max_stack":    30,
        "bite_bonus":   0.08,
        "quality_bias": {"jade": 0.12, "gold": 0.08},
        "rare_bonus":   0.02,
        "xp_bonus":     1.20,
        "license_cost": 2_000,
        "flavor":       "A glittering morsel that tempts even proud fish.",
    },
    {
        "id":           "astral_larvae",
        "name":         "Astral Larvae",
        "description":  "Born in the space between stars. Its faint glow attracts rare and powerful fish.",
        "tier":         4,
        "price":        350,
        "max_stack":    20,
        "bite_bonus":   0.12,
        "quality_bias": {"gold": 0.15, "astral": 0.10},
        "rare_bonus":   0.05,
        "xp_bonus":     1.35,
        "license_cost": 8_000,
        "flavor":       "Few can obtain it. Fewer still waste it on common fish.",
    },
    {
        "id":           "void_silk",
        "name":         "Void Silk Thread",
        "description":  "Woven from the essence of collapsed space. Said to be invisible to all fish except the mightiest.",
        "tier":         5,
        "price":        1_200,
        "max_stack":    10,
        "bite_bonus":   0.18,
        "quality_bias": {"astral": 0.15, "immortal": 0.12},
        "rare_bonus":   0.10,
        "xp_bonus":     1.50,
        "license_cost": 25_000,
        "flavor":       "Immortal cultivators keep a few strands for sacred hunts.",
    },
]

# Quick lookup by id
BAIT_BY_ID: dict = {b["id"]: b for b in BAITS}

# Ordered list of bait ids (cheapest → rarest), used for shop display
BAIT_ORDER = [b["id"] for b in BAITS]

# Max bait tier upgrade table:
# rod_upgrades.max_bait_tier (0-9) → flat bonus added to each bait's max_stack
MAX_BAIT_BONUS = [0, 5, 10, 15, 25, 35, 50, 65, 80, 100]


def get_bait(bait_id: str) -> dict | None:
    """Return bait dict or None if not found."""
    return BAIT_BY_ID.get(bait_id)


def get_max_stack(bait_id: str, max_bait_tier: int) -> int:
    """Return effective carry limit for a bait given the user's max_bait_tier upgrade."""
    bait = BAIT_BY_ID.get(bait_id)
    if bait is None:
        return 0
    bonus = MAX_BAIT_BONUS[min(max_bait_tier, len(MAX_BAIT_BONUS) - 1)]
    return bait["max_stack"] + bonus
