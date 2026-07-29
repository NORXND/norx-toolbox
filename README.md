# norx-toolbox-bot

Private Telegram bot for downloading, converting, and editing media — built for personal use.

## Features

- **`/download <url> [format]`** — download video/audio via yt-dlp, optionally convert to any supported format
- **`/download_trim <url> <start> <end> [format]`** — download and trim in one step
- **`/trim <start> <end>`** (attach video/audio) — trim an uploaded file
- **`/convert <format>`** (attach file) — convert between 100+ formats via a registry of specialized tools (ffmpeg, LibreOffice, pandoc, ImageMagick, Inkscape, and more)
- **`/crop`** (attach image/video) — opens a web page to select a crop region, delivers the result back via Telegram
- **`/shorten <url> [duration]`** — URL shortener, permanent by default
- **`/share [duration]`** (attach file) — temporary file sharing link, expires by default (1 day)
- Bare links sent in chat are auto-downloaded (no command needed)
- Per-user dashboard for managing your own links/files

## Stack

- **[aiogram 3](https://docs.aiogram.dev/)** — Telegram bot framework
- **[Quart](https://quart.palletsprojects.com/)** — async web server (file sharing, crop tool, dashboard)
- **[Hypercorn](https://hypercorn.readthedocs.io/)** — ASGI server, runs alongside the bot in one event loop
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — video/audio downloading
- **SQLite** — link/file metadata, no external DB needed
- A registry of subprocess-based converters (ffmpeg, GraphicsMagick, LibreOffice, pandoc, Inkscape, assimp, potrace, vtracer, dasel, dvisvgm, heif-convert, jpeg-xl, latexmk, vips) plus Pillow for in-process image conversion - based on amazing work at [ConvertX](https://github.com/C4illin/ConvertX) !!

## Project structure

```
norx_toolbox/
├── main.py # entrypoint — runs bot + web server + cleanup loops together
├── config.py # env-driven config, single source of truth
├── db.py # SQLite schema + connection helper
├── bot/
│ └── main.py # bot/dispatcher setup
│ └── helpers.py # various helpers
│ └── markdown.py # markdown formatting
├── handlers/ # one router per command/feature
├── converters/
│ ├── base.py # shared subprocess runner
│ ├── registry.py # format-pair -> converter routing, with pair-level overrides
│ └── providers/ # one module per external tool
├── ytdlp.py
├── task_manager.py
├── delivery/
│ ├── storage.py # file storage, token generation
│ └── deliver.py # Telegram delivery, size-based fallback to link
├── web/
│ ├── app.py # Quart routes
│ └── templates/
└── utils/
```

## Setup

### Requirements

- Python 3.14+
- All converter binaries listed in the `Dockerfile` (or run inside the devcontainer/Docker image, which has them preinstalled)

### Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Default |
| --- | --- | --- |
| `BOT_TOKEN` | Telegram bot token from [@BotFather](https://t.me/BotFather) | *(required)* |
| `PUBLIC_URL` | Base URL for `/workspace` tool pages (crop, dashboard) | *(required)* |
| `SHARE_BASE` | Base URL for `/share` file links | *(required)* |
| `SHORTEN_BASE` | Base URL for `/shorten` short links | *(required)* |
| `OUTPUT_DIR` | Directory for stored files + SQLite DB | `/data/norx-toolbox` |
| `DOWNLOAD_COOKIE_FILE` | Path for cookie file to be used with yt-dlp | *(optional)* |
| `UPLOAD_MAX_BYTES` | Maxium size (in bytes) of files uploaded outside Telegram (via web UI) | 104857600 (100 MB) |
| `LINK_TTL_SECONDS` | Default expiry for delivery-fallback links | `3600` |
| `WEB_BIND` | Hypercorn bind address | `0.0.0.0:8000` |

### Running locally

```bash
pip install --break-system-packages -e .
python -m norx_toolbox.main
```

### Running via Docker

```bash
docker compose up -d
```

## Notes

- This is a personal project that is still in-progress.
- As said, this is not a tool designed for public multi-tenant use!
- Files and short links are stored in SQLite (`OUTPUT_DIR/toolbox.db`) — make sure `OUTPUT_DIR` is on a persistent volume in production, or all state is lost on redeploy.
