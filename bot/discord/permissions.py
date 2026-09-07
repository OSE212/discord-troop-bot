"""Role-based permission checks (spec section 23).

V1 keeps this simple: Discord server roles named via
ADMIN_ROLE_NAME / CALCULATOR_ROLE_NAME in the environment. Server
admins (Manage Guild / Administrator) are always treated as bot
admins too, so there's no lockout risk if the named role hasn't been
created yet.
"""
from __future__ import annotations

import discord

from bot.settings import settings


def _has_role(member: discord.Member, role_name: str) -> bool:
    return any(role.name == role_name for role in member.roles)


def is_admin(member: discord.Member) -> bool:
    if isinstance(member, discord.Member):
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
        return _has_role(member, settings.admin_role_name)
    return False


def is_calculator(member: discord.Member) -> bool:
    """Authorized to run /calculate: admins, or anyone with the
    calculator role (spec section 23: "Authorized
    calculator/admin")."""
    if is_admin(member):
        return True
    if isinstance(member, discord.Member):
        return _has_role(member, settings.calculator_role_name)
    return False


class NotAuthorized(Exception):
    """Raised by command handlers when a permission check fails."""
