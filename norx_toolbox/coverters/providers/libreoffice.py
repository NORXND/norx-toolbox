from pathlib import Path

from norx_toolbox.coverters.base import run_subprocess

FROM_FORMATS = {
    "602",
    "abw",
    "csv",
    "cwk",
    "doc",
    "docm",
    "docx",
    "dot",
    "dotx",
    "dotm",
    "epub",
    "fb2",
    "fodt",
    "htm",
    "html",
    "hwp",
    "mcw",
    "mw",
    "mwd",
    "lwp",
    "lrf",
    "odt",
    "ott",
    "pages",
    "pdf",
    "psw",
    "rtf",
    "sdw",
    "stw",
    "sxw",
    "tab",
    "tsv",
    "txt",
    "wn",
    "wpd",
    "wps",
    "wpt",
    "wri",
    "xhtml",
    "xml",
    "zabw",
}

TO_FORMATS = {
    "csv",
    "doc",
    "docm",
    "docx",
    "dot",
    "dotx",
    "dotm",
    "epub",
    "fodt",
    "htm",
    "html",
    "odt",
    "ott",
    "pdf",
    "rtf",
    "tab",
    "tsv",
    "txt",
    "wps",
    "wpt",
    "xhtml",
    "xml",
}

_TEXT_FILTERS: dict[str, str] = {
    "602": "T602Document",
    "abw": "AbiWord",
    "csv": "Text",
    "doc": "MS Word 97",
    "docm": "MS Word 2007 XML VBA",
    "docx": "MS Word 2007 XML",
    "dot": "MS Word 97 Vorlage",
    "dotx": "MS Word 2007 XML Template",
    "dotm": "MS Word 2007 XML Template",
    "epub": "EPUB",
    "fb2": "Fictionbook 2",
    "fodt": "OpenDocument Text Flat XML",
    "htm": "HTML (StarWriter)",
    "html": "HTML (StarWriter)",
    "hwp": "writer_MIZI_Hwp_97",
    "mcw": "MacWrite",
    "mw": "MacWrite",
    "mwd": "Mariner_Write",
    "lwp": "LotusWordPro",
    "lrf": "BroadBand eBook",
    "odt": "writer8",
    "ott": "writer8_template",
    "pages": "Apple Pages",
    "pdf": "writer_pdf_import",
    "psw": "PocketWord File",
    "rtf": "Rich Text Format",
    "sdw": "StarOffice_Writer",
    "stw": "writer_StarOffice_XML_Writer_Template",
    "sxw": "StarOffice XML (Writer)",
    "tab": "Text",
    "tsv": "Text",
    "txt": "Text",
    "wn": "WriteNow",
    "wpd": "WordPerfect",
    "wps": "MS Word 97",
    "wpt": "MS Word 97 Vorlage",
    "wri": "MS_Write",
    "xhtml": "HTML (StarWriter)",
    "xml": "OpenDocument Text Flat XML",
    "zabw": "AbiWord",
}

_CALC_FILTERS: dict[str, str] = (
    {}
)  # not populated in the source — reserved for future spreadsheet support


def _get_filters(file_type: str, convert_to: str) -> tuple[str | None, str | None]:
    if convert_to == "pdf":
        return None, None
    if file_type in _TEXT_FILTERS and convert_to in _TEXT_FILTERS:
        return _TEXT_FILTERS[file_type], _TEXT_FILTERS[convert_to]
    if file_type in _CALC_FILTERS and convert_to in _CALC_FILTERS:
        return _CALC_FILTERS[file_type], _CALC_FILTERS[convert_to]
    return None, None


async def convert(input_path: Path, output_path: Path) -> Path:
    from_ext = input_path.suffix.lstrip(".").lower()
    to_ext = output_path.suffix.lstrip(".").lower()
    out_dir = output_path.parent

    in_filter, out_filter = _get_filters(from_ext, to_ext)

    args = ["--headless"]
    if in_filter:
        args.append(f"--infilter={in_filter}")

    if out_filter:
        args += [
            "--convert-to",
            f"{to_ext}:{out_filter}",
            "--outdir",
            str(out_dir),
            str(input_path),
        ]
    else:
        args += ["--convert-to", to_ext, "--outdir", str(out_dir), str(input_path)]

    await run_subprocess("soffice", *args)

    # soffice names its output after the input stem, not your desired output_path —
    # find what it actually produced and rename to match.
    produced = out_dir / f"{input_path.stem}.{to_ext}"
    if produced != output_path and produced.exists():
        produced.rename(output_path)

    return output_path
