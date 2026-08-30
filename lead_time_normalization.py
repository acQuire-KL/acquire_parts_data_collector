"""Lead-time normalisation for operational BOM reporting.

Provider source values remain untouched in the Knowledge Base.  This module only
creates a consistent user-facing value in whole calendar weeks.  Delivery-week
notations such as ``Week 45`` are treated as ISO calendar weeks, not as a
45-week duration.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
import re
from typing import Any

_REQUEST_QUOTE = (
    "request delivery quote",
    "request quote",
    "contact supplier",
    "contact manufacturer",
    "call for",
)
_NOT_STATED = ("not stated", "not available", "unknown", "n/a", "na", "-")

# Deliberately require an explicit calendar-week form so "45 weeks" remains a duration.
_CALENDAR_WEEK_RE = re.compile(
    r"^\s*(?:delivery\s+)?(?:iso\s*)?(?:week|wk|cw|w)\s*[-:#]?\s*(\d{1,2})(?:\s*[/,-]?\s*(20\d{2}))?\s*$",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


@dataclass(frozen=True)
class LeadTimeDisplay:
    weeks: int | None
    display: str
    interpretation: str


def _next_iso_week_start(week: int, year: int | None, today: date) -> tuple[date, int]:
    if not 1 <= week <= 53:
        raise ValueError(f"ISO week must be 1..53, got {week}")

    candidate_year = year or today.isocalendar().year
    while True:
        try:
            start = date.fromisocalendar(candidate_year, week, 1)
        except ValueError:
            # Week 53 does not exist in every ISO year.
            candidate_year += 1
            continue
        if year is not None or start >= today:
            return start, candidate_year
        candidate_year += 1


def normalise_lead_time(value: Any, *, today: date | None = None, default_unit: str = "weeks") -> LeadTimeDisplay:
    """Return a whole-week reporting value, always rounded up.

    ``default_unit`` is used only for bare numeric values.  Operational PDC
    profiles call this with ``weeks`` because the common field is named
    ``manufacturer_lead_weeks``.
    """
    current = today or date.today()
    if value is None:
        return LeadTimeDisplay(None, "", "missing")

    text = " ".join(str(value).strip().split())
    if not text:
        return LeadTimeDisplay(None, "", "missing")
    lower = text.casefold()

    if any(token in lower for token in _REQUEST_QUOTE):
        return LeadTimeDisplay(None, "Request Delivery Quote", "request_quote")
    if lower in _NOT_STATED:
        return LeadTimeDisplay(None, "Not stated", "not_stated")

    week_match = _CALENDAR_WEEK_RE.match(text)
    if week_match:
        week = int(week_match.group(1))
        year = int(week_match.group(2)) if week_match.group(2) else None
        try:
            target, target_year = _next_iso_week_start(week, year, current)
        except ValueError:
            return LeadTimeDisplay(None, text, "unrecognised")
        days = max(0, (target - current).days)
        weeks = max(1, math.ceil(days / 7.0))
        return LeadTimeDisplay(weeks, f"{weeks} {'week' if weeks == 1 else 'weeks'} (delivery Week {week}, {target:%d %b %Y})", "calendar_week")

    match = _NUMBER_RE.search(text.replace(",", ""))
    if not match:
        return LeadTimeDisplay(None, text, "unrecognised")
    numeric = float(match.group(0))

    # Zero manufacturer lead time is not useful evidence of immediate supply.
    # Treat it conservatively rather than implying same-day availability.
    if numeric <= 0:
        return LeadTimeDisplay(None, "Request Delivery Quote", "zero_or_negative")

    if "day" in lower:
        weeks_float = numeric / 7.0
    elif "week" in lower or "wk" in lower:
        weeks_float = numeric
    else:
        weeks_float = numeric / 7.0 if default_unit.casefold().startswith("day") else numeric

    weeks = max(1, math.ceil(weeks_float))
    return LeadTimeDisplay(weeks, f"{weeks} {'week' if weeks == 1 else 'weeks'}", "duration")


def lead_time_display(value: Any, *, today: date | None = None, default_unit: str = "weeks") -> str:
    return normalise_lead_time(value, today=today, default_unit=default_unit).display
