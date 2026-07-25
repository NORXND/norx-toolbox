from pathlib import Path

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {"svg"}
TO_FORMATS = {"png"}


async def convert(input_path: Path, output_path: Path) -> Path:
    await run_subprocess("resvg", str(input_path), str(output_path))
    return output_path
