from __future__ import annotations

import asyncio
from aiohttp.test_utils import TestClient, TestServer

from bot.database.base import Database
from bot.rules.configuration import default_config
from bot.settings import Settings
from bot.web.app import create_web_app


def create_test_app_and_settings(tmp_path):
    db_path = tmp_path / "test_troop.db"
    rules_path = tmp_path / "test_rules.json"

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
    return app, settings


def test_auth_login_and_me(tmp_path):
    async def _test():
        app, settings = create_test_app_and_settings(tmp_path)
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            # Initially guest
            resp = await client.get("/api/auth/me")
            assert resp.status == 200
            data = await resp.json()
            assert data["authenticated"] is False
            assert data["role"] == "guest"

            # Wrong passkey
            resp = await client.post("/api/auth/login", json={"passkey": "wrong"})
            assert resp.status == 401

            # Correct passkey
            resp = await client.post("/api/auth/login", json={"passkey": "secretpass123"})
            assert resp.status == 200
            login_data = await resp.json()
            assert login_data["success"] is True
            assert login_data["role"] == "owner"

            # Now authenticated
            resp = await client.get("/api/auth/me")
            assert resp.status == 200
            me_data = await resp.json()
            assert me_data["authenticated"] is True
            assert me_data["role"] == "owner"

            # Logout
            resp = await client.post("/api/auth/logout")
            assert resp.status == 200
            resp = await client.get("/api/auth/me")
            assert (await resp.json())["authenticated"] is False
        finally:
            await client.close()

    asyncio.run(_test())


def test_player_crud_and_stats(tmp_path):
    async def _test():
        app, settings = create_test_app_and_settings(tmp_path)
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            # Login
            await client.post("/api/auth/login", json={"passkey": "secretpass123"})

            # Check initial stats
            resp = await client.get("/api/stats")
            assert resp.status == 200
            stats = await resp.json()
            assert stats["total_players"] == 0

            # Create Player
            player_payload = {
                "name": "Alexios",
                "game_player_id": "G1001",
                "march_limit": 130000,
                "discord_user_id": "manual_G1001",
                "troops": {
                    "infantry": {"helios": True, "level": 8, "helios_quantity": 400000},
                    "lancers": {"helios": False, "level": 7, "helios_quantity": None},
                    "marksman": {"helios": True, "level": 8, "helios_quantity": 300000},
                },
            }
            resp = await client.post("/api/players", json=player_payload)
            assert resp.status == 201
            created = await resp.json()
            assert created["name"] == "Alexios"
            assert created["is_complete"] is True
            player_id = created["id"]

            # List players
            resp = await client.get("/api/players")
            assert resp.status == 200
            players = await resp.json()
            assert len(players) == 1
            assert players[0]["game_player_id"] == "G1001"

            # Update player
            update_payload = {
                "march_limit": 150000,
                "troops": {
                    "lancers": {"helios": True, "level": 8, "helios_quantity": 250000}
                },
            }
            resp = await client.put(f"/api/players/{player_id}", json=update_payload)
            assert resp.status == 200
            updated = await resp.json()
            assert updated["march_limit"] == 150000
            assert updated["troops"]["lancers"]["helios"] is True

            # Check stats after creation
            resp = await client.get("/api/stats")
            stats = await resp.json()
            assert stats["total_players"] == 1
            assert stats["total_capacity"] == 150000

            # Run calculation via web API
            calc_payload = {
                "mode": "attack",
                "formation_type": "rally",
                "capacity": 100000,
                "ratio": {"infantry": 50, "lancers": 20, "marksman": 30},
            }
            resp = await client.post("/api/calculate", json=calc_payload)
            assert resp.status == 200
            calc_res = await resp.json()
            assert calc_res["mode"] == "attack"
            assert calc_res["formation_type"] == "rally"
            assert calc_res["total_assigned"] == 100000

            # Delete Player
            resp = await client.delete(f"/api/players/{player_id}")
            assert resp.status == 200
            del_res = await resp.json()
            assert del_res["success"] is True

            # Verify list is empty
            resp = await client.get("/api/players")
            players = await resp.json()
            assert len(players) == 0
        finally:
            await client.close()

    asyncio.run(_test())


