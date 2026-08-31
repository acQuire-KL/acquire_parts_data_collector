"""BOM identity recovery and manufacturer variant discovery for Sprint 4.7.2.

The module deliberately separates *candidate discovery* from identity approval.
A candidate may be strongly supported by provider evidence and still remains a
review item until the engineering identity/orderable variant is confirmed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Iterable
import math

from manufacturer_resolver import names_equivalent


def normalise_mpn(value: Any) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def _text(value: Any) -> str:
    return str(value or "").strip()


_COMMON_VALUE_RE = re.compile(
    r"^\s*[0-9.]+\s*(?:R|K|M|OHM|PF|NF|UF|µF|MF|NH|UH|µH|MH|V|A|MA|HZ|KHZ|MHZ|GHZ|%)\s*$",
    re.IGNORECASE,
)


def looks_like_mpn(value: Any) -> bool:
    """Conservative test for a BOM field that plausibly contains an MPN.

    It intentionally rejects common passive values such as 10k, 100nF and 3.3V.
    Manufacturer order codes containing punctuation are retained unchanged.
    """
    text = _text(value)
    if len(text) < 4 or len(text) > 80:
        return False
    if _COMMON_VALUE_RE.match(text):
        return False
    compact = normalise_mpn(text)
    if len(compact) < 4:
        return False
    has_alpha = any(ch.isalpha() for ch in compact)
    has_digit = any(ch.isdigit() for ch in compact)
    return has_alpha and has_digit




@dataclass(frozen=True)
class SearchVariant:
    text: str
    kind: str
    reduction_percent: int = 0


def search_variants(value: Any) -> list[SearchVariant]:
    """Build traceable discovery forms without altering the source search text."""
    source = _text(value)
    if not source:
        return []
    alpha = normalise_mpn(source)
    variants = [SearchVariant(source, "Source Search Text")]
    if alpha and alpha != source.upper():
        variants.append(SearchVariant(alpha, "Alphanumeric Search Key"))
    return variants


def family_search_variants(value: Any) -> list[SearchVariant]:
    """Controlled right-truncation keys for family discovery.

    The search stops at a conservative 25% maximum reduction floor.  These keys are
    discovery-only and can never establish identity by themselves.
    """
    alpha = normalise_mpn(value)
    n = len(alpha)
    if n < 10:
        return []
    max_reduction = 0.25
    floor = max(6, math.ceil(n * (1.0 - max_reduction)))
    # Prefer useful steps rather than one API call per removed character.
    lengths = []
    step = max(1, round(n * 0.10))
    length = n - step
    while length >= floor:
        lengths.append(length)
        length -= step
    if floor not in lengths and floor < n:
        lengths.append(floor)
    seen = set()
    result = []
    for length in lengths:
        key = alpha[:length]
        if key in seen or key == alpha:
            continue
        seen.add(key)
        reduction = round((n - length) * 100 / n)
        result.append(SearchVariant(key, "Family Search Key", reduction))
    return result


@dataclass(frozen=True)
class RecoveryCandidate:
    manufacturer: str
    mpn: str
    relationship: str
    sources: tuple[str, ...] = ()
    package: str = ""
    datasheet_url: str = ""
    footprint_check: str = "Not assessed"
    notes: str = ""


def recover_mpn_from_bom(manufacturer: str, requested_mpn: str, bom_context: dict[str, Any] | None) -> RecoveryCandidate | None:
    """Recover a *candidate* MPN from BOM context without changing the BOM MPN."""
    if _text(requested_mpn):
        return None
    context = bom_context or {}
    for key, label in (("value", "BOM Value"), ("description", "BOM Description")):
        value = _text(context.get(key))
        if looks_like_mpn(value):
            return RecoveryCandidate(
                manufacturer=_text(manufacturer),
                mpn=value,
                relationship="Recovered MPN candidate",
                sources=(label,),
                notes="Input MPN is blank; candidate recovered from BOM context. Review required.",
            )
    return None


def classify_mpn_relationship(reference_mpn: str, candidate_mpn: str) -> str:
    """Classify a candidate relative to an input/search MPN without approving it."""
    reference = normalise_mpn(reference_mpn)
    candidate = normalise_mpn(candidate_mpn)
    if not reference or not candidate:
        return "Unknown relationship"
    if reference == candidate:
        return "Exact identity"

    # Controlled suffix discovery only.  The suffix is *not* assumed to be
    # packaging-only; it remains a candidate requiring evidence.
    if candidate.startswith(reference) and 1 <= len(candidate) - len(reference) <= 4:
        return "Orderable suffix variant candidate"
    if reference.startswith(candidate) and 1 <= len(reference) - len(candidate) <= 4:
        return "Truncated suffix candidate"

    # One-character edit can recover common BOM transcription mistakes, but is
    # intentionally never treated as an identity match.
    if min(len(reference), len(candidate)) >= 6 and _levenshtein_distance(reference, candidate) == 1:
        return "Near MPN candidate"
    return "Different variant candidate"


def _levenshtein_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(
                current[-1] + 1,
                previous[j] + 1,
                previous[j - 1] + (ca != cb),
            ))
        previous = current
    return previous[-1]


def footprint_consistency(bom_footprint: Any, candidate_package: Any, candidate_mpn: Any = "") -> str:
    """Return only strong footprint evidence; otherwise leave the comparison open.

    CAD footprint names and distributor package terminology vary substantially,
    so absence of token overlap is not automatically a conflict.
    """
    footprint = _text(bom_footprint).casefold()
    package = _text(candidate_package).casefold()
    mpn = _text(candidate_mpn).casefold()
    if not footprint:
        return "No BOM footprint"
    if not package and not mpn:
        return "Not assessed"

    compact_footprint = normalise_mpn(footprint)
    compact_mpn = normalise_mpn(mpn)
    if compact_mpn and len(compact_mpn) >= 6 and compact_mpn in compact_footprint:
        return "Consistent - MPN referenced by footprint"

    tokens = set(re.findall(r"[a-z]+\d+[a-z0-9]*|\d+[a-z]+[a-z0-9]*", footprint))
    package_tokens = set(re.findall(r"[a-z]+\d+[a-z0-9]*|\d+[a-z]+[a-z0-9]*", package))
    meaningful = {t for t in package_tokens if len(t) >= 3}
    if meaningful and tokens.intersection(meaningful):
        return "Consistent - package token match"
    return "Not assessed"


def candidate_from_profile(
    *, provider: str, requested_manufacturer: str, reference_mpn: str,
    profile: dict[str, Any], bom_footprint: Any = "",
) -> RecoveryCandidate | None:
    candidate_mpn = _text(profile.get("manufacturer_part_number"))
    candidate_mfg = _text(profile.get("manufacturer"))
    if not candidate_mpn or not names_equivalent(requested_manufacturer, candidate_mfg):
        return None
    relationship = classify_mpn_relationship(reference_mpn, candidate_mpn)
    if relationship == "Exact identity":
        return None
    package = _text(profile.get("package"))
    return RecoveryCandidate(
        manufacturer=candidate_mfg or requested_manufacturer,
        mpn=candidate_mpn,
        relationship=relationship,
        sources=(provider,),
        package=package,
        datasheet_url=_text(profile.get("datasheet_url")),
        footprint_check=footprint_consistency(bom_footprint, package, candidate_mpn),
        notes="Candidate discovered from provider evidence; not automatically approved or substituted.",
    )


def consolidate_candidates(candidates: Iterable[RecoveryCandidate]) -> list[RecoveryCandidate]:
    """Combine the same MFG+MPN candidate across providers without losing sources."""
    grouped: dict[tuple[str, str], list[RecoveryCandidate]] = {}
    for candidate in candidates:
        key = (normalise_mpn(candidate.manufacturer), normalise_mpn(candidate.mpn))
        grouped.setdefault(key, []).append(candidate)

    result: list[RecoveryCandidate] = []
    for group in grouped.values():
        # Prefer a provider/evidence-returned representation over raw BOM text
        # when both reduce to the same alphanumeric manufacturer order code.
        # This changes formatting only; different alphanumeric codes remain
        # different candidates (for example Hirose DS vs DP).
        provider_like = [
            item for item in group
            if any(source not in ("BOM Value", "BOM Description") for source in item.sources)
        ]
        first = next(
            (item for item in provider_like if item.relationship == "Formatting-normalised identity candidate"),
            provider_like[0] if provider_like else group[0],
        )
        sources = tuple(dict.fromkeys(source for item in group for source in item.sources))
        package_values = [item.package for item in group if item.package]
        datasheets = [item.datasheet_url for item in group if item.datasheet_url]
        footprint_checks = [item.footprint_check for item in group if item.footprint_check]
        relationship = next((item.relationship for item in group if item.relationship != "Different variant candidate"), first.relationship)
        result.append(RecoveryCandidate(
            manufacturer=first.manufacturer,
            mpn=first.mpn,
            relationship=relationship,
            sources=sources,
            package=package_values[0] if package_values else "",
            datasheet_url=datasheets[0] if datasheets else "",
            footprint_check=next((x for x in footprint_checks if x.startswith("Consistent")), footprint_checks[0] if footprint_checks else "Not assessed"),
            notes=first.notes,
        ))
    return sorted(result, key=lambda item: (normalise_mpn(item.mpn), item.relationship))


def discover_payload_candidates(provider: str, payload: Any, *, requested_manufacturer: str, reference_mpn: str, bom_footprint: Any = "") -> list[RecoveryCandidate]:
    """Extract manufacturer/order-code candidates from provider search payloads.

    This parser is intentionally permissive about provider JSON casing while
    conservative about manufacturer identity. It returns candidates only; it
    never changes the BOM or identity status.
    """
    provider_key = _text(provider).casefold()
    candidates: list[RecoveryCandidate] = []

    def add(mfg: Any, mpn: Any, package: Any = "", datasheet: Any = ""):
        mfg_text = _text(mfg)
        mpn_text = _text(mpn)
        if not mpn_text:
            return
        if mfg_text and requested_manufacturer and not names_equivalent(requested_manufacturer, mfg_text):
            return
        relationship = classify_mpn_relationship(reference_mpn, mpn_text)
        # In a provider SEARCH response an alphanumeric-equivalent MPN can be the
        # corrected punctuation/order-code we are trying to recover. Retain it.
        if relationship == "Exact identity":
            if provider_key == "digikey":
                if _text(reference_mpn) != mpn_text:
                    relationship = "Formatting-normalised identity candidate"
                else:
                    relationship = "Exact identity"
            else:
                return
        candidates.append(RecoveryCandidate(
            manufacturer=mfg_text or requested_manufacturer,
            mpn=mpn_text,
            relationship=relationship,
            sources=(provider,),
            package=_text(package),
            datasheet_url=_text(datasheet),
            footprint_check=footprint_consistency(bom_footprint, package, mpn_text),
            notes="Candidate discovered from provider search results; review required.",
        ))

    if not isinstance(payload, dict):
        return []
    # KnowledgeRecord wrappers are common in PDC.
    raw = payload.get("provider_response", payload)

    if provider_key == "mouser":
        results = raw.get("SearchResults") or raw.get("searchResults") or {}
        for part in results.get("Parts") or results.get("parts") or []:
            if not isinstance(part, dict):
                continue
            mfg = part.get("Manufacturer") or part.get("manufacturer")
            mpn = part.get("ManufacturerPartNumber") or part.get("manufacturerPartNumber")
            add(mfg, mpn, "", part.get("DataSheetUrl") or part.get("datasheetUrl"))
            for alt in part.get("AlternatePackagings") or []:
                if isinstance(alt, dict):
                    add(mfg, alt.get("APMfrPN") or alt.get("ManufacturerPartNumber"), "", part.get("DataSheetUrl"))

    elif provider_key == "tme":
        data = raw.get("data") or {}
        products = data.get("products") or {}
        for part in products.get("elements") or []:
            if not isinstance(part, dict):
                continue
            manufacturer = part.get("manufacturer") or {}
            mfg = manufacturer.get("name") if isinstance(manufacturer, dict) else manufacturer
            symbols = list(part.get("manufacturer_symbols") or [])
            if part.get("symbol"):
                symbols.append(part.get("symbol"))
            for symbol in symbols:
                add(mfg, symbol)

    elif provider_key == "digikey":
        # ProductInformation V4 keyword search has changed container names over
        # time, so walk likely lists and read common identity keys.
        stack = [raw]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                mpn = (item.get("ManufacturerProductNumber") or item.get("ManufacturerPartNumber")
                       or item.get("MfrPartNumber"))
                manufacturer = item.get("Manufacturer") or item.get("manufacturer")
                if isinstance(manufacturer, dict):
                    manufacturer = manufacturer.get("Name") or manufacturer.get("name")
                if mpn:
                    add(manufacturer, mpn, item.get("Package") or item.get("PackageType"),
                        item.get("DatasheetUrl") or item.get("DatasheetURL"))
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)

    return consolidate_candidates(candidates)
