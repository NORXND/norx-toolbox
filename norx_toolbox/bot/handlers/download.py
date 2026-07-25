import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from norx_toolbox.bot.helpers import (
    Arg,
    code,
    escape_md,
    require_user,
    send_error,
    with_args,
)
from norx_toolbox.coverters.providers import ffmpeg
from norx_toolbox.coverters.registry import convert_file
from norx_toolbox.delivery.deliver import deliver_result
from norx_toolbox.task_manager import TaskKind
from norx_toolbox.ytdlp import AUDIO_FORMATS, download_source

if TYPE_CHECKING:
    from norx_toolbox.task_manager import TaskManager

router = Router(name="download")


def _parse_timestamp(value: str) -> str:
    """Validate MM:SS or HH:MM:SS, return as-is for ffmpeg (which accepts both natively)."""
    parts = value.split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        raise ValueError("expected MM:SS or HH:MM:SS")
    return value


async def _do_download(
    url: str, format: str, start: str | None = None, end: str | None = None
) -> Path:
    """Shared core: download, optionally trim, then convert to target format."""
    source_path = await asyncio.to_thread(
        download_source, url, audio_only=(format in AUDIO_FORMATS)
    )

    if start and end:
        trimmed_path = source_path.parent / f"{source_path.stem}_trimmed.mp4"
        source_path = await ffmpeg.trim(source_path, trimmed_path, start, end)

    return await convert_file(source_path, format, source_path.parent)


@router.message(Command("download"))
@require_user
@with_args(Arg("url"), Arg("format", optional=True, default="mp4"))
async def cmd_download(
    message: Message,
    url: str,
    format: str,
    user_id: int,
    task_manager: "TaskManager",
    **_,
):
    async def on_done(job, result_path: Path):
        await deliver_result(message, result_path)

    async def on_error(job, exc: Exception):
        await send_error(message, "Download failed", exc)

    task_manager.submit(
        user_id,
        TaskKind.DOWNLOAD,
        lambda: _do_download(url, format),
        on_done,
        on_error,
    )
    await message.answer(
        escape_md(f"Queued your download from ") + code(url) + escape_md(f" in format ") + code(format) + escape_md(f".")
    )


@router.message(Command("download_trim"))
@require_user
@with_args(
    Arg("url"),
    Arg("start", type=_parse_timestamp),
    Arg("end", type=_parse_timestamp),
    Arg("format", optional=True, default="mp4"),
)
async def cmd_download_trim(
    message: Message,
    url: str,
    start: str,
    end: str,
    format: str,
    user_id: int,
    task_manager: "TaskManager",
    **_,
):
    async def on_done(job, result_path: Path):
        await deliver_result(message, result_path)

    async def on_error(job, exc: Exception):
        await send_error(message, "Download failed", exc)

    task_manager.submit(
        user_id,
        TaskKind.DOWNLOAD,
        lambda: _do_download(url, format, start, end),
        on_done,
        on_error,
    )
    await message.answer(
        escape_md(
            f"Queued your download from ") + code(url) + escape_md(f" with trim ") + code(start) + escape_md(f"-") + code(end) + escape_md(f" in format ") + code(format) + escape_md(f".")
        )
