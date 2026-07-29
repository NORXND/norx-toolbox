import os
from pathlib import Path


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


class Config:
    BOT_TOKEN = _require_env("BOT_TOKEN")
    PUBLIC_URL = _require_env("PUBLIC_URL").rstrip("/")
    SHARE_BASE = _require_env("SHARE_BASE").rstrip("/")
    SHORTEN_BASE = _require_env("SHORTEN_BASE").rstrip("/")
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/data/norx-toolbox"))
    DOWNLOAD_COOKIE_FILE = os.getenv("DOWNLOAD_COOKIE_FILE", None)
    LINK_TTL_SECONDS = int(os.getenv("LINK_TTL_SECONDS", "3600"))
    WEB_BIND = os.getenv("WEB_BIND", "0.0.0.0:8000")


config = Config()
