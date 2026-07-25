import re

_MD_V2_SPECIAL = re.compile(r"([_*\[\]()~`>#+\-=|{}.!])")


def escape_md(text: str) -> str:
    """Escape arbitrary text for safe inclusion in MarkdownV2 (outside code blocks)."""
    return _MD_V2_SPECIAL.sub(r"\\\1", text)


def code(text: str) -> str:
    """Inline code span. Content is NOT escaped with escape_md — backticks/backslashes
    inside a code span only need backtick and backslash itself escaped, per Telegram's spec.
    """
    escaped = text.replace("\\", "\\\\").replace("`", "\\`")
    return f"`{escaped}`"


def code_block(text: str, lang: str = "") -> str:
    """Fenced code block, e.g. for error tracebacks/logs."""
    escaped = text.replace("\\", "\\\\").replace("`", "\\`")
    return f"```{lang}\n{escaped}\n```"


def bold(text: str) -> str:
    return f"*{escape_md(text)}*"


def italic(text: str) -> str:
    return f"_{escape_md(text)}_"


def link(text: str, url: str) -> str:
    safe_url = url.replace("\\", "\\\\").replace(")", "\\)")
    return f"[{escape_md(text)}]({safe_url})"
