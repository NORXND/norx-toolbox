from pathlib import Path
from typing import Any

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {"jpg", "jpeg", "png", "bmp", "gif", "tiff", "tif", "webp"}
TO_FORMATS = {"svg"}

_VALID_OPTIONS = {
    "colormode",
    "hierarchical",
    "mode",
    "filter_speckle",
    "color_precision",
    "layer_difference",
    "corner_threshold",
    "length_threshold",
    "max_iterations",
    "splice_threshold",
    "path_precision",
}


async def convert(
    input_path: Path, output_path: Path, options: dict[str, Any] | None = None
) -> Path:
    args = ["--input", str(input_path), "--output", str(output_path)]

    if options:
        for key in _VALID_OPTIONS:
            if key in options and options[key] is not None:
                args += [f"--{key}", str(options[key])]

    await run_subprocess("vtracer", *args)
    return output_path
