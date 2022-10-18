import os


class Config:
    __slots__ = ()

    DEVELOPMENT_MODE: bool = False

    DISCORD_BOT_TOKEN: str = (
        os.environ["DISCORD_BOT_TOKEN__DEVELOPMENT"]
        if DEVELOPMENT_MODE
        else os.environ["DISCORD_BOT_TOKEN"]
    )
    BOT_PREFIX: str = "!" if DEVELOPMENT_MODE else "!"
