import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from aiogram.types import FSInputFile

from norx_toolbox.bot.helpers import escape_md

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import Message

from .storage import store_for_download

MAX_TELEGRAM_SIZE = 50 * 1024 * 1024


async def deliver_result(message: "Message", filepath: Path):
    size = filepath.stat().st_size
    workdir = filepath.parent

    if size <= MAX_TELEGRAM_SIZE:
        await message.answer_document(FSInputFile(filepath))
        filepath.unlink(missing_ok=True)
    else:
        stored = store_for_download(filepath)
        mb = size / 1024 / 1024
        await message.answer(
            escape_md(
                f"File is {mb:.1f}MB, too big for Telegram.\n"
                f"Here's a link (expires in 1h):\n{stored.url}"
            )
        )

    shutil.rmtree(workdir, ignore_errors=True)


async def deliver_to_chat(bot: "Bot", chat_id: int, filepath: Path):
    size = filepath.stat().st_size
    if size <= MAX_TELEGRAM_SIZE:
        await bot.send_document(chat_id, FSInputFile(filepath))
    else:
        stored = store_for_download(filepath)
        await bot.send_message(
            chat_id, escape_md(f"File is too big for Telegram, link (1h): {stored.url}")
        )
