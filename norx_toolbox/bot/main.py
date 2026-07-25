from os import getenv
from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

from norx_toolbox.bot.handlers import routers
from norx_toolbox.bot.markdown import code, escape_md

if TYPE_CHECKING:
    from aiogram.types import Message

    from norx_toolbox.bot.handlers.download import TaskManager

dp = Dispatcher()
dp.include_routers(*routers)


@dp.message(CommandStart())
async def command_start_handler(message: "Message") -> None:
    """
    This handler receives messages with `/start` command
    """
    lines = [
        escape_md(
            "NorxBox — a toolbox bot for stuff I do often and got tired of looking up sketchy sites for."
        ),
        "",
        "Available commands:",
        "",
        f"{code('/start')} — show this message",
        "",
        escape_md("Downloading:"),
        f"{code('/download <url> [format]')} — download video/audio, default format mp4",
        f"{code('/download_trim <url> <start> <end> [format]')} — download and trim in one step",
        escape_md("Just send a link with no command and it'll auto-download."),
        "",
        escape_md("Converting & editing (attach a file to these):"),
        f"{code('/convert <format>')} — convert an attached file",
        f"{code('/trim <start> <end>')} — trim an attached video/audio file",
        f"{code('/crop')} — crop an attached image/video via a web page",
        "",
        escape_md("Sharing:"),
        f"{code('/shorten <url> [duration]')} — shorten a URL, permanent by default",
        f"{code('/share [duration]')} — temporary file share link, 1 day by default",
        "",
        escape_md(
            "Made for private use only — if you see it, congrats, you are worthy or something."
        ),
        escape_md("Help or whatever: @norxnd"),
    ]

    await message.answer("\n".join(lines))

def prepare_bot() -> Bot:
    TOKEN = getenv("BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN env variable is not set")

    bot = Bot(
        token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
    )
    return bot


async def bot_start(bot: Bot, task_manager: "TaskManager") -> None:
    dp["task_manager"] = task_manager
    await dp.start_polling(bot)
