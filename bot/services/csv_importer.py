from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from bot.database.models.player import Player, TroopType
from bot.database.repositories.player_repository import PlayerRepository


@dataclass
class ImportResult:
    total_rows: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
        }


def _normalize_header(header: str) -> str:
    """Lowercase, strip quotes, replace underscores/hyphens with spaces, collapse spaces."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", header.lower().strip())
    return " ".join(cleaned.split())


def parse_number(val: Any) -> Optional[int]:
    """Parse integers supporting suffixes (k, m) and separators (comma, dot)."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s == "-":
        return None

    # Check for k/m suffix
    multiplier = 1
    if s.lower().endswith("k"):
        multiplier = 1_000
        s = s[:-1].strip()
    elif s.lower().endswith("m"):
        multiplier = 1_000_000
        s = s[:-1].strip()

    # Handle European vs US separators
    if "," in s and "." in s:
        # Check which comes last
        if s.rfind(".") > s.rfind(","):
            # 1,250.50
            s = s.replace(",", "")
        else:
            # 1.250,50
            s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # e.g. 165,000
        s = s.replace(",", "")
    elif "." in s:
        # If dot is followed by exactly 3 digits and no other dot, likely thousands separator: 165.000
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) == 3 and multiplier == 1:
            s = "".join(parts)

    try:
        float_val = float(s)
        return int(round(float_val * multiplier))
    except ValueError:
        return None


