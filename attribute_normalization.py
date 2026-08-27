"""Conservative engineering-attribute normalisation for provider comparison.

Normalisation is used only to decide whether provider values are equivalent and
produce a compact review value. Raw provider evidence remains unchanged.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_TEMP_RE = re.compile(
    r"^\s*([+-]?\d+(?:\.\d+)?)\s*(?:°\s*)?[cC]?\s*(?:~|to|[-–—])\s*"
    r"([+-]?\d+(?:\.\d+)?)\s*(?:°\s*)?[cC](?:\s*\([^)]*\))?\s*$",
    re.IGNORECASE,
)
_NUM_UNIT_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*([%a-zA-ZµμΩ°]+)\s*$")


def _number(text: str) -> str:
    try:
        value = Decimal(text)
    except InvalidOperation:
        return text
    if value == value.to_integral():
        return str(int(value))
    return format(value.normalize(), "f")


def normalise_attribute(value: object, attribute: str = "") -> tuple[str, str]:
    """Return (comparison_key, clean_display) without altering source evidence."""
    text = " ".join(str(value or "").strip().split())
    if not text:
        return "", ""

    temp = _TEMP_RE.match(text)
    if temp and ("temperature" in attribute.casefold() or "c" in text.casefold()):
        low, high = _number(temp.group(1)), _number(temp.group(2))
        return f"temp_c:{low}:{high}", f"{low}°C to {high}°C"

    compact = text.replace("μ", "µ")
    match = _NUM_UNIT_RE.match(compact)
    if match:
        number, unit = _number(match.group(1)), match.group(2)
        unit_key = unit.casefold().replace("µ", "u")
        display_unit = "%" if unit == "%" else unit
        return f"num:{number}:{unit_key}", f"{number} {display_unit}" if display_unit != "%" else f"{number}%"

    key = compact.casefold().replace("° ", "°")
    key = re.sub(r"\s*([~/])\s*", r"\1", key)
    return key, text
