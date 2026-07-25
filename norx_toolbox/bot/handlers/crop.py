from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from norx_toolbox.bot.helpers import (
    download_attachment,
    escape_md,
    extract_attachment,
    require_user,
)
from norx_toolbox.config import config
from norx_toolbox.delivery.storage import create_crop_session

router = Router(name="crop")


@router.message(Command("crop"))
@require_user
async def cmd_crop(message: Message, user_id: int, **_):
    tg_file = extract_attachment(message)
    if tg_file is None:
        await message.answer(
            escape_md("Attach an image or video to the /crop message.")
        )
        return

    local_path = await download_attachment(message, tg_file)
    is_video = message.video is not None or (
        message.document is not None and "video" in (message.document.mime_type or "")
    )

    session = create_crop_session(local_path, user_id, message.chat.id, is_video)

    await message.answer(
        escape_md(f"Open this link to crop:\n{config.PUBLIC_URL}/workspace/crop/{session.token}")
    )
