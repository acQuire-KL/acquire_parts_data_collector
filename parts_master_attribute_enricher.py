"""Enrich the generated Parts Master index from stored provider technical JSON.

Sprint 4.6.1.2 principles:
- no live provider calls;
- compare only stored provider technical evidence;
- all available providers agree -> Provider Verified;
- one provider supplies the attribute -> Single Provider;
- providers disagree -> Needs Verification and no resolved value is asserted;
- no provider supplies the attribute -> attribute is omitted from Technical_Attributes.

Provider corroboration is not manufacturer verification.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import json
import re
import unicodedata
from typing import Any

SCHEMA_VERSION = "1.1"

# Commercial/logistics attributes are intentionally excluded from engineering enrichment.
_EXCLUDED = {
    "manufacturer", "packaging", "standard pack qty", "standard package",
    "manufacturer standard package", "kind of package", "price", "stock",
    "availability", "lead time", "minimum order quantity", "moq",
}

_ATTRIBUTE_ALIASES = {
    "capacitance": "Capacitance",
    "resistance": "Resistance",
    "inductance": "Inductance",
    "tolerance": "Tolerance",
    "voltage rated": "Voltage_Rated",
    "rated voltage": "Voltage_Rated",
    "operating voltage": "Voltage_Rated",
    "voltage operating": "Voltage_Rated",
    "dielectric": "Dielectric",
    "temperature coefficient": "Temperature_Coefficient",
    "power watts": "Power_Rating",
    "power rating": "Power_Rating",
    "current rating amps": "Current_Rating",
    "current rating": "Current_Rating",
    "operating temperature": "Operating_Temperature",
    "package case": "Package",
    "case inch": "Package",
    "supplier device package": "Supplier_Device_Package",
    "mounting type": "Mounting_Type",
    "mounting": "Mounting_Type",
    "type of capacitor": "Technology",
    "type of resistor": "Technology",
    "type of diode": "Technology",
    "type of integrated circuit": "Component_Type",
    "kind of capacitor": "Component_Subtype",
    "kind of integrated circuit": "Component_Subtype",
    "composition": "Composition",
    "frequency": "Frequency",
    "topology": "Topology",
    "input voltage": "Input_Voltage",
    "output voltage": "Output_Voltage",
    "output current": "Output_Current",
    "number of channels": "Channel_Count",
    "number of regulators": "Channel_Count",
    "features": "Features",
    "applications": "Applications",
    "size dimension": "Size_Dimension",
    "height seated max": "Height_Max",
    "thickness max": "Thickness_Max",
    "number of terminations": "Termination_Count",
}

_DIELECTRIC_CODES = re.compile(r"^(?:x[578][rs]|c0g|np0|y5v|z5u|u2j)$", re.I)


def _key(text: Any) -> str:
    s = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    s = s.lower().replace("+/-", " ")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def _attribute_name(raw_name: str, raw_value: Any = None) -> str:
    k = _key(raw_name)
    if k in _ATTRIBUTE_ALIASES:
        name = _ATTRIBUTE_ALIASES[k]
        # DigiKey uses Temperature Coefficient for both resistor ppm/°C and capacitor X5R/X7R.
        if name == "Temperature_Coefficient" and _DIELECTRIC_CODES.match(str(raw_value or "").strip()):
            return "Dielectric"
        return name
    # Preserve unknown technical attributes in a predictable machine-friendly form.
    return "_".join(word.capitalize() for word in k.split()) if k else ""


def _normalise_compare(value: Any, attribute_name: str = "") -> str:
    """Normalise formatting differences without pretending unlike engineering values are equal."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        vals = [_normalise_compare(v, attribute_name) for v in value if _normalise_compare(v, attribute_name)]
        return "|".join(sorted(set(vals)))
    s = str(value).strip().lower()
    if attribute_name == "Package":
        # Treat distributor forms such as "0603 (1608 Metric)" and "0603" as the same PCB package.
        m = re.search(r"(?<!\d)(0201|0402|0603|0805|1206|1210|1812|2010|2512)(?!\d)", s)
        if m:
            return m.group(1)
    if attribute_name == "Mounting_Type":
        if "surface mount" in s or "smd" in s or "smt" in s:
            return "smd"
        if "through hole" in s or "tht" in s:
            return "tht"
    if attribute_name == "Operating_Temperature":
        nums = re.findall(r"[-+]?\d+(?:\.\d+)?", s)
        if len(nums) >= 2:
            return f"{float(nums[0]):g}...{float(nums[1]):g}c"
    s = s.replace("μ", "u").replace("µ", "u").replace("ω", "ohm")
    s = s.replace("±", "").replace("+/-", "")
    s = s.replace("ohms", "ohm")
    s = re.sub(r"\s+", "", s)
    # Provider formatting commonly differs in range separators.
    s = s.replace("~", "...").replace("–", "-").replace("—", "-")
    s = s.replace("°", "")
    return s


