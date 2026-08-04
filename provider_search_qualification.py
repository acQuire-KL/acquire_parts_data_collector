"""Provider search qualification and candidate capture.

Sprint 4.4 Patch 3 keeps provider evidence separate from engineering approval.
Candidates may be ranked, but this module never selects a candidate or updates
any Parts Master record.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from typing import Any, Iterable

from manufacturer_resolver import manufacturer_similarity, names_equivalent

STATUS_EXACT_MATCH = "Exact Match"
STATUS_ALIAS_MATCH = "Alias Match"
STATUS_MULTIPLE_CANDIDATES = "Multiple Candidates"
STATUS_NOT_FOUND = "Not Found"
STATUS_PROVIDER_ERROR = "Provider Error"


def normalise_mpn(value: object) -> str:
    """Comparison-only MPN form; the source and returned values are preserved."""
    return "".join(character for character in str(value or "").casefold() if character.isalnum())


@dataclass(frozen=True, slots=True)
class ProviderCandidate:
    provider: str
    source_manufacturer: str
    source_mpn: str
    returned_manufacturer: str
    returned_mpn: str
    provider_part_number: str = ""
    description: str = ""
    product_url: str = ""
    manufacturer_id: int | None = None
    source_stage: str = "MPN-only fallback"
    rank: int = 0
    manufacturer_score: float = 0.0
    mpn_exact: bool = False
    manufacturer_equivalent: bool = False

    def to_row(self, record_id: str) -> OrderedDict[str, object]:
        return OrderedDict([
            ("Record ID", record_id),
            ("Provider", self.provider),
            ("Source Manufacturer", self.source_manufacturer),
            ("Source MPN", self.source_mpn),
            ("Candidate Rank", self.rank),
            ("Returned Manufacturer", self.returned_manufacturer),
            ("Returned MPN", self.returned_mpn),
            ("Provider Part Number", self.provider_part_number),
            ("Description", self.description),
            ("Product URL", self.product_url),
            ("Manufacturer ID", self.manufacturer_id if self.manufacturer_id is not None else ""),
            ("Source Stage", self.source_stage),
            ("MPN Exact", self.mpn_exact),
            ("Manufacturer Equivalent", self.manufacturer_equivalent),
            ("Manufacturer Score", round(self.manufacturer_score, 4)),
            ("Approval Status", "Review Required"),
        ])


def _first(mapping: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in mapping and mapping[name] not in (None, ""):
            return mapping[name]
    return None


def _manufacturer(item: dict[str, Any]) -> tuple[str, int | None]:
    value = _first(item, "Manufacturer", "manufacturer")
    if isinstance(value, dict):
        name = str(_first(value, "Name", "name") or "")
        raw_id = _first(value, "Id", "id")
    else:
        name = str(value or _first(item, "ManufacturerName", "manufacturerName") or "")
        raw_id = _first(item, "ManufacturerId", "manufacturerId")
    try:
        return name, int(raw_id) if raw_id is not None else None
    except (TypeError, ValueError):
        return name, None


def _digikey_products(payload: dict[str, Any]) -> list[dict[str, Any]]:
    products = payload.get("Products") or payload.get("products") or []
    if isinstance(products, dict):
        products = products.get("Items") or products.get("items") or []
    return [item for item in products if isinstance(item, dict)] if isinstance(products, list) else []


def extract_digikey_candidates(
    payload: dict[str, Any], source_manufacturer: str, source_mpn: str
) -> list[ProviderCandidate]:
    candidates: list[ProviderCandidate] = []
    for item in _digikey_products(payload):
        manufacturer, manufacturer_id = _manufacturer(item)
        returned_mpn = str(_first(
            item, "ManufacturerProductNumber", "manufacturerProductNumber",
            "ManufacturerPartNumber", "manufacturerPartNumber"
        ) or "")
        provider_number = str(_first(item, "DigiKeyProductNumber", "digiKeyProductNumber", "ProductNumber") or "")
        description_value = _first(item, "Description", "description", "DetailedDescription", "detailedDescription")
        if isinstance(description_value, dict):
            description_value = _first(description_value, "ProductDescription", "productDescription", "DetailedDescription")
        product_url = str(_first(item, "ProductUrl", "ProductURL", "productUrl") or "")
        mpn_exact = bool(normalise_mpn(source_mpn) and normalise_mpn(source_mpn) == normalise_mpn(returned_mpn))
        equivalent = names_equivalent(source_manufacturer, manufacturer)
        score = manufacturer_similarity(source_manufacturer, manufacturer)
        candidates.append(ProviderCandidate(
            provider="DigiKey",
            source_manufacturer=source_manufacturer,
            source_mpn=source_mpn,
            returned_manufacturer=manufacturer,
            returned_mpn=returned_mpn,
            provider_part_number=provider_number,
            description=str(description_value or ""),
            product_url=product_url,
            manufacturer_id=manufacturer_id,
            manufacturer_score=score,
            mpn_exact=mpn_exact,
            manufacturer_equivalent=equivalent,
        ))
    # Exact MPN first, then source-manufacturer agreement, then similarity.
    ordered = sorted(
        candidates,
        key=lambda item: (item.mpn_exact, item.manufacturer_equivalent, item.manufacturer_score),
        reverse=True,
    )
    return [replace(item, rank=rank) for rank, item in enumerate(ordered, start=1)]


def qualification_status(candidates: Iterable[ProviderCandidate]) -> str:
    values = list(candidates)
    if not values:
        return STATUS_NOT_FOUND
    agreeing = [item for item in values if item.mpn_exact and item.manufacturer_equivalent]
    if len(values) == 1 and agreeing:
        return STATUS_ALIAS_MATCH
    return STATUS_MULTIPLE_CANDIDATES
