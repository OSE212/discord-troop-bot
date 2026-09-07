from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.database.base import Database
from bot.discord.interactions.calculation_flow import CalculationSetupView
from bot.discord.permissions import is_calculator
from bot.rules.configuration import RankingConfig


class CalculationCog(commands.Cog):
    """/calculate (spec sections 9-19). Never modifies player
    registration data -- purely reads players and returns a result.
    """

    def __init__(self, bot: commands.Bot, db: Database, config: RankingConfig):
        self.bot = bot
        self.db = db
        self.config = config

    @app_commands.command(
        name="calculate",
        description="Calculate an optimized Rally/Garrison formation.",
    )
    async def calculate(self, interaction: discord.Interaction):
        if not (
            isinstance(interaction.user, discord.Member) and is_calculator(interaction.user)
        ):
            await interaction.response.send_message(
                "You don't have permission to run calculations.", ephemeral=True
            )
            return

        view = CalculationSetupView(self.db, self.config)
        await interaction.response.send_message(
            "Step 1/2 - Choose Attack/Defence and Rally/Garrison:",
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot, db: Database, config: RankingConfig):
    await bot.add_cog(CalculationCog(bot, db, config))
