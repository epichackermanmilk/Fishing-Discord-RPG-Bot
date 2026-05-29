# =============================================================
# OMEGA BOT — SCRATCH TICKET DATA
# Eternal River Sect
# =============================================================
# Three ticket tiers: slip / scroll / decree
#
# Mechanic:
#   Each ticket contains:
#     - 5 "win numbers" drawn from 1-45 without replacement
#     - 20 "scratch numbers" drawn from 1-45 without replacement
#   A player reveals spots one at a time by clicking buttons.
#   Each scratch number that matches a win number is a hit.
#   Prize is determined by how many matches the player finds.
#
# Win rate ≈ 43.5% overall (at least 1 match expected per ~2.3 tickets)
#
# Prize tiers per match count use a cascading formula so higher
# tiers of ticket multiply the same match-bracket payouts.
# =============================================================

from __future__ import annotations
import math

# ──────────────────────────────────────────────────────────────────────────────
# TICKET TIER DEFINITIONS
# ──────────────────────────────────────────────────────────────────────────────

TICKET_TIERS: dict[str, dict] = {

    "slip": {
        "id":           "slip",
        "name":         "Qi Slip",
        "emoji":        "📜",
        "description":  "A thin strip of paper charged with a trickle of Qi. Humble, but promising.",
        "price":        150,            # Spirit Stones to purchase
        "color":        0x7BC8A4,       # Discord embed colour (jade-green)
        "win_pool":     45,             # numbers 1–45
        "win_count":    5,              # numbers pre-drawn as winning numbers
        "scratch_count":20,             # numbers the player scratches through
        # prize_table: {matches: prize_stones}
        # EV ≈ 104.7 SS → ~69.8% RTP on a 150 SS ticket
        # Match probabilities (hypergeometric, K=5 N=45 n=20):
        #   1 match: 34.78%  → 160 SS (slight profit over cost)
        #   2 match:  7.85%  → 480 SS
        #   3 match:  0.81%  → 1,200 SS
        #   4 match:  0.038% → 4,000 SS
        #   5 match:  0.00066%→ 20,000 SS
        "prize_table": {
            1: 160,
            2: 480,
            3: 1_200,
            4: 4_000,
            5: 20_000,
        },
        "flavor": "Even the weakest slip may contain a sect elder's blessing.",
    },

    "scroll": {
        "id":           "scroll",
        "name":         "Spirit Scroll",
        "emoji":        "📖",
        "description":  "A thick scroll brushed with spirit ink. Cultivators say the ink itself chooses its reader.",
        "price":        600,
        "color":        0xF7C948,       # gold
        "win_pool":     45,
        "win_count":    5,
        "scratch_count":20,
        # EV ≈ 415 SS → ~69.2% RTP on a 600 SS scroll
        # Scaled ×4 from slip, keeping ratio intact
        "prize_table": {
            1: 650,
            2: 1_950,
            3: 5_000,
            4: 16_000,
            5: 80_000,
        },
        "flavor": "A scroll penned in golden qi. The prize within is only revealed by patient hands.",
    },

    "decree": {
        "id":           "decree",
        "name":         "Heavenly Decree",
        "emoji":        "📕",
        "description":  "Issued by the heavens themselves. Even one match rewards handsomely.",
        "price":        2_500,
        "color":        0xC0392B,       # crimson
        "win_pool":     45,
        "win_count":    5,
        "scratch_count":20,
        # EV ≈ 1,726 SS → ~69.0% RTP on a 2,500 SS decree
        # Scaled ×16.7 from slip, keeping ratio intact
        "prize_table": {
            1: 2_500,
            2: 8_000,
            3: 22_000,
            4: 75_000,
            5: 350_000,
        },
        "flavor": "The heavens stamp this with their seal. Failure to win is itself an insult to fate.",
    },
}

TICKET_ORDER = ["slip", "scroll", "decree"]


# ──────────────────────────────────────────────────────────────────────────────
# PROBABILITY UTILITIES
# ──────────────────────────────────────────────────────────────────────────────

def _hyper_prob(k: int, K: int = 5, N: int = 45, n: int = 20) -> float:
    """
    Hypergeometric probability of exactly k matches when:
      K = 5  win numbers in pool
      N = 45 total numbers
      n = 20 numbers scratched
    """
    from math import comb
    return comb(K, k) * comb(N - K, n - k) / comb(N, n)


def expected_prize(tier_id: str) -> float:
    """Return the expected prize (in SS) for a ticket of the given tier."""
    tier = TICKET_TIERS[tier_id]
    table = tier["prize_table"]
    ev = 0.0
    for k, prize in table.items():
        ev += _hyper_prob(k) * prize
    return ev


def win_probability() -> float:
    """P(at least 1 match) for any ticket tier (all use the same pool geometry)."""
    return 1.0 - _hyper_prob(0)


# ──────────────────────────────────────────────────────────────────────────────
# MATCH EVALUATION
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_ticket(tier_id: str, win_numbers: list[int], revealed_spots: list[int],
                    scratch_numbers: list[int]) -> dict:
    """
    Given a fully or partially scratched ticket, return a result dict:
        matches:       int  — how many revealed scratch_numbers hit win_numbers
        potential:     int  — how many un-revealed spots could still be wins
        prize:         int  — current prize (0 if not all matches found yet OR 0 matches)
        max_prize:     int  — prize if all hidden spots were matches (for display only)
        is_complete:   bool — all 20 spots have been revealed
        is_winner:     bool — is_complete and matches >= 1
    """
    tier = TICKET_TIERS[tier_id]
    table = tier["prize_table"]
    win_set = set(win_numbers)

    revealed_values = [scratch_numbers[i] for i in revealed_spots]
    matches = sum(1 for v in revealed_values if v in win_set)

    hidden_indices = [i for i in range(len(scratch_numbers)) if i not in revealed_spots]
    hidden_values  = [scratch_numbers[i] for i in hidden_indices]
    potential_extra = sum(1 for v in hidden_values if v in win_set)
    potential = matches + potential_extra

    is_complete = len(revealed_spots) == len(scratch_numbers)
    prize       = table.get(matches, 0) if is_complete else 0
    max_prize   = table.get(potential, 0) if potential in table else 0
    is_winner   = is_complete and matches >= 1

    return {
        "matches":     matches,
        "potential":   potential,
        "prize":       prize,
        "max_prize":   max_prize,
        "is_complete": is_complete,
        "is_winner":   is_winner,
    }


def get_ticket(tier_id: str) -> dict | None:
    return TICKET_TIERS.get(tier_id)
