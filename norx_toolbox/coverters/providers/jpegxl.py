from pathlib import Path

from norx_toolbox.coverters.base import ConversionError, run_subprocess

FROM_FORMATS = {
    "jxl",
    "apng",
    "exr",
    "gif",
    "jpeg",
    "pam",
    "pfm",
    "pgm",
    "pgx",
    "png",
    "ppm",
}
TO_FORMATS = {"jxl", "apng", "exr", "jpeg", "pam", "pfm", "pgm", "pgx", "png", "ppm"}


async def convert(input_path: Path, output_path: Path) -> Path:
    from_ext = input_path.suffix.lstrip(".").lower()
    to_ext = output_path.suffix.lstrip(".").lower()

    if from_ext == "jxl":
        tool = "djxl"
    elif to_ext == "jxl":
        tool = "cjxl"
    else:
        raise ConversionError(
            f"jpegxl converter needs jxl on one side, got {from_ext} → {to_ext}"
        )

    await run_subprocess(tool, str(input_path), str(output_path))
    return output_path
