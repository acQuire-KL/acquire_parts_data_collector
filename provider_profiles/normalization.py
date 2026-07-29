"""Provider-independent value normalisation helpers."""

from __future__ import annotations

import re
from typing import Any


_NUMBER = re.compile(r"[-+]?\d+(?:[.,]\d+)?")
_RANGE = re.compile(
    r"(?P<minimum>[-+]?\d+(?:[.,]\d+)?)\s*(?:\.\.\.|\.\.|–|—|to)\s*"
    r"(?P<maximum>[-+]?\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)


def number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    match = _NUMBER.search(str(value or "").replace(" ", ""))
    if not match:
        return None
    parsed = float(match.group(0).replace(",", "."))
    return int(parsed) if parsed.is_integer() else parsed


def range_values(value: Any) -> tuple[float | None, float | None]:
    match = _RANGE.search(str(value or ""))
    if not match:
        parsed = number(value)
        return (float(parsed), float(parsed)) if parsed is not None else (None, None)
    return (
        float(match.group("minimum").replace(",", ".")),
        float(match.group("maximum").replace(",", ".")),
    )


def normalise_url(value: Any) -> str:
    text = str(value or "").strip()
    return f"https:{text}" if text.startswith("//") else text


def normalise_package(value: Any) -> str:
    text = str(value or "").strip().upper().replace("_", "-").replace(" ", "")
    common = {
        "SOT23-5": "SOT-23-5",
        "SOT-23-5": "SOT-23-5",
        "SOT235": "SOT-23-5",
        "SOT23-6": "SOT-23-6",
        "SOT-23-6": "SOT-23-6",
        "SOT236": "SOT-23-6",
    }
    return common.get(text, str(value or "").strip())


def normalise_mounting(value: Any) -> str:
    text = str(value or "").strip()
    lookup = {
        "smd": "SMD",
        "smt": "SMD",
        "surface mount": "SMD",
        "surface-mount": "SMD",
        "tht": "THT",
        "through hole": "THT",
        "through-hole": "THT",
    }
    return lookup.get(text.lower(), text)


def normalise_pack_format(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    if "reel" in lowered:
        return "Reel"
    if "tape" in lowered:
        return "Tape"
    if "tube" in lowered:
        return "Tube"
    if "tray" in lowered:
        return "Tray"
    if "bag" in lowered:
        return "Bag"
    if "box" in lowered:
        return "Box"
    if "bulk" in lowered or "loose" in lowered:
        return "Loose"
    return text
