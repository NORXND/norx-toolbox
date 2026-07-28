import tempfile
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from norx_toolbox.bot.helpers import (
    Arg,
    code,
    download_attachment,
    escape_md,
    extract_attachment,
    require_user,
    send_error,
    with_args,
)
from norx_toolbox.config import config
from norx_toolbox.coverters.registry import NoConverterError, convert_file
from norx_toolbox.delivery.deliver import deliver_result
from norx_toolbox.delivery.storage import create_upload_session
from norx_toolbox.task_manager import TaskKind, TaskManager

router = Router(name="convert")


@router.message(Command("convert"))
@require_user
@with_args(Arg("format"))
async def cmd_convert(
    message: Message, format: str, user_id: int, task_manager: TaskManager, **_
):
    tg_file = extract_attachment(message)
    if tg_file is None:
        session = create_upload_session(
            "convert", {"format": format}, user_id, message.chat.id
        )
        await message.answer(
            escape_md(
                f"No file attached — or it might be too large for Telegram to hand off to me (20MB limit on downloads).\n\n"
                f"Upload directly here instead:\n{config.PUBLIC_URL}/workspace/upload/{session.token}"
            )
        )
        return

    async def do_convert():
        workdir = Path(tempfile.mkdtemp(prefix="convert_"))
        local_path = await download_attachment(message, tg_file)

        try:
            return await convert_file(local_path, format, workdir)
        except NoConverterError as e:
            raise RuntimeError(str(e))

    async def on_done(job, result_path: Path):
        await deliver_result(message, result_path)

    async def on_error(job, exc: Exception):
        await send_error(message, "Conversion failed", exc)

    task_manager.submit(user_id, TaskKind.CONVERT, do_convert, on_done, on_error)
    await message.answer(escape_md(f"Converting to ") + code(format) + escape_md(f"…"))
