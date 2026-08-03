"""Provider-independent value normalisation helpers."""

from __future__ import annotations

import re
from typing import Any


_NUMBER = re.compile(r"[-+]?\d+(?:[.,]\d+)?")
_RANGE = re.compile(
    r"(?P<minimum>[-+]?\d+(?:[.,]\d+)?)\s*(?:°?\s*[A-Za-zµΩ%]+)?\s*"
    r"(?:\.\.\.|\.\.|~|–|—|\bto\b)\s*"
    r"(?P<maximum>[-+]?\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
_TEMPERATURE_UNIT = re.compile(r"°?\s*([CF])\b", re.IGNORECASE)
_RANGE_HINT = re.compile(r"(?:\.\.\.|\.\.|~|–|—|\bto\b)", re.IGNORECASE)


class RangeValidationError(ValueError):
    """Raised when text appears to contain a range but it is not valid."""


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


def _temperature_unit(value: Any) -> str | None:
    matches = _TEMPERATURE_UNIT.findall(str(value or ""))
    if not matches:
        return None
    units = {match.upper() for match in matches}
    if len(units) != 1:
        raise RangeValidationError(f"Mixed temperature units in range: {value!r}")
    return units.pop()


def _fahrenheit_to_celsius(value: float) -> float:
    return (value - 32.0) * 5.0 / 9.0


def range_values(
    value: Any,
    *,
    target_unit: str | None = None,
    allow_single: bool = False,
) -> tuple[float | None, float | None]:
    """Parse and validate a numeric range.

    Supported separators include ``...``, ``..``, ``~``, en/em dashes and
    ``to``. Signs are retained. When ``target_unit='C'``, Fahrenheit values are
    converted to Celsius before validation.

    A value that is not a range returns ``(value, None)`` only when
    ``allow_single=True``; otherwise it returns ``(None, None)``. Text that
    clearly indicates a range but cannot be parsed raises ``RangeValidationError``.
    """

    text = str(value or "").strip()
    match = _RANGE.search(text)
    if not match:
        if _RANGE_HINT.search(text):
            raise RangeValidationError(f"Could not parse range: {value!r}")
        parsed = number(value)
        if parsed is None:
            return None, None
        return (float(parsed), None) if allow_single else (None, None)

    minimum = float(match.group("minimum").replace(",", "."))
    maximum = float(match.group("maximum").replace(",", "."))

    source_unit = _temperature_unit(text)
    normalised_target = str(target_unit or "").strip().upper().replace("°", "")
    if normalised_target == "C" and source_unit == "F":
        minimum = _fahrenheit_to_celsius(minimum)
        maximum = _fahrenheit_to_celsius(maximum)
    elif normalised_target and source_unit and source_unit != normalised_target:
        raise RangeValidationError(
            f"Unsupported range conversion from {source_unit} to {normalised_target}"
        )

    # A parsed range must have a meaningful ascending order after signs and
    # units have been normalised. This catches duplicated-bound parser errors.
    if maximum <= minimum:
        raise RangeValidationError(
            f"Invalid range {minimum} to {maximum}: maximum must be greater than minimum"
        )

    # Avoid floating-point noise after Fahrenheit conversion while retaining
    # sufficient precision for component specifications.
    return round(minimum, 9), round(maximum, 9)


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
    if "cut tape" in lowered:
        return "Cut Tape"
    if "digi-reel" in lowered or "digireel" in lowered:
        return "DigiReel"
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
