from __future__ import annotations

from typing import Awaitable, Callable, Optional

import discord

from bot.database.models.player import TroopType

TROOP_TYPE_LABELS = {
    TroopType.INFANTRY: "Infantry",
    TroopType.LANCERS: "Lancers",
    TroopType.MARKSMAN: "Marksman",
}


class HeliosMultiSelect(discord.ui.Select):
    """Multi-select for "which troop types have Helios" (spec section
    5, Step 2)."""

    def __init__(self, *, default: Optional[set[TroopType]] = None):
        default = default or set()
        options = [
            discord.SelectOption(
                label="None (No Helios)",
                value="none",
                description="I don't have Helios for any troop type",
            )
        ] + [
            discord.SelectOption(
                label=label,
                value=troop_type.value,
                default=troop_type in default,
            )
            for troop_type, label in TROOP_TYPE_LABELS.items()
        ]
        super().__init__(
            placeholder="Select which troop types have Helios (or None)",
            min_values=0,
            max_values=len(options),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Selection state is read by the parent view's Continue button;
        # just acknowledge so Discord doesn't show a stale "loading".
        await interaction.response.defer()


class HeliosSelectView(discord.ui.View):
    """A Helios multi-select plus Continue and None buttons. `on_continue`
    receives the chosen set of TroopType and the interaction that
    triggered Continue.
    """

    def __init__(
        self,
        on_continue: Callable[[discord.Interaction, set[TroopType]], Awaitable[None]],
        *,
        default: Optional[set[TroopType]] = None,
        timeout: float = 300,
    ):
        super().__init__(timeout=timeout)
        self.on_continue = on_continue
        self.select = HeliosMultiSelect(default=default)
        self.add_item(self.select)

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary, row=1)
    async def continue_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        raw_values = set(self.select.values)
        if "none" in raw_values:
            chosen = set()
        else:
            chosen = {TroopType(v) for v in raw_values if v in [t.value for t in TroopType]}
        await self.on_continue(interaction, chosen)

    @discord.ui.button(label="None / No Helios", style=discord.ButtonStyle.secondary, row=1)
    async def none_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.on_continue(interaction, set())


class ConfirmView(discord.ui.View):
    """Yes/No confirmation for destructive admin actions (remove,
    reset)."""

    def __init__(
        self,
        on_confirm: Callable[[discord.Interaction], Awaitable[None]],
        *,
        confirm_label: str = "Confirm",
        timeout: float = 60,
    ):
        super().__init__(timeout=timeout)
        self.on_confirm = on_confirm
        self.children[0].label = confirm_label  # type: ignore[union-attr]

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.on_confirm(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Cancelled.", view=None)
