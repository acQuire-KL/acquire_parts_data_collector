from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher


IGNORED_WORDS = {
    'inc', 'incorporated', 'ltd', 'limited', 'llc', 'plc', 'corp',
    'corporation', 'company', 'co', 'gmbh', 'ag', 'sa', 'nv', 'bv',
    'electronics', 'electronic', 'semiconductor', 'semiconductors',
    'technology', 'technologies', 'international',
}

# Common names in customer Parts Masters versus DigiKey's catalogue names.
ALIASES = {
    'analog devices maxim integrated': 'analog devices inc maxim integrated',
    'analog devices maxim': 'analog devices inc maxim integrated',
    'maxim integrated': 'analog devices inc maxim integrated',
    'on semiconductor': 'onsemi',
    'on semi': 'onsemi',
    'amphenol cs': 'amphenol icc fci',
    'amphenol fci': 'amphenol icc fci',
    'te connectivity': 'te connectivity amp',
    'wurth elektronik': 'wurth elektronik',
    'würth elektronik': 'wurth elektronik',
}


@dataclass(frozen=True)
class ManufacturerResolution:
    manufacturer_id: int | None
    matched_name: str
    confidence: float
    status: str
    reason: str


def _ascii(value: str) -> str:
    return unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode()


def normalise_name(value: str) -> str:
    words = re.findall(r'[a-z0-9]+', _ascii(value).lower())
    useful = [w for w in words if w not in IGNORED_WORDS]
    result = ' '.join(useful)
    return ALIASES.get(result, result)


def _score(requested: str, candidate: str) -> float:
    a = normalise_name(requested)
    b = normalise_name(candidate)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    a_words, b_words = set(a.split()), set(b.split())
    token_score = len(a_words & b_words) / len(a_words | b_words)
    sequence_score = SequenceMatcher(None, a, b).ratio()
    containment = 0.95 if a in b or b in a else 0.0
    return max(token_score, sequence_score, containment)


def _manufacturer_items(payload):
    items = payload.get('Manufacturers') or payload.get('manufacturers') or []
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict)]


def resolve_manufacturer(requested_name: str, payload: dict) -> ManufacturerResolution:
    if not requested_name.strip():
        return ManufacturerResolution(None, '', 0.0, 'NO_MANUFACTURER', 'No manufacturer supplied.')

    scored = []
    for item in _manufacturer_items(payload):
        candidate_name = str(item.get('Name') or item.get('name') or '')
        candidate_id = item.get('Id') if 'Id' in item else item.get('id')
        try:
            candidate_id = int(candidate_id)
        except (TypeError, ValueError):
            continue
        scored.append((_score(requested_name, candidate_name), candidate_name, candidate_id))

    if not scored:
        return ManufacturerResolution(None, '', 0.0, 'NOT_FOUND', 'DigiKey manufacturer list was empty.')

    scored.sort(reverse=True)
    best_score, best_name, best_id = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0

    if best_score == 1.0:
        return ManufacturerResolution(best_id, best_name, best_score, 'RESOLVED', 'Exact normalised manufacturer match.')
    if best_score >= 0.90 and best_score - second_score >= 0.05:
        return ManufacturerResolution(best_id, best_name, best_score, 'RESOLVED', 'Strong unique manufacturer match.')
    if best_score >= 0.75 and best_score - second_score >= 0.15:
        return ManufacturerResolution(best_id, best_name, best_score, 'RESOLVED', 'Unique manufacturer match above threshold.')

    return ManufacturerResolution(
        None,
        best_name,
        best_score,
        'REVIEW',
        f'Manufacturer could not be resolved uniquely; best candidate was {best_name!r}.',
    )