def test_import_csv_and_garrison_api(tmp_path):
    async def _test():
        app, settings = create_test_app_and_settings(tmp_path)
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            # Authenticate
            await client.post("/api/auth/login", json={"passkey": "secretpass123"})

            # Upload CSV text
            csv_content = """Player Name,Account ID,March Capacity,Infantry Level,Lancer Level,Marksman Level
GarrisonLeader,GL01,165k,30,28,29
DefenderTwo,GL02,150k,28,27,27
"""
            resp = await client.post("/api/players/import", json={"csv_text": csv_content})
            assert resp.status == 200
            import_data = await resp.json()
            assert import_data["created"] == 2
            assert import_data["total_rows"] == 2

            # Run Garrison calculation: capacity 100,000 -> target capacity 167,000 (1.67x)
            calc_payload = {
                "mode": "defence",
                "formation_type": "garrison",
                "capacity": 100000,
                "ratio": {"infantry": 50, "lancers": 20, "marksman": 30},
            }
            resp = await client.post("/api/calculate", json=calc_payload)
            assert resp.status == 200
            calc_res = await resp.json()
            assert calc_res["formation_type"] == "garrison"
            assert calc_res["base_capacity"] == 100000
            assert calc_res["target_capacity"] == 167000
            assert "garrison_gap" in calc_res
        finally:
            await client.close()

    asyncio.run(_test())


def test_multipart_file_upload_xlsx_and_macintosh_csv(tmp_path):
    import io
    import openpyxl
    from aiohttp import FormData

    async def _test():
        app, settings = create_test_app_and_settings(tmp_path)
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            # Login
            await client.post("/api/auth/login", json={"passkey": "secretpass123"})

            # 1. Test Macintosh CSV upload via multipart FormData
            mac_csv_bytes = (
                "In-Game Name;Game ID;March Limit;Infantry FC;Lancers FC;Marksman FC\r"
                "MacHero;7001;175000;8;8;8\r"
            ).encode("utf-8")

            form_mac = FormData()
            form_mac.add_field("file", mac_csv_bytes, filename="players_mac.csv", content_type="text/csv")
            resp = await client.post("/api/players/import", data=form_mac)
            assert resp.status == 200
            res_data = await resp.json()
            assert res_data["created"] == 1

            # 2. Test Excel .xlsx upload via multipart FormData
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["In-Game Name", "Game ID", "March Limit", "Infantry FC"])
            ws.append(["ExcelKing", "7002", 200000, 8])
            buf = io.BytesIO()
            wb.save(buf)

            form_xlsx = FormData()
            form_xlsx.add_field("file", buf.getvalue(), filename="roster.xlsx", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp_xlsx = await client.post("/api/players/import", data=form_xlsx)
            assert resp_xlsx.status == 200
            res_xlsx = await resp_xlsx.json()
            assert res_xlsx["created"] == 1
        finally:
            await client.close()

    asyncio.run(_test())


def test_rallies_calculate_custom_ratios(tmp_path):
    async def _test():
        app, settings = create_test_app_and_settings(tmp_path)
        server = TestServer(app)
        client = TestClient(server)
        await client.start_server()

        try:
            await client.post("/api/auth/login", json={"passkey": "secretpass123"})
            csv_content = """Player Name,Account ID,March Capacity,Infantry Level,Lancer Level,Marksman Level
Captain1,C01,150k,30,28,29
Captain2,C02,150k,28,30,27
Joiner1,J01,100k,25,25,25
"""
            await client.post("/api/players/import", json={"csv_text": csv_content})

            rallies_payload = {
                "rally_count": 2,
                "online_only": False,
                "rally_captains": [
                    {
                        "player_name": "Captain1",
                        "ratio": {"infantry": 60, "lancers": 20, "marksman": 20}
                    },
                    {
                        "player_name": "Captain2",
                        "ratio": {"infantry": 40, "lancers": 30, "marksman": 30}
                    }
                ],
                "alliance_tag": None
            }
            resp = await client.post("/api/rallies/calculate", json=rallies_payload)
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "success"
            assert len(data["rallies"]) == 2
            assert data["rallies"][0]["ratio"] == {"infantry": 60, "lancers": 20, "marksman": 20}
            assert data["rallies"][1]["ratio"] == {"infantry": 40, "lancers": 30, "marksman": 30}
            assert data["rallies"][0]["players"][0]["player_name"] == "Captain1"
            assert data["rallies"][1]["players"][0]["player_name"] == "Captain2"
        finally:
            await client.close()

    asyncio.run(_test())




