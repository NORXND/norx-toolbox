from pathlib import Path

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {
    "avci",
    "avcs",
    "avif",
    "h264",
    "heic",
    "heics",
    "heif",
    "heifs",
    "hif",
    "mkv",
    "mp4",
}

TO_FORMATS = {"jpeg", "png", "y4m"}


async def convert(input_path: Path, output_path: Path) -> Path:
    await run_subprocess("heif-convert", str(input_path), str(output_path))
    return output_path