def parse_level(val: Any) -> Optional[int]:
    """Extract numeric FC / troop level from strings like 'FC 5', 'fc3', 'Level 8', 'T10', '5'."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s == "-":
        return None

    match = re.search(r"(?:fc|level|lvl|tier|t)?\s*(\d+)", s, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def parse_helios(val: Any) -> tuple[bool, Optional[int]]:
    """Parse Helios value.
    Returns (has_helios: bool, explicit_quantity: Optional[int]).
    Supports both boolean ('Yes'/'No') and direct quantities ('150k', '150,000').
    """
    if val is None:
        return False, None
    s = str(val).strip().lower()
    if not s or s in ("no", "n", "false", "0", "-", "none", "non", "nein"):
        return False, None

    if s in ("yes", "y", "true", "oui", "ja", "si", "x", "v", "1"):
        return True, None

    # Check if a number was entered directly
    qty = parse_number(val)
    if qty is not None:
        if qty > 0:
            return True, qty
        return False, None

    return False, None


def parse_hero_spec(val: Any) -> Optional[tuple[int, int]]:
    """Parse hero star (1-5) and skill 1 level (1-5).
    Returns (stars, skill_level) or None if absent/not owned.
    """
    if val is None:
        return None
    s = str(val).strip().lower()
    if not s or s in ("no", "n", "false", "0", "-", "none", "na", "n/a"):
        return None
    if s in ("yes", "y", "true", "oui", "1"):
        return 5, 5

    # Patterns like "4* 5s", "4* 5skill", "4/5", "4-5", "4 5"
    m = re.search(r"(\d)\s*(?:\*|★|star|stars)?\s*(?:/|-|\s|,)?\s*(?:skill|s|lvl)?\s*(\d)", s)
    if m:
        stars = max(1, min(5, int(m.group(1))))
        skill = max(1, min(5, int(m.group(2))))
        return stars, skill

    # Single digit like "4*", "4 stars", "4★", "4"
    m_single = re.search(r"(\d)", s)
    if m_single:
        stars = max(1, min(5, int(m_single.group(1))))
        return stars, 5

    return None


# Alias dictionaries for header matching
HEADER_SYNONYMS: dict[str, set[str]] = {
    "name": {
        "name", "player name", "ign", "in game name", "ingamename",
        "player", "username", "governor name", "governor", "lord",
        "lord name", "nick", "nickname",
    },
    "game_player_id": {
        "game id", "player id", "governor id", "lord id", "id",
        "account id", "gameplayerid", "gameid", "in game id",
        "ingame id", "game user id",
    },
    "march_limit": {
        "march limit", "march capacity", "march size", "capacity",
        "troop capacity", "march", "squad limit", "squad capacity",
        "squad size", "marchlimit", "max march",
    },
    "discord_user_id": {
        "discord id", "discord", "discord tag", "discord username",
        "discord user id", "discord name", "user id", "discordid",
    },
    "infantry_level": {
        "infantry fc", "inf fc", "infantry level", "infantry tier",
        "inf tier", "inf lvl", "infantry fire crystal", "infantry",
        "inf", "infantry fc level", "infantrylevel", "inf level",
    },
    "infantry_helios": {
        "infantry helios", "inf helios", "t11 infantry", "helios inf",
        "infantry t11", "t11 inf", "infantry helios troops",
        "infantry t11 count", "inf t11", "infantry t11?", "inf helios?",
    },
    "infantry_helios_qty": {
        "infantry helios quantity", "inf helios quantity", "infantry helios qty",
        "inf helios qty", "infantry t11 quantity", "infantry t11 qty",
        "infantry helios count", "inf helios count",
    },
    "lancers_level": {
        "lancers fc", "lancer fc", "cav fc", "cavalry fc",
        "lancer level", "lancers level", "lancer tier", "lancers tier",
        "lancers", "lancer", "cav", "cavalry", "lancers fc level",
        "lancer fc level", "cav level", "cav tier",
    },
    "lancers_helios": {
        "lancers helios", "lancer helios", "t11 lancers", "t11 lancer",
        "t11 cavalry", "helios cav", "lancers t11", "lancer t11",
        "cav helios", "cavalry helios", "t11 cav", "lancer t11 count",
    },
    "lancers_helios_qty": {
        "lancers helios quantity", "lancer helios quantity", "lancers helios qty",
        "lancer helios qty", "t11 lancers quantity", "t11 lancers qty",
        "cav helios quantity", "cav helios qty", "lancers helios count",
    },
    "marksman_level": {
        "marksman fc", "marksmen fc", "archer fc", "archers fc",
        "bow fc", "marksman level", "marksmen level", "mm fc",
        "marksman", "marksmen", "archer", "archers", "marksman fc level",
        "mm level", "archer level", "marksman tier",
    },
    "marksman_helios": {
        "marksman helios", "marksmen helios", "t11 marksman", "t11 marksmen",
        "helios mm", "archer helios", "archers helios", "marksman t11",
        "marksmen t11", "t11 archer", "mm helios", "marksman t11 count",
    },
    "marksman_helios_qty": {
        "marksman helios quantity", "marksmen helios quantity",
        "marksman helios qty", "marksmen helios qty", "t11 marksman quantity",
        "t11 marksman qty", "archer helios quantity", "archer helios qty",
        "marksman helios count",
    },
    # Key Joiner Heroes (King Shield Guide)
    "hero_jessie": {"jessie", "jessie stars", "jessie skill", "jessie level"},
    "hero_patrick": {"patrick", "patrick stars", "patrick skill", "patrick level"},
    "hero_jasser": {"jasser", "jasser stars", "jasser skill"},
    "hero_seoyoon": {"seoyoon", "seo yoon", "seoyon", "seoyoon stars"},
    "hero_sergey": {"sergey", "sergei", "sergey stars"},
    "hero_ling_xue": {"ling xue", "lingxue", "ling", "ling xue stars"},
    "hero_ahmose": {"ahmose", "ahmose stars", "ahmose skill", "ahmose level"},
    "hero_norah": {"norah", "nora", "norah stars", "norah skill"},
    "hero_edith": {"edith", "edith stars", "edith skill"},
    "hero_hendrik": {"hendrik", "hendrick", "hendrik stars"},
    "hero_blanchette": {"blanchette", "blanchet", "blanchette stars"},
    "hero_alonso": {"alonso", "alonso stars"},
    "hero_renee": {"renee", "rene", "renee stars"},
    "hero_philly": {"philly", "phily", "philly stars"},
    "hero_gatot": {"gatot", "gatot stars"},
    "hero_wu_ming": {"wu ming", "wuming", "wu ming stars"},
    "hero_hector": {"hector", "hector stars"},
    "hero_gregory": {"gregory", "greg", "gregory stars"},
    "hero_eleonora": {"eleonora", "eleonore", "eleonora stars"},
    "hero_hervor": {"hervor", "hervor stars"},
}


class CsvImporter:
    """Parses arbitrary CSV/TSV data and bulk upserts players."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = PlayerRepository(session)

    @staticmethod
    def detect_delimiter(text: str) -> str:
        """Detect whether text is comma, tab, or semicolon separated."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ","
        first_line = lines[0]
        counts = {
            ",": first_line.count(","),
            ";": first_line.count(";"),
            "\t": first_line.count("\t"),
            "|": first_line.count("|"),
        }
        best = max(counts, key=counts.get)  # type: ignore
        return best if counts[best] > 0 else ","

    @staticmethod
    def map_columns(header_row: list[str]) -> dict[str, int]:
        """Map canonical field names to column indexes."""
        column_map: dict[str, int] = {}
        for idx, col in enumerate(header_row):
            norm = _normalize_header(col)
            for canon_key, synonyms in HEADER_SYNONYMS.items():
                if canon_key not in column_map and norm in synonyms:
                    column_map[canon_key] = idx
                    break
        return column_map

    def import_text(self, text: str) -> ImportResult:
        result = ImportResult()

        # Remove BOM if present
        if text.startswith("\ufeff"):
            text = text[1:]

        delimiter = self.detect_delimiter(text)
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)

        rows = list(reader)
        if not rows:
            result.errors.append("File is empty.")
            return result

        header_row = rows[0]
        col_map = self.map_columns(header_row)

        if "name" not in col_map:
            result.errors.append(
                "Missing required 'Name' or 'Player Name' / 'IGN' column."
            )
            return result
        if "march_limit" not in col_map:
            result.errors.append(
                "Missing required 'March Limit' or 'March Capacity' column."
            )
            return result

        data_rows = rows[1:]
        result.total_rows = len(data_rows)

        for line_num, row in enumerate(data_rows, start=2):
            if not row or not any(cell.strip() for cell in row):
                result.total_rows -= 1
                continue

            def get_val(key: str) -> str:
                idx = col_map.get(key)
                if idx is not None and idx < len(row):
                    return row[idx].strip()
                return ""

            name = get_val("name")
            if not name:
                result.skipped += 1
                result.errors.append(f"Row {line_num}: Player name is empty.")
                continue

            raw_march = get_val("march_limit")
            march_limit = parse_number(raw_march)
            if not march_limit or march_limit <= 0:
                result.skipped += 1
                result.errors.append(
                    f"Row {line_num} ({name}): Invalid march limit '{raw_march}'."
                )
                continue

            game_id = get_val("game_player_id")
            if not game_id:
                # If no game_player_id, fallback to sanitized name or discord_id
                discord_id_candidate = get_val("discord_user_id")
                game_id = discord_id_candidate or re.sub(r"\s+", "_", name.lower())

            discord_id = get_val("discord_user_id")
            if not discord_id:
                discord_id = f"manual_{game_id}"

            # Parse troops data
            troop_configs: dict[TroopType, dict[str, Any]] = {}
            troop_types_keys = [
                (TroopType.INFANTRY, "infantry"),
                (TroopType.LANCERS, "lancers"),
                (TroopType.MARKSMAN, "marksman"),
            ]

            for t_type, prefix in troop_types_keys:
                level_val = get_val(f"{prefix}_level")
                level = parse_level(level_val) if level_val else 1
                if level is None or level <= 0:
                    level = 1

                helios_val = get_val(f"{prefix}_helios")
                helios_qty_val = get_val(f"{prefix}_helios_qty")

                has_helios, explicit_qty = parse_helios(helios_val)
                if helios_qty_val:
                    parsed_sep_qty = parse_number(helios_qty_val)
                    if parsed_sep_qty is not None:
                        has_helios = has_helios or (parsed_sep_qty > 0)
                        explicit_qty = parsed_sep_qty

                # If helios is True but no quantity given, default to march limit
                if has_helios and explicit_qty is None:
                    explicit_qty = march_limit

                troop_configs[t_type] = {
                    "helios": has_helios,
                    "level": level,
                    "helios_quantity": explicit_qty if has_helios else None,
                }

            # Parse heroes data
            heroes_data: dict[str, dict] = {}
            for col_key in col_map:
                if col_key.startswith("hero_"):
                    hero_canonical_name = col_key[5:]
                    raw_hero_val = get_val(col_key)
                    parsed_hero = parse_hero_spec(raw_hero_val)
                    if parsed_hero:
                        stars, skill_level = parsed_hero
                        heroes_data[hero_canonical_name] = {
                            "stars": stars,
                            "skill_level": skill_level,
                        }

            # Upsert into database
            try:
                # 1. Match by game_player_id
                player = self.repo.get_by_game_player_id(game_id)
                # 2. If not found and discord_id is standard, check discord_user_id
                if player is None and not discord_id.startswith("manual_"):
                    player = self.repo.get_by_discord_id(discord_id)

                if player is not None:
                    # Update player
                    self.repo.update_player_fields(
                        player,
                        game_player_id=game_id,
                        name=name,
                        march_limit=march_limit,
                    )
                    for t_type, t_data in troop_configs.items():
                        self.repo.update_troop_profile(
                            player,
                            t_type,
                            helios=t_data["helios"],
                            level=t_data["level"],
                            helios_quantity=t_data["helios_quantity"],
                        )
                    for h_name, h_info in heroes_data.items():
                        self.repo.upsert_hero(
                            player,
                            h_name,
                            stars=h_info["stars"],
                            skill_level=h_info["skill_level"],
                        )
                    result.updated += 1
                else:
                    # Create new player
                    # Check if discord_id already exists to prevent duplicate key constraint
                    existing_by_discord = self.repo.get_by_discord_id(discord_id)
                    if existing_by_discord:
                        discord_id = f"{discord_id}_{int(line_num)}"

                    self.repo.create_player(
                        discord_user_id=discord_id,
                        game_player_id=game_id,
                        name=name,
                        march_limit=march_limit,
                        troop_data=troop_configs,
                        heroes_data=heroes_data,
                    )
                    result.created += 1

            except Exception as exc:
                result.skipped += 1
                result.errors.append(f"Row {line_num} ({name}): {str(exc)}")

        self.session.flush()
        return result
