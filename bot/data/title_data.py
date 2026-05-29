# =============================================================
# OMEGA BOT — TITLE DATA
# Eternal River Sect
# =============================================================
# Total titles: 132
#   - 50 general/progression titles
#   - 82 species titles
#       78 species × L1 (catch once)
#       +4 ultra-rare species × L2 (catch 5 times)  = 82
#
# Title IDs for species titles MUST match the title_l1 / title_l2
# values stored in fish_data.py so fish catches auto-unlock them.
#
# Fields:
#   id          : str   — unique key (matches title_l1/l2 in fish_data)
#   name        : str   — display name / Discord role name
#   description : str   — flavour text shown in /profile
#   category    : str   — "general" | "species"
#   xp_mult     : float — passive fishing XP multiplier when active
#   qi_mult     : float — passive Qi gain multiplier when active
#   unlock_type : str   —
#       "level"         fishing level threshold
#       "realm"         realm reached
#       "fish_count"    total fish caught milestone
#       "fish_species"  catch a specific species (L1 or L2)
#       "spirit_stones" total SS earned milestone
#       "adventure"     total adventures milestone
#       "codex"         codex completion % milestone
#   unlock_value: int/str — threshold or species_id
#   unlock_level: int   — 0 for non-species; 1 = catch once, 2 = catch 5×
# =============================================================

# ──────────────────────────────────────────────────────────────────────────────
# GENERAL / PROGRESSION TITLES (50)
# ──────────────────────────────────────────────────────────────────────────────

