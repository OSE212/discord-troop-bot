from bot.database.models.player import TroopType
from bot.optimizer.ranking import score_contribution
from bot.optimizer.types import FormationType, Mode, TroopAvailability
from bot.rules.configuration import default_config


def test_fc8_ranks_above_fc7_when_configured():
    config = default_config()
    fc7 = TroopAvailability(helios=False, level=7, available_quantity=None)
    fc8 = TroopAvailability(helios=False, level=8, available_quantity=None)

    score_fc7 = score_contribution(
        TroopType.INFANTRY, fc7, Mode.ATTACK, FormationType.RALLY, config
    )
    score_fc8 = score_contribution(
        TroopType.INFANTRY, fc8, Mode.ATTACK, FormationType.RALLY, config
    )
    assert score_fc8 > score_fc7


def test_helios_bonus_increases_score():
    config = default_config()
    no_helios = TroopAvailability(helios=False, level=7, available_quantity=None)
    with_helios = TroopAvailability(helios=True, level=7, available_quantity=100_000)

    score_no_helios = score_contribution(
        TroopType.INFANTRY, no_helios, Mode.ATTACK, FormationType.RALLY, config
    )
    score_helios = score_contribution(
        TroopType.INFANTRY, with_helios, Mode.ATTACK, FormationType.RALLY, config
    )
    assert score_helios > score_no_helios


def test_attack_profile_favors_marksman_and_infantry_over_lancers():
    config = default_config()
    avail = TroopAvailability(helios=False, level=7, available_quantity=None)

    infantry_score = score_contribution(
        TroopType.INFANTRY, avail, Mode.ATTACK, FormationType.RALLY, config
    )
    lancer_score = score_contribution(
        TroopType.LANCERS, avail, Mode.ATTACK, FormationType.RALLY, config
    )
    marksman_score = score_contribution(
        TroopType.MARKSMAN, avail, Mode.ATTACK, FormationType.RALLY, config
    )
    assert infantry_score > lancer_score
    assert marksman_score > lancer_score


def test_defence_profile_favors_infantry_and_penalizes_marksman():
    config = default_config()
    avail = TroopAvailability(helios=False, level=7, available_quantity=None)

    infantry_score = score_contribution(
        TroopType.INFANTRY, avail, Mode.DEFENCE, FormationType.RALLY, config
    )
    marksman_score = score_contribution(
        TroopType.MARKSMAN, avail, Mode.DEFENCE, FormationType.RALLY, config
    )
    lancer_score = score_contribution(
        TroopType.LANCERS, avail, Mode.DEFENCE, FormationType.RALLY, config
    )
    assert infantry_score > lancer_score > marksman_score