def _clean_display(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def _mpn_key(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _part_profile_attributes(record: dict[str, Any]) -> dict[str, str]:
    pp = record.get("part_profile") or {}
    attrs: dict[str, str] = {}
    for raw_name, raw_value in (pp.get("attributes") or {}).items():
        if _key(raw_name) in _EXCLUDED or raw_value in (None, "", "-"):
            continue
        name = _attribute_name(raw_name, raw_value)
        if name:
            attrs[name] = _clean_display(raw_value)
    for raw_name, raw_value in {
        "Package / Case": pp.get("package"),
        "Mounting Type": pp.get("mounting_type"),
    }.items():
        if raw_value:
            attrs.setdefault(_attribute_name(raw_name, raw_value), _clean_display(raw_value))
    return attrs


def _tme_parameter_attributes(record: dict[str, Any]) -> dict[str, str]:
    attrs: dict[str, str] = {}
    elements = (((record.get("provider_response") or {}).get("data") or {}).get("elements") or [])
    for product in elements:
        params = (((product or {}).get("parameters") or {}).get("elements") or [])
        for param in params:
            raw_name = str(param.get("name") or "")
            if _key(raw_name) in _EXCLUDED:
                continue
            values = [v.get("value") for v in (param.get("values") or []) if v.get("value") not in (None, "", "-")]
            if not values:
                continue
            raw_value: Any = values[0] if len(values) == 1 else values
            name = _attribute_name(raw_name, raw_value)
            if name:
                attrs[name] = _clean_display(raw_value)
    return attrs


def build_provider_attribute_bank(knowledge_base: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Return MPN -> provider -> technical attributes from Current provider evidence."""
    bank: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    current = knowledge_base / "Current"

    sources = [
        ("DigiKey", current / "DigiKey" / "Product_Details", _part_profile_attributes),
        ("Mouser", current / "Mouser" / "Part_Number_Search", _part_profile_attributes),
        ("TME", current / "TME" / "Product_Parameters", _tme_parameter_attributes),
    ]
    for provider, folder, extractor in sources:
        if not folder.exists():
            continue
        for path in folder.glob("*.json"):
            record = _read_json(path)
            if not record:
                continue
            meta = record.get("knowledge_base_metadata") or {}
            pp = record.get("part_profile") or {}
            mpn = meta.get("input_mpn") or pp.get("manufacturer_part_number")
            if not mpn and provider == "TME":
                elems = (((record.get("provider_response") or {}).get("data") or {}).get("elements") or [])
                mpn = elems[0].get("symbol") if elems else None
            if not mpn:
                continue
            attrs = extractor(record)
            if attrs:
                bank[_mpn_key(mpn)][provider] = attrs
    return bank


def _merge_attribute(provider_values: dict[str, str], attribute_name: str = "") -> dict[str, Any]:
    usable = {p: v for p, v in provider_values.items() if v not in (None, "", "-")}
    if not usable:
        return {"Value": None, "Verification": "Not Available"}
    groups: dict[str, list[str]] = defaultdict(list)
    for provider, value in usable.items():
        groups[_normalise_compare(value, attribute_name)].append(provider)
    if len(usable) == 1:
        value = next(iter(usable.values()))
        return {"Value": value, "Verification": "Single Provider"}
    if len(groups) == 1:
        # Prefer the shortest clean representation when providers differ only in formatting.
        value = min(usable.values(), key=lambda x: (len(str(x)), str(x)))
        return {"Value": value, "Verification": "Provider Verified"}
    # Do not assert an engineering value when providers disagree.
    observed = []
    for value in usable.values():
        if value not in observed:
            observed.append(value)
    return {"Value": None, "Verification": "Needs Verification", "Observed_Values": observed}


def enrich_index(index_data: dict[str, Any], knowledge_base: Path) -> dict[str, Any]:
    result = deepcopy(index_data)
    bank = build_provider_attribute_bank(knowledge_base)
    summary = {
        "parts_total": 0,
        "parts_with_provider_technical_data": 0,
        "attributes_total": 0,
        "provider_verified": 0,
        "single_provider": 0,
        "needs_verification": 0,
    }
    for part in result.get("parts", []):
        summary["parts_total"] += 1
        per_provider = bank.get(_mpn_key(part.get("MPN")), {})
        by_attribute: dict[str, dict[str, str]] = defaultdict(dict)
        for provider, attrs in per_provider.items():
            for name, value in attrs.items():
                by_attribute[name][provider] = value
        merged: dict[str, dict[str, Any]] = {}
        for name in sorted(by_attribute):
            merged[name] = _merge_attribute(by_attribute[name], name)
            state = merged[name]["Verification"]
            summary["attributes_total"] += 1
            if state == "Provider Verified": summary["provider_verified"] += 1
            elif state == "Single Provider": summary["single_provider"] += 1
            elif state == "Needs Verification": summary["needs_verification"] += 1
        part["Technical_Attributes"] = merged
        part["Technical_Attribute_Summary"] = {
            "Provider_Count": len(per_provider),
            "Attribute_Count": len(merged),
            "Needs_Verification_Count": sum(1 for v in merged.values() if v["Verification"] == "Needs Verification"),
        }
        if merged:
            summary["parts_with_provider_technical_data"] += 1
    result["schema_version"] = SCHEMA_VERSION
    result["attribute_enrichment_summary"] = summary
    result["attribute_verification_definitions"] = {
        "Provider Verified": "Two or more stored providers supplied the attribute and agree after normalisation.",
        "Single Provider": "Only one stored provider supplied the attribute.",
        "Needs Verification": "Two or more stored providers supplied conflicting values; no resolved value is asserted.",
        "Not Available": "No stored provider supplied the attribute.",
        "note": "Provider Verified is distributor corroboration and is not manufacturer verification.",
    }
    return result


def enrich_index_file(index_path: Path, knowledge_base: Path, output_path: Path | None = None) -> tuple[Path, dict[str, Any]]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    enriched = enrich_index(data, knowledge_base)
    out = output_path or index_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(enriched, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out, enriched.get("attribute_enrichment_summary", {})
