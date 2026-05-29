# =============================================================
# OMEGA BOT — QUEST DATA
# Eternal River Sect
# =============================================================
# Quests are repeating, multi-level objectives.
# Each quest has several levels (stages); completing one level
# unlocks the next and awards Spirit Stones + XP.
#
# DB table: quests
#   user_id, quest_id, current_progress, level_reached, last_updated
#
# Quest structure:
#   id          : str  — unique key (stored in DB)
#   name        : str  — display name
#   description : str  — flavour text
#   category    : str  — "fishing" | "selling" | "adventure" | "cultivation"
#                        | "collecting" | "gambling"
#   quest_tag   : str  — matches fish_data quest_tags for tag-based tracking
#                        (None for non-fishing quests)
#   levels      : list[dict] — each level:
#       level        : int   — 1-based
#       goal         : int   — cumulative target (not per-level delta)
#       description  : str   — "Catch X…" shown in UI
#       reward_stones: int   — Spirit Stones on completion
#       reward_xp    : int   — Fishing XP on completion
# =============================================================

QUESTS: list[dict] = [

    # ──────────────────────────────────────────────────────────
    # FISHING — Generic
    # ──────────────────────────────────────────────────────────
    {
        "id":          "total_fish_caught",
        "name":        "River's Blessing",
        "description": "The river rewards those who cast often.",
        "category":    "fishing",
        "quest_tag":   None,
        "levels": [
            {"level": 1, "goal":     10, "description": "Catch 10 fish",       "reward_stones":    50, "reward_xp":   20},
            {"level": 2, "goal":     50, "description": "Catch 50 fish",       "reward_stones":   150, "reward_xp":   60},
            {"level": 3, "goal":    100, "description": "Catch 100 fish",      "reward_stones":   300, "reward_xp":  120},
            {"level": 4, "goal":    250, "description": "Catch 250 fish",      "reward_stones":   600, "reward_xp":  250},
            {"level": 5, "goal":    500, "description": "Catch 500 fish",      "reward_stones": 1_200, "reward_xp":  500},
            {"level": 6, "goal":  1_000, "description": "Catch 1,000 fish",    "reward_stones": 2_500, "reward_xp": 1_000},
            {"level": 7, "goal":  2_500, "description": "Catch 2,500 fish",    "reward_stones": 5_000, "reward_xp": 2_000},
            {"level": 8, "goal":  5_000, "description": "Catch 5,000 fish",    "reward_stones":10_000, "reward_xp": 4_000},
            {"level": 9, "goal": 10_000, "description": "Catch 10,000 fish",   "reward_stones":25_000, "reward_xp":10_000},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # FISHING — Freshwater
    # ──────────────────────────────────────────────────────────
    {
        "id":          "freshwater_fisher",
        "name":        "Jade Creek Disciple",
        "description": "Prove your mastery in the freshwater channels.",
        "category":    "fishing",
        "quest_tag":   "freshwater",
        "levels": [
            {"level": 1, "goal":    10, "description": "Catch 10 freshwater fish",   "reward_stones":    60, "reward_xp":   25},
            {"level": 2, "goal":    50, "description": "Catch 50 freshwater fish",   "reward_stones":   180, "reward_xp":   70},
            {"level": 3, "goal":   150, "description": "Catch 150 freshwater fish",  "reward_stones":   400, "reward_xp":  160},
            {"level": 4, "goal":   400, "description": "Catch 400 freshwater fish",  "reward_stones":   900, "reward_xp":  350},
            {"level": 5, "goal": 1_000, "description": "Catch 1,000 freshwater fish","reward_stones": 2_000, "reward_xp":  800},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # FISHING — Saltwater
    # ──────────────────────────────────────────────────────────
    {
        "id":          "saltwater_fisher",
        "name":        "Crimson Tide Veteran",
        "description": "The ocean tests disciples with salt, storm, and depth.",
        "category":    "fishing",
        "quest_tag":   "saltwater",
        "levels": [
            {"level": 1, "goal":    10, "description": "Catch 10 saltwater fish",    "reward_stones":    60, "reward_xp":   25},
            {"level": 2, "goal":    50, "description": "Catch 50 saltwater fish",    "reward_stones":   180, "reward_xp":   70},
            {"level": 3, "goal":   150, "description": "Catch 150 saltwater fish",   "reward_stones":   400, "reward_xp":  160},
            {"level": 4, "goal":   400, "description": "Catch 400 saltwater fish",   "reward_stones":   900, "reward_xp":  350},
            {"level": 5, "goal": 1_000, "description": "Catch 1,000 saltwater fish", "reward_stones": 2_000, "reward_xp":  800},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # FISHING — High Tier (tier4+)
    # ──────────────────────────────────────────────────────────
    {
        "id":          "high_tier_hunter",
        "name":        "Dragon's Spine Seeker",
        "description": "Rare, powerful fish await those who know where to look.",
        "category":    "fishing",
        "quest_tag":   "high_tier",
        "levels": [
            {"level": 1, "goal":   5, "description": "Catch 5 high-tier fish (Tier 4+)",   "reward_stones":   200, "reward_xp":   80},
            {"level": 2, "goal":  20, "description": "Catch 20 high-tier fish (Tier 4+)",  "reward_stones":   700, "reward_xp":  280},
            {"level": 3, "goal":  60, "description": "Catch 60 high-tier fish (Tier 4+)",  "reward_stones": 2_000, "reward_xp":  800},
            {"level": 4, "goal": 150, "description": "Catch 150 high-tier fish (Tier 4+)", "reward_stones": 5_000, "reward_xp": 2_000},
            {"level": 5, "goal": 400, "description": "Catch 400 high-tier fish (Tier 4+)", "reward_stones":12_000, "reward_xp": 5_000},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # FISHING — Rare Fish
    # ──────────────────────────────────────────────────────────
    {
        "id":          "rare_hunter",
        "name":        "Sovereign's Eye",
        "description": "True cultivators seek what others cannot find.",
        "category":    "fishing",
        "quest_tag":   "rare",
        "levels": [
            {"level": 1, "goal":  1, "description": "Catch 1 rare fish",   "reward_stones":   500, "reward_xp":  200},
            {"level": 2, "goal":  5, "description": "Catch 5 rare fish",   "reward_stones": 2_000, "reward_xp":  800},
            {"level": 3, "goal": 15, "description": "Catch 15 rare fish",  "reward_stones": 6_000, "reward_xp": 2_500},
            {"level": 4, "goal": 40, "description": "Catch 40 rare fish",  "reward_stones":18_000, "reward_xp": 7_000},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # FISHING — Event Fish
    # ──────────────────────────────────────────────────────────
    {
        "id":          "event_chaser",
        "name":        "Omen Chaser",
        "description": "Heaven sends signs. Wise cultivators fish when omens appear.",
        "category":    "fishing",
        "quest_tag":   "event",
        "levels": [
            {"level": 1, "goal":  1, "description": "Catch 1 event fish",   "reward_stones":   300, "reward_xp":  120},
            {"level": 2, "goal":  5, "description": "Catch 5 event fish",   "reward_stones": 1_000, "reward_xp":  400},
            {"level": 3, "goal": 15, "description": "Catch 15 event fish",  "reward_stones": 3_000, "reward_xp": 1_200},
            {"level": 4, "goal": 40, "description": "Catch 40 event fish",  "reward_stones": 8_000, "reward_xp": 3_200},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # FISHING — Elemental Fish
    # ──────────────────────────────────────────────────────────
    {
        "id":          "elemental_angler",
        "name":        "Five Elements Fisher",
        "description": "The elements manifest in fish form. Catch each when they arise.",
        "category":    "fishing",
        "quest_tag":   "elemental",
        "levels": [
            {"level": 1, "goal":  1, "description": "Catch 1 elemental fish",  "reward_stones":   400, "reward_xp":  160},
            {"level": 2, "goal":  5, "description": "Catch 5 elemental fish",  "reward_stones": 1_500, "reward_xp":  600},
            {"level": 3, "goal": 20, "description": "Catch 20 elemental fish", "reward_stones": 5_000, "reward_xp": 2_000},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # COLLECTING — Junk
    # ──────────────────────────────────────────────────────────
    {
        "id":          "junk_collector",
        "name":        "Bottom Feeder",
        "description": "Even junk from the riverbed has value to the discerning eye.",
        "category":    "collecting",
        "quest_tag":   "junk",
        "levels": [
            {"level": 1, "goal":   5, "description": "Pull up 5 junk items",    "reward_stones":    30, "reward_xp":   10},
            {"level": 2, "goal":  25, "description": "Pull up 25 junk items",   "reward_stones":   100, "reward_xp":   40},
            {"level": 3, "goal": 100, "description": "Pull up 100 junk items",  "reward_stones":   300, "reward_xp":  120},
            {"level": 4, "goal": 500, "description": "Pull up 500 junk items",  "reward_stones":   800, "reward_xp":  320},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # SELLING — Spirit Stones earned
    # ──────────────────────────────────────────────────────────
    {
        "id":          "spirit_stone_earner",
        "name":        "Stone Magnate",
        "description": "Wealth and cultivation walk hand in hand.",
        "category":    "selling",
        "quest_tag":   None,
        "levels": [
            {"level": 1, "goal":     1_000, "description": "Earn 1,000 Spirit Stones from fishing",     "reward_stones":    100, "reward_xp":   40},
            {"level": 2, "goal":    10_000, "description": "Earn 10,000 Spirit Stones from fishing",    "reward_stones":    500, "reward_xp":  200},
            {"level": 3, "goal":    50_000, "description": "Earn 50,000 Spirit Stones from fishing",    "reward_stones":  2_000, "reward_xp":  800},
            {"level": 4, "goal":   250_000, "description": "Earn 250,000 Spirit Stones from fishing",   "reward_stones":  8_000, "reward_xp": 3_000},
            {"level": 5, "goal": 1_000_000, "description": "Earn 1,000,000 Spirit Stones from fishing", "reward_stones": 30_000, "reward_xp":12_000},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # ADVENTURE
    # ──────────────────────────────────────────────────────────
    {
        "id":          "adventurer",
        "name":        "Wandering Sword",
        "description": "Leave the sect's safety and walk the perilous path.",
        "category":    "adventure",
        "quest_tag":   None,
        "levels": [
            {"level": 1, "goal":   1, "description": "Complete 1 adventure",    "reward_stones":    80, "reward_xp":   30},
            {"level": 2, "goal":   5, "description": "Complete 5 adventures",   "reward_stones":   250, "reward_xp":  100},
            {"level": 3, "goal":  20, "description": "Complete 20 adventures",  "reward_stones":   800, "reward_xp":  320},
            {"level": 4, "goal":  50, "description": "Complete 50 adventures",  "reward_stones": 2_000, "reward_xp":  800},
            {"level": 5, "goal": 100, "description": "Complete 100 adventures", "reward_stones": 5_000, "reward_xp": 2_000},
            {"level": 6, "goal": 250, "description": "Complete 250 adventures", "reward_stones":12_000, "reward_xp": 5_000},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # CULTIVATION — Realms reached
    # ──────────────────────────────────────────────────────────
    {
        "id":          "realm_climber",
        "name":        "Heaven Ascender",
        "description": "The path of cultivation is the path of becoming.",
        "category":    "cultivation",
        "quest_tag":   None,
        "levels": [
            {"level": 1, "goal": 1, "description": "Reach Realm 1 (Qi Condensation)",     "reward_stones":   500, "reward_xp":  200},
            {"level": 2, "goal": 2, "description": "Reach Realm 2 (Foundation Establishment)", "reward_stones": 1_500, "reward_xp":  600},
            {"level": 3, "goal": 3, "description": "Reach Realm 3 (Golden Core)",         "reward_stones": 4_000, "reward_xp": 1_600},
            {"level": 4, "goal": 4, "description": "Reach Realm 4 (Nascent Soul)",        "reward_stones":10_000, "reward_xp": 4_000},
            {"level": 5, "goal": 5, "description": "Reach Realm 5 (Spirit Severing)",     "reward_stones":25_000, "reward_xp":10_000},
            {"level": 6, "goal": 6, "description": "Reach Realm 6 (Void Crossing)",       "reward_stones":50_000, "reward_xp":20_000},
            {"level": 7, "goal": 7, "description": "Reach Realm 7 (Dao Manifestation)",   "reward_stones":100_000,"reward_xp":40_000},
            {"level": 8, "goal": 8, "description": "Reach Realm 8 (Immortal Ascension)",  "reward_stones":200_000,"reward_xp":80_000},
            {"level": 9, "goal": 9, "description": "Reach Realm 9 (Eternal Sovereign)",   "reward_stones":500_000,"reward_xp":200_000},
        ],
    },

    # ──────────────────────────────────────────────────────────
    # GAMBLING — Scratch tickets used
    # ──────────────────────────────────────────────────────────
    {
        "id":          "gambler",
        "name":        "Fate Temptress",
        "description": "Some call it luck. Cultivators call it fate-testing.",
        "category":    "gambling",
        "quest_tag":   None,
        "levels": [
            {"level": 1, "goal":   1, "description": "Use 1 scratch ticket",    "reward_stones":    50, "reward_xp":   20},
            {"level": 2, "goal":  10, "description": "Use 10 scratch tickets",  "reward_stones":   200, "reward_xp":   80},
            {"level": 3, "goal":  50, "description": "Use 50 scratch tickets",  "reward_stones":   700, "reward_xp":  280},
            {"level": 4, "goal": 200, "description": "Use 200 scratch tickets", "reward_stones": 2_000, "reward_xp":  800},
            {"level": 5, "goal": 500, "description": "Use 500 scratch tickets", "reward_stones": 5_000, "reward_xp": 2_000},
        ],
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# LOOKUP HELPERS
# ──────────────────────────────────────────────────────────────────────────────

QUEST_BY_ID: dict[str, dict] = {q["id"]: q for q in QUESTS}

# Index quests by quest_tag for fast fishing-catch lookups
QUESTS_BY_TAG: dict[str, list[dict]] = {}
for _q in QUESTS:
    if _q["quest_tag"]:
        QUESTS_BY_TAG.setdefault(_q["quest_tag"], []).append(_q)


def get_quest(quest_id: str) -> dict | None:
    return QUEST_BY_ID.get(quest_id)


def get_level(quest: dict, level_num: int) -> dict | None:
    """Return the level dict for a quest at 1-based level_num."""
    for lvl in quest["levels"]:
        if lvl["level"] == level_num:
            return lvl
    return None


def next_level(quest: dict, current_level_reached: int) -> dict | None:
    """Return the next uncompleted level dict, or None if quest is fully complete."""
    return get_level(quest, current_level_reached + 1)


def quests_for_tag(tag: str) -> list[dict]:
    """Return all quests that track the given quest_tag."""
    return QUESTS_BY_TAG.get(tag, [])


def quests_by_category(category: str) -> list[dict]:
    return [q for q in QUESTS if q["category"] == category]
