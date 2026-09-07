from bot.database.models.player import TroopType
from bot.optimizer.optimizer import optimize
from bot.optimizer.types import FormationRequest, FormationType, Mode, Status
from bot.rules.configuration import default_config
from tests.test_optimizer import make_player, ratio


def test_player_with_no_helios_at_all():
    player = make_player(
        1,
        "Plain",
        march_limit=50_000,
        infantry=(False, 6, None),
        lancers=(False, 6, None),
        marksman=(False, 6, None),
    )
    request = FormationRequest(
        mode=Mode.ATTACK, formation_type=FormationType.RALLY,
        ratio=ratio(34, 33, 33), capacity=50_000,
    )
    result = optimize([player], request, default_config())
    assert result.status == Status.EXACT


def test_player_with_helios_in_only_one_troop_type():
    player = make_player(
        1, "OneHelios", march_limit=100_000,
        infantry=(True, 8, 40_000), lancers=(False, 6, None),
    )
    request = FormationRequest(
        mode=Mode.ATTACK, formation_type=FormationType.RALLY,
        ratio=ratio(50, 50, 0), capacity=100_000,
    )
    result = optimize([player], request, default_config())
    assert result.final[TroopType.INFANTRY] == 40_000  # capped by Helios qty
    assert result.final[TroopType.LANCERS] == 50_000


def test_player_with_helios_in_all_three_types():
    player = make_player(
        1, "TripleHelios", march_limit=300_000,
        infantry=(True, 8, 200_000),
        lancers=(True, 8, 200_000),
        marksman=(True, 8, 200_000),
    )
    request = FormationRequest(
        mode=Mode.ATTACK, formation_type=FormationType.RALLY,
        ratio=ratio(34, 33, 33), capacity=300_000,
    )
    result = optimize([player], request, default_config())
    assert result.status == Status.EXACT
    assert sum(result.final.values()) == 300_000


def test_helios_quantity_smaller_than_march_limit():
    player = make_player(1, "SmallQty", march_limit=1_000_000, infantry=(True, 8, 10_000))
    request = FormationRequest(
        mode=Mode.ATTACK, formation_type=FormationType.RALLY,
        ratio=ratio(100, 0, 0), capacity=1_000_000,
    )
    result = optimize([player], request, default_config())
    assert result.final[TroopType.INFANTRY] == 10_000
    assert result.status == Status.BEST_EFFORT


def test_march_limit_smaller_than_required_contribution():
    player = make_player(1, "SmallMarch", march_limit=1_000, infantry=(False, 8, None))
    request = FormationRequest(
        mode=Mode.ATTACK, formation_type=FormationType.RALLY,
        ratio=ratio(100, 0, 0), capacity=1_000_000,
    )
    result = optimize([player], request, default_config())
    assert result.final[TroopType.INFANTRY] == 1_000
    assert result.status == Status.BEST_EFFORT


def test_insufficient_total_players_returns_best_effort():
    result = optimize(
        [],
        FormationRequest(
            mode=Mode.ATTACK, formation_type=FormationType.RALLY,
            ratio=ratio(34, 33, 33), capacity=1_000,
        ),
        default_config(),
    )
    assert result.status == Status.BEST_EFFORT
    assert sum(result.final.values()) == 0


def test_capacity_larger_than_available_useful_troops():
    player = make_player(1, "Limited", march_limit=5_000, infantry=(False, 8, None))
    request = FormationRequest(
        mode=Mode.ATTACK, formation_type=FormationType.RALLY,
        ratio=ratio(100, 0, 0), capacity=1_000_000,
    )
    result = optimize([player], request, default_config())
    assert result.final[TroopType.INFANTRY] == 5_000
    assert result.status == Status.BEST_EFFORT


def test_ratio_requiring_a_type_few_players_can_provide():
    players = [
        make_player(i, f"Infantry{i}", march_limit=100_000, infantry=(False, 8, None))
        for i in range(10)
    ] + [make_player(99, "LonelyLancer", march_limit=100_000, lancers=(False, 8, None))]
    request = FormationRequest(
        mode=Mode.ATTACK, formation_type=FormationType.RALLY,
        ratio=ratio(45, 10, 45), capacity=1_000_000,
    )
    result = optimize(players, request, default_config())
    assert result.final[TroopType.LANCERS] == 100_000  # capped by the one lancer player
    assert result.status == Status.BEST_EFFORT
