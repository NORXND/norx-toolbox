import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from norx_toolbox.bot.helpers import (
    Arg,
    download_attachment,
    escape_md,
    extract_attachment,
    require_user,
    send_error,
    with_args,
)
from norx_toolbox.config import config
from norx_toolbox.db import get_dashboard_token, get_db
from norx_toolbox.utils.duration import parse_duration

router = Router(name="share")

DEFAULT_SHARE_SECONDS = 86400  # 1 day


@router.message(Command("share"))
@require_user
@with_args(Arg("expires", optional=True, default=None))
async def cmd_share(message: Message, expires: str | None, user_id: int, **_):
    tg_file = extract_attachment(message)
    if tg_file is None:
        await message.answer(escape_md("Attach a file to the /share message."))
        return

    try:
        ttl_seconds = parse_duration(expires) if expires else DEFAULT_SHARE_SECONDS
    except ValueError as e:
        await send_error(message, "Invalid expires value", e)
        return

    local_path = await download_attachment(message, tg_file)

    import secrets

    token = secrets.token_urlsafe(24)
    expires_at = time.time() + ttl_seconds

    with get_db() as conn:
        conn.execute(
            "INSERT INTO files (token, filename, path, user_id, chat_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                token,
                local_path.name,
                str(local_path),
                user_id,
                message.chat.id,
                time.time(),
                expires_at,
            ),
        )

    dash_token = get_dashboard_token(user_id)
    await message.answer(
        escape_md(
            f"{config.SHARE_BASE}/share/{token}/{local_path.name}\nExpires in {ttl_seconds // 3600}h — manage at {config.PUBLIC_URL}/workspace/dashboard/{dash_token}"
        )
    )
