# Troop Command Bot - System Mechanisms

This document explains the core mechanisms and calculations used across the Troop Command Bot application.

## 1. Formation Optimizer (`bot/optimizer/ratio.py`)

The formation optimizer is responsible for taking a player's desired formation type (e.g., "60/20/20" for Infantry/Lancers/Marksman) and converting it into exact troop counts that precisely sum to the player's total March Limit.

### Calculation Method (Largest-Remainder Method)
The optimizer uses the **Largest-Remainder Method** (also known as the Hare-Niemeyer method) to ensure that the sum of the calculated troops perfectly matches the `march_limit` without any silent rounding losses.

1. **Calculate Raw Targets:** For each troop type, calculate the exact floating-point target: `raw = march_limit * (percentage / 100)`.
2. **Floor Values:** Take the integer (floored) part of each raw target.
3. **Calculate Remainder:** Find how many troops are missing: `remainder = march_limit - sum(floored_values)`.
4. **Distribute Remainder:** Sort the troop types by their fractional part (i.e., `raw - floored`) in descending order. Give 1 extra troop to the types with the largest fractional parts until the `remainder` is exhausted.

## 2. Level Progression and Mapping (`bot/services/csv_importer.py` & UI)

The system unified the representation of standard levels (F1-F30) and Fire Crystal (FC) levels (FC1-FC10) into a continuous integer scale internally.

### Internal Mapping:
- **Levels 1 to 30**: Represent standard levels `F1` through `F30`.
- **Levels 31 to 40**: Represent Fire Crystal levels `FC1` through `FC10`.

*Formula: `Internal Level = 30 + FC Level`*

### Display Formatting:
When displaying levels in the UI or Bot commands, the system uses formatting helpers (like `formatFcLevel`):
- If `level > 30`: Displays as `FC{level - 30}` (e.g., 31 -> FC1).
- If `level <= 30`: Displays as `F{level}` (e.g., 28 -> F28).

## 3. Data Lifecycle

The application provides multiple entry points for managing player data, which all flow into a centralized `PlayerRepository`.

### Registration and Updates:
1. **Discord Bot Commands:** Users can register or update their profiles via `/register` and `/troops`. The Discord bot creates a `RegistrationDraft` and passes it to the `PlayerService`.
2. **Multi-Format Roster Import (`CsvImporter`):** Alliance leaders can mass-import rosters in the Admin Panel. The system universally supports:
   - **Excel Workbooks:** Modern `.xlsx` (OpenXML via `openpyxl` with fallback XML parser) and legacy `.xls` (BIFF8 via `xlrd`).
   - **Encodings:** Automatic detection of `UTF-8` (with/without BOM), `UTF-16 LE/BE` (Unicode text exports from Excel), `Windows-1252 / CP1252` (Western European Excel), `MacRoman` (classic Macintosh), and `Latin-1`.
   - **Line Breaks:** Normalization of classic Mac (`\r`), Windows (`\r\n`), and Unix (`\n`), eliminating `new-line character seen in unquoted field` errors.
   - **Delimiters:** Automatic detection of semicolons (`point-virgule ;`), commas (`,`), tabs (`\t`), and pipes (`|`), as well as Excel's `sep=;` top-line directives.
   - **Natural Language & Synonyms:** Maps flexible column headers (e.g., "marksmen fc", "archer level", "Capacité de marche", "IGN") into canonical fields and bulk-upserts the database records.
3. **Admin Panel UI:** The Web API (`api.py`) exposes endpoints for manually adding or editing players, which ultimately reuse the `PlayerService` for validation.

### Database Constraints and Migrations:
- **SQLite Schema:** The backend uses an SQLite database with SQLAlchemy ORM.
- **Alliance Tag:** The `alliance_tag` column is indexed and persisted. To support seamless updates on existing deployments, the system runs an automatic `ALTER TABLE` schema check at startup (in `bot/database/base.py`) to inject missing columns without data loss.

## 4. Helios Troops Processing

Helios troops are handled dynamically. A player specifies whether they have unlocked Helios (`True`/`False`) and optionally provides a specific count (`helios_quantity`).
- If Helios is `True` but no quantity is specified, the system defaults the maximum available Helios troops to the player's `march_limit`.
- During CSV import, natural language combinations like "Yes - 150k" or boolean values like "Yes"/"No" are parsed into the `(helios, helios_quantity)` schema.
