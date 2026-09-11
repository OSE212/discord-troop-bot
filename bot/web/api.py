from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

from aiohttp import ClientSession, web

from bot.database.models.player import Player, TroopType
from bot.database.repositories.player_repository import PlayerRepository
from bot.optimizer.types import FormationType, Mode
from bot.rules.configuration import RankingConfig, load_config
from bot.rules.formation_guide import FORMATION_GUIDE_PRESETS
from bot.optimizer.ratio import InvalidCapacityError, InvalidRatioError
from bot.services.csv_importer import CsvImporter
from bot.services.formation_service import FormationService
from bot.services.player_service import (
    PlayerService,
    RegistrationDraft,
    TroopTypeInput,
    ValidationError,
)
from bot.settings import Settings

logger = logging.getLogger("troop_bot.web")


def serialize_player(player: Player) -> dict[str, Any]:
    troops: dict[str, Any] = {}
    for troop_type in TroopType:
        profile = player.profile_for(troop_type)
        if profile:
            troops[troop_type.value] = {
                "helios": profile.helios,
                "level": profile.level,
                "helios_quantity": profile.helios_quantity,
            }
        else:
            troops[troop_type.value] = {
                "helios": False,
                "level": None,
                "helios_quantity": None,
            }

    return {
        "id": player.id,
        "guild_id": player.guild_id,
        "discord_user_id": player.discord_user_id,
        "game_player_id": player.game_player_id,
        "name": player.name,
        "alliance_tag": player.alliance_tag,
        "march_limit": player.march_limit,

        "is_complete": player.is_complete(),
        "created_at": player.created_at.isoformat() if player.created_at else None,
        "updated_at": player.updated_at.isoformat() if player.updated_at else None,
        "troops": troops,

        "heroes": [
            {
                "name": h.hero_name,
                "stars": h.stars,
                "skill_level": h.skill_level,
            }
            for h in (player.heroes or [])
        ],
    }


def _apply_heroes_to_player(
    repo: "PlayerRepository",
    player: "Player",
    heroes_data: list,
) -> None:
    """Upsert hero entries and remove any not present in the new list."""
    if not isinstance(heroes_data, list):
        return
    incoming_names = set()
    for h in heroes_data:
        hero_name = str(h.get("name", "")).strip()
        if not hero_name:
            continue
        stars = max(1, min(5, int(h.get("stars", 1))))
        skill_level = max(1, min(5, int(h.get("skill_level", 1))))
        repo.upsert_hero(player, hero_name, stars=stars, skill_level=skill_level)
        incoming_names.add(hero_name.lower().strip())
    # Remove heroes that are no longer in the list
    to_remove = [h for h in (player.heroes or []) if h.hero_name not in incoming_names]
    for h in to_remove:
        player.heroes.remove(h)
        repo.session.delete(h)
    repo.session.flush()


def _sign_session(data: dict[str, Any], secret: str) -> str:
    raw = json.dumps(data, separators=(",", ":"))
    payload = base64.urlsafe_b64encode(raw.encode()).decode()
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _verify_session(token: str, secret: str, max_age_seconds: int = 86400 * 7) -> Optional[dict[str, Any]]:
    try:
        if "." in token:
            payload, sig = token.split(".", 1)
            expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                return None
            data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
            if time.time() - data.get("timestamp", 0) > max_age_seconds:
                return None
            return data

        # Legacy 4-colon format: role:name:timestamp:sig
        parts = token.split(":")
        if len(parts) == 4:
            role, user_name, timestamp_str, sig = parts
            payload = f"{role}:{user_name}:{timestamp_str}"
            expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                return None
            if time.time() - int(timestamp_str) > max_age_seconds:
                return None
            return {
                "user_id": "legacy",
                "role": role,
                "name": user_name,
                "avatar": None,
                "admin_guilds": [{"id": "*", "name": "🌐 All Servers (Global)"}],
                "admin_guild_ids": ["*"],
            }
        return None
    except Exception:
        return None


def get_current_user(request: web.Request) -> Optional[dict[str, Any]]:
    secret = request.app["settings"].admin_panel_key
    cookie = request.cookies.get("troop_session")
    if not cookie:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            cookie = auth_header[7:].strip()
    if not cookie:
        return None
    return _verify_session(cookie, secret)


def get_target_guild_id(request: web.Request, user: dict[str, Any]) -> Optional[str]:
    """Determine the active server/guild ID for multi-tenant data isolation."""
    guild_id = request.query.get("guild_id") or request.headers.get("X-Guild-Id")
    user_role = user.get("role", "guest")
    admin_ids = user.get("admin_guild_ids", [])

    if user_role == "owner":
        if not guild_id or guild_id in ("*", "all"):
            return "*"
        return guild_id

    # For regular admins:
    if not guild_id or guild_id in ("*", "all"):
        return admin_ids[0] if admin_ids else None

    if guild_id not in admin_ids:
        return None
    return guild_id


# --- Bot Info & Guilds Endpoints ---

async def handle_bot_info(request: web.Request) -> web.Response:
    settings: Settings = request.app["settings"]
    bot = request.app.get("bot")

    client_id = settings.discord_client_id
    bot_name = "Troop Command Bot"
    avatar_url = None
    server_count = 0

    if bot and getattr(bot, "user", None):
        client_id = client_id or str(bot.user.id)
        bot_name = bot.user.name
        if bot.user.avatar:
            avatar_url = bot.user.avatar.url
        server_count = len(getattr(bot, "guilds", []))

    invite_url = ""
    if client_id:
        invite_url = (
            f"https://discord.com/api/oauth2/authorize?client_id={client_id}"
            f"&permissions=277025778752&scope=bot%20applications.commands"
        )

    return web.json_response({
        "client_id": client_id,
        "bot_name": bot_name,
        "avatar_url": avatar_url,
        "server_count": server_count,
        "invite_url": invite_url,
        "has_discord_oauth": bool(settings.discord_client_id and settings.discord_client_secret),
    })


