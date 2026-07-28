import asyncio
import secrets
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from norx_toolbox.config import config
from norx_toolbox.db import get_db

TEMP_JOB_MAX_AGE = 3 * 3600


@dataclass
class StoredFile:
    token: str
    filename: str
    path: Path
    expires_at: float

    @property
    def url(self) -> str:
        return f"{config.SHARE_BASE}/downloads/{self.token}/{self.filename}"


def store_for_download(src_path: Path) -> StoredFile:
    token = secrets.token_urlsafe(24)
    dest_dir = config.OUTPUT_DIR / token
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / src_path.name
    shutil.move(str(src_path), dest_path)

    return StoredFile(
        token=token,
        filename=src_path.name,
        path=dest_path,
        expires_at=time.time() + config.LINK_TTL_SECONDS,
    )


def resolve_download(token: str, filename: str) -> Path | None:
    dest = config.OUTPUT_DIR / token / filename
    return dest if dest.exists() else None


def resolve(token: str, filename: str) -> Path | None:
    """Look up a file by token, used by the Quart route. Returns None if missing/expired."""
    dest = config.OUTPUT_DIR / token / filename
    if not dest.exists():
        return None
    # expiry is enforced by the sweep, not checked here — sweep deletes the dir entirely
    return dest

async def sweep_sessions():
    """Cleans up expired crop/upload sessions."""
    while True:
        now = time.time()
        for token in list(_crop_sessions.keys()):
            if _crop_sessions[token].expires_at < now:
                del _crop_sessions[token]
        for token in list(_upload_sessions.keys()):
            if _upload_sessions[token].expires_at < now:
                del _upload_sessions[token]
        await asyncio.sleep(600)

async def sweep_expired():
    """Cleans DB-tracked files/links (user-created, has dashboard entries)."""
    while True:
        now = time.time()
        with get_db() as conn:
            expired_files = conn.execute(
                "SELECT path FROM files WHERE expires_at < ?", (now,)
            ).fetchall()
            for row in expired_files:
                shutil.rmtree(Path(row["path"]).parent, ignore_errors=True)
            conn.execute("DELETE FROM files WHERE expires_at < ?", (now,))
            conn.execute(
                "DELETE FROM short_links WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,),
            )
        await asyncio.sleep(600)


async def sweep_orphaned_tempdirs():
    """Cleans job scratch space (tempfile.mkdtemp() dirs from download/convert/trim/crop)
    that never got claimed into the `files` table — e.g. a crashed job, or a small
    Telegram-delivered file whose workdir should've been cleaned right after send
    but wasn't (safety net for anywhere that cleanup was missed)."""
    import tempfile

    tmp_root = Path(tempfile.gettempdir())
    while True:
        now = time.time()
        for entry in (
            tmp_root.glob("tg_*"),
            tmp_root.glob("ytdlp_*"),
            tmp_root.glob("convert_*"),
            tmp_root.glob("trim_*"),
            tmp_root.glob("crop_*"),
        ):
            for path in entry:
                if path.is_dir() and (now - path.stat().st_mtime) > TEMP_JOB_MAX_AGE:
                    shutil.rmtree(path, ignore_errors=True)
        await asyncio.sleep(1800)

@dataclass
class Session:
    token: str
    user_id: int
    chat_id: int
    expires_at: float

@dataclass
class CropSession(Session):
    file_path: Path
    is_video: bool

_crop_sessions: dict[str, CropSession] = {}


def create_crop_session(
    file_path: Path, user_id: int, chat_id: int, is_video: bool
) -> CropSession:
    token = secrets.token_urlsafe(24)
    session = CropSession(
        token=token,
        file_path=file_path,
        user_id=user_id,
        chat_id=chat_id,
        is_video=is_video,
        expires_at=time.time() + 3600,
    )
    _crop_sessions[token] = session
    return session


def get_crop_session(token: str) -> CropSession | None:
    session = _crop_sessions.get(token)
    if session and session.expires_at > time.time():
        return session
    return None


@dataclass
class UploadSession(Session):
    kind: Literal["convert", "trim", "crop"]
    params: dict[str, Any]


_upload_sessions: dict[str, UploadSession] = {}


def create_upload_session(
    kind: Literal["convert", "trim", "crop"], params: dict[str, Any], user_id: int, chat_id: int
) -> UploadSession:
    token = secrets.token_urlsafe(24)
    session = UploadSession(
        token=token,
        kind=kind,
        params=params,
        user_id=user_id,
        chat_id=chat_id,
        expires_at=time.time() + 3600,
    )
    _upload_sessions[token] = session
    return session


def get_upload_session(token: str) -> UploadSession | None:
    session = _upload_sessions.get(token)
    if session and session.expires_at > time.time():
        return session
    return None


def pop_upload_session(token: str) -> UploadSession | None:
    return _upload_sessions.pop(token, None)
