-- =============================================================
-- OMEGA BOT — DATABASE SCHEMA
-- Eternal River Sect
-- =============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- -------------------------------------------------------------
-- USERS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    discord_id      INTEGER PRIMARY KEY,
    username        TEXT    NOT NULL,
    spirit_stones   INTEGER NOT NULL DEFAULT 0,
    fishing_xp      INTEGER NOT NULL DEFAULT 0,
    fishing_level   INTEGER NOT NULL DEFAULT 1,
    qi              INTEGER NOT NULL DEFAULT 0,
    realm           INTEGER NOT NULL DEFAULT 0,   -- 0=Mortal, 1-9=major realms
    stage           INTEGER NOT NULL DEFAULT 0,   -- 0-8 within realm (stage 1-9)
    active_title_id TEXT    DEFAULT NULL,
    rod_id          TEXT    NOT NULL DEFAULT 'mortal_reed',
    bait_id         TEXT    NOT NULL DEFAULT 'spirit_worm',
    lure_id         TEXT    NOT NULL DEFAULT 'mortal_hook',
    last_reel       REAL    NOT NULL DEFAULT 0,
    last_adventure  REAL    NOT NULL DEFAULT 0,
    total_fish_caught       INTEGER NOT NULL DEFAULT 0,
    total_spirit_stones_earned INTEGER NOT NULL DEFAULT 0,
    total_adventures        INTEGER NOT NULL DEFAULT 0,
    joined_at       REAL    NOT NULL DEFAULT (unixepoch())
);

