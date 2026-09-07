from __future__ import annotations

import asyncio
import pytest
from aiohttp.test_utils import TestClient, TestServer

from bot.database.base import Database
from bot.database.models.player import TroopType
from bot.optimizer.optimizer import optimize
from bot.optimizer.types import (
    FormationRequest,
    FormationType,
    Mode,
    OptimizerPlayer,
    TroopAvailability,
)
from bot.rules.configuration import default_config
from bot.settings import Settings
from bot.web.app import create_web_app


def make_player_with_heroes(
    player_id: int,
    name: str,
    march_limit: int,
    heroes: dict[str, tuple[int, int]] | None = None,
    **types,
) -> OptimizerPlayer:
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
        player_id=player_id,
        name=name,
        march_limit=march_limit,
        troop_types=troop_types,
        heroes=heroes or {},
    )


def test_optimizer_respects_target_joiners():
    p1 = make_player_with_heroes(
        1,
        "Alice",
        100_000,
        heroes={"jessie": (5, 5), "patrick": (4, 4)},
        infantry=(True, 10, 200_000),
    )
    p2 = make_player_with_heroes(
        2,
        "Bob",
        100_000,
        heroes={"jasser": (5, 5), "seoyoon": (4, 3)},
        infantry=(True, 10, 200_000),
    )
    p3 = make_player_with_heroes(
        3,
        "Charlie",
        100_000,
        heroes={"seoyoon": (5, 5), "patrick": (3, 2)},
        infantry=(True, 10, 200_000),
    )
    p4 = make_player_with_heroes(
        4,
        "Dave",
        100_000,
        heroes={"patrick": (5, 5)},
        infantry=(True, 10, 200_000),
    )

    request = FormationRequest(
        mode=Mode.ATTACK,
        formation_type=FormationType.RALLY,
        ratio={TroopType.INFANTRY: 100.0, TroopType.LANCERS: 0.0, TroopType.MARKSMAN: 0.0},
        capacity=400_000,
        target_joiners=("jessie", "jasser", "seoyoon", "patrick"),
    )

    result = optimize([p1, p2, p3, p4], request, default_config())

    assert len(result.joiners) == 4
    joiner_heroes = [j.hero_name.lower() for j in result.joiners]
    assert joiner_heroes == ["jessie", "jasser", "seoyoon", "patrick"]

    # Alice has best Jessie, Bob has Jasser, Charlie has best Seoyoon (5,5), Dave has best Patrick (5,5)
    joiner_names = [j.player_name for j in result.joiners]
    assert joiner_names == ["Alice", "Bob", "Charlie", "Dave"]


def test_optimizer_double_joiner_hero():
    """Verify that multiple slots with the same hero (e.g., Patrick) select distinct players."""
    p1 = make_player_with_heroes(
        1,
        "Whale1",
        100_000,
        heroes={"patrick": (5, 5), "sergey": (5, 4)},
        infantry=(True, 10, 200_000),
    )
    p2 = make_player_with_heroes(
        2,
        "Whale2",
        100_000,
        heroes={"patrick": (5, 4), "ling_xue": (5, 5)},
        infantry=(True, 10, 200_000),
    )
    p3 = make_player_with_heroes(
        3,
        "Whale3",
        100_000,
        heroes={"sergey": (5, 5)},
        infantry=(True, 10, 200_000),
    )
    p4 = make_player_with_heroes(
        4,
        "Whale4",
        100_000,
        heroes={"ling_xue": (4, 4), "patrick": (4, 4)},
        infantry=(True, 10, 200_000),
    )

    request = FormationRequest(
        mode=Mode.DEFENCE,
        formation_type=FormationType.GARRISON,
        ratio={TroopType.INFANTRY: 100.0, TroopType.LANCERS: 0.0, TroopType.MARKSMAN: 0.0},
        capacity=400_000,
        target_joiners=("patrick", "patrick", "sergey", "ling_xue"),
    )

    result = optimize([p1, p2, p3, p4], request, default_config())

    assert len(result.joiners) == 4
    player_ids = [j.player_id for j in result.joiners]
    assert len(set(player_ids)) == 4, "All 4 joiners must be distinct players"
    assert result.joiners[0].hero_name.lower() == "patrick"
    assert result.joiners[1].hero_name.lower() == "patrick"


def create_test_app(tmp_path):
    db_path = tmp_path / "test_troop_heroes.db"
    rules_path = tmp_path / "test_rules_heroes.json"

    settings = Settings(
        discord_token="fake_token",
        database_url=f"sqlite:///{db_path}",
        admin_role_name="Troop Admin",
        calculator_role_name="Troop Calculator",
        rules_config_path=rules_path,
        web_host="127.0.0.1",
        web_port=8080,
        admin_panel_key="secretpass123",
        bot_owner_id="",
        discord_client_id="",
        discord_client_secret="",
        discord_redirect_uri="",
    )

    db = Database(settings.database_url)
    db.create_all()
    config = default_config()
    app = create_web_app(db, config, settings)
    return app


def test_api_heroes_catalog(tmp_path):
    async def _test():
        app = create_test_app(tmp_path)
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            resp = await client.get("/api/heroes")
            assert resp.status == 200
            data = await resp.json()
            assert "heroes" in data
            assert "presets" in data
            assert isinstance(data["heroes"], list)
            hero_names = {h["name"] for h in data["heroes"]}
            assert "Jessie" in hero_names
            assert "Patrick" in hero_names
            preset_ids = {p["id"] for p in data["presets"]}
            assert "attack_all_out" in preset_ids
            assert "fortress_defense" in preset_ids
        finally:
            await client.close()

    asyncio.run(_test())


def test_api_calculate_with_target_joiners(tmp_path):
    async def _test():
        app = create_test_app(tmp_path)
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            # Login as owner
            login_resp = await client.post("/api/auth/login", json={"passkey": "secretpass123"})
            assert login_resp.status == 200

            calc_payload = {
                "mode": "attack",
                "formation_type": "rally",
                "ratio": {"infantry": 50, "lancers": 20, "marksman": 30},
                "capacity": 500000,
                "target_joiners": ["jessie", "jasser", "seoyoon", "patrick"],
            }
            resp = await client.post("/api/calculate", json=calc_payload)
            assert resp.status == 200
            data = await resp.json()
            assert "status" in data
            assert "players" in data
            assert "joiner_recommendations" in data
        finally:
            await client.close()

    asyncio.run(_test())


