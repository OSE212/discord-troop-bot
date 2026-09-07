from bot.database.models.player import TroopType
from bot.optimizer.optimizer import optimize
from bot.optimizer.types import (
    FormationRequest,
    FormationType,
    Mode,
    OptimizerPlayer,
    Status,
    TroopAvailability,
)
from bot.rules.configuration import default_config


def ratio(infantry, lancers, marksman):
    return {
        TroopType.INFANTRY: infantry,
        TroopType.LANCERS: lancers,
        TroopType.MARKSMAN: marksman,
    }


def make_player(player_id, name, march_limit, **types):
    """types: troop_type_name -> (helios, level, quantity_or_None)"""
    mapping = {
        "infantry": TroopType.INFANTRY,
        "lancers": TroopType.LANCERS,
        "marksman": TroopType.MARKSMAN,
    }
    troop_types = {}
    for key, (helios, level, qty) in types.items():
        troop_types[mapping[key]] = TroopAvailability(
            helios=helios, level=level, available_quantity=qty
        )
    return OptimizerPlayer(
        player_id=player_id, name=name, march_limit=march_limit, troop_types=troop_types
    )


def test_march_limit_never_exceeded_even_when_split_across_types():
    ahmed = make_player(
        1,
        "Ahmed",
        march_limit=120_000,
        infantry=(True, 8, 850_000),
        marksman=(True, 7, 900_000),
    )
    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio=ratio(50, 0, 50),
        capacity=200_000,
    )
    result = optimize([ahmed], request, default_config())
    summary = result.selected_players[0]
    assert summary.total <= 120_000


def test_helios_quantity_is_respected():
    # Tiny Helios quantity, huge march limit -> capped by quantity, not march limit.
    player = make_player(
        1, "Small Helios", march_limit=1_000_000, infantry=(True, 8, 5_000)
    )
    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio=ratio(100, 0, 0),
        capacity=1_000_000,
    )
    result = optimize([player], request, default_config())
    assert result.final[TroopType.INFANTRY] == 5_000
    assert result.status == Status.BEST_EFFORT


def test_non_helios_troops_are_valid_candidates_and_unbounded_by_quantity():
    player = make_player(
        1, "No Helios", march_limit=500_000, infantry=(False, 8, None)
    )
    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio=ratio(100, 0, 0),
        capacity=500_000,
    )
    result = optimize([player], request, default_config())
    assert result.final[TroopType.INFANTRY] == 500_000
    assert result.status == Status.EXACT


def test_formation_capacity_is_never_exceeded():
    players = [
        make_player(i, f"P{i}", march_limit=10_000_000, infantry=(False, 8, None))
        for i in range(5)
    ]
    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio=ratio(100, 0, 0),
        capacity=1_000_000,
    )
    result = optimize(players, request, default_config())
    assert sum(result.final.values()) <= request.capacity
    assert result.status == Status.EXACT


def test_exact_ratio_achieved_when_available():
    players = [
        make_player(1, "Infantry Guy", march_limit=1_000_000, infantry=(False, 8, None)),
        make_player(2, "Lancer Guy", march_limit=1_000_000, lancers=(False, 8, None)),
        make_player(3, "Marksman Guy", march_limit=1_000_000, marksman=(False, 8, None)),
    ]
    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio=ratio(49, 2, 49),
        capacity=2_000_000,
    )
    result = optimize(players, request, default_config())
    assert result.status == Status.EXACT
    assert result.final[TroopType.INFANTRY] == 980_000
    assert result.final[TroopType.LANCERS] == 40_000
    assert result.final[TroopType.MARKSMAN] == 980_000


def test_impossible_ratio_returns_best_effort_with_deviation():
    # Nobody has any Lancers registered -> the ratio can't be met exactly.
    players = [
        make_player(1, "Infantry Guy", march_limit=2_000_000, infantry=(False, 8, None)),
        make_player(2, "Marksman Guy", march_limit=2_000_000, marksman=(False, 8, None)),
    ]
    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio=ratio(49, 2, 49),
        capacity=2_000_000,
    )
    result = optimize(players, request, default_config())
    assert result.status == Status.BEST_EFFORT
    assert result.final[TroopType.LANCERS] == 0
    assert result.deviation[TroopType.LANCERS] != 0


def test_no_player_is_duplicated_in_results():
    player = make_player(
        1,
        "Ahmed",
        march_limit=120_000,
        infantry=(False, 8, None),
        marksman=(False, 7, None),
    )
    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio=ratio(50, 0, 50),
        capacity=200_000,
    )
    result = optimize([player], request, default_config())
    assert len(result.selected_players) == 1


def test_player_can_split_march_across_troop_types_when_beneficial():
    # Confirmed mechanic: splitting is allowed, subject to march limit.
    ahmed = make_player(
        1,
        "Ahmed",
        march_limit=120_000,
        infantry=(False, 8, None),
        marksman=(False, 8, None),
    )
    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio=ratio(50, 0, 50),
        capacity=120_000,
    )
    result = optimize([ahmed], request, default_config())
    summary = result.selected_players[0]
    assert summary.contributions.get(TroopType.INFANTRY, 0) == 60_000
    assert summary.contributions.get(TroopType.MARKSMAN, 0) == 60_000
    assert summary.total == 120_000


def test_defence_profile_prefers_infantry_heavy_player_first():
    strong_infantry = make_player(
        1, "Tank", march_limit=100_000, infantry=(True, 8, 100_000)
    )
    weak_marksman_only = make_player(
        2, "Glass Cannon", march_limit=100_000, marksman=(True, 8, 100_000)
    )
    request = FormationRequest(
        mode=Mode.DEFENCE,
        formation_type=FormationType.GARRISON,
        ratio=ratio(50, 0, 50),
        capacity=100_000,
    )
    result = optimize([strong_infantry, weak_marksman_only], request, default_config())
    infantry_summary = next(
        s for s in result.selected_players if s.player_id == 1
    )
    # Garrison inflates capacity to 167,000 (1.67x buffer), so 50% target is 83,500
    assert result.base_capacity == 100_000
    assert result.target_capacity == 167_000
    assert infantry_summary.contributions[TroopType.INFANTRY] == 83_500
