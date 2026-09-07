from __future__ import annotations

import logging

import discord
from discord.ext import commands

from bot.database.base import Database
from bot.discord.commands import admin, calculation, registration
from bot.rules.configuration import RankingConfig, load_config
from bot.settings import Settings

logger = logging.getLogger("troop_bot")


class TroopBot(commands.Bot):
    """The bot's composition root: owns the Database and RankingConfig
    and wires them into each cog. Kept intentionally thin -- all real
    logic lives in bot.services / bot.optimizer.
    """

    def __init__(self, settings: Settings):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        self.db = Database(settings.database_url)
        self.config: RankingConfig = load_config(settings.rules_config_path)

    async def setup_hook(self) -> None:
        self.db.create_all()
        await registration.setup(self, self.db)
        await admin.setup(self, self.db)
        await calculation.setup(self, self.db, self.config)

        synced = await self.tree.sync()
        logger.info("Synced %d application commands.", len(synced))

        # Start web server runner in background if enabled
        import os
        from aiohttp import web
        from bot.web.app import create_web_app

        if os.getenv("ENABLE_WEB_PANEL", "true").lower() in ("1", "true", "yes"):
            try:
                app = create_web_app(self.db, self.config, self.settings)
                self.web_runner = web.AppRunner(app)
                await self.web_runner.setup()
                self.web_site = web.TCPSite(
                    self.web_runner, self.settings.web_host, self.settings.web_port
                )
                await self.web_site.start()
                logger.info(
                    "Web Admin Panel active at http://localhost:%d (Passkey: %s)",
                    self.settings.web_port,
                    self.settings.admin_panel_key,
                )
            except Exception as e:
                logger.warning("Could not start background web panel: %s", e)

    async def close(self) -> None:
        if hasattr(self, "web_runner") and self.web_runner:
            await self.web_runner.cleanup()
        await super().close()

    async def on_ready(self) -> None:  # pragma: no cover - runtime only
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id if self.user else "?")


def build_bot() -> TroopBot:
    from bot.settings import settings as loaded_settings

    return TroopBot(loaded_settings)
