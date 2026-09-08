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


def decode_text_bytes(data: bytes) -> str:
    """Decode raw bytes into a string trying multiple encodings:
    - UTF-16 LE/BE (with BOM or heuristic null-byte check)
    - UTF-8 (with BOM or standard)
    - Windows-1252 / CP1252 (Western European, French/German/Spanish Excel)
    - MacRoman (classic Macintosh CSV export)
    - ISO-8859-1 / Latin-1 (lossless fallback)
    """
    if not data:
        return ""

    # Check for UTF-16 BOM
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            pass

    # Detect UTF-16 without BOM (alternating null bytes in ASCII text)
    if len(data) >= 4:
        sample = data[:min(len(data), 200)]
        if len(sample) >= 4 and (
            sample[1::2].count(b"\x00") > len(sample) // 4
            or sample[0::2].count(b"\x00") > len(sample) // 4
        ):
            try:
                return data.decode("utf-16")
            except UnicodeDecodeError:
                pass

    # Try UTF-8 with BOM support
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass

    # Try CP1252 (Windows ANSI / Western European - covers French, German, Spanish, etc.)
    try:
        return data.decode("cp1252")
    except UnicodeDecodeError:
        pass

    # Try MacRoman (classic Macintosh)
    try:
        return data.decode("mac_roman")
    except UnicodeDecodeError:
        pass

    # Fallback Latin-1
    return data.decode("latin-1", errors="replace")


