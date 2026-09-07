import pytest

from bot.database.models.player import TroopType
from bot.services.player_service import RegistrationDraft, TroopTypeInput, ValidationError


def make_complete_draft(discord_id="111"):
    draft = RegistrationDraft(discord_user_id=discord_id)
    draft.game_player_id = "123456"
    draft.name = "Ahmed"
    draft.march_limit = 120_000
    draft.troop_types[TroopType.INFANTRY] = TroopTypeInput(
        helios=True, level=8, helios_quantity=850_000
    )
    draft.troop_types[TroopType.LANCERS] = TroopTypeInput(helios=False, level=7)
    draft.troop_types[TroopType.MARKSMAN] = TroopTypeInput(
        helios=True, level=7, helios_quantity=900_000
    )
    return draft


def test_create_new_player(player_service):
    draft = make_complete_draft()
    player = player_service.register_player(draft)
    assert player.id is not None
    assert player.name == "Ahmed"
    assert player.march_limit == 120_000


def test_helios_and_fc_are_independent(player_service):
    draft = make_complete_draft()
    player = player_service.register_player(draft)
    infantry = player.profile_for(TroopType.INFANTRY)
    assert infantry.helios is True
    assert infantry.level == 8
    lancers = player.profile_for(TroopType.LANCERS)
    assert lancers.helios is False
    assert lancers.level == 7


def test_non_helios_quantity_is_not_requested_or_stored(player_service):
    draft = make_complete_draft()
    player = player_service.register_player(draft)
    lancers = player.profile_for(TroopType.LANCERS)
    assert lancers.helios_quantity is None
    assert lancers.available_quantity() is None  # "unlimited" sentinel


def test_helios_quantity_is_stored_when_helios_true(player_service):
    draft = make_complete_draft()
    player = player_service.register_player(draft)
    infantry = player.profile_for(TroopType.INFANTRY)
    assert infantry.available_quantity() == 850_000


def test_march_limit_required(player_service):
    draft = make_complete_draft()
    draft.march_limit = None
    with pytest.raises(ValidationError):
        player_service.register_player(draft)


def test_fc8_stored_correctly(player_service):
    draft = make_complete_draft()
    player = player_service.register_player(draft)
    assert player.profile_for(TroopType.INFANTRY).level == 8


def test_helios_quantity_required_when_helios_yes(player_service):
    draft = make_complete_draft()
    draft.troop_types[TroopType.INFANTRY] = TroopTypeInput(helios=True, level=8, helios_quantity=None)
    with pytest.raises(ValidationError):
        player_service.register_player(draft)


def test_cannot_register_twice(player_service):
    draft = make_complete_draft()
    player_service.register_player(draft)
    with pytest.raises(ValidationError):
        player_service.register_player(make_complete_draft())


def test_update_existing_player(player_service):
    draft = make_complete_draft()
    player = player_service.register_player(draft)
    player_service.update_identity(player, march_limit=150_000)
    assert player.march_limit == 150_000


def test_toggle_helios_off_clears_quantity(player_service):
    draft = make_complete_draft()
    player = player_service.register_player(draft)
    player_service.update_troop_type(player, TroopType.INFANTRY, helios=False)
    infantry = player.profile_for(TroopType.INFANTRY)
    assert infantry.helios is False
    assert infantry.helios_quantity is None


def test_toggle_helios_on_requires_quantity_before_complete(player_service):
    draft = make_complete_draft()
    player = player_service.register_player(draft)
    player_service.update_troop_type(player, TroopType.LANCERS, helios=True)
    # Quantity not supplied yet -> record is no longer "complete".
    assert player.is_complete() is False
    player_service.update_troop_type(
        player, TroopType.LANCERS, helios=True, helios_quantity=500_000
    )
    assert player.is_complete() is True


def test_parse_level_handles_fc_prefixes():
    from bot.discord.interactions.registration_flow import parse_level

    assert parse_level("7") == 7
    assert parse_level("FC7") == 7
    assert parse_level("fc7") == 7
    assert parse_level("FC 7") == 7
    assert parse_level("fc-8") == 8
    assert parse_level("T10") == 10
    assert parse_level("Level 9") == 9

    with pytest.raises(ValidationError):
        parse_level("invalid")


def test_parse_int_handles_formatting_and_suffixes():
    from bot.discord.interactions.registration_flow import parse_int

    assert parse_int("120,000", "march") == 120_000
    assert parse_int("850k", "qty") == 850_000
    assert parse_int("1.2m", "qty") == 1_200_000
    assert parse_int("FC7", "Infantry Level") == 7


def test_admin_identity_modal_and_manual_id(db, player_service):
    from bot.discord.interactions.registration_flow import IdentityModal

    modal = IdentityModal(
        db,
        on_done=None,
        target_discord_id="999888777",
        default_name="CommanderX",
    )
    assert modal.target_discord_id == "999888777"
    assert modal.name.default == "CommanderX"

    # Verify a manual/off-discord player draft registers cleanly
    draft = make_complete_draft(discord_id="manual_123456")
    player = player_service.register_player(draft)
    assert player.discord_user_id == "manual_123456"
    assert player.name == "Ahmed"
