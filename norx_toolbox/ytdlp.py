import tempfile
from pathlib import Path

import yt_dlp  # type: ignore[import-untyped]

from norx_toolbox.config import config

AUDIO_FORMATS = {"mp3", "wav", "flac", "aac", "ogg", "opus", "m4a", "wma"}


def download_source(url: str, audio_only: bool = False) -> Path:
    """
    Blocking — must be called via asyncio.to_thread.
    Downloads the best available source (whatever format yt-dlp/the host gives us —
    often webm) into a fresh temp dir. Does NOT handle final format conversion;
    that's the caller's job via converters.ffmpeg.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="ytdlp_"))
    outtmpl = str(tmp_dir / "%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best" if audio_only else "bestvideo+bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": (
            str(Path(config.DOWNLOAD_COOKIE_FILE))
            if config.DOWNLOAD_COOKIE_FILE
            else None
        ),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
        info = ydl.extract_info(url, download=True)
        if "entries" in info:
            raise RuntimeError("yt-dlp returned a playlist, but noplaylist was set")
        filename = ydl.prepare_filename(info)

        result_path = Path(filename)
        if not result_path.exists():
            candidates = list(tmp_dir.glob("*"))
            if not candidates:
                raise RuntimeError(
                    "yt-dlp reported success but no output file was found"
                )
            result_path = candidates[0]

    return result_path
