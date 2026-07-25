import asyncio
from pathlib import Path

from PIL import Image
from PIL.Image import Image as PILImage

FROM_FORMATS = {
    "png",
    "jpg",
    "jpeg",
    "bmp",
    "gif",
    "tiff",
    "tif",
    "webp",
    "ico",
    "ppm",
    "pgm",
    "pbm",
    "pnm",
    "eps",
    "im",
    "msp",
    "sgi",
    "tga",
    "xbm",
}

TO_FORMATS = {
    "png",
    "jpg",
    "jpeg",
    "bmp",
    "gif",
    "tiff",
    "tif",
    "webp",
    "ico",
    "ppm",
    "eps",
    "im",
    "msp",
    "sgi",
    "tga",
    "xbm",
}


def _convert_sync(input_path: Path, output_path: Path) -> Path:
    with Image.open(input_path) as img_file:
        img: PILImage = img_file
        target_ext = output_path.suffix.lstrip(".").lower()

        if target_ext in ("jpg", "jpeg", "bmp") and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        img.save(output_path)
    return output_path


async def convert(input_path: Path, output_path: Path) -> Path:
    return await asyncio.to_thread(_convert_sync, input_path, output_path)


def _crop_and_resize_sync(
    input_path: Path,
    output_path: Path,
    x: int,
    y: int,
    w: int,
    h: int,
    resize_w: int | None = None,
    resize_h: int | None = None,
) -> Path:
    with Image.open(input_path) as img_file:
        img: PILImage = img_file
        cropped = img.crop((x, y, x + w, y + h))

        if resize_w and resize_h:
            cropped = cropped.resize((resize_w, resize_h))

        target_ext = output_path.suffix.lstrip(".").lower()
        if target_ext in ("jpg", "jpeg", "bmp") and cropped.mode in ("RGBA", "P", "LA"):
            cropped = cropped.convert("RGB")

        cropped.save(output_path)
    return output_path


async def crop_and_resize(
    input_path: Path,
    output_path: Path,
    x: int,
    y: int,
    w: int,
    h: int,
    resize_w: int | None = None,
    resize_h: int | None = None,
) -> Path:
    return await asyncio.to_thread(
        _crop_and_resize_sync, input_path, output_path, x, y, w, h, resize_w, resize_h
    )
