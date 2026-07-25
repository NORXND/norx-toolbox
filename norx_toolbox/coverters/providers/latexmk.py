from pathlib import Path

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {"tex", "latex"}
TO_FORMATS = {"pdf"}


async def convert(input_path: Path, output_path: Path) -> Path:
    out_dir = output_path.parent

    await run_subprocess(
        "latexmk",
        "-xelatex",
        "-interaction=nonstopmode",
        f"-output-directory={out_dir}",
        str(input_path),
    )

    # latexmk names output after input_path's stem, not output_path — same gotcha as LibreOffice
    produced = out_dir / f"{input_path.stem}.pdf"
    if produced != output_path and produced.exists():
        produced.rename(output_path)

    return output_path
