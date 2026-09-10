"""
Hero knowledge base — captain and joiner recommendations by generation and role.
Derived from heros-data.md and the hero selection matrix.
"""
from __future__ import annotations
from typing import List, Tuple

# ──────────────────────────────────────────────────────────────────────
# Generation thresholds (furnace/FC level of the SERVER, not the player)
# Gen 1 ≈ F1–F20, Gen 2 ≈ F20–F25, Gen 3 ≈ F25–F28,
# Gen 4 ≈ F28–F30, Gen 5 ≈ FC1–FC3, Gen 6 ≈ FC4–FC6, Gen 7 ≈ FC7+
# ──────────────────────────────────────────────────────────────────────

# Universal epic joiners — always relevant regardless of generation
UNIVERSAL_JOINERS = ["Jessie", "Jasser", "Seo-yoon"]
GARRISON_UNIVERSAL_JOINERS = ["Sergey", "Patrick", "Ahmose"]

HERO_BUFF_DESCRIPTIONS: dict[str, str] = {
    "jessie": "+25% Damage Dealt (Offensive Rally Joiner)",
    "jasser": "+25% Attack (Offensive Rally Joiner)",
    "seo-yoon": "+25% Attack / Damage (Offensive Rally Joiner)",
    "sergey": "-20% Damage Taken (Garrison Defense Joiner)",
    "patrick": "+25% Max HP (Garrison Defense Joiner)",
    "ahmose": "-15% Damage Taken & Shield (Defensive Joiner)",
    "jeronimo": "+25% Attack & Rally Damage Boost",
    "molly": "+15% Stun Chance & Flank Attack",
    "flint": "+20% Defense & Shield Frontline",
    "alonso": "+20% Marksman Crit & Snipe",
    "mia": "+25% Single-Target DPS & Skill Boost",
    "philly": "+20% Garrison Defense & Health",
    "lynn": "+20% Marksman Precision & Lethality",
    "norah": "+25% Lancer Combined Arms Buff",
    "wayne": "+20% Marksman Armor Penetration",
    "wu ming": "+25% Infantry Frontline Resistance",
    "gatot": "+20% Counter-Attack & Defense",
    "hendrik": "+20% Spear Charge & Attack",
    "xura": "+25% Marksman Penetration DPS",
    "edith": "+20% Garrison Stun & Counter Damage",
}

# (min_gen, captain_infantry, captain_lancer, captain_marksman, 4th_joiner_offense, 4th_joiner_garrison)
_HERO_TABLE: List[Tuple[int, str, str, str, str, str]] = [
    # gen, inf_cap, lan_cap, mrk_cap, 4th_off_joiner, 4th_def_joiner
    (1, "Jeronimo", "Molly",   "Bahiti",  "Jeronimo",  "Flint"),
    (2, "Flint",    "Molly",   "Alonso",  "Jeronimo",  "Flint"),
    (3, "Flint",    "Mia",     "Alonso",  "Mia",       "Philly"),
    (4, "Ahmose",   "Mia",     "Lynn",    "Mia",       "Ahmose"),
    (5, "Hector",   "Norah",   "Lynn",    "Mia",       "Ahmose"),
    (6, "Wu Ming",  "Norah",   "Wayne",   "Mia",       "Edith"),
    (7, "Gatot",    "Hendrik", "Xura",    "Mia",       "Edith"),
]

# Role-specific ratio presets (infantry%, lancer%, marksman%)
ROLE_RATIOS = {
    "main_strike":       {"infantry": 50, "lancer": 20, "marksman": 30},
    "garrison_defense":  {"infantry": 60, "lancer": 20, "marksman": 20},
    "suicide_breaker":   {"infantry": 40, "lancer": 10, "marksman": 50},
}

# Norah special ratio — if Norah is lancer captain, use combined arms
NORAH_RATIO = {"infantry": 50, "lancer": 20, "marksman": 30}


def get_hero_recommendations(generation: int, role: str) -> dict:
    """Return captain and joiner recommendations for a generation and role.

    Args:
        generation: Server generation (1–7+)
        role: 'main_strike', 'garrison_defense', or 'suicide_breaker'

    Returns:
        dict with 'captain_inf', 'captain_lan', 'captain_mrk',
                  'joiners', 'ratio'
    """
    gen = max(1, min(generation, 7))

    # Walk down the table to find the highest matching entry
    row = _HERO_TABLE[0]
    for entry in _HERO_TABLE:
        if entry[0] <= gen:
            row = entry

    _, inf_cap, lan_cap, mrk_cap, joiner_4th_off, joiner_4th_def = row

    is_garrison = role == "garrison_defense"

    if is_garrison:
        captain_inf = inf_cap if gen >= 4 else "Flint"
        captain_lan = "Philly" if gen <= 4 else lan_cap
        captain_mrk = "Edith" if gen >= 6 else ("Lynn" if gen >= 4 else "Alonso")
        joiners = GARRISON_UNIVERSAL_JOINERS[:3] + [joiner_4th_def]
    else:
        captain_inf = inf_cap
        captain_lan = lan_cap
        captain_mrk = mrk_cap
        joiners = UNIVERSAL_JOINERS + [joiner_4th_off]

    # Primary captain displayed in output (infantry is usually flag)
    primary_captain = captain_inf

    # Adjust ratio if Norah is lancer lead
    ratio = dict(ROLE_RATIOS.get(role, ROLE_RATIOS["main_strike"]))
    if lan_cap == "Norah" and not is_garrison:
        ratio = dict(NORAH_RATIO)

    return {
        "captain_inf": captain_inf,
        "captain_lan": captain_lan,
        "captain_mrk": captain_mrk,
        "primary_captain": primary_captain,
        "joiners": joiners,
        "ratio": ratio,
    }