-- -------------------------------------------------------------
-- ROD UPGRADE TIERS (per user)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rod_upgrades (
    user_id         INTEGER PRIMARY KEY,
    reel_speed_tier INTEGER NOT NULL DEFAULT 0,   -- 0-5 (reduces cooldown)
    xp_bonus_tier   INTEGER NOT NULL DEFAULT 0,   -- 0-9 (increases fishing XP)
    rod_luck_tier   INTEGER NOT NULL DEFAULT 0,   -- 0-5 (Spirit Pouch quality)
    max_bait_tier   INTEGER NOT NULL DEFAULT 0,   -- 0-9 (bait carry limit)
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- BAIT LICENSES (unlocks bait type in shop)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bait_licenses (
    user_id     INTEGER NOT NULL,
    bait_id     TEXT    NOT NULL,
    purchased_at REAL   NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, bait_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- BAIT STOCK (how much of each bait a user has)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bait_stock (
    user_id     INTEGER NOT NULL,
    bait_id     TEXT    NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, bait_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- LURES OWNED
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lures_owned (
    user_id     INTEGER NOT NULL,
    lure_id     TEXT    NOT NULL,
    purchased_at REAL   NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, lure_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- RODS OWNED
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rods_owned (
    user_id     INTEGER NOT NULL,
    rod_id      TEXT    NOT NULL,
    purchased_at REAL   NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, rod_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- FISH INVENTORY
-- Each row = one caught fish instance
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fish_inventory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    species_id  TEXT    NOT NULL,
    quality     TEXT    NOT NULL,   -- dust/bronze/jade/gold/astral/immortal
    size        REAL    NOT NULL,   -- cm
    value       INTEGER NOT NULL,   -- sell price in Spirit Stones
    caught_at   REAL    NOT NULL DEFAULT (unixepoch()),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- Index for fast per-user fish lookups
CREATE INDEX IF NOT EXISTS idx_fish_inventory_user ON fish_inventory(user_id);

-- -------------------------------------------------------------
-- BREAKTHROUGH TRACKER (per realm, per user)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cultivation_tracker (
    user_id         INTEGER NOT NULL,
    realm           INTEGER NOT NULL,   -- 1-9
    failure_count   INTEGER NOT NULL DEFAULT 0,
    current_pill_cost INTEGER NOT NULL, -- starts at base, doubles per failure
    PRIMARY KEY (user_id, realm),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- FISH CODEX (per user, per species)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS codex (
    user_id         INTEGER NOT NULL,
    species_id      TEXT    NOT NULL,
    caught_count    INTEGER NOT NULL DEFAULT 0,
    best_quality    TEXT    DEFAULT NULL,
    largest_size    REAL    DEFAULT NULL,
    smallest_size   REAL    DEFAULT NULL,
    largest_value   INTEGER DEFAULT NULL,
    smallest_value  INTEGER DEFAULT NULL,
    first_caught_at REAL    DEFAULT NULL,
    PRIMARY KEY (user_id, species_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- QUESTS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quests (
    user_id         INTEGER NOT NULL,
    quest_id        TEXT    NOT NULL,
    current_progress INTEGER NOT NULL DEFAULT 0,
    level_reached   INTEGER NOT NULL DEFAULT 0,   -- highest quest level completed
    last_updated    REAL    NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, quest_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- TITLES EARNED
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_titles (
    user_id     INTEGER NOT NULL,
    title_id    TEXT    NOT NULL,
    earned_at   REAL    NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, title_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- SCRATCH-OFF TICKETS (stored pending open)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scratch_tickets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    tier            TEXT    NOT NULL,   -- slip / scroll / decree
    win_numbers     TEXT    NOT NULL,   -- JSON: [7, 14, 23, 31, 45]
    scratch_numbers TEXT    NOT NULL,   -- JSON: [n0..n19]
    revealed_spots  TEXT    NOT NULL DEFAULT '[]',  -- JSON: [index, ...]
    opened          INTEGER NOT NULL DEFAULT 0,     -- 0=unopened, 1=opened
    prize_amount    INTEGER NOT NULL DEFAULT 0,
    created_at      REAL    NOT NULL DEFAULT (unixepoch()),
    opened_at       REAL    DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scratch_user ON scratch_tickets(user_id, opened);

-- -------------------------------------------------------------
-- BREAKTHROUGH PILLS IN INVENTORY
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pill_inventory (
    user_id     INTEGER NOT NULL,
    realm       INTEGER NOT NULL,   -- which realm this pill is for (1-9)
    quantity    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, realm),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- ACTIVE ELEMENTAL / MISC EVENTS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS active_events (
    fish_id     TEXT    PRIMARY KEY,  -- species_id of the event fish
    start_time  REAL    NOT NULL,
    end_time    REAL    NOT NULL,
    announced   INTEGER NOT NULL DEFAULT 0
);

-- -------------------------------------------------------------
-- EVENT COOLDOWNS (when was the last event for each fish)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_cooldowns (
    fish_id         TEXT    PRIMARY KEY,
    last_event_end  REAL    NOT NULL DEFAULT 0
);

-- -------------------------------------------------------------
-- CHANNEL CONFIG
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS channel_config (
    channel_id      INTEGER PRIMARY KEY,
    channel_type    TEXT    NOT NULL,
    -- Types: fishing | shop | announce | mod_log | mod_review |
    --        welcome | rules | server_guide | commands_guide |
    --        role_selection | general | breakthrough_hall
    biome_id        TEXT    DEFAULT NULL,   -- freshwater1/2/3, saltwater1/2/3, special1/2/3, secret
    unlock_condition TEXT   DEFAULT NULL,   -- for locked channels
    guild_id        INTEGER NOT NULL
);

-- -------------------------------------------------------------
-- CHANNEL UNLOCKS (per user, for locked fishing channels)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS channel_unlocks (
    user_id     INTEGER NOT NULL,
    channel_id  INTEGER NOT NULL,
    unlocked_at REAL    NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, channel_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- USER BIOMES FISHED (tracks which default biomes a user has cast in)
-- Used for Phantom Lotus Grotto unlock condition
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_biomes_fished (
    user_id     INTEGER NOT NULL,
    biome_id    TEXT    NOT NULL,
    first_fished_at REAL NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, biome_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- USER BIOME UNLOCKS (tracks which locked biomes a user has earned)
-- Stored by biome_id so it survives /omega_setup channel recreation
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_biome_unlocks (
    user_id     INTEGER NOT NULL,
    biome_id    TEXT    NOT NULL,   -- special1/special2/special3/secret
    unlocked_at REAL    NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (user_id, biome_id),
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- BANNED WORDS (auto-mod)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS banned_words (
    word        TEXT    PRIMARY KEY,
    added_by    INTEGER NOT NULL,
    added_at    REAL    NOT NULL DEFAULT (unixepoch())
);

-- -------------------------------------------------------------
-- MODERATION ACTIONS LOG
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mod_actions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT    NOT NULL,   -- mute/kick/ban/unmute/warn
    target_id   INTEGER NOT NULL,
    target_name TEXT    NOT NULL,
    moderator_id    INTEGER NOT NULL,
    moderator_name  TEXT    NOT NULL,
    reason      TEXT    DEFAULT NULL,
    duration_seconds INTEGER DEFAULT NULL,
    created_at  REAL    NOT NULL DEFAULT (unixepoch())
);

-- -------------------------------------------------------------
-- ACTIVE MUTES (for auto-unmute on bot restart)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS active_mutes (
    user_id     INTEGER PRIMARY KEY,
    guild_id    INTEGER NOT NULL,
    expires_at  REAL    NOT NULL   -- unixepoch; NULL = permanent
);

-- -------------------------------------------------------------
-- SERVER RECORDS (all-time bests)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS server_records (
    record_type TEXT    PRIMARY KEY,
    -- largest_fish | smallest_fish | most_valuable_fish
    -- highest_realm | most_fish_caught | most_spirit_stones
    species_id  TEXT    DEFAULT NULL,
    value       REAL    DEFAULT NULL,
    user_id     INTEGER DEFAULT NULL,
    username    TEXT    DEFAULT NULL,
    extra_data  TEXT    DEFAULT NULL,  -- JSON for quality, size, etc.
    set_at      REAL    DEFAULT NULL
);

-- Pre-populate record slots
INSERT OR IGNORE INTO server_records (record_type) VALUES
    ('largest_fish'),
    ('smallest_fish'),
    ('most_valuable_fish'),
    ('highest_realm'),
    ('most_fish_caught'),
    ('most_spirit_stones_earned');

-- -------------------------------------------------------------
-- LEADERBOARD CACHE (refreshed periodically)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS leaderboard_cache (
    category    TEXT    NOT NULL,   -- spirit_stones / fishing_level / realm / fish_caught
    rank        INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    username    TEXT    NOT NULL,
    value       INTEGER NOT NULL,
    updated_at  REAL    NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY (category, rank)
);
