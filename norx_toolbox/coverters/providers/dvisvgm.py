from pathlib import Path

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {"dvi", "xdv", "pdf", "eps"}
TO_FORMATS = {"svg", "svgz"}


async def convert(input_path: Path, output_path: Path) -> Path:
    from_ext = input_path.suffix.lstrip(".").lower()
    to_ext = output_path.suffix.lstrip(".").lower()

    args = ["dvisvgm"]
    if from_ext == "eps":
        args.append("--eps")
    if from_ext == "pdf":
        args.append("--pdf")
    if to_ext == "svgz":
        args.append("-z")

    args += [str(input_path), "-o", str(output_path)]
    await run_subprocess(*args)
    return output_path
