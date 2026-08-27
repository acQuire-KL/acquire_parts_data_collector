"""Provider-neutral aggregation for one requested manufacturer part.

PDC uses this module only to describe collected evidence. It does not rank,
prefer or recommend providers; those decisions belong to PIE.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from commercial_profile import commercial_offers
from manufacturer_resolver import names_equivalent


def normalise_identity(value: Any) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def normalise_engineering(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


@dataclass(frozen=True)
class ProviderEvidence:
    provider: str
    execution_status: str
    message: str = ""
    part_profile: dict[str, Any] | None = None
    commercial_profile: dict[str, Any] | None = None
    captured_at_utc: str = ""
    source_mode: str = ""

    @property
    def identity_match(self) -> bool:
        return bool((self.part_profile or {}).get("identity_match"))


ORDERING_SUFFIXES = ("T", "R", "TR")


def mpn_identity_equivalent(requested_mpn: str, returned_mpn: str) -> bool:
    """Conservative equality for base MPN versus common ordering suffixes.

    Punctuation such as '+' is already ignored by normalise_identity().  In
    addition, providers often expose the same engineering part with a terminal
    tape/reel ordering suffix (for example TPS628438YKA vs TPS628438YKAR or
    MAX40203ANS vs MAX40203ANS+T).  Only a small explicit suffix set is
    accepted; arbitrary prefix matching is deliberately rejected.
    """
    requested = normalise_identity(requested_mpn)
    returned = normalise_identity(returned_mpn)
    if not requested or not returned:
        return False
    if requested == returned:
        return True
    for suffix in ORDERING_SUFFIXES:
        if requested + suffix == returned or returned + suffix == requested:
            return True
    return False


def provider_identity_match(requested_manufacturer: str, requested_mpn: str, profile: dict[str, Any]) -> bool:
    returned_mpn = profile.get("manufacturer_part_number", "")
    returned_manufacturer = profile.get("manufacturer", "")
    return (
        mpn_identity_equivalent(requested_mpn, returned_mpn)
        and names_equivalent(requested_manufacturer, returned_manufacturer)
    )


def evidence_status(evidence: Iterable[ProviderEvidence]) -> tuple[str, str]:
    items = list(evidence)
    matched = [item.provider for item in items if item.identity_match]
    completed = [item.provider for item in items if item.execution_status == "success"]
    errors = [item.provider for item in items if item.execution_status == "error"]
    skipped = [item.provider for item in items if item.execution_status == "skipped"]
    no_matches = [item.provider for item in items if item.execution_status == "no_match"]

    if matched:
        status = "Matched"
        reason = f"Identity matched by: {', '.join(matched)}."
    elif completed:
        status = "Review Required"
        reason = "Provider searches returned part data but no exact manufacturer + MPN identity match was confirmed."
    elif no_matches and not errors:
        status = "Not Found"
        reason = "No enabled provider returned part data for the requested identity."
    elif errors or skipped:
        status = "Review Required"
        reason = "No provider identity match could be confirmed because collection was incomplete."
    else:
        status = "Not Found"
        reason = "No provider returned usable part data."

    details = []
    if errors:
        details.append(f"Errors: {', '.join(errors)}")
    if skipped:
        details.append(f"Skipped: {', '.join(skipped)}")
    if details:
        reason = f"{reason} {'; '.join(details)}."
    return status, reason


def engineering_confirmation(evidence: Iterable[ProviderEvidence]) -> str:
    matched_profiles = [item.part_profile or {} for item in evidence if item.identity_match]
    if not matched_profiles:
        return "No matched provider data"
    if len(matched_profiles) == 1:
        return "Single provider evidence"

    comparable_fields = ("package", "mounting_type", "lifecycle_status", "rohs_status")
    compared = 0
    disagreements = 0
    for field in comparable_fields:
        values = [normalise_engineering(profile.get(field)) for profile in matched_profiles]
        values = [value for value in values if value]
        if len(values) >= 2:
            compared += 1
            if len(set(values)) > 1:
                disagreements += 1
    if compared == 0:
        return "Multiple providers; insufficient common fields"
    if disagreements:
        return f"Differences present ({disagreements}/{compared} common fields)"
    return f"Confirmed across providers ({compared} common fields)"


def merged_value(evidence: Iterable[ProviderEvidence], field: str) -> str:
    values: list[tuple[str, str]] = []
    for item in evidence:
        if not item.identity_match:
            continue
        value = str((item.part_profile or {}).get(field) or "").strip()
        if value:
            values.append((item.provider, value))
    if not values:
        return ""
    normalised = {normalise_engineering(value) for _, value in values}
    if len(normalised) == 1:
        return values[0][1]
    return "\n".join(f"{provider}: {value}" for provider, value in values)


def provider_availability(profile: dict[str, Any] | None) -> Any:
    profile = profile or {}
    value = profile.get("product_quantity_available")
    if value not in (None, ""):
        return value
    quantities = [offer.get("quantity_available") for offer in commercial_offers(profile)]
    numeric = [value for value in quantities if isinstance(value, (int, float))]
    return max(numeric) if numeric else ""
