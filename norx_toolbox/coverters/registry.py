from pathlib import Path
from typing import Protocol

from norx_toolbox.coverters.providers import (
    assimp,
    dasel,
    dvisvgm,
    ffmpeg,
    graphicsmagick,
    heif_convert,
    inkscape,
    jpegxl,
    latexmk,
    libreoffice,
    pandoc,
    pillow_conv,
    potrace,
    resvg,
    vcf_contacts,
    vips,
    vtracer,
)


class ConverterModule(Protocol):
    FROM_FORMATS: set[str]
    TO_FORMATS: set[str]

    async def convert(self, input_path: Path, output_path: Path) -> Path: ...


class NoConverterError(Exception):
    pass


_MODULES_BY_NAME: dict[str, ConverterModule] = {
    "ffmpeg": ffmpeg,
    "pillow_conv": pillow_conv,
    "graphicsmagick": graphicsmagick,
    "assimp": assimp,
    "dasel": dasel,
    "dvisvgm": dvisvgm,
    "inkscape": inkscape,
    "heif_convert": heif_convert,
    "jpegxl": jpegxl,
    "libreoffice": libreoffice,
    "pandoc": pandoc,
    "potrace": potrace,
    "resvg": resvg,
    "vcf_contacts": vcf_contacts,
    "vips": vips,
    "vtracer": vtracer,
    "latexmk": latexmk,
}

_CONVERTERS: list[ConverterModule] = list(_MODULES_BY_NAME.values())


def _mod(name: str) -> ConverterModule:
    return _MODULES_BY_NAME[name]


# Explicit overrides for specific (from_ext, to_ext) pairs where the "best" tool
# isn't simply whichever comes first in _CONVERTERS. Checked before falling back
# to list order. Keep this list to genuine judgment calls, not every pair.
_PREFERRED: dict[tuple[str, str], ConverterModule] = {
    # SVG rasterization: resvg is a purpose-built, more spec-correct SVG renderer
    # than GraphicsMagick or vips for this specific pair.
    ("svg", "png"): _mod("resvg"),
    # SVG -> other vector/print formats: Inkscape has the most complete SVG support.
    ("svg", "pdf"): _mod("inkscape"),
    ("svg", "eps"): _mod("inkscape"),
    ("svg", "ps"): _mod("inkscape"),
    # Raster -> SVG (proper vectorization, not just embedding): vtracer for
    # photographic/color images, potrace for simple bilevel/line art.
    ("png", "svg"): _mod("vtracer"),
    ("jpg", "svg"): _mod("vtracer"),
    ("jpeg", "svg"): _mod("vtracer"),
    ("bmp", "svg"): _mod("potrace"),
    ("pbm", "svg"): _mod("potrace"),
    ("pgm", "svg"): _mod("potrace"),
    # Office documents: LibreOffice has the most faithful layout fidelity for
    # real document formats (doc/docx/odt/rtf), over pandoc's markup-focused conversion.
    ("docx", "pdf"): _mod("libreoffice"),
    ("doc", "pdf"): _mod("libreoffice"),
    ("odt", "pdf"): _mod("libreoffice"),
    ("rtf", "pdf"): _mod("libreoffice"),
    ("docx", "odt"): _mod("libreoffice"),
    ("doc", "docx"): _mod("libreoffice"),
    # LaTeX -> PDF: latexmk (proper build tool: handles bibliography/references/
    # multiple passes) over pandoc's more basic pdf-engine invocation.
    ("tex", "pdf"): _mod("latexmk"),
    ("latex", "pdf"): _mod("latexmk"),
}


def find_converter(from_ext: str, to_ext: str) -> ConverterModule:
    from_ext, to_ext = from_ext.lower().lstrip("."), to_ext.lower().lstrip(".")

    preferred = _PREFERRED.get((from_ext, to_ext))
    if (
        preferred
        and from_ext in preferred.FROM_FORMATS
        and to_ext in preferred.TO_FORMATS
    ):
        return preferred

    for module in _CONVERTERS:
        if from_ext in module.FROM_FORMATS and to_ext in module.TO_FORMATS:
            return module

    raise NoConverterError(f"No converter supports {from_ext} → {to_ext}")


async def convert_file(input_path: Path, to_ext: str, output_dir: Path) -> Path:
    from_ext = input_path.suffix.lstrip(".")
    to_ext = to_ext.lstrip(".")

    if from_ext.lower() == to_ext.lower():
        return input_path

    module = find_converter(from_ext, to_ext)
    output_path = output_dir / f"{input_path.stem}.{to_ext}"
    return await module.convert(input_path, output_path)
