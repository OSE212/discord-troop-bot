from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.database.base import Database
from bot.database.repositories.player_repository import PlayerRepository
from bot.discord.interactions.registration_flow import IdentityModal
from bot.discord.interactions.update_flow import UpdateFieldView


class RegistrationCog(commands.Cog):
    """/register-troops and /update-troops (spec section 5-6)."""

    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db

    @app_commands.command(
        name="register-troops", description="Register your troop information."
    )
    async def register_troops(self, interaction: discord.Interaction):
        with self.db.session() as session:
            existing = PlayerRepository(session).get_by_discord_id(
                str(interaction.user.id)
            )
        if existing is not None:
            await interaction.response.send_message(
                "You're already registered. Use /update-troops to change your "
                "information.",
                ephemeral=True,
            )
            return

        modal = IdentityModal(self.db, on_done=None)
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="update-troops", description="Update your registered troop information."
    )
    async def update_troops(self, interaction: discord.Interaction):
        with self.db.session() as session:
            player = PlayerRepository(session).get_by_discord_id(
                str(interaction.user.id)
            )
            if player is None:
                await interaction.response.send_message(
                    "You're not registered yet. Use /register-troops first.",
                    ephemeral=True,
                )
                return

            view = UpdateFieldView(self.db, player.id)
            await interaction.response.send_message(
                "What would you like to update?", view=view, ephemeral=True
            )


async def setup(bot: commands.Bot, db: Database):
    await bot.add_cog(RegistrationCog(bot, db))
