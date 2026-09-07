from __future__ import annotations

import logging
from pathlib import Path
from aiohttp import web

from bot.database.base import Database
from bot.rules.configuration import RankingConfig
from bot.settings import Settings
from bot.web.api import (
    handle_auth_me,
    handle_bot_info,
    handle_calculate,
    handle_create_player,
    handle_delete_player,
    handle_discord_callback,
    handle_discord_login,
    handle_download_template_csv,
    handle_get_guilds,
    handle_get_heroes,
    handle_get_player,
    handle_get_presets,
    handle_get_rules,
    handle_get_stats,
    handle_import_players_csv,
    handle_list_alliance_tags,
    handle_list_players,
    handle_login_passkey,

    handle_logout,
    handle_update_player,
    handle_update_rules,
)

logger = logging.getLogger("troop_bot.web")
STATIC_DIR = Path(__file__).resolve().parent / "static"


async def handle_index(request: web.Request) -> web.FileResponse:
    index_path = STATIC_DIR / "index.html"
    return web.FileResponse(index_path)


def create_web_app(
    db: Database,
    config: RankingConfig,
    settings: Settings,
    bot: Optional[Any] = None,
) -> web.Application:
    app = web.Application()
    app["db"] = db
    app["config"] = config
    app["settings"] = settings
    app["bot"] = bot

    # --- API Routes ---
    app.router.add_get("/api/bot/info", handle_bot_info)
    app.router.add_get("/api/guilds", handle_get_guilds)

    app.router.add_get("/api/auth/me", handle_auth_me)
    app.router.add_post("/api/auth/login", handle_login_passkey)
    app.router.add_post("/api/auth/logout", handle_logout)
    app.router.add_get("/api/auth/discord/login", handle_discord_login)
    app.router.add_get("/api/auth/discord/callback", handle_discord_callback)

    app.router.add_get("/api/stats", handle_get_stats)
    app.router.add_get("/api/players", handle_list_players)
    app.router.add_get("/api/alliance-tags", handle_list_alliance_tags)
    app.router.add_get("/api/players/template-csv", handle_download_template_csv)

    app.router.add_post("/api/players", handle_create_player)
    app.router.add_post("/api/players/import", handle_import_players_csv)
    app.router.add_get("/api/players/{id}", handle_get_player)
    app.router.add_put("/api/players/{id}", handle_update_player)
    app.router.add_delete("/api/players/{id}", handle_delete_player)

    app.router.add_post("/api/calculate", handle_calculate)

    app.router.add_get("/api/presets", handle_get_presets)
    app.router.add_get("/api/heroes", handle_get_heroes)

    app.router.add_get("/api/rules", handle_get_rules)
    app.router.add_put("/api/rules", handle_update_rules)


    # --- Frontend SPA & Static Routes ---
    app.router.add_get("/", handle_index)
    app.router.add_static("/static/", path=STATIC_DIR, name="static")

    return app
