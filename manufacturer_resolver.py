from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher


# Words that commonly vary between a Parts Master and distributor catalogues.
# They are removed only for comparison; the original names are always retained.
IGNORED_WORDS = {
    'inc', 'incorporated', 'ltd', 'limited', 'llc', 'plc', 'corp',
    'corporation', 'company', 'co', 'gmbh', 'ag', 'sa', 'nv', 'bv',
    'pte', 'pty', 'srl', 'spa', 'kg', 'kk',
    'electronics', 'electronic', 'semiconductor', 'semiconductors',
    'technology', 'technologies', 'international',
}

# Explicit aliases are reserved for names that are genuinely different after
# corporate-suffix normalisation. Keep this table small and auditable.
ALIASES = {
    'analog devices maxim integrated': 'analog devices maxim integrated',
    'analog devices maxim': 'analog devices maxim integrated',
    'maxim integrated': 'analog devices maxim integrated',
    'on semiconductor': 'onsemi',
    'on semi': 'onsemi',
    'amphenol cs': 'amphenol icc fci',
    'amphenol fci': 'amphenol icc fci',
    'te connectivity': 'te connectivity amp',
    'wurth': 'wurth elektronik',
    'wurth elektronik': 'wurth elektronik',
}


@dataclass(frozen=True)
class ManufacturerResolution:
    manufacturer_id: int | None
    matched_name: str
    confidence: float
    status: str
    reason: str
    method: str = ''


def _ascii(value: str) -> str:
    return unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode()


def normalise_name(value: str) -> str:
    """Return a comparison form without changing the stored manufacturer name."""
    words = re.findall(r'[a-z0-9]+', _ascii(value).lower())
    useful = [word for word in words if word not in IGNORED_WORDS]
    result = ' '.join(useful)
    return ALIASES.get(result, result)


def names_equivalent(first: str, second: str) -> bool:
    """True when two names are identical after controlled normalisation."""
    left = normalise_name(first)
    right = normalise_name(second)
    return bool(left and right and left == right)


def manufacturer_similarity(first: str, second: str) -> float:
    """Controlled similarity score used only after exact normalisation fails."""
    left = normalise_name(first)
    right = normalise_name(second)
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0

    left_words = set(left.split())
    right_words = set(right.split())
    token_score = len(left_words & right_words) / len(left_words | right_words)
    sequence_score = SequenceMatcher(None, left, right).ratio()
    containment = 0.95 if left in right or right in left else 0.0
    return max(token_score, sequence_score, containment)


def _manufacturer_items(payload: dict) -> list[dict]:
    items = payload.get('Manufacturers') or payload.get('manufacturers') or []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def resolve_manufacturer(requested_name: str, payload: dict) -> ManufacturerResolution:
    if not requested_name.strip():
        return ManufacturerResolution(
            None, '', 0.0, 'NO_MANUFACTURER', 'No manufacturer supplied.', 'none'
        )

    scored: list[tuple[float, str, int]] = []
    for item in _manufacturer_items(payload):
        candidate_name = str(item.get('Name') or item.get('name') or '')
        candidate_id = item.get('Id') if 'Id' in item else item.get('id')
        try:
            candidate_id = int(candidate_id)
        except (TypeError, ValueError):
            continue
        scored.append((manufacturer_similarity(requested_name, candidate_name), candidate_name, candidate_id))

    if not scored:
        return ManufacturerResolution(
            None, '', 0.0, 'NOT_FOUND', 'DigiKey manufacturer list was empty.', 'none'
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_name, best_id = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0

    if names_equivalent(requested_name, best_name):
        return ManufacturerResolution(
            best_id,
            best_name,
            1.0,
            'RESOLVED',
            'Exact normalised manufacturer match.',
            'normalised_exact',
        )
    if best_score >= 0.90 and best_score - second_score >= 0.05:
        return ManufacturerResolution(
            best_id,
            best_name,
            best_score,
            'RESOLVED',
            'Strong unique manufacturer match.',
            'fuzzy_high',
        )
    if best_score >= 0.75 and best_score - second_score >= 0.15:
        return ManufacturerResolution(
            best_id,
            best_name,
            best_score,
            'RESOLVED',
            'Unique manufacturer match above threshold.',
            'fuzzy_unique',
        )

    return ManufacturerResolution(
        None,
        best_name,
        best_score,
        'REVIEW',
        f'Manufacturer could not be resolved uniquely; best candidate was {best_name!r}.',
        'review',
    )
