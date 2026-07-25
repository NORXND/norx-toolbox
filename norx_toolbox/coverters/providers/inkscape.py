from pathlib import Path

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {"svg", "pdf", "eps", "ps", "wmf", "emf", "png"}

TO_FORMATS = {
    "dxf",
    "emf",
    "eps",
    "fxg",
    "gpl",
    "hpgl",
    "html",
    "odg",
    "pdf",
    "png",
    "pov",
    "ps",
    "sif",
    "svg",
    "svgz",
    "tex",
    "wmf",
}


async def convert(input_path: Path, output_path: Path) -> Path:
    await run_subprocess("inkscape", str(input_path), "-o", str(output_path))
    return output_path
