"""Entrypoint: `python run.py` starts the Discord bot.

All configuration comes from environment variables (see .env.example).
"""
from __future__ import annotations

import logging
import sys

from bot.discord_bot import build_bot


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bot = build_bot()
    if not bot.settings.discord_token:
        print(
            "ERROR: DISCORD_TOKEN is not set. Copy .env.example to .env and "
            "fill in your bot token before running.",
            file=sys.stderr,
        )
        sys.exit(1)

    bot.run(bot.settings.discord_token)


if __name__ == "__main__":
    main()
