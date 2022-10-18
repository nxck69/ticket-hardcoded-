import asyncio
import datetime
import logging
import os
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Any

import hikari
import lightbulb
import miru
from humanize import precisedelta

from config import CONFIG
from utils import utcnow

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s]: [ %(levelname)8s ] [ %(name)20s ] -> %(message)s",
)
logger = logging.getLogger("bot")

INTENTS = (
    hikari.Intents.GUILDS
    | hikari.Intents.GUILD_MEMBERS
    | hikari.Intents.DM_MESSAGES
)

CACHE_SETTINGS = hikari.impl.CacheSettings(
    components=(
        hikari.api.CacheComponents.ROLES
        | hikari.api.CacheComponents.MEMBERS
        | hikari.api.CacheComponents.GUILDS
        | hikari.api.CacheComponents.GUILD_CHANNELS
        | hikari.api.CacheComponents.ME
    ),
    max_messages=0,
    max_dm_channel_ids=0,
)


class Bot(lightbulb.BotApp):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.loop: AbstractEventLoop = asyncio.get_event_loop()
        self._uptime: datetime.datetime = utcnow()
        self.CWD: Path = Path(__file__).resolve().parent
        self.display_avatar_url: hikari.URL | None = None
        self.footer_text: str = "https://killfeed.xyz | DayZ++"

        miru.load(self)

        self.subscribe(hikari.StartedEvent, self.on_started)
        self.subscribe(hikari.StoppingEvent, self.on_stopping)

        self.load_extensions_from("plugins", recursive=True)

    @property
    def uptime(self) -> str:
        return precisedelta(
            int((self._uptime - utcnow()).total_seconds()),
            format="%0.0f",
        )

    async def on_started(self, _event: hikari.StartedEvent) -> None:
        self.display_avatar_url = self.get_me().display_avatar_url
        logger.info("Bot started successfully.")

    async def on_stopping(self, _: hikari.StoppedEvent) -> None:
        logger.info("Shutting the Bot down and closing DB connections.")
        logger.info(
            "Shut the Bot down and closed all DB connections successfully."
        )


async def run() -> None:
    bot = Bot(
        prefix=CONFIG.BOT_PREFIX,
        token=CONFIG.DISCORD_BOT_TOKEN,
        help_slash_command=False,
        intents=INTENTS,
        cache_settings=CACHE_SETTINGS,
        default_enabled_guilds=(int(os.environ["GUILD_ID"]),),
        owner_ids=(int(os.environ["BOT_OWNER_ID"]),),
        delete_unbound_commands=False,
    )

    await bot.start()
    bot.loop.run_forever()