async def handle_get_guilds(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    settings: Settings = request.app["settings"]
    bot = request.app.get("bot")
    bot_guilds_map = {str(g.id): g for g in (getattr(bot, "guilds", None) or [])}
    client_id = settings.discord_client_id or (str(bot.user.id) if bot and getattr(bot, "user", None) else "")

    def make_invite(gid: str) -> str:
        if not client_id:
            return ""
        return (
            f"https://discord.com/api/oauth2/authorize?client_id={client_id}"
            f"&permissions=277025778752&scope=bot%20applications.commands&guild_id={gid}"
        )

    guild_list: list[dict[str, Any]] = []

    if user.get("role") == "owner":
        guild_list.append({
            "id": "*",
            "name": "🌐 All Servers (Global)",
            "icon": None,
            "bot_installed": True,
            "member_count": sum(getattr(g, "member_count", 0) or 0 for g in bot_guilds_map.values()),
            "invite_url": "",
        })
        for gid, g in bot_guilds_map.items():
            guild_list.append({
                "id": gid,
                "name": g.name,
                "icon": g.icon.url if g.icon else None,
                "bot_installed": True,
                "member_count": getattr(g, "member_count", 0) or 0,
                "invite_url": "",
            })
    else:
        admin_guilds = user.get("admin_guilds", [])
        for ag in admin_guilds:
            gid = str(ag.get("id"))
            name = ag.get("name", "Unknown Server")
            icon_hash = ag.get("icon")
            icon_url = (
                f"https://cdn.discordapp.com/icons/{gid}/{icon_hash}.png"
                if icon_hash
                else None
            )
            is_installed = gid in bot_guilds_map
            member_count = getattr(bot_guilds_map[gid], "member_count", None) if is_installed else None

            guild_list.append({
                "id": gid,
                "name": name,
                "icon": icon_url,
                "bot_installed": is_installed,
                "member_count": member_count,
                "invite_url": make_invite(gid) if not is_installed else "",
            })

    return web.json_response(guild_list)


# --- Auth Endpoints ---

async def handle_auth_me(request: web.Request) -> web.Response:
    user = get_current_user(request)
    settings: Settings = request.app["settings"]
    has_discord_oauth = bool(settings.discord_client_id and settings.discord_client_secret)
    if user:
        return web.json_response({
            "authenticated": True,
            "role": user.get("role", "admin"),
            "name": user.get("name", "User"),
            "avatar": user.get("avatar"),
            "has_discord_oauth": has_discord_oauth,
            "admin_guilds": user.get("admin_guilds", []),
        })
    return web.json_response({
        "authenticated": False,
        "role": "guest",
        "name": None,
        "avatar": None,
        "has_discord_oauth": has_discord_oauth,
        "admin_guilds": [],
    })


async def handle_login_passkey(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    passkey = str(data.get("passkey", "")).strip()
    settings: Settings = request.app["settings"]

    if passkey and passkey == settings.admin_panel_key:
        session_data = {
            "user_id": "master_owner",
            "name": "Master Owner",
            "avatar": None,
            "role": "owner",
            "admin_guilds": [{"id": "*", "name": "🌐 All Servers (Global)"}],
            "admin_guild_ids": ["*"],
            "timestamp": int(time.time()),
        }
        token = _sign_session(session_data, settings.admin_panel_key)
        response = web.json_response({
            "success": True,
            "role": "owner",
            "name": "Master Owner",
            "admin_guilds": session_data["admin_guilds"],
        })
        response.set_cookie(
            "troop_session",
            token,
            max_age=86400 * 7,
            httponly=True,
            samesite="Lax",
        )
        return response

    return web.json_response({"error": "Invalid admin passkey"}, status=401)


async def handle_logout(request: web.Request) -> web.Response:
    response = web.json_response({"success": True})
    response.del_cookie("troop_session")
    return response


async def handle_discord_login(request: web.Request) -> web.Response:
    settings: Settings = request.app["settings"]
    if not (settings.discord_client_id and settings.discord_client_secret):
        return web.json_response({"error": "Discord OAuth is not configured on this server"}, status=400)

    redirect_uri = settings.discord_redirect_uri
    scope = "identify guilds"
    oauth_url = (
        f"https://discord.com/oauth2/authorize?client_id={settings.discord_client_id}"
        f"&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    )
    raise web.HTTPFound(oauth_url)


async def handle_discord_callback(request: web.Request) -> web.Response:
    code = request.query.get("code")
    if not code:
        return web.Response(text="Missing OAuth code", status=400)

    settings: Settings = request.app["settings"]
    token_url = "https://discord.com/api/oauth2/token"
    data = {
        "client_id": settings.discord_client_id,
        "client_secret": settings.discord_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.discord_redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with ClientSession() as session:
        async with session.post(token_url, data=data, headers=headers) as resp:
            if resp.status != 200:
                text_err = await resp.text()
                logger.error("Discord OAuth token exchange error: %s", text_err)
                return web.Response(text="Failed to exchange Discord OAuth token", status=400)
            token_data = await resp.json()

        access_token = token_data.get("access_token")
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Fetch user profile
        async with session.get("https://discord.com/api/users/@me", headers=auth_headers) as user_resp:
            if user_resp.status != 200:
                return web.Response(text="Failed to fetch Discord user profile", status=400)
            user_data = await user_resp.json()

        user_id = str(user_data.get("id"))
        username = user_data.get("global_name") or user_data.get("username", "Discord User")
        avatar_hash = user_data.get("avatar")
        avatar_url = (
            f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
            if avatar_hash
            else None
        )

        admin_guilds_list = []
        is_bot_owner = bool(settings.bot_owner_id and user_id == str(settings.bot_owner_id))

        # Check user's guilds
        async with session.get("https://discord.com/api/users/@me/guilds", headers=auth_headers) as guilds_resp:
            if guilds_resp.status == 200:
                guilds = await guilds_resp.json()
                for g in guilds:
                    permissions = int(g.get("permissions", 0))
                    # Check Administrator (0x8) or Manage Server (0x20) or guild owner
                    if g.get("owner", False) or (permissions & 0x8) or (permissions & 0x20):
                        admin_guilds_list.append({
                            "id": str(g.get("id")),
                            "name": g.get("name", "Unknown Server"),
                            "icon": g.get("icon"),
                        })

        role = "guest"
        if is_bot_owner:
            role = "owner"
            admin_guilds_list.insert(0, {"id": "*", "name": "🌐 All Servers (Global)", "icon": None})
        elif admin_guilds_list:
            role = "admin"

        if role == "guest":
            return web.Response(
                text="Access Denied: You must be a server administrator or have 'Manage Server' permission on at least one Discord server to access the admin panel.",
                status=403,
            )

        session_data = {
            "user_id": user_id,
            "name": username,
            "avatar": avatar_url,
            "role": role,
            "admin_guilds": admin_guilds_list,
            "admin_guild_ids": [g["id"] for g in admin_guilds_list],
            "timestamp": int(time.time()),
        }

        token = _sign_session(session_data, settings.admin_panel_key)
        response = web.HTTPFound("/")
        response.set_cookie("troop_session", token, max_age=86400 * 7, httponly=True, samesite="Lax")
        return response



# --- Stats Endpoints ---

async def handle_get_stats(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    target_guild = get_target_guild_id(request, user)
    if target_guild is None and user.get("role") != "owner":
        return web.json_response({"error": "You do not have access to this server."}, status=403)

    db = request.app["db"]
    with db.session() as session:
        repo = PlayerRepository(session)
        players = repo.list_all(guild_id=target_guild)

        total = len(players)
        complete = sum(1 for p in players if p.is_complete())
        incomplete = total - complete
        total_capacity = sum(p.march_limit for p in players)

        helios_counts = {t.value: 0 for t in TroopType}
        fc_levels = {t.value: [] for t in TroopType}

        for p in players:
            for t in TroopType:
                prof = p.profile_for(t)
                if prof:
                    if prof.helios:
                        helios_counts[t.value] += (prof.helios_quantity or 0)
                    if prof.level is not None:
                        fc_levels[t.value].append(prof.level)

        avg_fc = {
            k: (round(sum(v) / len(v), 1) if v else 0) for k, v in fc_levels.items()
        }

    return web.json_response({
        "total_players": total,
        "complete_players": complete,
        "incomplete_players": incomplete,
        "total_capacity": total_capacity,
        "helios_quantities": helios_counts,
        "average_levels": avg_fc,
        "guild_id": target_guild,
    })


# --- Players Endpoints ---

async def handle_list_players(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    target_guild = get_target_guild_id(request, user)
    if target_guild is None and user.get("role") != "owner":
        return web.json_response({"error": "You do not have access to this server."}, status=403)

    q = request.query.get("q", "").strip().lower()
    filter_mode = request.query.get("filter", "all").strip().lower()
    alliance_tag_filter = request.query.get("alliance_tag", "").strip()

    db = request.app["db"]
    with db.session() as session:
        repo = PlayerRepository(session)
        players = repo.list_all(guild_id=target_guild, alliance_tag=alliance_tag_filter or None)

        results = []
        for p in players:
            # Query search filter
            if q:
                matches_name = q in p.name.lower()
                matches_game_id = q in p.game_player_id.lower()
                matches_discord_id = q in p.discord_user_id.lower()
                matches_tag = p.alliance_tag and q in p.alliance_tag.lower()
                if not (matches_name or matches_game_id or matches_discord_id or matches_tag):
                    continue

            # State filter
            if filter_mode == "complete" and not p.is_complete():
                continue
            if filter_mode == "incomplete" and p.is_complete():
                continue
            if filter_mode == "helios":
                has_helios = any(
                    prof.helios for prof in p.troop_profiles
                )
                if not has_helios:
                    continue

            results.append(serialize_player(p))

    return web.json_response(results)


async def handle_list_alliance_tags(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    db = request.app["db"]
    with db.session() as session:
        repo = PlayerRepository(session)
        tags = repo.list_distinct_alliance_tags()

    return web.json_response(tags)




async def handle_get_player(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        player_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid player ID"}, status=400)

    db = request.app["db"]
    with db.session() as session:
        repo = PlayerRepository(session)
        player = repo.get_by_id(player_id)
        if not player:
            return web.json_response({"error": "Player not found"}, status=404)
        return web.json_response(serialize_player(player))


async def handle_create_player(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    game_player_id = str(data.get("game_player_id", "")).strip()
    name = str(data.get("name", "")).strip()
    march_limit = data.get("march_limit")
    discord_id = str(data.get("discord_user_id", "")).strip() or f"manual_{game_player_id}"[:32]

    try:
        march_limit = int(march_limit)
        if march_limit <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return web.json_response({"error": "March limit must be a positive whole number."}, status=400)

    troops_data = data.get("troops", {})

    target_guild = get_target_guild_id(request, user)
    if target_guild is None and user.get("role") != "owner":
        return web.json_response({"error": "You do not have access to this server."}, status=403)

    guild_to_set = target_guild if target_guild and target_guild != "*" else None

    draft = RegistrationDraft(discord_user_id=discord_id)
    draft.guild_id = guild_to_set
    draft.game_player_id = game_player_id
    draft.name = name
    draft.march_limit = march_limit

    for troop_type in TroopType:
        t_data = troops_data.get(troop_type.value, {})
        helios = bool(t_data.get("helios", False))
        level = t_data.get("level")
        qty = t_data.get("helios_quantity")

        if level is not None:
            try:
                level = int(level)
            except ValueError:
                return web.json_response({"error": f"{troop_type.value.capitalize()} level must be a number."}, status=400)

        if helios and qty is not None:
            try:
                qty = int(qty)
            except ValueError:
                return web.json_response({"error": f"{troop_type.value.capitalize()} quantity must be a number."}, status=400)
        else:
            qty = None

        draft.troop_types[troop_type] = TroopTypeInput(
            helios=helios,
            level=level,
            helios_quantity=qty,
        )

    db = request.app["db"]
    try:
        with db.session() as session:
            repo = PlayerRepository(session)
            existing = repo.get_by_discord_id(discord_id, guild_id=guild_to_set)
            if existing is not None:
                return web.json_response({"error": f"A player with Discord/Identifier '{discord_id}' already exists."}, status=409)

            service = PlayerService(repo)
            player = service.register_player(draft)


            # Apply hero data if present
            heroes_data = data.get("heroes", [])
            if heroes_data:
                _apply_heroes_to_player(repo, player, heroes_data)

            return web.json_response(serialize_player(player), status=201)
    except ValidationError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:
        logger.exception("Error registering player via web API")
        return web.json_response({"error": str(exc)}, status=500)


async def handle_update_player(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        player_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid player ID"}, status=400)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    db = request.app["db"]
    with db.session() as session:
        repo = PlayerRepository(session)
        player = repo.get_by_id(player_id)
        if not player:
            return web.json_response({"error": "Player not found"}, status=404)

        service = PlayerService(repo)

        # Update identity fields if provided
        game_player_id = data.get("game_player_id")
        name = data.get("name")
        march_limit = data.get("march_limit")
        alliance_tag = data.get("alliance_tag")

        if march_limit is not None:
            try:
                march_limit = int(march_limit)
            except ValueError:
                return web.json_response({"error": "March limit must be a number"}, status=400)

        try:
            service.update_identity(
                player,
                game_player_id=str(game_player_id).strip() if game_player_id else None,
                name=str(name).strip() if name else None,
                march_limit=march_limit,
                alliance_tag=str(alliance_tag).strip() if alliance_tag is not None else None,
            )
        except ValidationError as exc:
            return web.json_response({"error": str(exc)}, status=400)


        # Update troops
        troops_data = data.get("troops")
        if troops_data and isinstance(troops_data, dict):
            for troop_type in TroopType:
                if troop_type.value in troops_data:
                    t_info = troops_data[troop_type.value]
                    helios = bool(t_info.get("helios", False))
                    level = t_info.get("level")
                    qty = t_info.get("helios_quantity")

                    if level is not None:
                        try:
                            level = int(level)
                        except ValueError:
                            return web.json_response({"error": f"{troop_type.value} level must be an integer"}, status=400)

                    if helios and qty is not None:
                        try:
                            qty = int(qty)
                        except ValueError:
                            return web.json_response({"error": f"{troop_type.value} quantity must be an integer"}, status=400)
                    else:
                        qty = None

                    try:
                        service.update_troop_type(
                            player,
                            troop_type,
                            helios=helios,
                            level=level,
                            helios_quantity=qty,
                        )
                    except ValidationError as exc:
                        return web.json_response({"error": str(exc)}, status=400)

        # Update heroes if present in payload
        heroes_data = data.get("heroes")
        if heroes_data is not None:
            _apply_heroes_to_player(repo, player, heroes_data)

        return web.json_response(serialize_player(player))


async def handle_delete_player(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        player_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid player ID"}, status=400)

    db = request.app["db"]
    with db.session() as session:
        repo = PlayerRepository(session)
        player = repo.get_by_id(player_id)
        if not player:
            return web.json_response({"error": "Player not found"}, status=404)
        PlayerService(repo).remove_player(player)

    return web.json_response({"success": True})


async def handle_clear_players(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    target_guild = get_target_guild_id(request, user)
    if target_guild is None and user.get("role") != "owner":
        return web.json_response({"error": "You do not have access to this server."}, status=403)

    db = request.app["db"]
    try:
        with db.session() as session:
            repo = PlayerRepository(session)
            deleted_count = repo.delete_all(guild_id=target_guild)
            return web.json_response({
                "success": True,
                "deleted_count": deleted_count,
                "guild_id": target_guild,
            })
    except Exception as exc:
        logger.exception("Error clearing player data")
        return web.json_response({"error": str(exc)}, status=500)


async def handle_import_players_csv(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    target_guild = get_target_guild_id(request, user)
    if target_guild is None and user.get("role") != "owner":
        return web.json_response({"error": "You do not have access to this server."}, status=403)
    guild_to_set = target_guild if target_guild and target_guild != "*" else None

    raw_bytes: bytes = b""
    filename: str = ""
    json_csv_text: str = ""

    content_type = request.content_type.lower()
    if "multipart/form-data" in content_type:
        reader = await request.multipart()
        while True:
            field = await reader.next()
            if field is None:
                break
            if field.name in ("file", "csv", "csv_file"):
                filename = field.filename or ""
                raw_bytes = await field.read()
                break
    elif "application/json" in content_type:
        try:
            body = await request.json()
            json_csv_text = str(body.get("csv_text", "")).strip()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)
    else:
        raw_bytes = await request.read()

    if not raw_bytes and not json_csv_text:
        return web.json_response({"error": "No file or CSV content provided."}, status=400)

    db = request.app["db"]
    try:
        with db.session() as session:
            importer = CsvImporter(session)
            if raw_bytes:
                result = importer.import_file_bytes(raw_bytes, filename=filename, guild_id=guild_to_set)
            else:
                result = importer.import_text(json_csv_text, guild_id=guild_to_set)
            return web.json_response(result.to_dict())
    except Exception as exc:
        logger.exception("Error during roster file import")
        return web.json_response({"error": str(exc)}, status=500)


TEMPLATE_CSV_CONTENT = (
    "In-Game Name,Game ID,March Limit,Discord Username,Infantry FC,Infantry Helios,Lancers FC,Lancers Helios,Marksman FC,Marksman Helios,Jessie,Patrick,Jasser,Seoyoon\n"
    "LordVader,10001,165000,vader_01,30,Yes,28,No,29,150k,5,4,4,5\n"
    "CommanderLuke,10002,150000,luke_sky,25,No,25,No,25,No,4,5,3,4\n"
    "Solo,10003,160000,,28,No,28,Yes,28,No,5,3,4,3\n"
)


async def handle_download_template_csv(request: web.Request) -> web.Response:
    return web.Response(
        text=TEMPLATE_CSV_CONTENT,
        content_type="text/csv",
        charset="utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="alliance_roster_template.csv"',
        },
    )


# --- Formation Calculation Endpoint ---

async def handle_calculate(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    target_guild = get_target_guild_id(request, user)
    if target_guild is None and user.get("role") != "owner":
        return web.json_response({"error": "You do not have access to this server."}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    raw_mode = str(data.get("mode", "attack")).strip().lower()
    raw_formation = str(data.get("formation_type", "rally")).strip().lower()
    capacity_val = data.get("capacity")
    raw_ratio = data.get("ratio", {})

    try:
        mode = Mode(raw_mode)
    except ValueError:
        return web.json_response({"error": "Invalid mode (must be attack or defence)"}, status=400)

    try:
        formation_type = FormationType(raw_formation)
    except ValueError:
        return web.json_response({"error": "Invalid formation_type (must be rally or garrison)"}, status=400)

    try:
        capacity = int(capacity_val)
    except (TypeError, ValueError):
        return web.json_response({"error": "Capacity must be a positive whole number"}, status=400)

    try:
        ratio = {
            TroopType.INFANTRY: float(raw_ratio.get("infantry", 0)),
            TroopType.LANCERS: float(raw_ratio.get("lancers", 0)),
            TroopType.MARKSMAN: float(raw_ratio.get("marksman", 0)),
        }
    except (TypeError, ValueError):
        return web.json_response({"error": "Ratio percentages must be numbers"}, status=400)

    raw_joiners = data.get("target_joiners") or data.get("joiners")
    target_joiners: Optional[list[str]] = None
    if isinstance(raw_joiners, list):
        target_joiners = [str(h).strip() for h in raw_joiners if str(h).strip()]

    raw_cap_id = data.get("captain_id")
    captain_id: Optional[int] = None
    if raw_cap_id is not None and str(raw_cap_id).strip() != "":
        try:
            captain_id = int(raw_cap_id)
        except ValueError:
            captain_id = None

    raw_cap_heroes = data.get("captain_heroes") or []
    captain_heroes: list[str] = []
    if isinstance(raw_cap_heroes, list):
        captain_heroes = [str(h).strip() for h in raw_cap_heroes if str(h).strip()]

    alliance_tag_filter = str(data.get("alliance_tag", "")).strip()

    db = request.app["db"]
    config: RankingConfig = request.app["config"]

    with db.session() as session:
        repo = PlayerRepository(session)
        service = FormationService(repo, config)
        try:
            result = service.calculate(
                mode=mode,
                formation_type=formation_type,
                ratio=ratio,
                capacity=capacity,
                captain_id=captain_id,
                captain_heroes=captain_heroes,
                target_joiners=target_joiners,
                guild_id=target_guild if target_guild and target_guild != "*" else None,
                alliance_tag=alliance_tag_filter or None,
            )

        except (InvalidRatioError, InvalidCapacityError) as exc:
            return web.json_response({"error": str(exc)}, status=400)

        # Structure response for UI visualization
        total_assigned = sum(result.final.values())
        base_cap = result.base_capacity or capacity
        target_cap = result.target_capacity or capacity
        fill_pct = round((total_assigned / base_cap * 100), 2) if base_cap > 0 else 0
        garrison_gap = max(0, target_cap - total_assigned) if formation_type == FormationType.GARRISON else 0

        # Collect FC levels and helios for selected players
        player_db_map = {p.id: p for p in repo.list_all()}

        allocations = []
        for player_summary in result.selected_players:
            p_obj = player_db_map.get(player_summary.player_id)
            p_levels = [t.level for t in p_obj.troop_profiles if t.level is not None] if p_obj else []
            p_avg_fc = round(sum(p_levels) / len(p_levels)) if p_levels else None
            p_helios = any(t.helios for t in p_obj.troop_profiles) if p_obj else False

            for troop_type, amount in player_summary.contributions.items():
                allocations.append({
                    "player_id": player_summary.player_id,
                    "player_name": player_summary.player_name,
                    "troop_type": troop_type.value,
                    "amount": amount,
                    "fc_level": p_avg_fc,
                    "helios": p_helios,
                })

        joiner_recs = [
            {
                "slot": jr.slot,
                "player_id": jr.player_id,
                "player_name": jr.player_name,
                "hero_name": jr.hero_name,
                "stars": jr.stars,
                "skill_level": jr.skill_level,
                "buff_description": jr.buff_description,
            }
            for jr in (result.joiners or [])
        ]

        from bot.recommendations.hero_data import HERO_BUFF_DESCRIPTIONS
        cap_hero_buffs = [
            {
                "hero": h,
                "buff": HERO_BUFF_DESCRIPTIONS.get(h.lower(), "Expedition Skill Buff")
            }
            for h in captain_heroes
        ]

        return web.json_response({
            "mode": mode.value,
            "formation_type": formation_type.value,
            "capacity": capacity,
            "captain_id": captain_id,
            "captain_heroes": captain_heroes,
            "captain_hero_buffs": cap_hero_buffs,
            "avg_fc_level": result.avg_fc_level,
            "base_capacity": base_cap,
            "target_capacity": target_cap,
            "garrison_gap": garrison_gap,
            "total_assigned": total_assigned,
            "fill_percentage": fill_pct,
            "status": result.status.value,
            "deviation": {t.value: round(v, 2) for t, v in result.deviation.items()},
            "deviation_sum": round(sum(abs(v) for v in result.deviation.values()), 2),
            "target_ratios": {t.value: round(ratio[t], 2) for t in TroopType},
            "targets": {t.value: result.target[t] for t in TroopType},
            "actuals": {t.value: result.final[t] for t in TroopType},
            "actual_ratios": {t.value: round(result.actual_ratio[t], 2) for t in TroopType},
            "players_count": len(result.selected_players),
            "players": [
                {
                    "player_id": p.player_id,
                    "player_name": p.player_name,
                    "total": p.total,
                    "contributions": {t.value: amt for t, amt in p.contributions.items()},
                    "fc_level": (round(sum([t.level for t in player_db_map[p.player_id].troop_profiles if t.level is not None]) / len([t.level for t in player_db_map[p.player_id].troop_profiles if t.level is not None])) if (p.player_id in player_db_map and [t.level for t in player_db_map[p.player_id].troop_profiles if t.level is not None]) else None),
                    "helios": (any(t.helios for t in player_db_map[p.player_id].troop_profiles) if p.player_id in player_db_map else False),
                }
                for p in result.selected_players
            ],
            "allocations": allocations,
            "joiner_recommendations": joiner_recs,
        })


# --- Formation Presets Endpoint ---

async def handle_get_presets(request: web.Request) -> web.Response:
    """Return all Gen 1-12 + Extreme formation presets for the UI dropdown."""
    presets = [p.to_dict() for p in FORMATION_GUIDE_PRESETS]
    return web.json_response(presets)


# --- Hero Catalog & Presets Endpoint ---

HERO_CATALOG = [
    # Infantry Heroes
    {"name": "Sergey",     "role": "defence", "troop_type": "infantry", "buff": "+20% Defense (Skill 5)",               "gen_introduced": 1},
    {"name": "Jeronimo",   "role": "caller",  "troop_type": "infantry", "buff": "+25% Attack & Rally Damage Boost",     "gen_introduced": 1},
    {"name": "Flint",      "role": "defence", "troop_type": "infantry", "buff": "+20% Infantry Defense & Burn",         "gen_introduced": 1},
    {"name": "Natalia",    "role": "caller",  "troop_type": "infantry", "buff": "+15% Rally Defense & Stun",            "gen_introduced": 1},
    {"name": "Ling Xue",   "role": "defence", "troop_type": "infantry", "buff": "+20% Defense (Skill 5)",               "gen_introduced": 1},
    {"name": "Logan",      "role": "defence", "troop_type": "infantry", "buff": "Frontline HP Scaling & Self-Healing", "gen_introduced": 3},
    {"name": "Ahmose",     "role": "defence", "troop_type": "infantry", "buff": "Frontline Shield & Counter-strike",    "gen_introduced": 4},
    {"name": "Hector",     "role": "defence", "troop_type": "infantry", "buff": "+20% Infantry HP & Shield",            "gen_introduced": 4},
    {"name": "Wu Ming",    "role": "defence", "troop_type": "infantry", "buff": "Infantry Absolute Shield",             "gen_introduced": 6},
    {"name": "Gatot",      "role": "defence", "troop_type": "infantry", "buff": "Lancer Breaker & Momentum",            "gen_introduced": 7},
    {"name": "Edith",      "role": "defence", "troop_type": "infantry", "buff": "Frontline Defensive Aegis & Shielding","gen_introduced": 7},
    {"name": "Bradley",    "role": "defence", "troop_type": "infantry", "buff": "Infantry Block & Counter-blow",        "gen_introduced": 7},
    {"name": "Magnus",     "role": "defence", "troop_type": "infantry", "buff": "Ironclad Defense & Sustain",           "gen_introduced": 9},

    # Lancer Heroes
    {"name": "Jessie",     "role": "attack",  "troop_type": "lancer",   "buff": "+25% Damage Dealt (Skill 5)",          "gen_introduced": 1},
    {"name": "Molly",      "role": "caller",  "troop_type": "lancer",   "buff": "+15% Skill Damage & Stun",             "gen_introduced": 1},
    {"name": "Philly",     "role": "defence", "troop_type": "lancer",   "buff": "Continuous Rally Health Regeneration", "gen_introduced": 2},
    {"name": "Mia",        "role": "attack",  "troop_type": "lancer",   "buff": "+20% Lancer Damage & Strike",          "gen_introduced": 3},
    {"name": "Reina",      "role": "attack",  "troop_type": "lancer",   "buff": "Normal Attack Damage Multiplier",     "gen_introduced": 4},
    {"name": "Norah",      "role": "attack",  "troop_type": "lancer",   "buff": "Enemy Damage Reduction & Attack boost","gen_introduced": 5},
    {"name": "Renee",      "role": "attack",  "troop_type": "lancer",   "buff": "Lancer Cavalry Penetration",           "gen_introduced": 6},
    {"name": "Gordon",     "role": "defence", "troop_type": "lancer",   "buff": "Lancer Charge & Armor Vulnerability",  "gen_introduced": 7},
    {"name": "Hendrik",    "role": "attack",  "troop_type": "lancer",   "buff": "Lethality boost & Ranged Amplification","gen_introduced": 8},
    {"name": "Sonya",      "role": "defence", "troop_type": "lancer",   "buff": "Lancer Defense & Armor Reinforcement", "gen_introduced": 8},
    {"name": "Fred",       "role": "attack",  "troop_type": "lancer",   "buff": "Lancer Critical Surge",                "gen_introduced": 9},

    # Marksman Heroes
    {"name": "Jasser",     "role": "attack",  "troop_type": "marksman", "buff": "+25% Damage Dealt (Skill 5)",          "gen_introduced": 1},
    {"name": "Seoyoon",    "role": "attack",  "troop_type": "marksman", "buff": "+25% Attack (Skill 5)",                "gen_introduced": 1},
    {"name": "Bahiti",     "role": "attack",  "troop_type": "marksman", "buff": "+20% Marksman Precision",             "gen_introduced": 1},
    {"name": "Zinman",     "role": "caller",  "troop_type": "marksman", "buff": "Defense & Rally March Speed",          "gen_introduced": 1},
    {"name": "Patrick",    "role": "defence", "troop_type": "marksman", "buff": "+25% HP (Skill 5)",                    "gen_introduced": 1},
    {"name": "Alonso",     "role": "attack",  "troop_type": "marksman", "buff": "AoE Burst & Backline Disruption",      "gen_introduced": 2},
    {"name": "Greg",       "role": "attack",  "troop_type": "marksman", "buff": "+20% Marksman Attack",                 "gen_introduced": 3},
    {"name": "Lynn",       "role": "attack",  "troop_type": "marksman", "buff": "Marksman Critical Boost",              "gen_introduced": 4},
    {"name": "Gwen",       "role": "attack",  "troop_type": "marksman", "buff": "Backline Armor Piercing",            "gen_introduced": 5},
    {"name": "Wayne",      "role": "attack",  "troop_type": "marksman", "buff": "+25% Rally Attack & Shield",           "gen_introduced": 6},
    {"name": "Xura",       "role": "attack",  "troop_type": "marksman", "buff": "+25% Marksman Penetration DPS",       "gen_introduced": 7},
    {"name": "Blanchette", "role": "attack",  "troop_type": "marksman", "buff": "Marksman Vulnerability & Critical Stun","gen_introduced": 10},
    {"name": "Teresa",     "role": "attack",  "troop_type": "marksman", "buff": "Marksman Lethality Amplification",     "gen_introduced": 10},
]

HERO_PRESETS = [
    {
        "id": "attack_all_out",
        "name": "⚡ Attack All-Out",
        "heroes": ["Jessie", "Jasser", "Seoyoon", "Norah"],
        "description": "Max Damage (+50%) & Attack (+25%)",
    },
    {
        "id": "fortress_defense",
        "name": "🛡️ Fortress Defense",
        "heroes": ["Patrick", "Sergey", "Ling Xue", "Ahmose"],
        "description": "Max HP (+25%), Defense (+40%) & Shields",
    },
    {
        "id": "mixed_svs",
        "name": "⚔️ Mixed / SvS",
        "heroes": ["Jessie", "Seoyoon", "Patrick", "Sergey"],
        "description": "Balanced Rally & Reinforcement Buffs",
    },
    {
        "id": "double_damage",
        "name": "🔥 Double Jessie",
        "heroes": ["Jessie", "Jasser", "Jessie", "Seoyoon"],
        "description": "Double Jessie Skill 5 for maximum damage spike",
    },
    {
        "id": "double_hp",
        "name": "🏰 Double Patrick",
        "heroes": ["Patrick", "Sergey", "Ling Xue", "Patrick"],
        "description": "Double Patrick Skill 5 for maximum HP sustain",
    },
]


async def handle_get_heroes(request: web.Request) -> web.Response:
    """Return catalog of heroes, presets, and any custom heroes registered in player database."""
    db = request.app["db"]
    known_names = {h["name"].lower() for h in HERO_CATALOG}
    custom_heroes = []
    try:
        with db.session() as session:
            from bot.database.models.player import PlayerHero
            rows = session.query(PlayerHero.hero_name).distinct().all()
            for (r_name,) in rows:
                clean = str(r_name).strip()
                if clean and clean.lower() not in known_names:
                    known_names.add(clean.lower())
                    custom_heroes.append({
                        "name": clean,
                        "role": "custom",
                        "buff": "Expedition Skill Buff",
                    })
    except Exception as exc:
        logger.warning("Could not query distinct heroes from DB: %s", exc)

    return web.json_response({
        "heroes": HERO_CATALOG + custom_heroes,
        "presets": HERO_PRESETS,
    })


# --- Rules Config Endpoints ---

async def handle_get_rules(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)

    settings: Settings = request.app["settings"]
    rules_path: Path = settings.rules_config_path
    if rules_path.is_file():
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return web.json_response(data)
        except Exception as exc:
            return web.json_response({"error": f"Failed to read rules: {exc}"}, status=500)

    # Return default config serialized
    config: RankingConfig = request.app["config"]
    return web.json_response({
        "attack_importance": [t.value for t in config.attack_importance],
        "defence_importance": [t.value for t in config.defence_importance],
        "helios_bonus": config.helios_bonus,
        "fc_weight": config.fc_weight,
    })


async def handle_update_rules(request: web.Request) -> web.Response:
    user = get_current_user(request)
    if not user or user["role"] != "owner":
        return web.json_response({"error": "Only the Bot Owner can modify optimizer rules."}, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    settings: Settings = request.app["settings"]
    rules_path: Path = settings.rules_config_path
    try:
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        with open(rules_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        # Reload config in app
        request.app["config"] = load_config(rules_path)
        return web.json_response({"success": True, "config": data})
    except Exception as exc:
        return web.json_response({"error": f"Failed to save rules: {exc}"}, status=500)


# --- War Room / Attendance Endpoints ---

def _get_attendance_set(request: web.Request, guild_id: Optional[str]) -> set:
    key = guild_id or "global"
    if "attendance" not in request.app:
        request.app["attendance"] = {}
    if key not in request.app["attendance"]:
        request.app["attendance"][key] = set()
    return request.app["attendance"][key]

async def handle_get_attendance(request: web.Request) -> web.Response:
    """Returns the set of currently checked-in player IDs."""
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)
    
    target_guild = get_target_guild_id(request, user)
    attendance_set = _get_attendance_set(request, target_guild)
    
    return web.json_response({
        "status": "success",
        "checked_in_ids": list(attendance_set),
        "total_online": len(attendance_set)
    })

async def handle_attendance_check_in(request: web.Request) -> web.Response:
    """Toggles online check-in status for specific players."""
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)
    
    target_guild = get_target_guild_id(request, user)
    
    try:
        data = await request.json()
        player_ids = set(data.get("player_ids", []))
        is_online = bool(data.get("is_online", True))
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    
    attendance_set = _get_attendance_set(request, target_guild)
        
    if is_online:
        attendance_set.update(player_ids)
    else:
        attendance_set.difference_update(player_ids)
        
    return web.json_response({
        "status": "success",
        "total_online": len(attendance_set)
    })

async def handle_attendance_select_all(request: web.Request) -> web.Response:
    """Selects all given players as online."""
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)
    
    target_guild = get_target_guild_id(request, user)
    
    try:
        data = await request.json()
        all_ids = set(data.get("player_ids", []))
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
        
    key = target_guild or "global"
    if "attendance" not in request.app:
        request.app["attendance"] = {}
    request.app["attendance"][key] = all_ids
    
    return web.json_response({
        "status": "success", 
        "total_online": len(all_ids)
    })

async def handle_attendance_reset(request: web.Request) -> web.Response:
    """Clears all online check-ins."""
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)
        
    target_guild = get_target_guild_id(request, user)
    key = target_guild or "global"
    if "attendance" not in request.app:
        request.app["attendance"] = {}
    request.app["attendance"][key] = set()
    
    return web.json_response({
        "status": "success",
        "total_online": 0
    })

async def handle_calculate_rallies(request: web.Request) -> web.Response:
    """Executes multi-rally calculations dynamically filtering for online players."""
    user = get_current_user(request)
    if not user:
        return web.json_response({"error": "Unauthorized"}, status=401)
        
    try:
        data = await request.json()
        event_scope_str = data.get("event_scope", "state")
        alliance_tag = data.get("alliance_tag")
        rally_count = int(data.get("rally_count", 3))
        generation = int(data.get("generation", 1))
        online_only = bool(data.get("online_only", True))
        rally_captains = data.get("rally_captains") or []
        default_cap = data.get("capacity")
        if default_cap:
            for rc in rally_captains:
                if isinstance(rc, dict) and not rc.get("capacity"):
                    rc["capacity"] = default_cap
    except Exception:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)
        
    from bot.recommendations.schemas import EventScope
    from bot.recommendations.assignment_engine import MultiRallyAssignmentEngine
    
    try:
        scope = EventScope(event_scope_str)
    except ValueError:
        return web.json_response({"error": f"Invalid event scope: {event_scope_str}"}, status=400)
        
    target_guild = get_target_guild_id(request, user)
    
    with request.app["db"].session() as session:
        repo = PlayerRepository(session)
        if target_guild:
            players_db = repo.list_all(guild_id=target_guild)
        else:
            players_db = repo.list_all()
            
    # Serialize players for engine
    pool = []
    for p in players_db:
        player_dict = {
            "id": p.id,
            "name": p.name,
            "alliance_tag": p.alliance_tag,
            "march_limit": p.march_limit,
            "troops": {}
        }
        for troop in p.troop_profiles:
            player_dict["troops"][troop.troop_type.value] = {
                "level": troop.level,
                "helios": troop.helios,
                "helios_quantity": troop.helios_quantity,
            }
        pool.append(player_dict)
        
    attendance_set = _get_attendance_set(request, target_guild)
    
    results = MultiRallyAssignmentEngine.process_assignments(
        players=pool,
        rally_count=rally_count,
        generation=generation,
        scope=scope,
        alliance_tag=alliance_tag,
        online_only=online_only,
        attendance=attendance_set,
        rally_captains=rally_captains
    )
    
    # Optionally post to Discord channel if requested by user logic
    post_to_discord = bool(data.get("post_to_discord", False))
    if post_to_discord and target_guild and request.app.get("bot"):
        bot = request.app["bot"]
        # In a real implementation we'd let them pick a channel, but for now just returning to web UI
        pass
    
    return web.json_response({
        "status": "success",
        "rallies": [r.to_dict() for r in results]
    })

