from __future__ import annotations

import discord

from bot.database.base import Database
from bot.database.models.player import TroopType
from bot.database.repositories.player_repository import PlayerRepository
from bot.discord.interactions.registration_flow import parse_int
from bot.optimizer.ratio import InvalidCapacityError, InvalidRatioError
from bot.optimizer.types import FormationType, Mode
from bot.rules.configuration import RankingConfig
from bot.services.formation_service import FormationService, format_result


class ModeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Attack", value=Mode.ATTACK.value),
            discord.SelectOption(label="Defence", value=Mode.DEFENCE.value),
        ]
        super().__init__(placeholder="Attack or Defence?", options=options)

    async def callback(self, interaction: discord.Interaction):
        view: CalculationSetupView = self.view  # type: ignore[assignment]
        view.mode = Mode(self.values[0])
        await view.maybe_advance(interaction)


class FormationTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Rally", value=FormationType.RALLY.value),
            discord.SelectOption(label="Garrison", value=FormationType.GARRISON.value),
        ]
        super().__init__(placeholder="Rally or Garrison?", options=options)

    async def callback(self, interaction: discord.Interaction):
        view: CalculationSetupView = self.view  # type: ignore[assignment]
        view.formation_type = FormationType(self.values[0])
        await view.maybe_advance(interaction)


class CalculationSetupView(discord.ui.View):
    """Step 1+2 of /calculate: pick Attack/Defence and Rally/Garrison,
    then open the ratio+capacity modal (spec section 9)."""

    def __init__(
        self, db: Database, config: RankingConfig, *, timeout: float = 180
    ):
        super().__init__(timeout=timeout)
        self.db = db
        self.config = config
        self.mode: Mode | None = None
        self.formation_type: FormationType | None = None
        self.add_item(ModeSelect())
        self.add_item(FormationTypeSelect())

    async def maybe_advance(self, interaction: discord.Interaction):
        if self.mode is None or self.formation_type is None:
            await interaction.response.defer()
            return
        modal = RatioCapacityModal(self.db, self.config, self.mode, self.formation_type)
        await interaction.response.send_modal(modal)


class RatioCapacityModal(discord.ui.Modal, title="Calculate - Ratio & Capacity"):
    infantry_pct = discord.ui.TextInput(label="Infantry %", required=True, max_length=8)
    lancers_pct = discord.ui.TextInput(label="Lancers %", required=True, max_length=8)
    marksman_pct = discord.ui.TextInput(label="Marksman %", required=True, max_length=8)
    capacity = discord.ui.TextInput(
        label="Total Formation Capacity", required=True, max_length=16
    )

    def __init__(
        self, db: Database, config: RankingConfig, mode: Mode, formation_type: FormationType
    ):
        super().__init__()
        self.db = db
        self.config = config
        self.mode = mode
        self.formation_type = formation_type

    async def on_submit(self, interaction: discord.Interaction):
        try:
            infantry = float(str(self.infantry_pct.value).strip())
            lancers = float(str(self.lancers_pct.value).strip())
            marksman = float(str(self.marksman_pct.value).strip())
            capacity = parse_int(str(self.capacity.value), "Capacity")
        except ValueError:
            await interaction.response.send_message(
                "Percentages must be numbers.", ephemeral=True
            )
            return

        ratio = {
            TroopType.INFANTRY: infantry,
            TroopType.LANCERS: lancers,
            TroopType.MARKSMAN: marksman,
        }

        with self.db.session() as session:
            repository = PlayerRepository(session)
            service = FormationService(repository, self.config)
            try:
                result = service.calculate(
                    mode=self.mode,
                    formation_type=self.formation_type,
                    ratio=ratio,
                    capacity=capacity,
                )
            except (InvalidRatioError, InvalidCapacityError) as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
            text = format_result(result)

        # Discord messages cap at 2000 chars; wrap in a code block and
        # split if needed rather than silently truncating the result.
        chunks = _chunk_for_discord(text)
        await interaction.response.send_message(chunks[0], ephemeral=True)
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk, ephemeral=True)


def _chunk_for_discord(text: str, limit: int = 1900) -> list[str]:
    lines = text.split("\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        if current_len + len(line) + 1 > limit and current:
            chunks.append("```\n" + "\n".join(current) + "\n```")
            current, current_len = [], 0
        current.append(line)
        current_len += len(line) + 1
    if current:
        chunks.append("```\n" + "\n".join(current) + "\n```")
    return chunks
