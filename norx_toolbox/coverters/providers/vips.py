from pathlib import Path

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {
    "avif",
    "bif",
    "csv",
    "exr",
    "fits",
    "gif",
    "hdr.gz",
    "hdr",
    "heic",
    "heif",
    "img.gz",
    "img",
    "j2c",
    "j2k",
    "jp2",
    "jpeg",
    "jpx",
    "jxl",
    "mat",
    "mrxs",
    "ndpi",
    "nia.gz",
    "nia",
    "nii.gz",
    "nii",
    "pdf",
    "pfm",
    "pgm",
    "pic",
    "png",
    "ppm",
    "raw",
    "scn",
    "svg",
    "svs",
    "svslide",
    "szi",
    "tif",
    "tiff",
    "v",
    "vips",
    "vms",
    "vmu",
    "webp",
    "zip",
}

TO_FORMATS = {
    "avif",
    "dzi",
    "fits",
    "gif",
    "hdr.gz",
    "heic",
    "heif",
    "img.gz",
    "j2c",
    "j2k",
    "jp2",
    "jpeg",
    "jpx",
    "jxl",
    "mat",
    "nia.gz",
    "nia",
    "nii.gz",
    "nii",
    "png",
    "tiff",
    "vips",
    "webp",
}


async def convert(input_path: Path, output_path: Path) -> Path:
    from_ext = input_path.suffix.lstrip(".").lower()
    action = "pdfload" if from_ext == "pdf" else "copy"
    await run_subprocess("vips", action, str(input_path), str(output_path))
    return output_path
