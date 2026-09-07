"""Entrypoint: `python web_run.py` starts the Web Admin Panel.

Serves on http://localhost:8080 (or configured WEB_PORT in .env).
"""
from __future__ import annotations

import logging
from aiohttp import web

from bot.database.base import Database
from bot.rules.configuration import load_config
from bot.settings import settings
from bot.web.app import create_web_app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    db = Database(settings.database_url)
    db.create_all()
    config = load_config(settings.rules_config_path)

    app = create_web_app(db, config, settings)
    print("\n=======================================================")
    print(f"[WEB] Troop Command Web Panel running at: http://localhost:{settings.web_port}")
    print(f"[KEY] Admin Master Passkey: {settings.admin_panel_key}")
    print("=======================================================\n")

    web.run_app(app, host=settings.web_host, port=settings.web_port)


if __name__ == "__main__":
    main()
