from pathlib import Path
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from norx_toolbox.config import config
from norx_toolbox.bot.handlers.convert import download_attachment
from norx_toolbox.bot.handlers.download import escape_md, send_error
from norx_toolbox.bot.helpers import Arg, code, require_user, with_args
from norx_toolbox.coverters.providers import ffmpeg
from norx_toolbox.delivery.deliver import deliver_result
from norx_toolbox.delivery.storage import create_upload_session
from norx_toolbox.task_manager import TaskKind
from norx_toolbox.utils.duration import parse_timestamp

if TYPE_CHECKING:
    from norx_toolbox.task_manager import TaskManager

router = Router(name="trim")


@router.message(Command("trim"))
@require_user
@with_args(Arg("start", type=parse_timestamp), Arg("end", type=parse_timestamp))
async def cmd_trim(
    message: Message,
    start: str,
    end: str,
    user_id: int,
    task_manager: "TaskManager",
    **_,
):
    tg_file = message.video or message.document
    if tg_file is None:
        session = create_upload_session("trim", {"start": start, "end": end}, user_id, message.chat.id)
        await message.answer(
            escape_md(
                f"No file attached — or it might be too large for Telegram to hand off to me (20MB limit on downloads).\n\n"
                f"Upload directly here instead:\n{config.PUBLIC_URL}/workspace/upload/{session.token}"
            )
        )
        return

    async def do_trim():
        local_path = await download_attachment(message, tg_file)
        output_path = (
            local_path.parent / f"{local_path.stem}_trimmed.mp4"
        )  # always mp4 — matches trim()'s hardcoded h264/aac
        return await ffmpeg.trim(local_path, output_path, start, end)

    async def on_done(job, result_path: Path):
        await deliver_result(message, result_path)

    async def on_error(job, exc: Exception):
        await send_error(message, "Trim failed", exc)

    task_manager.submit(user_id, TaskKind.TRIM, do_trim, on_done, on_error)
    await message.answer(escape_md(f"Trimming {code(start)} → {code(end)}…"))
