# Discord Troop Optimizer Bot — V1

A Discord bot for registering per-player troop data and calculating
deterministic, rule-based Rally/Garrison formations. Built from
`Discord_Troop_Optimizer_V1_Spec.md`.

No LLM is used to decide troop assignments — the optimizer is a
deterministic, configurable, rule-based algorithm (spec rule 10).

## Setup & Running the Bot

### 1. Environment & Configuration
1. Copy `.env.example` to `.env` and fill in `DISCORD_TOKEN` (from the [Discord Developer Portal](https://discord.com/developers/applications)). Leave `DATABASE_URL` blank to use the default local SQLite file (`troop_bot.db`).
2. In the Discord Developer Portal, invite the bot to your server with the `applications.commands` and `bot` scopes, and at least "Send Messages" / "Use Slash Commands" permissions.
3. Create two server roles matching `ADMIN_ROLE_NAME` / `CALCULATOR_ROLE_NAME` in `.env` (defaults: "Troop Admin", "Troop Calculator") and assign them. Anyone with "Manage Server" or "Administrator" permission is automatically treated as a bot admin.

---

### 2. Run Commands by Terminal

#### Windows PowerShell

**Quickest way (no activation needed):**
```powershell
# Run the bot
.\.venv\Scripts\python.exe run.py

# Run tests
.\.venv\Scripts\pytest
```

**Using Virtual Environment Activation:**
```powershell
# 1. (Optional - if venv does not exist yet):
py -m venv .venv

# 2. Activate venv:
.\.venv\Scripts\Activate.ps1

# Note: If PowerShell blocks script execution, run:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Install requirements (first time only):
pip install -r requirements.txt

# 4. Start the bot:
python run.py

# 5. Run tests:
pytest
```

---

#### Windows Git Bash

**Quickest way (direct path):**
```bash
# Run the bot
./.venv/Scripts/python run.py

# Run tests
./.venv/Scripts/pytest
```

**Using Virtual Environment Activation:**
```bash
# 1. (Optional - if venv does not exist yet):
py -m venv .venv

# 2. Activate venv:
source .venv/Scripts/activate

# 3. Install requirements (first time only):
pip install -r requirements.txt

# 4. Start the bot:
python run.py

# 5. Run tests:
pytest
```

---

#### Linux / macOS (Bash / Zsh)
```bash
# 1. Activate venv
source .venv/bin/activate

# 2. Start the bot
python run.py

# 3. Run tests
pytest
```

Slash commands sync automatically on startup (`setup_hook`). It can take up to an hour for *global* command updates to propagate on Discord's side the first time; if commands don't show up immediately, that's expected.

---

## Running the Tests

You can execute the 41-test suite with either:

* **PowerShell**: `.\.venv\Scripts\pytest` (or `pytest` if activated)
* **Git Bash**: `./.venv/Scripts/pytest` (or `pytest` if activated)

**Note on this delivery:** the sandbox this bot was built in has no
network access, so `sqlalchemy`, `pytest`, and `discord.py` could not
be installed there and the test suite could not actually be executed
before hand-off. The core ratio/optimizer math (largest-remainder
rounding and the greedy allocation algorithm) was manually verified
against the spec's own worked examples with a standalone script, but
please run `pytest` yourself after installing dependencies before
trusting this in production. If anything fails, the most likely
culprits are minor SQLAlchemy/discord.py version-API mismatches
(caught in a few minutes) rather than the core algorithm logic.

## What's covered

- **Registration** (`/register-troops`): guided, multi-step (identity
  → Helios multi-select → FC levels → Helios quantities). Nothing is
  written to the database until every required field is collected.
- **Updates** (`/update-troops`): update identity, march limit, or any
  single troop type's Helios/level/quantity independently. Turning
  Helios off clears the stored quantity; turning it on requires a
  fresh quantity before the record counts as "complete" again.
- **Admin** (`/register-player`, `/player-info`, `/list-players`,
  `/remove-player`, `/reset-player`): role-gated. Admins can register a
  player on their behalf (targeting a Discord member or an off-Discord player).
  Remove/Reset both require an explicit confirmation button before touching data.
- **Calculation** (`/calculate`): guided (Attack/Defence → Rally/
  Garrison → ratio % + capacity modal). Read-only against player data;
  never modifies registration.
- **Web Admin Panel** (`http://localhost:8080`): Modern browser dashboard
  for Bot Owners and Server Admins. Provides live overview statistics, full
  player roster management (add/edit/delete with single unified forms), an
  interactive Formation Simulator with real-time ratio sliders, and optimizer
  rules tuning.
- **Optimizer**: deterministic greedy allocator. Respects march limits
  (including when a player's march is split across troop types),
  finite Helios quantities, abundant non-Helios availability, formation
  capacity, and the confirmed rule that a player is only used once
  even when contributing multiple troop types.

## Assumptions made (documented per spec instructions)

The spec's own "Important Mechanical Ambiguity" (section 11) flagged
one open question as materially affecting correctness, so it was
asked directly rather than guessed:

> **Can a player split their march across multiple troop types in one
> formation?** — **Confirmed: yes**, subject to their total march
> limit. The optimizer treats a player's remaining march limit as
> shared state across all troop types they contribute, so the sum of
> everything they're assigned never exceeds it.

A few smaller implementation choices were made to keep V1 simple,
each reversible without an architecture change:

- **Optimizer algorithm is a greedy heuristic, not a global optimum
  solver.** It scores every (player, troop type) combination and
  greedily fills the highest-scoring slots first, subject to all
  constraints. This is simple, fast, and fully deterministic, but for
  unusual inputs it *can* find a slightly worse total score than a
  true mixed-integer-programming solution would. Given the spec's
  emphasis on "simple and reliable" for V1, this tradeoff seemed
  right — an exact solver (e.g. via `pulp` or `OR-Tools`) would be a
  reasonable V2 upgrade if formations start looking suboptimal in
  practice.
- **`/reset-player` vs `/remove-player`**: both clear a player's data
  today (Reset wipes troop profiles back to blank so they must
  `/update-troops` again; Remove deletes the row entirely). They're
  kept as separate repository/service methods specifically so a
  future version can make Reset non-destructive (e.g. an audit log or
  "soft reset") without touching Remove's semantics.
- **Ranking weights are placeholders.** `bot/rules/configuration.py`
  encodes only the *relative* ordering the spec confirmed (e.g.
  "Infantry is most important for Defence") using arbitrary numbers,
  clearly commented as non-canonical. Edit `config/rules.json` (or
  delete it to regenerate defaults) once real game statistics are
  available — no code changes needed.
- **Registration state lives in memory during the guided flow**, and
  only reaches the database once every required field is present.
  If a player abandons the flow partway through, nothing partial is
  saved — they just start over with `/register-troops`.
- **Ties in the optimizer** are broken deterministically by player ID
  then troop type, so re-running an identical calculation always
  produces an identical result.

## Project structure

```
bot/
  database/        SQLAlchemy models + repositories (only place that touches SQL)
  optimizer/        Deterministic scoring + greedy allocation algorithm
  rules/             Configurable, editable ranking weights (config/rules.json)
  services/          Business logic + validation, DB-agnostic and Discord-agnostic
  discord/
    commands/        Slash command cogs (thin wrappers over services)
    interactions/     Modals/Views implementing the guided registration/update/calculate flows
    views/            Small reusable UI components
tests/               pytest suite for ratio math, ranking, optimizer, validation, edge cases
config/rules.json     Editable optimizer weights (auto-created on first run)
```

## 24/7 Cloud Hosting (Always Free)

To host both the Discord bot and Web Admin Panel 24/7 for free without needing a domain name, follow the **[Oracle Cloud Free Tier Deployment Guide](ORACLE_CLOUD_DEPLOY.md)**.

