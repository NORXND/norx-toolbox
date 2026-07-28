import inspect
import re
import shlex
import tempfile
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from aiogram.filters import CommandObject
from aiogram.types import Animation, Audio, Document, Message, PhotoSize, Video, VideoNote, Voice

from norx_toolbox.bot.markdown import bold, code, code_block, escape_md


class ArgError(Exception):
    """Raised when arguments don't match what's expected - message shown to user."""

    pass


@dataclass
class Arg:
    name: str
    type: Callable[[str], Any] = str
    optional: bool = False
    default: Any = None


def parse_args(raw: str | None, *specs: Arg) -> dict[str, Any]:
    tokens = shlex.split(raw) if raw else []
    result = {}

    for i, spec in enumerate(specs):
        if i < len(tokens):
            try:
                result[spec.name] = spec.type(tokens[i])
            except ValueError:
                raise ArgError(
                    f"'{tokens[i]}' isn't a valid {spec.type.__name__} for {spec.name}"
                )
        elif spec.optional:
            result[spec.name] = spec.default
        else:
            raise ArgError(f"Missing required argument: {spec.name}")

    return result


def build_usage(command_name: str, specs: tuple[Arg, ...]) -> str:
    parts = [f"/{command_name}"]
    for spec in specs:
        if spec.optional:
            default_hint = f"={spec.default}" if spec.default is not None else ""
            parts.append(f"[{spec.name}{default_hint}]")
        else:
            parts.append(spec.name)
    return " ".join(parts)


def _filter_kwargs(handler, kwargs: dict) -> dict:
    """Keep only kwargs that `handler` actually declares, so unrelated aiogram-injected
    context (dispatcher, bot, etc.) doesn't get forwarded and blow up on unexpected kwargs.
    """
    sig = inspect.signature(handler)
    accepted = set(sig.parameters.keys())
    # if handler itself takes **kwargs, just pass everything through
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        return kwargs
    return {k: v for k, v in kwargs.items() if k in accepted}


def with_args(*specs: Arg, command_name: str | None = None):
    def decorator(handler):
        name = command_name or handler.__name__.removeprefix("cmd_")
        usage = build_usage(name, specs)

        async def wrapper(message: Message, command: CommandObject, *a, **kw):
            try:
                parsed = parse_args(command.args, *specs)
            except ArgError as e:
                await message.answer(
                    escape_md(f"⚠️ ")
                    + escape_md(str(e))
                    + escape_md(f"\nUsage: ")
                    + code(usage),
                )
                return
            combined = {**parsed, **kw}
            filtered = _filter_kwargs(handler, combined)
            return await handler(message, *a, **filtered)

        return wrapper

    return decorator


def require_user(handler):
    @wraps(handler)
    async def wrapper(message: Message, *a, **kw):
        if message.from_user is None:
            await message.answer(
                escape_md(
                    "⚠️ This command can only be used in private chats with a user."
                )
            )
            return
        combined = {**kw, "user_id": message.from_user.id}
        filtered = _filter_kwargs(handler, combined)
        return await handler(message, *a, **filtered)

    return wrapper


def extract_attachment(
    message: Message,
) -> Document | Video | Audio | Voice | VideoNote | Animation | PhotoSize | None:
    if message.photo:
        return message.photo[-1]  # largest available size
    return (
        message.document
        or message.video
        or message.audio
        or message.voice
        or message.video_note
        or message.animation
    )


def _url_safe_filename(name: str) -> str:
    """Convert a filename into a URL-safe and filesystem-safe string."""
    safe_name = re.sub(r"[^\w\.-]", "_", name)
    return re.sub(r"_+", "_", safe_name).strip("_")


async def download_attachment(message: Message, tg_file) -> Path:
    assert message.bot is not None
    workdir = Path(tempfile.mkdtemp(prefix="tg_"))

    file_name = getattr(tg_file, "file_name", None)
    if file_name:
        local_name = _url_safe_filename(file_name)
    else:
        base_id = _url_safe_filename(tg_file.file_id)
        if isinstance(tg_file, PhotoSize):
            local_name = f"{base_id}.jpg"  # Telegram always compresses photos to JPEG
        elif hasattr(tg_file, "duration"):
            local_name = f"{base_id}.ogg"  # voice notes / audio without a filename
        else:
            local_name = base_id

    local_path = workdir / local_name

    file_info = await message.bot.get_file(tg_file.file_id)
    if file_info.file_path is None:
        raise RuntimeError(
            "Telegram didn't provide a file path — file may be unavailable"
        )

    await message.bot.download_file(file_info.file_path, destination=local_path)
    return local_path


async def send_error(message: Message, title: str, exc: Exception):
    await message.answer(
        bold(title)+ "\n" + code_block(str(exc)[-1500:]),
    )