GENERAL_TITLES: list[dict] = [

    # ── Fishing Level milestones ────────────────────────────────────────────
    {
        "id": "river_novice", "name": "River Novice",
        "description": "A fresh disciple who has just discovered the art of the fishing rod.",
        "category": "general", "xp_mult": 1.01, "qi_mult": 1.00,
        "unlock_type": "level", "unlock_value": 1, "unlock_level": 0,
    },
    {
        "id": "stream_walker", "name": "Stream Walker",
        "description": "You've learned to read the current. The fish are no longer strangers.",
        "category": "general", "xp_mult": 1.02, "qi_mult": 1.00,
        "unlock_type": "level", "unlock_value": 5, "unlock_level": 0,
    },
    {
        "id": "still_water_disciple", "name": "Still Water Disciple",
        "description": "Patience refined to an art. You wait. The fish come.",
        "category": "general", "xp_mult": 1.03, "qi_mult": 1.00,
        "unlock_type": "level", "unlock_value": 10, "unlock_level": 0,
    },
    {
        "id": "jade_hook_initiate", "name": "Jade Hook Initiate",
        "description": "The sect has noticed your dedication. A jade hook is your reward.",
        "category": "general", "xp_mult": 1.05, "qi_mult": 1.01,
        "unlock_type": "level", "unlock_value": 15, "unlock_level": 0,
    },
    {
        "id": "river_adept", "name": "River Adept",
        "description": "You feel the Qi in the water with every cast.",
        "category": "general", "xp_mult": 1.06, "qi_mult": 1.01,
        "unlock_type": "level", "unlock_value": 20, "unlock_level": 0,
    },
    {
        "id": "deep_current_seeker", "name": "Deep Current Seeker",
        "description": "Most fishers watch the surface. You watch what moves beneath.",
        "category": "general", "xp_mult": 1.08, "qi_mult": 1.02,
        "unlock_type": "level", "unlock_value": 25, "unlock_level": 0,
    },
    {
        "id": "spirit_fisher", "name": "Spirit Fisher",
        "description": "Your line moves in harmony with the spiritual currents of the world.",
        "category": "general", "xp_mult": 1.10, "qi_mult": 1.02,
        "unlock_type": "level", "unlock_value": 30, "unlock_level": 0,
    },
    {
        "id": "star_net_caster", "name": "Star Net Caster",
        "description": "Your cast arcs like a falling star and lands without a ripple.",
        "category": "general", "xp_mult": 1.12, "qi_mult": 1.03,
        "unlock_type": "level", "unlock_value": 35, "unlock_level": 0,
    },
    {
        "id": "elder_fishers_peer", "name": "Elder Fisher's Peer",
        "description": "The elders nod when you walk to the river's edge.",
        "category": "general", "xp_mult": 1.14, "qi_mult": 1.04,
        "unlock_type": "level", "unlock_value": 40, "unlock_level": 0,
    },
    {
        "id": "master_of_tides", "name": "Master of Tides",
        "description": "Even the river obeys your intent.",
        "category": "general", "xp_mult": 1.18, "qi_mult": 1.05,
        "unlock_type": "level", "unlock_value": 50, "unlock_level": 0,
    },
    {
        "id": "sovereign_of_the_river", "name": "Sovereign of the River",
        "description": "You are the river. The river is you.",
        "category": "general", "xp_mult": 1.22, "qi_mult": 1.06,
        "unlock_type": "level", "unlock_value": 60, "unlock_level": 0,
    },
    {
        "id": "heavens_angler", "name": "Heaven's Angler",
        "description": "The heavens themselves have acknowledged your fishing dao.",
        "category": "general", "xp_mult": 1.30, "qi_mult": 1.08,
        "unlock_type": "level", "unlock_value": 70, "unlock_level": 0,
    },

    # ── Realm milestones ───────────────────────────────────────────────────
    {
        "id": "qi_condensate", "name": "Qi Condensate",
        "description": "Your Qi has begun to condense. The first step on the immortal path.",
        "category": "general", "xp_mult": 1.03, "qi_mult": 1.05,
        "unlock_type": "realm", "unlock_value": 1, "unlock_level": 0,
    },
    {
        "id": "foundation_walker", "name": "Foundation Walker",
        "description": "A solid foundation beneath your feet. The peak is now a possibility.",
        "category": "general", "xp_mult": 1.05, "qi_mult": 1.08,
        "unlock_type": "realm", "unlock_value": 2, "unlock_level": 0,
    },
    {
        "id": "golden_core_bearer", "name": "Golden Core Bearer",
        "description": "A golden core spins within your dantian. The mortal world cannot contain you.",
        "category": "general", "xp_mult": 1.08, "qi_mult": 1.12,
        "unlock_type": "realm", "unlock_value": 3, "unlock_level": 0,
    },
    {
        "id": "nascent_born", "name": "Nascent Born",
        "description": "Your soul has taken a second form. You are no longer entirely human.",
        "category": "general", "xp_mult": 1.12, "qi_mult": 1.18,
        "unlock_type": "realm", "unlock_value": 4, "unlock_level": 0,
    },
    {
        "id": "spirit_severer", "name": "Spirit Severer",
        "description": "You have cut the chains of the mortal spirit. Only the Way remains.",
        "category": "general", "xp_mult": 1.15, "qi_mult": 1.22,
        "unlock_type": "realm", "unlock_value": 5, "unlock_level": 0,
    },
    {
        "id": "void_crossing_sage", "name": "Void Crossing Sage",
        "description": "You have stepped through the void and emerged unchanged.",
        "category": "general", "xp_mult": 1.18, "qi_mult": 1.28,
        "unlock_type": "realm", "unlock_value": 6, "unlock_level": 0,
    },
    {
        "id": "dao_manifestation", "name": "Dao Manifestation",
        "description": "Your will bends reality. The Dao speaks through your every motion.",
        "category": "general", "xp_mult": 1.22, "qi_mult": 1.35,
        "unlock_type": "realm", "unlock_value": 7, "unlock_level": 0,
    },
    {
        "id": "immortal_ascendant", "name": "Immortal Ascendant",
        "description": "You stand at the threshold of immortality. The river bows to you.",
        "category": "general", "xp_mult": 1.28, "qi_mult": 1.45,
        "unlock_type": "realm", "unlock_value": 8, "unlock_level": 0,
    },
    {
        "id": "eternal_sovereign", "name": "Eternal Sovereign",
        "description": "The ninth heaven. Beyond this, there is only legend.",
        "category": "general", "xp_mult": 1.40, "qi_mult": 1.60,
        "unlock_type": "realm", "unlock_value": 9, "unlock_level": 0,
    },

    # ── Fish Count milestones ──────────────────────────────────────────────
    {
        "id": "first_catch", "name": "First Catch",
        "description": "One fish. The journey is real.",
        "category": "general", "xp_mult": 1.01, "qi_mult": 1.00,
        "unlock_type": "fish_count", "unlock_value": 1, "unlock_level": 0,
    },
    {
        "id": "ten_haul", "name": "Ten Haul",
        "description": "Ten fish hauled. The river remembers you now.",
        "category": "general", "xp_mult": 1.02, "qi_mult": 1.00,
        "unlock_type": "fish_count", "unlock_value": 10, "unlock_level": 0,
    },
    {
        "id": "century_catcher", "name": "Century Catcher",
        "description": "One hundred fish. You've graduated past beginner's luck.",
        "category": "general", "xp_mult": 1.03, "qi_mult": 1.01,
        "unlock_type": "fish_count", "unlock_value": 100, "unlock_level": 0,
    },
    {
        "id": "five_hundred_strong", "name": "Five Hundred Strong",
        "description": "500 catches. Your name surfaces in sect fishing records.",
        "category": "general", "xp_mult": 1.05, "qi_mult": 1.01,
        "unlock_type": "fish_count", "unlock_value": 500, "unlock_level": 0,
    },
    {
        "id": "thousand_scale", "name": "Thousand Scale",
        "description": "1,000 fish. Entire shoals have passed through your hands.",
        "category": "general", "xp_mult": 1.08, "qi_mult": 1.02,
        "unlock_type": "fish_count", "unlock_value": 1_000, "unlock_level": 0,
    },
    {
        "id": "ten_thousand_tides", "name": "Ten Thousand Tides",
        "description": "10,000 fish. You are a legend of the waterways.",
        "category": "general", "xp_mult": 1.15, "qi_mult": 1.04,
        "unlock_type": "fish_count", "unlock_value": 10_000, "unlock_level": 0,
    },

    # ── Spirit Stone milestones ────────────────────────────────────────────
    {
        "id": "stone_hoarder", "name": "Stone Hoarder",
        "description": "1,000 Spirit Stones earned. The cultivation path is costly—you understand this now.",
        "category": "general", "xp_mult": 1.01, "qi_mult": 1.01,
        "unlock_type": "spirit_stones", "unlock_value": 1_000, "unlock_level": 0,
    },
    {
        "id": "jade_vault_keeper", "name": "Jade Vault Keeper",
        "description": "10,000 Spirit Stones earned through the art of fishing.",
        "category": "general", "xp_mult": 1.03, "qi_mult": 1.02,
        "unlock_type": "spirit_stones", "unlock_value": 10_000, "unlock_level": 0,
    },
    {
        "id": "golden_river_merchant", "name": "Golden River Merchant",
        "description": "100,000 Spirit Stones earned. The river flows gold when you fish.",
        "category": "general", "xp_mult": 1.06, "qi_mult": 1.03,
        "unlock_type": "spirit_stones", "unlock_value": 100_000, "unlock_level": 0,
    },
    {
        "id": "sect_pillar", "name": "Sect Pillar",
        "description": "500,000 Spirit Stones earned. Your contributions are beyond measure.",
        "category": "general", "xp_mult": 1.10, "qi_mult": 1.05,
        "unlock_type": "spirit_stones", "unlock_value": 500_000, "unlock_level": 0,
    },
    {
        "id": "million_stone_immortal", "name": "Million Stone Immortal",
        "description": "1,000,000 Spirit Stones earned. Sects court you for donations.",
        "category": "general", "xp_mult": 1.15, "qi_mult": 1.08,
        "unlock_type": "spirit_stones", "unlock_value": 1_000_000, "unlock_level": 0,
    },

    # ── Adventure milestones ───────────────────────────────────────────────
    {
        "id": "wandering_disciple", "name": "Wandering Disciple",
        "description": "You've left the safety of the sect, even briefly.",
        "category": "general", "xp_mult": 1.02, "qi_mult": 1.02,
        "unlock_type": "adventure", "unlock_value": 1, "unlock_level": 0,
    },
    {
        "id": "ten_trials_survivor", "name": "Ten Trials Survivor",
        "description": "Ten expeditions. Scars and stories in equal measure.",
        "category": "general", "xp_mult": 1.03, "qi_mult": 1.03,
        "unlock_type": "adventure", "unlock_value": 10, "unlock_level": 0,
    },
    {
        "id": "demon_fish_slayer", "name": "Demon Fish Slayer",
        "description": "25 adventures completed. Some fish should never have been caught. You caught them anyway.",
        "category": "general", "xp_mult": 1.05, "qi_mult": 1.04,
        "unlock_type": "adventure", "unlock_value": 25, "unlock_level": 0,
    },
    {
        "id": "iron_road_walker", "name": "Iron Road Walker",
        "description": "50 adventures. The path has hardened your Dao-heart.",
        "category": "general", "xp_mult": 1.07, "qi_mult": 1.05,
        "unlock_type": "adventure", "unlock_value": 50, "unlock_level": 0,
    },
    {
        "id": "hundred_trial_sage", "name": "Hundred Trial Sage",
        "description": "100 adventures. You have seen more of the world than most elders.",
        "category": "general", "xp_mult": 1.10, "qi_mult": 1.07,
        "unlock_type": "adventure", "unlock_value": 100, "unlock_level": 0,
    },

    # ── Codex milestones ───────────────────────────────────────────────────
    {
        "id": "curious_scholar", "name": "Curious Scholar",
        "description": "You've catalogued a quarter of all known fish.",
        "category": "general", "xp_mult": 1.03, "qi_mult": 1.02,
        "unlock_type": "codex", "unlock_value": 25, "unlock_level": 0,
    },
    {
        "id": "half_codex_sage", "name": "Half Codex Sage",
        "description": "The first half of the great codex is yours.",
        "category": "general", "xp_mult": 1.06, "qi_mult": 1.04,
        "unlock_type": "codex", "unlock_value": 50, "unlock_level": 0,
    },
    {
        "id": "grand_codex_archivist", "name": "Grand Codex Archivist",
        "description": "Three quarters of all fish documented. The elders consult your notes.",
        "category": "general", "xp_mult": 1.10, "qi_mult": 1.06,
        "unlock_type": "codex", "unlock_value": 75, "unlock_level": 0,
    },
    {
        "id": "boundless_net", "name": "Boundless Net",
        "description": "90% codex complete. Your reach extends to every corner of the waters.",
        "category": "general", "xp_mult": 1.14, "qi_mult": 1.08,
        "unlock_type": "codex", "unlock_value": 90, "unlock_level": 0,
    },
    {
        "id": "eternal_codex_master", "name": "Eternal Codex Master",
        "description": "Every fish catalogued. The elders step aside when you enter the archive.",
        "category": "general", "xp_mult": 1.20, "qi_mult": 1.10,
        "unlock_type": "codex", "unlock_value": 100, "unlock_level": 0,
    },

    # ── Rare / Prestige general titles ────────────────────────────────────
    {
        "id": "tide_touched", "name": "Tide-Touched",
        "description": "The tides of fate have marked you. Fish sense your coming.",
        "category": "general", "xp_mult": 1.08, "qi_mult": 1.04,
        "unlock_type": "fish_count", "unlock_value": 250, "unlock_level": 0,
    },
    {
        "id": "iron_patience", "name": "Iron Patience",
        "description": "You've waited beside silent waters long enough to outlast mountains.",
        "category": "general", "xp_mult": 1.09, "qi_mult": 1.05,
        "unlock_type": "fish_count", "unlock_value": 750, "unlock_level": 0,
    },
    {
        "id": "unbroken_line", "name": "Unbroken Line",
        "description": "No fish has ever snapped your line. 2,000 catches proves it.",
        "category": "general", "xp_mult": 1.11, "qi_mult": 1.06,
        "unlock_type": "fish_count", "unlock_value": 2_000, "unlock_level": 0,
    },
    {
        "id": "void_angler", "name": "Void Angler",
        "description": "You fish not just in rivers, but in the space between worlds.",
        "category": "general", "xp_mult": 1.18, "qi_mult": 1.08,
        "unlock_type": "realm", "unlock_value": 5, "unlock_level": 0,
    },
    {
        "id": "astral_current_rider", "name": "Astral Current Rider",
        "description": "You don't follow the river. You let the astral current carry you.",
        "category": "general", "xp_mult": 1.20, "qi_mult": 1.12,
        "unlock_type": "realm", "unlock_value": 6, "unlock_level": 0,
    },
    {
        "id": "dao_of_the_river", "name": "Dao of the River",
        "description": "You have not merely mastered fishing. You have become the Dao of the River.",
        "category": "general", "xp_mult": 1.50, "qi_mult": 1.30,
        "unlock_type": "fish_count", "unlock_value": 50_000, "unlock_level": 0,
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# SPECIES TITLES (82)
# title IDs match fish_data.py title_l1 / title_l2 strings exactly
# unlock_value = species_id; unlock_level 1=first catch, 2=5 catches
# ──────────────────────────────────────────────────────────────────────────────

SPECIES_TITLES: list[dict] = [

    # ─── FRESHWATER (32 fish → 33 titles incl. 1 L2) ─────────────────────

    # Tier 1 — all freshwater channels
    {"id": "salmon_patriarch",    "name": "Salmon Patriarch",
     "description": "A River Dragon Salmon answered your first call to the water.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "river_dragon_salmon",      "unlock_level": 1},
    {"id": "carp_ancestor",       "name": "Carp Ancestor",
     "description": "The jade-scaled carp of primordial rivers — yours.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "jade_river_carp",          "unlock_level": 1},
    {"id": "rainbow_sage",        "name": "Rainbow Sage",
     "description": "Five colors, one line. The trout chose wisely.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "five_colored_spirit_trout","unlock_level": 1},
    {"id": "iron_jaw",            "name": "Iron Jaw",
     "description": "Its jaw could crush iron. Your rod held firm.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "iron_jaw_spirit_bass",     "unlock_level": 1},
    {"id": "jade_current",        "name": "Jade Current",
     "description": "Small, beautiful, and surprisingly stubborn.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "jade_perch",               "unlock_level": 1},
    {"id": "spirit_eye",          "name": "Spirit Eye",
     "description": "Those eyes see through illusions. They couldn't see past your bait.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "spirit_eye_walleye",       "unlock_level": 1},
    {"id": "azure_moon",          "name": "Azure Moon",
     "description": "Moon-touched gill patterns that shimmer with each breath.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "azure_moon_gill",          "unlock_level": 1},

    # Tier 2 — all freshwater channels
    {"id": "fortune_child",       "name": "Fortune Child",
     "description": "The crimson fortune fish brings prosperity. It brought you a title.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "crimson_fortune_fish",     "unlock_level": 1},
    {"id": "thunder_claw",        "name": "Thunder Claw",
     "description": "Those claws could snap a cultivator's finger. Yours survived.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "thunder_claw_crayfish",    "unlock_level": 1},
    {"id": "drum_sage",           "name": "Drum Sage",
     "description": "The sound it makes is said to shake loose trapped Qi.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "rumbling_drum_fish",       "unlock_level": 1},
    {"id": "wind_step",           "name": "Wind Step",
     "description": "Blinks forward with wind-step speed. Caught anyway.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "wind_step_minnow",         "unlock_level": 1},
    {"id": "shell_sage",          "name": "Shell Sage",
     "description": "A jade shell that seals secrets within. You opened one.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "jade_shell_snail",         "unlock_level": 1},
    {"id": "mist_walker",         "name": "Mist Walker",
     "description": "Moves in silver mist where lines disappear. Yours found it.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "silver_mist_crappie",      "unlock_level": 1},
    {"id": "sword_spine",         "name": "Sword Spine",
     "description": "Each spine a blade. A pike both beautiful and dangerous.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "sword_spine_pike",         "unlock_level": 1},
    {"id": "serpent_spine",       "name": "Serpent Spine",
     "description": "Its spine ripples like a serpent in motion.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "serpent_spine_bowfin",     "unlock_level": 1},

    # Tier 3 — paired freshwater channels
    {"id": "whisker_ancient",     "name": "Whisker Ancient",
     "description": "Void whiskers that sense Qi disturbances. They sensed yours—and surrendered.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "void_whisker_catfish",     "unlock_level": 1},
    {"id": "jade_leaper",         "name": "Jade Leaper",
     "description": "Leaps between realms on jade-webbed feet. Caught mid-leap.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "spirit_jade_frog",         "unlock_level": 1},
    {"id": "thunder_herald",      "name": "Thunder Herald",
     "description": "Its croak precedes lightning storms. You caught the herald.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "thunder_toad",             "unlock_level": 1},
    {"id": "tortoise_elder",      "name": "Tortoise Elder",
     "description": "A black tortoise older than the sect's first patriarch.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "black_tortoise_turtle",    "unlock_level": 1},
    {"id": "blood_cultivator",    "name": "Blood Cultivator",
     "description": "It feeds on Qi-rich blood. It found yours irresistible.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "blood_qi_leech",           "unlock_level": 1},
    {"id": "dragon_king",         "name": "Dragon King",
     "description": "The Dragon King Salmon rules its tributary. You dethroned it.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "dragon_king_salmon",       "unlock_level": 1},
    {"id": "heaven_gazer",        "name": "Heaven Gazer",
     "description": "Always looking upward—until your hook brought it down.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "heaven_gazing_koi",        "unlock_level": 1},
    {"id": "moon_soul",           "name": "Moon Soul",
     "description": "Its soul is tethered to the moon. You caught it at low tide.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "moonlit_soul_fish",        "unlock_level": 1},
    {"id": "jade_wanderer",       "name": "Jade Wanderer",
     "description": "A salamander that walks between water and air. Now it walks your path.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "jade_salamander",          "unlock_level": 1},
    {"id": "pup_immortal",        "name": "Pup Immortal",
     "description": "Tiny, yet its Qi signature rivals Foundation-stage cultivators.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "immortal_pup_fish",        "unlock_level": 1},

    # Tier 4 — channel exclusives
    {"id": "scale_sovereign",     "name": "Scale Sovereign",
     "description": "A thousand scales, each a talisman. All yours now.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "thousand_scale_serpent",   "unlock_level": 1},
    {"id": "iron_spine",          "name": "Iron Spine",
     "description": "Its spine could pierce a Foundation-grade armor. Your rod held.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "iron_spine_sturgeon",      "unlock_level": 1},
    {"id": "stone_shell",         "name": "Stone Shell",
     "description": "That claw nearly took your finger. Worth it.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "stone_shell_crab",         "unlock_level": 1},
    {"id": "iron_scale",          "name": "Iron Scale",
     "description": "Scales harder than refined iron. Your hook found the gap.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "iron_scale_gar",           "unlock_level": 1},
    {"id": "dragon_lurker",       "name": "Dragon Lurker",
     "description": "200 cm of ambush predator, lurking in the deepest channel.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "dragon_scale_lurker",      "unlock_level": 1},
    {"id": "river_demon",         "name": "River Demon",
     "description": "The Demon River Shark terrorized this channel. Not anymore.",
     "category": "species", "xp_mult": 1.06, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "demon_river_shark",        "unlock_level": 1},

    # Tier 6 — ultra-rare (L1 + L2)
    {"id": "nine_dragon",         "name": "Nine Dragon's Guest",
     "description": "The Nine-Dragon Sovereign Carp surfaced for you. The sect whispers your name.",
     "category": "species", "xp_mult": 1.12, "qi_mult": 1.08,
     "unlock_type": "fish_species", "unlock_value": "nine_dragon_sovereign_carp","unlock_level": 1},
    {"id": "sovereign_of_nine_dragons", "name": "Sovereign of Nine Dragons",
     "description": "Five Nine-Dragon Sovereign Carp caught. You are a legend the fish whisper about.",
     "category": "species", "xp_mult": 1.28, "qi_mult": 1.18,
     "unlock_type": "fish_species", "unlock_value": "nine_dragon_sovereign_carp","unlock_level": 2},

    # ─── SALTWATER (32 fish → 33 titles incl. 1 L2) ──────────────────────

    # Tier 1
    {"id": "sea_pilgrim",         "name": "Sea Pilgrim",
     "description": "The ocean's first answer to your cast.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "azure_ocean_salmon",       "unlock_level": 1},
    {"id": "heaven_wing",         "name": "Heaven Wing",
     "description": "Leaps clear of the surface, for a moment touching the sky.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "heaven_wing_fish",         "unlock_level": 1},
    {"id": "shadow_veil",         "name": "Shadow Veil",
     "description": "Flatfish that blends with the seafloor. Your lure found it anyway.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "veil_shadow_flounder",     "unlock_level": 1},
    {"id": "five_poison",         "name": "Five Poison",
     "description": "Five toxins in one colorful package. You wore gloves.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "five_poison_clown_fish",   "unlock_level": 1},
    {"id": "thunder_child",       "name": "Thunder Child",
     "description": "Miniature thunder locked in a tiny body. Tiny but shocking.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "thunder_shrimp",           "unlock_level": 1},
    {"id": "silver_current",      "name": "Silver Current",
     "description": "Schools of silver so thick they block the sun.",
     "category": "species", "xp_mult": 1.02, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "silver_river_herring",     "unlock_level": 1},

    # Tier 2
    {"id": "krill_ascendant",     "name": "Krill Ascendant",
     "description": "Even the smallest creature can walk the immortal path.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "spirit_krill",             "unlock_level": 1},
    {"id": "pearl_keeper",        "name": "Pearl Keeper",
     "description": "Behind its gate: a perfect spirit pearl. Behind yours: a title.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "pearl_gate_oyster",        "unlock_level": 1},
    {"id": "storm_cloud",         "name": "Storm Cloud",
     "description": "Blue scales that carry the charge of incoming storms.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "storm_cloud_bluefish",     "unlock_level": 1},
    {"id": "iron_wall",           "name": "Iron Wall",
     "description": "A grouper so dense it creates its own gravity. Caught.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "iron_wall_grouper",        "unlock_level": 1},
    {"id": "jade_claw",           "name": "Jade Claw",
     "description": "Lobster claws of jade-hard chitin. Your rod is stronger.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.01,
     "unlock_type": "fish_species", "unlock_value": "jade_claw_lobster",        "unlock_level": 1},
    {"id": "storm_current",       "name": "Storm Current",
     "description": "Outraces ocean currents. Your cast was faster.",
     "category": "species", "xp_mult": 1.03, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "storm_current_tuna",       "unlock_level": 1},

    # Tier 3
    {"id": "thunder_vein",        "name": "Thunder Vein",
     "description": "Electric veins pulse with heaven's energy.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "thunder_vein_eel",         "unlock_level": 1},
    {"id": "ink_veil",            "name": "Ink Veil",
     "description": "Clouds the water in void-ink. You fished blind and still won.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "ink_veil_squid",           "unlock_level": 1},
    {"id": "sea_ancient",         "name": "Sea Ancient",
     "description": "An immortal sea tortoise older than any known sect.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "immortal_sea_tortoise",    "unlock_level": 1},
    {"id": "tide_specter",        "name": "Tide Specter",
     "description": "Neither fish nor ghost—something between.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "void_tide_specter",        "unlock_level": 1},
    {"id": "poison_tail",         "name": "Poison Tail",
     "description": "One sting and it's over. You didn't get stung.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "poison_tail_ray",          "unlock_level": 1},
    {"id": "eight_arms",          "name": "Eight Arms",
     "description": "Eight limbs wrapped your line. You had one rod and still won.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "eight_arm_void_octopus",   "unlock_level": 1},
    {"id": "sword_emperor",       "name": "Sword Emperor",
     "description": "Its bill is a sword forged by the sea itself.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "sword_emperor_marlin",     "unlock_level": 1},
    {"id": "sea_dragon",          "name": "Sea Dragon",
     "description": "A celestial sea dragon is a rare sight. You now have one.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "celestial_sea_dragon",     "unlock_level": 1},
    {"id": "flame_spine",         "name": "Flame Spine",
     "description": "Its spines stay warm long after death. Handle with care.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "flame_spine_lion_fish",    "unlock_level": 1},
    {"id": "demon_hound",         "name": "Demon Hound",
     "description": "Hunts in packs. One was enough to hunt you back.",
     "category": "species", "xp_mult": 1.04, "qi_mult": 1.02,
     "unlock_type": "fish_species", "unlock_value": "demon_hound_shark",        "unlock_level": 1},

    # Tier 4
    {"id": "frost_fang",          "name": "Frost Fang",
     "description": "Fangs that freeze on contact. You kept all your fingers.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "frost_fang_wolf_fish",     "unlock_level": 1},
    {"id": "hammer_forged",       "name": "Hammer Forged",
     "description": "Forged by ten thousand ocean pressures. Your rod was forged by fate.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "hammer_forged_demon_shark","unlock_level": 1},
    {"id": "sky_glider",          "name": "Sky Glider",
     "description": "Glides above the surface on wing-like fins. Caught mid-glide.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "sky_gliding_manta",        "unlock_level": 1},
    {"id": "heaven_splitter",     "name": "Heaven Splitter",
     "description": "Its bill cleaves the sky when it leaps. Now it cleaves nothing.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "heaven_splitting_swordfish","unlock_level": 1},
    {"id": "blade_spine",         "name": "Blade Spine",
     "description": "500 cm of serrated terror. One cast answered.",
     "category": "species", "xp_mult": 1.06, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "blade_spine_sawfish",      "unlock_level": 1},
    {"id": "radiant_one",         "name": "Radiant One",
     "description": "Its sunfish body radiates warmth like a tiny star.",
     "category": "species", "xp_mult": 1.05, "qi_mult": 1.03,
     "unlock_type": "fish_species", "unlock_value": "radiant_sun_fish",         "unlock_level": 1},

    # Tier 5
    {"id": "leviathan",           "name": "Leviathan",
     "description": "1,500 cm. You needed a longer rod.",
     "category": "species", "xp_mult": 1.08, "qi_mult": 1.05,
     "unlock_type": "fish_species", "unlock_value": "leviathan_whale",          "unlock_level": 1},
    {"id": "heaven_devourer",     "name": "Heaven Devourer",
     "description": "A shark that eats concepts. It tried to eat your patience. Failed.",
     "category": "species", "xp_mult": 1.08, "qi_mult": 1.05,
     "unlock_type": "fish_species", "unlock_value": "heaven_devouring_shark",   "unlock_level": 1},
    {"id": "void_ancient",        "name": "Void Ancient",
     "description": "The Coelacanth that swam when the world was young.",
     "category": "species", "xp_mult": 1.08, "qi_mult": 1.05,
     "unlock_type": "fish_species", "unlock_value": "ancient_void_coelacanth",  "unlock_level": 1},

    # Tier 6 — ultra-rare (L1 + L2)
    {"id": "golden_ray",          "name": "Golden Ray's Witness",
     "description": "The Sovereign Golden Ray graced your waters. You seized the moment.",
     "category": "species", "xp_mult": 1.12, "qi_mult": 1.08,
     "unlock_type": "fish_species", "unlock_value": "sovereign_golden_ray",     "unlock_level": 1},
    {"id": "ray_sovereign",       "name": "Ray Sovereign's Peer",
     "description": "Five Sovereign Golden Rays caught. The deep ocean acknowledges you.",
     "category": "species", "xp_mult": 1.28, "qi_mult": 1.18,
     "unlock_type": "fish_species", "unlock_value": "sovereign_golden_ray",     "unlock_level": 2},

    # ─── ELEMENTAL EVENT FISH (4 fish → 5 titles incl. 1 L2) ────────────

    {"id": "earth_sovereign",     "name": "Earth Sovereign",
     "description": "You caught the Terra Sovereign Koi during the Sovereign Pulse event.",
     "category": "species", "xp_mult": 1.08, "qi_mult": 1.06,
     "unlock_type": "fish_species", "unlock_value": "terra_sovereign_koi",      "unlock_level": 1},
    {"id": "frost_eclipse",       "name": "Frost Eclipse",
     "description": "The Frost Eclipse Serpent emerged when sun met moon. You caught it.",
     "category": "species", "xp_mult": 1.08, "qi_mult": 1.06,
     "unlock_type": "fish_species", "unlock_value": "frost_eclipse_serpent",    "unlock_level": 1},
    {"id": "solar_inferno",       "name": "Solar Inferno",
     "description": "A drake born in celestial fire. Your hands still smoke.",
     "category": "species", "xp_mult": 1.08, "qi_mult": 1.06,
     "unlock_type": "fish_species", "unlock_value": "solar_inferno_drake",      "unlock_level": 1},
    {"id": "tempest_wanderer",    "name": "Tempest Wanderer",
     "description": "You fished from the eye of a fracture and caught its avatar.",
     "category": "species", "xp_mult": 1.12, "qi_mult": 1.08,
     "unlock_type": "fish_species", "unlock_value": "tempest_void_eel",         "unlock_level": 1},
    {"id": "tempest_sovereign",   "name": "Tempest Sovereign",
     "description": "Five Tempest Void Eels. The storm itself fears your cast.",
     "category": "species", "xp_mult": 1.28, "qi_mult": 1.18,
     "unlock_type": "fish_species", "unlock_value": "tempest_void_eel",         "unlock_level": 2},

    # ─── JUNK (8 objects → 9 titles incl. 1 L2) ──────────────────────────

    {"id": "bone_collector",      "name": "Bone Collector",
     "description": "An immortal's shattered bone. Some would kill for this. You merely fished.",
     "category": "species", "xp_mult": 1.01, "qi_mult": 1.00,
     "unlock_type": "fish_species", "unlock_value": "shattered_immortal_bone",  "unlock_level": 1},
    {"id": "humble_wanderer",     "name": "Humble Wanderer",
     "description": "It's not a fish. It's not glory. It's a sect boot. Your sect boot now.",
     "category": "species", "xp_mult": 1.00, "qi_mult": 1.00,
     "unlock_type": "fish_species", "unlock_value": "waterlogged_sect_boot",    "unlock_level": 1},
    {"id": "branch_sage",         "name": "Branch Sage",
     "description": "A spirit branch, still alive after years adrift in the river.",
     "category": "species", "xp_mult": 1.00, "qi_mult": 1.00,
     "unlock_type": "fish_species", "unlock_value": "driftwood_spirit_branch",  "unlock_level": 1},
    {"id": "diamond_dust",        "name": "Diamond Dust",
     "description": "A shard of the original universe, reeled in on a quiet afternoon.",
     "category": "species", "xp_mult": 1.06, "qi_mult": 1.05,
     "unlock_type": "fish_species", "unlock_value": "chaos_diamond_shard",      "unlock_level": 1},
    {"id": "diamond_sovereign",   "name": "Diamond Sovereign",
     "description": "Five Chaos Diamond Shards. Creation itself acknowledges your dao.",
     "category": "species", "xp_mult": 1.20, "qi_mult": 1.15,
     "unlock_type": "fish_species", "unlock_value": "chaos_diamond_shard",      "unlock_level": 2},
    {"id": "ring_bearer",         "name": "Ring Bearer",
     "description": "Ancient bronze rings from a dynasty long forgotten.",
     "category": "species", "xp_mult": 1.00, "qi_mult": 1.00,
     "unlock_type": "fish_species", "unlock_value": "ancient_bronze_rings",     "unlock_level": 1},
    {"id": "pouch_guardian",      "name": "Pouch Guardian",
     "description": "A tattered sect pouch. Whatever was inside is lost. The title is not.",
     "category": "species", "xp_mult": 1.00, "qi_mult": 1.00,
     "unlock_type": "fish_species", "unlock_value": "tattered_sect_pouch",      "unlock_level": 1},
    {"id": "alchemists_bane",     "name": "Alchemist's Bane",
     "description": "Some poor alchemist's pill canister, dropped in the river.",
     "category": "species", "xp_mult": 1.00, "qi_mult": 1.00,
     "unlock_type": "fish_species", "unlock_value": "corroded_pill_canister",   "unlock_level": 1},
    {"id": "algae_cultivator",    "name": "Algae Cultivator",
     "description": "Even void algae can walk the path. Slowly.",
     "category": "species", "xp_mult": 1.00, "qi_mult": 1.00,
     "unlock_type": "fish_species", "unlock_value": "void_algae",               "unlock_level": 1},

    # ─── MISC EVENT FISH (2 → 2 titles) ──────────────────────────────────

    {"id": "void_rift_walker",    "name": "Void Rift Walker",
     "description": "A creature of collapsed void, born in the rift's single minute.",
     "category": "species", "xp_mult": 1.10, "qi_mult": 1.08,
     "unlock_type": "fish_species", "unlock_value": "void_rift_phantom",        "unlock_level": 1},
    {"id": "chaos_born",          "name": "Chaos Born",
     "description": "A primordial wraith of chaos energy—bound by bait and rod.",
     "category": "species", "xp_mult": 1.12, "qi_mult": 1.10,
     "unlock_type": "fish_species", "unlock_value": "primordial_chaos_wraith",  "unlock_level": 1},
]

# ──────────────────────────────────────────────────────────────────────────────
# COMBINED & LOOKUP TABLES
# ──────────────────────────────────────────────────────────────────────────────

ALL_TITLES: list[dict] = GENERAL_TITLES + SPECIES_TITLES

TITLE_BY_ID: dict[str, dict] = {t["id"]: t for t in ALL_TITLES}

# Species lookup: species_id → {unlock_level → title}
SPECIES_TITLE_MAP: dict[str, dict[int, dict]] = {}
for _t in SPECIES_TITLES:
    _sid: str = _t["unlock_value"]
    _lvl: int = _t["unlock_level"]
    SPECIES_TITLE_MAP.setdefault(_sid, {})[_lvl] = _t


def get_title(title_id: str) -> dict | None:
    return TITLE_BY_ID.get(title_id)


def get_species_title(species_id: str, level: int = 1) -> dict | None:
    """Return the title dict for (species_id, level) or None."""
    return SPECIES_TITLE_MAP.get(species_id, {}).get(level)


def titles_for_species(species_id: str) -> list[dict]:
    """Return all title dicts (L1 and optionally L2) for a species."""
    return list(SPECIES_TITLE_MAP.get(species_id, {}).values())


def general_titles_by_type(unlock_type: str) -> list[dict]:
    """Return all general titles of a given unlock_type."""
    return [t for t in GENERAL_TITLES if t["unlock_type"] == unlock_type]
