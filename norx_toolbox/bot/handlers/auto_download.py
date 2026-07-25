import re

from aiogram import F, Router
from aiogram.types import Message

from norx_toolbox.bot.handlers.download import _do_download  # reuse the shared core
from norx_toolbox.bot.helpers import escape_md, require_user, send_error, code
from norx_toolbox.delivery.deliver import deliver_result
from norx_toolbox.task_manager import TaskKind, TaskManager

router = Router(name="auto_download")

URL_RE = re.compile(r"https?://\S+")


@router.message(F.text.regexp(URL_RE.pattern))
@require_user
async def auto_download(message: Message, user_id: int, task_manager: TaskManager, **_):
    match = URL_RE.search(message.text or "")
    if not match:
        return
    url = match.group(0)

    async def on_done(job, result_path):
        await deliver_result(message, result_path)

    async def on_error(job, exc: Exception):
        await send_error(message, "Download failed", exc)

    task_manager.submit(
        user_id, TaskKind.DOWNLOAD, lambda: _do_download(url, "mp4"), on_done, on_error
    )
    await message.answer(escape_md(f"Downloading from ") + code(url) + escape_md(f"…"))
