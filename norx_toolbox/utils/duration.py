import re

_UNIT_SECONDS = {"m": 60, "h": 3600, "d": 86400}


def parse_duration(value: str) -> int:
    """Accepts '30m', '12h', '2d', or a bare number (assumed hours). Returns seconds."""
    value = value.strip().lower()
    match = re.fullmatch(r"(\d+)([mhd]?)", value)
    if not match:
        raise ValueError(f"'{value}' isn't a valid duration (use e.g. 12h, 2d, 30m)")
    amount, unit = match.groups()
    unit = unit or "h"
    return int(amount) * _UNIT_SECONDS[unit]


def parse_timestamp(value: str) -> str:
    parts = value.split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        raise ValueError("expected MM:SS or HH:MM:SS")
    return value
