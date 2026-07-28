import asyncio
import logging
import signal
import sys
from os import getenv

from dotenv import load_dotenv
from hypercorn.asyncio import serve
from hypercorn.config import Config

from norx_toolbox.bot.main import bot_start, prepare_bot
from norx_toolbox.config import config
from norx_toolbox.db import init_db
from norx_toolbox.delivery.storage import (sweep_expired,
                                           sweep_orphaned_tempdirs, sweep_sessions)
from norx_toolbox.task_manager import TaskManager
from norx_toolbox.web.app import app as quart_app

load_dotenv()

async def main():
    init_db()
    bot = prepare_bot()

    hypercorn_config = Config()
    hypercorn_config.bind = [config.WEB_BIND]

    stop_event = asyncio.Event()

    def _request_stop(*_):
        stop_event.set()

    # register handlers for graceful shutdown signals
    loop = asyncio.get_running_loop()
    try:
        # works on Unix; Windows doesn't support add_signal_handler for SIGINT in the same way
        loop.add_signal_handler(signal.SIGINT, _request_stop)
        loop.add_signal_handler(signal.SIGTERM, _request_stop)
    except NotImplementedError:
        # Windows fallback — rely on asyncio.run's default KeyboardInterrupt handling instead
        pass

    task_manager = TaskManager(bot, quart_app)
    quart_app.set_task_manager(task_manager)

    try:
        await asyncio.gather(
            bot_start(bot, task_manager),
            serve(quart_app, hypercorn_config, shutdown_trigger=stop_event.wait),
            sweep_expired(),
            sweep_orphaned_tempdirs(),
            sweep_sessions(),
        )
    except asyncio.CancelledError:
        pass
    finally:
        await bot.session.close()  # clean up aiohttp session aiogram opens

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())