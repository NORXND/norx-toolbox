from pathlib import Path

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {"pnm", "pbm", "pgm", "bmp"}
TO_FORMATS = {
    "svg",
    "pdf",
    "pdfpage",
    "eps",
    "postscript",
    "ps",
    "dxf",
    "geojson",
    "pgm",
    "gimppath",
    "xfig",
}


async def convert(input_path: Path, output_path: Path) -> Path:
    to_ext = output_path.suffix.lstrip(".").lower()
    await run_subprocess(
        "potrace", str(input_path), "-o", str(output_path), "-b", to_ext
    )
    return output_path
