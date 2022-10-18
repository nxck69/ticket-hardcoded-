import asyncio
import logging
import os
from pathlib import Path

import nest_asyncio

from models.bot import run

logger = logging.getLogger(Path(__file__).stem)


def launch() -> None:
    loop = asyncio.get_event_loop()
    if os.name != "nt":
        import uvloop

        uvloop.install()

    loop.run_until_complete(run())


if __name__ == "__main__":
    nest_asyncio.apply()
    launch()
