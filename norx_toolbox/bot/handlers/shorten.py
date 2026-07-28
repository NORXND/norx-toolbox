import secrets
import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from norx_toolbox.bot.helpers import Arg, escape_md, require_user, send_error, with_args
from norx_toolbox.config import config
from norx_toolbox.db import get_dashboard_token, get_db
from norx_toolbox.utils.duration import parse_duration

router = Router(name="shorten")


@router.message(Command("shorten"))
@require_user
@with_args(Arg("url"), Arg("expires", optional=True, default=None))
async def cmd_shorten(
    message: Message, url: str, expires: str | None, user_id: int, **_
):
    token = secrets.token_urlsafe(6)
    expires_at = None
    if expires:
        try:
            expires_at = time.time() + parse_duration(expires)
        except ValueError as e:
            await send_error(message, "Invalid expires value", e)
            return

    with get_db() as conn:
        conn.execute(
            "INSERT INTO short_links (token, target_url, user_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
            (token, url, user_id, time.time(), expires_at),
        )

    dash_token = get_dashboard_token(user_id)
    reply = f"{config.SHORTEN_BASE}/{token}"
    if expires_at is None:
        reply += (
            "\n(permanent — manage at "
            + f"{config.PUBLIC_URL}/workspace/dashboard/{dash_token})"
        )
    await message.answer(escape_md(reply))
