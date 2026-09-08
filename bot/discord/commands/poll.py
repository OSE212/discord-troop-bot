"""
/battle_poll — Deploys a persistent Discord embed with three attendance buttons.
Players click Online / Tentative / Absent to update the live embed.
Responses also sync to the Web Panel attendance API so the War Room tab
reflects the same data.
"""
from __future__ import annotations

import logging
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from bot.database.base import Database
from bot.discord.permissions import is_admin

logger = logging.getLogger("troop_bot.poll")

WEB_ATTENDANCE_URL = "http://127.0.0.1:{port}/api/attendance/check-in"


class BattlePollView(discord.ui.View):
    """Persistent view — survives bot restarts if re-registered."""

    def __init__(self, event_title: str, web_port: int = 8080):
        super().__init__(timeout=None)
        self.event_title = event_title
        self.web_port = web_port
        self.online: dict[str, int] = {}      # display_name → player_id (unknown = 0)
        self.tentative: dict[str, int] = {}
        self.absent: dict[str, int] = {}

    # ── helpers ──────────────────────────────────────────────────────
    def _clear_user(self, name: str) -> None:
        self.online.pop(name, None)
        self.tentative.pop(name, None)
        self.absent.pop(name, None)

    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"⚔️ Battle Attendance Poll: {self.event_title}",
            description="Mark your availability for the upcoming war phase.",
            color=0x00F2FE,
        )
        embed.add_field(
            name=f"🟢 Online / Ready ({len(self.online)})",
            value="\n".join(f"• {n}" for n in self.online) or "*None*",
            inline=True,
        )
        embed.add_field(
            name=f"🟡 Tentative ({len(self.tentative)})",
            value="\n".join(f"• {n}" for n in self.tentative) or "*None*",
            inline=True,
        )
        embed.add_field(
            name=f"🔴 Absent ({len(self.absent)})",
            value="\n".join(f"• {n}" for n in self.absent) or "*None*",
            inline=True,
        )
        embed.set_footer(text=f"Total confirmed online: {len(self.online)}")
        return embed

    async def _sync_to_web(self, player_id: int, is_online: bool) -> None:
        """Best-effort push to web panel attendance API."""
        if player_id == 0:
            return
        try:
            url = WEB_ATTENDANCE_URL.format(port=self.web_port)
            async with aiohttp.ClientSession() as session:
                await session.post(
                    url,
                    json={"player_ids": [player_id], "is_online": is_online},
                    timeout=aiohttp.ClientTimeout(total=3),
                )
        except Exception as exc:
            logger.debug("Web sync skipped: %s", exc)

    # ── buttons ───────────────────────────────────────────────────────
    @discord.ui.button(
        label="Online / Ready ⚔️",
        style=discord.ButtonStyle.green,
        custom_id="battle_poll:online",
    )
    async def btn_online(self, interaction: discord.Interaction, button: discord.ui.Button):
        name = interaction.user.display_name
        self._clear_user(name)
        self.online[name] = 0
        await self._sync_to_web(0, True)
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(
        label="Tentative ❓",
        style=discord.ButtonStyle.secondary,
        custom_id="battle_poll:tentative",
    )
    async def btn_tentative(self, interaction: discord.Interaction, button: discord.ui.Button):
        name = interaction.user.display_name
        self._clear_user(name)
        self.tentative[name] = 0
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(
        label="Absent ❌",
        style=discord.ButtonStyle.red,
        custom_id="battle_poll:absent",
    )
    async def btn_absent(self, interaction: discord.Interaction, button: discord.ui.Button):
        name = interaction.user.display_name
        self._clear_user(name)
        self.absent[name] = 0
        await interaction.response.edit_message(embed=self._build_embed(), view=self)


class PollCog(commands.Cog):
    """Slash commands for battle availability polling."""

    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db

    @app_commands.command(
        name="battle-poll",
        description="Post an attendance poll for an upcoming SvS / Fortress event.",
    )
    @app_commands.describe(event_title="Name of the battle event (e.g. SvS Day 2, Fortress 18:00)")
    async def battle_poll(self, interaction: discord.Interaction, event_title: str):
        if not (isinstance(interaction.user, discord.Member) and is_admin(interaction.user)):
            await interaction.response.send_message(
                "Only server admins can start a battle poll.", ephemeral=True
            )
            return

        web_port = getattr(self.bot, "settings", None)
        port = getattr(web_port, "web_port", 8080) if web_port else 8080

        view = BattlePollView(event_title, web_port=port)
        embed = view._build_embed()
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot, db: Database) -> None:
    await bot.add_cog(PollCog(bot, db))
