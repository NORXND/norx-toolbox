import asyncio
from pathlib import Path

from norx_toolbox.coverters.base import ConversionError, run_subprocess

FROM_FORMATS = {"yaml", "toml", "json", "xml", "csv"}
TO_FORMATS = {"yaml", "toml", "json", "csv"}


async def convert(input_path: Path, output_path: Path) -> Path:
    from_ext = input_path.suffix.lstrip(".")
    to_ext = output_path.suffix.lstrip(".")

    proc = await asyncio.create_subprocess_exec(
        "dasel",
        "--file",
        str(input_path),
        "--read",
        from_ext,
        "--write",
        to_ext,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise ConversionError(
            f"dasel failed (exit {proc.returncode}): {stderr.decode(errors='replace')}"
        )

    output_path.write_bytes(stdout)
    return output_path
