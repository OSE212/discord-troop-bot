"""Application settings loaded from environment variables (.env).

Keep all secrets/config here so the rest of the codebase never reads
os.environ directly. This makes it trivial to swap SQLite for Postgres
later, or to point the bot at a different guild during testing.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    # Loading dotenv is optional at import time so tests don't require it
    # to be installed as a hard runtime dependency of every module.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - only hit if python-dotenv missing
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    discord_token: str
    database_url: str
    admin_role_name: str
    calculator_role_name: str
    rules_config_path: Path
    web_host: str = "0.0.0.0"
    web_port: int = 8080
    admin_panel_key: str = "admin123"
    bot_owner_id: str = ""
    discord_client_id: str = ""
    discord_client_secret: str = ""
    discord_redirect_uri: str = ""

    @classmethod
    def load(cls) -> "Settings":
        db_url = os.getenv("DATABASE_URL") or f"sqlite:///{PROJECT_ROOT / 'troop_bot.db'}"
        admin_role = os.getenv("ADMIN_ROLE_NAME") or "Troop Admin"
        calc_role = os.getenv("CALCULATOR_ROLE_NAME") or "Troop Calculator"
        rules_path = os.getenv("RULES_CONFIG_PATH") or str(PROJECT_ROOT / "config" / "rules.json")

        try:
            port = int(os.getenv("WEB_PORT", os.getenv("PORT", "8080")))
        except ValueError:
            port = 8080

        return cls(
            discord_token=os.getenv("DISCORD_TOKEN", ""),
            database_url=db_url,
            admin_role_name=admin_role,
            calculator_role_name=calc_role,
            rules_config_path=Path(rules_path),
            web_host=os.getenv("WEB_HOST", "0.0.0.0"),
            web_port=port,
            admin_panel_key=os.getenv("ADMIN_PANEL_KEY", "admin123"),
            bot_owner_id=os.getenv("BOT_OWNER_ID", ""),
            discord_client_id=os.getenv("DISCORD_CLIENT_ID", ""),
            discord_client_secret=os.getenv("DISCORD_CLIENT_SECRET", ""),
            discord_redirect_uri=os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8080/api/auth/discord/callback"),
        )


settings = Settings.load()
