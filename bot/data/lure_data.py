# =============================================================
# OMEGA BOT — LURE DATA
# Eternal River Sect
# =============================================================
# Lures are permanent accessories equipped to the rod.
# Only one lure may be active at a time.
#
# Each lure has:
#   id            : str   — unique key, matches DB lure_id
#   name          : str   — display name
#   description   : str   — flavour text
#   tier          : int   — 1-5 prestige tier
#   price         : int   — shop purchase cost in Spirit Stones
#   rare_bonus    : float — additive bonus to rare-fish catch chance
#   quality_bias  : dict  — quality tier → additive weight modifier
#   size_bias     : str   — "large" / "small" / None (shifts size distribution)
#   bite_bonus    : float — additive bonus to bite chance
#   xp_bonus      : float — XP multiplier (1.0 = neutral)
#   unlock_realm  : int   — minimum realm required to purchase (0 = any)
#   flavor        : str   — short shop description
# =============================================================

LURES = [
    # ── Tier 1 ────────────────────────────────────────────────
    {
        "id":           "mortal_hook",
        "name":         "Mortal Hook",
        "description":  "A plain iron hook forged by a mortal blacksmith. Functional. Nothing more.",
        "tier":         1,
        "price":        0,          # default starter lure, costs nothing
        "rare_bonus":   0.00,
        "quality_bias": {},
        "size_bias":    None,
        "bite_bonus":   0.00,
        "xp_bonus":     1.00,
        "unlock_realm": 0,
        "flavor":       "Every cultivator begins here.",
    },
    {
        "id":           "jade_spinner",
        "name":         "Jade Spinner",
        "description":  "A polished jade disc that rotates in the current, emitting soft Qi pulses.",
        "tier":         2,
        "price":        1_500,
        "rare_bonus":   0.01,
        "quality_bias": {"bronze": 0.08, "jade": 0.05},
        "size_bias":    None,
        "bite_bonus":   0.04,
        "xp_bonus":     1.08,
        "unlock_realm": 0,
        "flavor":       "A beloved upgrade for Qi Condensation disciples.",
    },
    {
        "id":           "thunder_jig",
        "name":         "Thunder Jig",
        "description":  "Carved from petrified lightning-struck bamboo. Vibrates subtly and irritates large fish into biting.",
        "tier":         2,
        "price":        2_200,
        "rare_bonus":   0.00,
        "quality_bias": {},
        "size_bias":    "large",
        "bite_bonus":   0.06,
        "xp_bonus":     1.05,
        "unlock_realm": 0,
        "flavor":       "Best used when size matters more than quality.",
    },
    # ── Tier 3 ────────────────────────────────────────────────
    {
        "id":           "golden_dragon_lure",
        "name":         "Golden Dragon Lure",
        "description":  "Shaped like a coiling dragon. Radiates warmth that draws Gold-quality fish.",
        "tier":         3,
        "price":        8_000,
        "rare_bonus":   0.02,
        "quality_bias": {"jade": 0.10, "gold": 0.12},
        "size_bias":    None,
        "bite_bonus":   0.05,
        "xp_bonus":     1.15,
        "unlock_realm": 2,
        "flavor":       "Foundation Establishment disciples favor this lure.",
    },
    {
        "id":           "frost_needle",
        "name":         "Frost Needle",
        "description":  "An icicle of immortal frost, never melting. Attracts fish from cold-water biomes and boosts small-size catches.",
        "tier":         3,
        "price":        7_500,
        "rare_bonus":   0.02,
        "quality_bias": {"jade": 0.08, "gold": 0.06},
        "size_bias":    "small",
        "bite_bonus":   0.05,
        "xp_bonus":     1.12,
        "unlock_realm": 2,
        "flavor":       "Tiny, perfect fish are worth more than you think.",
    },
    # ── Tier 4 ────────────────────────────────────────────────
    {
        "id":           "void_eye_hook",
        "name":         "Void Eye Hook",
        "description":  "An obsidian hook with a pupil-like gem at its curve. Gazes into the deep and calls forth hidden rarities.",
        "tier":         4,
        "price":        28_000,
        "rare_bonus":   0.06,
        "quality_bias": {"gold": 0.12, "astral": 0.08},
        "size_bias":    None,
        "bite_bonus":   0.08,
        "xp_bonus":     1.25,
        "unlock_realm": 4,
        "flavor":       "Core Formation cultivators covet this for rare hunts.",
    },
    {
        "id":           "sovereign_bead",
        "name":         "Sovereign Bead",
        "description":  "A pearl said to have been coughed up by a dragon. Overwhelms fish with sovereign pressure.",
        "tier":         4,
        "price":        35_000,
        "rare_bonus":   0.04,
        "quality_bias": {"astral": 0.12, "immortal": 0.05},
        "size_bias":    "large",
        "bite_bonus":   0.10,
        "xp_bonus":     1.30,
        "unlock_realm": 4,
        "flavor":       "Emanates an aura that compels great fish to rise.",
    },
    # ── Tier 5 ────────────────────────────────────────────────
    {
        "id":           "celestial_feather_hook",
        "name":         "Celestial Feather Hook",
        "description":  "Plucked from a divine crane at the peak of the Nine Heavens. Fishing with it is an act of reverence.",
        "tier":         5,
        "price":        120_000,
        "rare_bonus":   0.12,
        "quality_bias": {"astral": 0.15, "immortal": 0.12},
        "size_bias":    None,
        "bite_bonus":   0.15,
        "xp_bonus":     1.50,
        "unlock_realm": 7,
        "flavor":       "Only those who have touched the heavens may wield this.",
    },
]

# Quick lookup by id
LURE_BY_ID: dict = {l["id"]: l for l in LURES}

# Ordered list for shop display
LURE_ORDER = [l["id"] for l in LURES]


def get_lure(lure_id: str) -> dict | None:
    """Return lure dict or None if not found."""
    return LURE_BY_ID.get(lure_id)
