import io

import discord
from discord import app_commands
from discord.ext import commands

from bot.database.base import Database
from bot.database.repositories.player_repository import PlayerRepository
from bot.discord.interactions.registration_flow import IdentityModal, summarize_player
from bot.discord.permissions import is_admin
from bot.discord.views.components import ConfirmView
from bot.services.csv_importer import CsvImporter
from bot.services.player_service import PlayerService


def _require_admin(interaction: discord.Interaction) -> bool:
    return isinstance(interaction.user, discord.Member) and is_admin(interaction.user)


class AdminCog(commands.Cog):
    """Admin management commands (spec section 8, 23)."""

    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db

    @app_commands.command(
        name="register-player",
        description="Register troop data for a player (admin).",
    )
    @app_commands.describe(
        member="The Discord member to register (leave blank for off-Discord players)"
    )
    async def register_player(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ):
        if not _require_admin(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        if member is not None:
            with self.db.session() as session:
                existing = PlayerRepository(session).get_by_discord_id(str(member.id))
                if existing is not None:
                    await interaction.response.send_message(
                        f"{member.display_name} is already registered. "
                        "Use /update-troops to change their data, or /reset-player.",
                        ephemeral=True,
                    )
                    return

            modal = IdentityModal(
                self.db,
                on_done=None,
                target_discord_id=str(member.id),
                default_name=member.display_name,
            )
        else:
            modal = IdentityModal(
                self.db,
                on_done=None,
                target_discord_id="manual",
                default_name=None,
            )

        await interaction.response.send_modal(modal)

    @app_commands.command(name="player-info", description="View a player's registration (admin).")
    @app_commands.describe(member="The Discord member to look up")
    async def player_info(self, interaction: discord.Interaction, member: discord.Member):
        if not _require_admin(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return
        with self.db.session() as session:
            player = PlayerRepository(session).get_by_discord_id(str(member.id))
            if player is None:
                await interaction.response.send_message(
                    f"{member.display_name} is not registered.", ephemeral=True
                )
                return
            summary = summarize_player(player)
        await interaction.response.send_message(
            f"**{member.display_name}**\n{summary}", ephemeral=True
        )

    @app_commands.command(name="list-players", description="List all registered players (admin).")
    async def list_players(self, interaction: discord.Interaction):
        if not _require_admin(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return
        with self.db.session() as session:
            players = PlayerRepository(session).list_all()
            if not players:
                await interaction.response.send_message(
                    "No players registered yet.", ephemeral=True
                )
                return
            lines = [
                f"- {p.name} (Game ID: {p.game_player_id}, March Limit: "
                f"{p.march_limit:,}){' [incomplete]' if not p.is_complete() else ''}"
                for p in players
            ]
        await interaction.response.send_message(
            "**Registered Players**\n" + "\n".join(lines), ephemeral=True
        )

    @app_commands.command(name="remove-player", description="Permanently remove a player (admin).")
    @app_commands.describe(member="The Discord member to remove")
    async def remove_player(self, interaction: discord.Interaction, member: discord.Member):
        if not _require_admin(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        async def do_remove(confirm_interaction: discord.Interaction):
            with self.db.session() as session:
                repository = PlayerRepository(session)
                player = repository.get_by_discord_id(str(member.id))
                if player is None:
                    await confirm_interaction.response.edit_message(
                        content=f"{member.display_name} is not registered.", view=None
                    )
                    return
                PlayerService(repository).remove_player(player)
            await confirm_interaction.response.edit_message(
                content=f"Removed {member.display_name}'s registration.", view=None
            )

        view = ConfirmView(do_remove, confirm_label="Remove")
        await interaction.response.send_message(
            f"Permanently remove {member.display_name}'s registration?",
            view=view,
            ephemeral=True,
        )

    @app_commands.command(
        name="reset-player",
        description="Reset a player's troop data so they must re-register (admin).",
    )
    @app_commands.describe(member="The Discord member to reset")
    async def reset_player(self, interaction: discord.Interaction, member: discord.Member):
        if not _require_admin(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        async def do_reset(confirm_interaction: discord.Interaction):
            with self.db.session() as session:
                repository = PlayerRepository(session)
                player = repository.get_by_discord_id(str(member.id))
                if player is None:
                    await confirm_interaction.response.edit_message(
                        content=f"{member.display_name} is not registered.", view=None
                    )
                    return
                PlayerService(repository).reset_player(player)
            await confirm_interaction.response.edit_message(
                content=(
                    f"Reset {member.display_name}'s troop data. They'll need to "
                    "use /update-troops to fill it back in."
                ),
                view=None,
            )

        view = ConfirmView(do_reset, confirm_label="Reset")
        await interaction.response.send_message(
            f"Reset {member.display_name}'s troop data?", view=view, ephemeral=True
        )

    @app_commands.command(
        name="import-csv",
        description="Bulk import/update players from a CSV/TSV file (admin).",
    )
    @app_commands.describe(file="The CSV or TSV file to import")
    async def import_csv(self, interaction: discord.Interaction, file: discord.Attachment):
        if not _require_admin(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            content_bytes = await file.read()
            try:
                csv_text = content_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                csv_text = content_bytes.decode("latin-1", errors="replace")

            with self.db.session() as session:
                importer = CsvImporter(session)
                result = importer.import_text(csv_text)

            embed = discord.Embed(
                title="📊 Bulk Player Import Results",
                color=0x22C55E if result.skipped == 0 else 0xEAB308,
            )
            embed.add_field(name="Total Rows", value=str(result.total_rows), inline=True)
            embed.add_field(name="Created", value=f"✅ {result.created}", inline=True)
            embed.add_field(name="Updated", value=f"🔄 {result.updated}", inline=True)
            if result.skipped > 0:
                embed.add_field(name="Skipped", value=f"⚠️ {result.skipped}", inline=True)

            if result.errors:
                sample_errors = "\n".join(f"• {err}" for err in result.errors[:5])
                if len(result.errors) > 5:
                    sample_errors += f"\n*...and {len(result.errors) - 5} more*"
                embed.add_field(name="Warnings/Errors", value=sample_errors, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(
                f"❌ Failed to process CSV: {exc}", ephemeral=True
            )

    @app_commands.command(
        name="csv-template",
        description="Get the recommended CSV template for player roster imports (admin).",
    )
    async def csv_template(self, interaction: discord.Interaction):
        if not _require_admin(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        template_text = (
            "Name,Game ID,March Limit,Discord ID,Infantry FC,Infantry Helios,Lancers FC,Lancers Helios,Marksman FC,Marksman Helios\n"
            "LordVader,10001,165000,123456789012345678,30,165000,30,165000,30,165000\n"
            "Skywalker,10002,150000,,28,Yes,27,No,28,Yes\n"
        )
        file = discord.File(
            io.BytesIO(template_text.encode("utf-8")),
            filename="roster_import_template.csv",
        )
        msg = (
            "**📋 Roster CSV Template**\n"
            "You can use this template for your Google Forms or spreadsheets.\n"
            "• **Flexible Column Names**: The bot understands synonyms like `IGN`, `Governor ID`, `March Capacity`, `Cav FC`, `Archer FC`, etc.\n"
            "• **Flexible Formats**: Numbers can use `165k` or commas (`165,000`). Helios can be `Yes`/`No` or exact quantities."
        )
        await interaction.response.send_message(msg, file=file, ephemeral=True)


async def setup(bot: commands.Bot, db: Database):
    await bot.add_cog(AdminCog(bot, db))