def parse_number(val: Any) -> Optional[int]:
    """Parse integers supporting suffixes (k, m), separators (comma, dot), and numeric types."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(round(val))

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
        if s.rfind(".") > s.rfind(","):
            s = s.replace(",", "")
        else:
            s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", "")
    elif "." in s:
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) == 3 and multiplier == 1:
            s = "".join(parts)

    try:
        float_val = float(s)
        return int(round(float_val * multiplier))
    except ValueError:
        return None


def parse_level(val: Any) -> Optional[int]:
    """Extract numeric FC / troop level.
    Levels 1-30 are F1-F30 (Furnace 1 to 30).
    FC1-FC10 map to 31-40 (Fire Crystal 1 to 10).
    Progression: F28 (28) < F29 (29) < F30 (30) < FC1 (31) < FC2 (32) < ... < FC8 (38).
    Supports 'FC 5', 'fc3', '8' (FC8), '28' (F28), 'Level 28', 'F28', 'T10', and direct numbers.
    """
    if val is None:
        return None

    if isinstance(val, (int, float)):
        num = int(round(val))
        if 1 <= num <= 10:
            return 30 + num
        return num

    s = str(val).strip()
    if not s or s == "-":
        return None

    # Check for explicit FC prefix first e.g. "FC 5", "fc3", "Fire Crystal 2"
    fc_match = re.search(r"(?:fc|fire\s*crystal)\s*(\d+)", s, re.IGNORECASE)
    if fc_match:
        try:
            fc_num = int(fc_match.group(1))
            # FC 1-10 -> 31-40. If someone wrote FC 28 or FC 30, it refers to Furnace 28 or 30
            if fc_num <= 10:
                return 30 + fc_num
            return fc_num
        except ValueError:
            return None

    # Standard level / F prefix / plain number (also handles '8.0' from Excel floats)
    match = re.search(r"(?:level|lvl|tier|t|f)?\s*(\d+)(?:\.0+)?", s, re.IGNORECASE)
    if match:
        try:
            num = int(match.group(1))
            # 1 to 10 in FC survey columns represents FC1 to FC10 (31 to 40)
            if 1 <= num <= 10:
                return 30 + num
            return num
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

    # Check if string contains "yes" along with a quantity, e.g. "Yes - 150k", "Yes (100,000)"
    if any(pos in s for pos in ("yes", "oui", "ja", "si", "true")):
        # Extract embedded numbers with potential suffixes k/m
        m = re.search(r"(\d+(?:[,\.]\d+)?\s*[kmKM]?)", s)
        if m:
            qty = parse_number(m.group(1))
            if qty is not None and qty > 0:
                return True, qty
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
    "alliance_tag": {
        "alliance tag", "alliance", "tag", "alliance_tag", "alliancetag",
        "guild tag", "guild", "clan", "clan tag",
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

HERO_CANONICAL_DISPLAY: dict[str, str] = {
    "hero_jessie": "Jessie",
    "hero_patrick": "Patrick",
    "hero_jasser": "Jasser",
    "hero_seoyoon": "Seoyoon",
    "hero_sergey": "Sergey",
    "hero_ling_xue": "Ling Xue",
    "hero_ahmose": "Ahmose",
    "hero_norah": "Norah",
    "hero_edith": "Edith",
    "hero_hendrik": "Hendrik",
    "hero_blanchette": "Blanchette",
    "hero_alonso": "Alonso",
    "hero_renee": "Renee",
    "hero_philly": "Philly",
    "hero_gatot": "Gatot",
    "hero_wu_ming": "Wu Ming",
    "hero_hector": "Hector",
    "hero_gregory": "Gregory",
    "hero_eleonora": "Eleonora",
    "hero_hervor": "Hervor",
}


class CsvImporter:
    """Parses arbitrary CSV/TSV data and bulk upserts players."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = PlayerRepository(session)

    @staticmethod
    def detect_delimiter(text: str) -> str:
        """Detect whether text is comma, tab, or semicolon separated.
        Supports Excel directives like 'sep=;' on the first line.
        """
        clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
        if not lines:
            return ","

        # Check for explicit sep= directive from Excel
        first_line = lines[0]
        if first_line.lower().startswith("sep=") and len(first_line) >= 5:
            return first_line[4:5]

        # Use header line for counting
        header_candidate = lines[1] if first_line.lower().startswith("sep=") and len(lines) > 1 else first_line
        counts = {
            ";": header_candidate.count(";"),
            ",": header_candidate.count(","),
            "\t": header_candidate.count("\t"),
            "|": header_candidate.count("|"),
        }
        best = max(counts, key=counts.get)  # type: ignore
        return best if counts[best] > 0 else ","

    @staticmethod
    def map_columns(header_row: list[str]) -> dict[str, int]:
        """Map canonical field names to column indexes."""
        column_map: dict[str, int] = {}
        for idx, col in enumerate(header_row):
            norm = _normalize_header(str(col))
            for canon_key, synonyms in HEADER_SYNONYMS.items():
                if canon_key not in column_map and norm in synonyms:
                    column_map[canon_key] = idx
                    break
        return column_map

    @staticmethod
    def _read_xlsx_bytes(data: bytes) -> list[list[str]]:
        """Extract all non-empty rows from an Excel (.xlsx) file."""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
            sheet = wb.active
            rows: list[list[str]] = []
            for row in sheet.iter_rows(values_only=True):
                row_strs = []
                for c in row:
                    if c is None:
                        row_strs.append("")
                    elif isinstance(c, float) and c.is_integer():
                        row_strs.append(str(int(c)))
                    else:
                        row_strs.append(str(c).strip())
                if any(cell for cell in row_strs):
                    rows.append(row_strs)
            return rows
        except ImportError:
            # Fallback zero-dependency XML parsing if openpyxl is not installed
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                shared_strings = []
                if "xl/sharedStrings.xml" in zf.namelist():
                    tree = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                    for si in tree.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                        t = si.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                        shared_strings.append(t.text if t is not None and t.text else "")
                sheet_name = "xl/worksheets/sheet1.xml"
                tree = ET.fromstring(zf.read(sheet_name))
                rows = []
                for row_elem in tree.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
                    row_data = []
                    for c_elem in row_elem.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                        t_attr = c_elem.get("t")
                        v_elem = c_elem.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                        val = v_elem.text if v_elem is not None and v_elem.text else ""
                        if t_attr == "s" and val.isdigit():
                            val = shared_strings[int(val)] if int(val) < len(shared_strings) else val
                        row_data.append(val.strip())
                    if any(c for c in row_data):
                        rows.append(row_data)
                return rows

    @staticmethod
    def _read_xls_bytes(data: bytes) -> list[list[str]]:
        """Extract all non-empty rows from a legacy Excel (.xls) file using xlrd."""
        import xlrd
        book = xlrd.open_workbook(file_contents=data)
        sheet = book.sheet_by_index(0)
        rows: list[list[str]] = []
        for r in range(sheet.nrows):
            row_vals = []
            for c in range(sheet.ncols):
                val = sheet.cell_value(r, c)
                if isinstance(val, float) and val.is_integer():
                    row_vals.append(str(int(val)))
                else:
                    row_vals.append(str(val).strip() if val != "" else "")
            if any(cell for cell in row_vals):
                rows.append(row_vals)
        return rows

    def import_file_bytes(
        self,
        data: bytes,
        filename: str = "",
        guild_id: Optional[str] = None,
    ) -> ImportResult:
        """Parse raw file bytes supporting .xlsx, .xls, and arbitrary text/csv encodings."""
        if not data:
            res = ImportResult()
            res.errors.append("File is empty.")
            return res

        fn = filename.lower().strip()

        # Modern Excel .xlsx (ZIP format starting with PK)
        if data.startswith(b"PK\x03\x04") or fn.endswith(".xlsx"):
            try:
                rows = self._read_xlsx_bytes(data)
                return self.import_rows(rows, guild_id=guild_id)
            except Exception as e:
                res = ImportResult()
                res.errors.append(f"Failed to read Excel (.xlsx) file: {e}")
                return res

        # Legacy Excel .xls (OLE Compound Document signature)
        if data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1") or fn.endswith(".xls"):
            try:
                rows = self._read_xls_bytes(data)
                return self.import_rows(rows, guild_id=guild_id)
            except Exception as e:
                res = ImportResult()
                res.errors.append(f"Failed to read Excel (.xls) file: {e}")
                return res

        # Plain text: CSV, TSV, Macintosh, UTF-8, UTF-16, CP1252, etc.
        text = decode_text_bytes(data)
        return self.import_text(text, guild_id=guild_id)

    def import_text(self, text: str, guild_id: Optional[str] = None) -> ImportResult:
        result = ImportResult()

        if not text or not text.strip():
            result.errors.append("File is empty.")
            return result

        # Remove BOM if present
        if text.startswith("\ufeff"):
            text = text[1:]

        # Normalize line endings to avoid 'new-line character seen in unquoted field' error
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        lines = [line for line in text.split("\n") if line.strip()]
        if not lines:
            result.errors.append("File is empty.")
            return result

        delimiter = self.detect_delimiter(text)

        # If first line was sep= directive, remove it before CSV parsing
        if lines[0].strip().lower().startswith("sep="):
            text = "\n".join(lines[1:])

        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
        rows = list(reader)
        return self.import_rows(rows, guild_id=guild_id)

    def import_rows(
        self,
        rows: list[list[Any]],
        guild_id: Optional[str] = None,
    ) -> ImportResult:
        result = ImportResult()

        if not rows:
            result.errors.append("File is empty.")
            return result

        header_row = [str(c).strip() for c in rows[0]]
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
                    hero_canonical_name = HERO_CANONICAL_DISPLAY.get(
                        col_key, col_key[5:].replace("_", " ").title()
                    )
                    raw_hero_val = get_val(col_key)
                    parsed_hero = parse_hero_spec(raw_hero_val)
                    if parsed_hero:
                        stars, skill_level = parsed_hero
                        heroes_data[hero_canonical_name] = {
                            "stars": stars,
                            "skill_level": skill_level,
                        }

            alliance_tag = get_val("alliance_tag") or None

            # Upsert into database
            try:
                # 1. Match by game_player_id
                player = self.repo.get_by_game_player_id(game_id, guild_id=guild_id)
                # 2. If not found and discord_id is standard, check discord_user_id
                if player is None and not discord_id.startswith("manual_"):
                    player = self.repo.get_by_discord_id(discord_id, guild_id=guild_id)

                if player is not None:
                    # Update player
                    self.repo.update_player_fields(
                        player,
                        game_player_id=game_id,
                        name=name,
                        march_limit=march_limit,
                        alliance_tag=alliance_tag,
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
                        guild_id=guild_id,
                        alliance_tag=alliance_tag,
                    )
                    result.created += 1



            except Exception as exc:
                result.skipped += 1
                result.errors.append(f"Row {line_num} ({name}): {str(exc)}")

        self.session.flush()
        return result
