"""Sprint 4.6.2a intelligent local candidate matching.

Uses the enriched Parts Master index only.  No provider/API calls and no
engineering approvals.  Descriptive BOM rows are parsed into explicit
engineering requirements and candidates are filtered/ranked against every
available matching technical attribute in the Parts Master index.

Important governance rule: only attributes explicitly present in the BOM are
allowed to reject a candidate.  Missing BOM attributes cannot be invented.
"""
from __future__ import annotations

import json
import math
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bom_intake_classifier import classify_source_bom, CLASS_MFG_MPN, CLASS_VALUE_FOOTPRINT
from manufacturer_resolver import resolve_manufacturer

STATUS_PM_EXACT = "Parts Master Match"
STATUS_INTELLIGENT = "Intelligent Local Candidate"
STATUS_MULTIPLE = "Multiple Intelligent Local Candidates"
STATUS_UNRESOLVED = "Unresolved"

_CAP_DIELECTRICS = ("C0G", "COG", "NP0", "NPO", "X5R", "X7R", "X8R", "Y5V", "Z5U")
_TECH_WORDS = {
    "CER": "ceramic", "CERAMIC": "ceramic", "MLCC": "ceramic",
    "TANT": "tantalum", "TANTALUM": "tantalum",
    "THICK FILM": "thick film", "THIN FILM": "thin film",
    "METAL FILM": "metal film", "WIREWOUND": "wirewound",
}


def _clean(v: Any) -> str:
    return " ".join(str(v or "").strip().split())


def _norm_text(v: Any) -> str:
    return _clean(v).casefold()


def _package_key(text: Any) -> str:
    s = _clean(text).upper()
    # KiCad footprint names normally encode imperial size before metric size.
    m = re.search(r"(?:^|[_:\-])(01005|0201|0402|0603|0805|1206|1210|1812)(?:[_:\-]|$)", s)
    if m:
        return m.group(1)
    m = re.search(r"\b(01005|0201|0402|0603|0805|1206|1210|1812)\b", s)
    return m.group(1) if m else _norm_text(s)


def _reference_family(reference: Any) -> str | None:
    ref = _clean(reference).upper()
    first = re.match(r"[A-Z]+", ref)
    prefix = first.group(0) if first else ""
    return {
        "C": "CAP", "R": "RES", "L": "IND", "FB": "FER",
        "D": "DIO", "LED": "LED", "Q": "TRA", "U": "IC",
        "J": "CON", "SW": "SWT", "Y": "OSC",
    }.get(prefix)


def _num_with_unit(text: str, unit: str) -> float | None:
    # SI prefixes are case-sensitive here: M=mega, m=milli.
    m = re.search(r"(?<![A-Za-z0-9])([0-9]+(?:\.[0-9]+)?)\s*([pnumkMµu]?)\s*" + re.escape(unit) + r"\b", text, re.I)
    if not m:
        return None
    prefix = m.group(2)
    factors = {"": 1.0, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6,
               "m": 1e-3, "k": 1e3, "K": 1e3, "M": 1e6}
    return float(m.group(1)) * factors.get(prefix, factors.get(prefix.lower(), 1.0))


def _parse_capacitance(text: Any) -> float | None:
    s = _clean(text).replace("μ", "µ")
    # allow familiar BOM notation without F, e.g. 10uF / 10u
    m = re.search(r"(?<![A-Za-z0-9])([0-9]+(?:\.[0-9]+)?)\s*([pnumµu])\s*F?\b", s, re.I)
    if not m:
        return None
    factors = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3}
    return float(m.group(1)) * factors[m.group(2).lower()]


def _parse_resistance(text: Any) -> float | None:
    s = _clean(text).replace("Ω", "R")
    # IEC embedded decimal: 4K7, 2R2
    m = re.search(r"(?<![A-Za-z0-9])([0-9]+)([RrKkMm])([0-9]+)(?![A-Za-z0-9])", s)
    if m:
        f = {"r": 1.0, "k": 1e3, "m": 1e6}[m.group(2).lower()]
        return (float(m.group(1)) + float("0." + m.group(3))) * f
    m = re.search(r"(?<![A-Za-z0-9])([0-9]+(?:\.[0-9]+)?)\s*([RrKkMm])(?:\b|$)", s)
    if m:
        f = {"r": 1.0, "k": 1e3, "m": 1e6}[m.group(2).lower()]
        return float(m.group(1)) * f
    # explicit ohm word or bare numeric on resistor rows
    m = re.search(r"(?<![A-Za-z0-9])([0-9]+(?:\.[0-9]+)?)\s*(?:OHM|R)?(?:\b|$)", s, re.I)
    return float(m.group(1)) if m else None


def _parse_voltage(text: Any) -> float | None:
    s = _clean(text)
    m = re.search(r"(?<![A-Za-z0-9])([0-9]+(?:\.[0-9]+)?)\s*V\b", s, re.I)
    return float(m.group(1)) if m else None


def _parse_tolerance(text: Any) -> float | None:
    s = _clean(text).replace("±", "")
    m = re.search(r"(?<![0-9])([0-9]+(?:\.[0-9]+)?)\s*%", s)
    return float(m.group(1)) if m else None


def _parse_dielectric(text: Any) -> str | None:
    s = _clean(text).upper().replace("COG", "C0G").replace("NPO", "NP0")
    for token in _CAP_DIELECTRICS:
        canonical = token.replace("COG", "C0G").replace("NPO", "NP0")
        if canonical in s:
            return canonical
    return None


def _parse_technology(text: Any) -> str | None:
    s = _clean(text).upper()
    for token, val in _TECH_WORDS.items():
        if token in s:
            return val
    return None


def _float_equal(a: float | None, b: float | None, rel: float = 1e-6) -> bool:
    return a is not None and b is not None and math.isclose(a, b, rel_tol=rel, abs_tol=1e-15)


def _tech_value(part: dict, name: str) -> Any:
    item = (part.get("Technical_Attributes") or {}).get(name) or {}
    if isinstance(item, dict):
        return item.get("Value")
    return item


def _part_capacitance(part: dict) -> float | None:
    value = _tech_value(part, "Capacitance")
    return _parse_capacitance(value) if value else _coerce_numeric_nominal(part.get("Value_Nominal"))


def _part_resistance(part: dict) -> float | None:
    value = _tech_value(part, "Resistance")
    return _parse_resistance(value) if value else _coerce_numeric_nominal(part.get("Value_Nominal"))


def _coerce_numeric_nominal(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _part_voltage(part: dict) -> float | None:
    v = _tech_value(part, "Voltage_Rated")
    return _parse_voltage(v) if v else None


def _part_tolerance(part: dict) -> float | None:
    v = _tech_value(part, "Tolerance")
    return _parse_tolerance(v) if v else None


def _part_dielectric(part: dict) -> str | None:
    return _parse_dielectric(_tech_value(part, "Dielectric"))


def _part_technology(part: dict) -> str | None:
    direct = _parse_technology(_tech_value(part, "Technology"))
    if direct:
        return direct
    subtype = _parse_technology(_tech_value(part, "Component_Subtype"))
    if subtype:
        return subtype
    return _parse_technology(part.get("Description"))


def _part_package(part: dict) -> str:
    return _package_key(_tech_value(part, "Package") or part.get("Footprint") or part.get("Package_Secondary"))


@dataclass(frozen=True)
class BOMRequirements:
    family: str | None
    package: str
    nominal_value: float | None
    nominal_label: str
    voltage: float | None = None
    tolerance: float | None = None
    dielectric: str | None = None
    technology: str | None = None
    pulse_rated: bool = False

    def explicit_attributes(self) -> list[str]:
        names = ["Family", "Value", "Footprint"]
        if self.voltage is not None: names.append("Voltage")
        if self.tolerance is not None: names.append("Tolerance")
        if self.dielectric: names.append("Dielectric")
        if self.technology: names.append("Technology")
        if self.pulse_rated: names.append("Pulse Rated")
        return names


def parse_bom_requirements(record: dict) -> BOMRequirements:
    ref = _clean(record.get("Reference"))
    value = _clean(record.get("Value"))
    footprint = _clean(record.get("Footprint"))
    family = _reference_family(ref)
    if family == "CAP":
        nominal = _parse_capacitance(value)
    elif family == "RES":
        nominal = _parse_resistance(value)
    else:
        nominal = None
    return BOMRequirements(
        family=family,
        package=_package_key(footprint),
        nominal_value=nominal,
        nominal_label=value,
        voltage=_parse_voltage(value),
        tolerance=_parse_tolerance(value),
        dielectric=_parse_dielectric(value),
        technology=_parse_technology(value),
        pulse_rated="PULSE" in value.upper(),
    )


@dataclass
class CandidateAssessment:
    part: dict
    matched: list[str]
    unknown: list[str]
    rejected: list[str]
    score: int

    @property
    def viable(self) -> bool:
        return not self.rejected


class PartsMasterIndex:
    def __init__(self, index_path: str | Path = "Parts_Master/parts_master_index.json"):
        self.path = Path(index_path)
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.parts = payload.get("parts", [])
        self.by_mpn: dict[str, list[dict]] = {}
        self.manufacturers = sorted({_clean(p.get("Manufacturer")) for p in self.parts if _clean(p.get("Manufacturer"))})
        for p in self.parts:
            mpn = _norm_text(p.get("MPN"))
            if mpn:
                self.by_mpn.setdefault(mpn, []).append(p)

    def exact_identity(self, manufacturer: str, mpn: str) -> list[dict]:
        found = []
        for p in self.by_mpn.get(_norm_text(mpn), []):
            pmfg = _clean(p.get("Manufacturer"))
            if _norm_text(manufacturer) == _norm_text(pmfg):
                found.append(p); continue
            res = resolve_manufacturer(manufacturer, self.manufacturers)
            if res.status == "RESOLVED" and _norm_text(res.standard_name) == _norm_text(pmfg):
                found.append(p)
        return found

    def assess_descriptive(self, req: BOMRequirements) -> tuple[list[CandidateAssessment], list[CandidateAssessment]]:
        viable: list[CandidateAssessment] = []
        rejected: list[CandidateAssessment] = []
        for p in self.parts:
            # Candidate discovery gate: same component family, nominal value and package.
            if req.family and _clean(p.get("Family")).upper() != req.family:
                continue
            if req.package and _part_package(p) != req.package:
                continue
            if req.nominal_value is not None:
                pnom = _part_capacitance(p) if req.family == "CAP" else _part_resistance(p) if req.family == "RES" else None
                if not _float_equal(req.nominal_value, pnom):
                    continue

            matched: list[str] = []
            unknown: list[str] = []
            fail: list[str] = []
            if req.family: matched.append(f"Family={req.family}")
            if req.nominal_value is not None: matched.append(f"Value={req.nominal_label}")
            if req.package: matched.append(f"Footprint={req.package}")

            # Only explicit BOM requirements below can reject a candidate.
            if req.voltage is not None:
                pv = _part_voltage(p)
                if pv is None: unknown.append("Voltage")
                elif pv + 1e-12 < req.voltage: fail.append(f"Voltage {pv:g}V < required {req.voltage:g}V")
                else: matched.append(f"Voltage≥{req.voltage:g}V")
            if req.tolerance is not None:
                pt = _part_tolerance(p)
                if pt is None: unknown.append("Tolerance")
                elif pt > req.tolerance + 1e-12: fail.append(f"Tolerance ±{pt:g}% worse than required ±{req.tolerance:g}%")
                else: matched.append(f"Tolerance≤±{req.tolerance:g}%")
            if req.dielectric:
                pd = _part_dielectric(p)
                if pd is None: unknown.append("Dielectric")
                elif pd != req.dielectric: fail.append(f"Dielectric {pd} != required {req.dielectric}")
                else: matched.append(f"Dielectric={req.dielectric}")
            if req.technology:
                pt = _part_technology(p)
                if pt is None: unknown.append("Technology")
                elif pt != req.technology: fail.append(f"Technology {pt} != required {req.technology}")
                else: matched.append(f"Technology={req.technology}")
            if req.pulse_rated:
                desc = _clean(p.get("Description")).upper()
                tech = _clean(_tech_value(p, "Pulse_Rated")).upper()
                if "PULSE" in desc or tech in {"YES", "TRUE", "PULSE", "PULSE RATED"}:
                    matched.append("Pulse Rated")
                else:
                    unknown.append("Pulse Rated")

            score = len(matched) * 10 - len(unknown) * 2
            a = CandidateAssessment(p, matched, unknown, fail, score)
            (viable if a.viable else rejected).append(a)

        viable.sort(key=lambda a: (-a.score, _clean(a.part.get("Manufacturer")), _clean(a.part.get("MPN"))))
        rejected.sort(key=lambda a: (_clean(a.part.get("Manufacturer")), _clean(a.part.get("MPN"))))
        return viable, rejected


@dataclass
class IntelligentMatch:
    intake: Any
    status: str
    method: str
    candidates: list[CandidateAssessment]
    rejected_count: int
    justification: str

    def output_rows(self):
        base = self.intake.as_output_record()
        rows = self.candidates or [None]
        for rank, assessment in enumerate(rows, 1):
            out = OrderedDict()
            for k in ("Classification", "Classification Reason", "Next Action"):
                out[k] = base.get(k, "")
            out["Match Status"] = self.status
            out["Match Method"] = self.method
            out["Candidate Count"] = len(self.candidates)
            out["Locally Rejected Count"] = self.rejected_count
            out["Candidate Rank"] = rank if assessment else ""
            p = assessment.part if assessment else {}
            out["Matched AIPN"] = p.get("AIPN") or ""
            out["Candidate Manufacturer"] = p.get("Manufacturer", "")
            out["Candidate MPN"] = p.get("MPN", "")
            out["Candidate Description"] = p.get("Description", "")
            out["Matched Engineering Attributes"] = "; ".join(assessment.matched) if assessment else ""
            out["Candidate Attributes Needing Verification"] = "; ".join(assessment.unknown) if assessment else ""
            out["PDC Justification"] = self.justification if not assessment else _candidate_justification(assessment)
            for k in ("MFG", "MPN", "Value", "Datasheet", "Footprint", "Quantity", "Reference", "DNP"):
                out[k] = base.get(k, "")
            yield out


def _candidate_justification(a: CandidateAssessment) -> str:
    msg = "Candidate satisfies all engineering requirements explicitly available in the BOM"
    if a.matched:
        msg += ": " + ", ".join(a.matched)
    if a.unknown:
        msg += ". Candidate data is incomplete for: " + ", ".join(a.unknown)
    return msg + ". Engineering approval is still required."


class IntelligentLocalMatcher:
    def __init__(self, index_path: str | Path = "Parts_Master/parts_master_index.json"):
        self.index = PartsMasterIndex(index_path)

    def match(self, intake) -> IntelligentMatch:
        b = intake.normalised_record
        if intake.classification == CLASS_MFG_MPN:
            exact = self.index.exact_identity(_clean(b.get("MFG")), _clean(b.get("MPN")))
            assessments = [CandidateAssessment(p, ["Manufacturer", "MPN"], [], [], 100) for p in exact]
            if assessments:
                return IntelligentMatch(intake, STATUS_PM_EXACT, "Parts Master Index MFG + MPN", assessments, 0,
                                        "Exact local identity found in Parts Master Index; no provider call made.")
            return IntelligentMatch(intake, STATUS_UNRESOLVED, "Parts Master Index MFG + MPN", [], 0,
                                    "No compatible MFG + MPN identity found locally. Eligible for later provider search.")

        if intake.classification == CLASS_VALUE_FOOTPRINT:
            req = parse_bom_requirements(b)
            viable, rejected = self.index.assess_descriptive(req)
            if len(viable) == 1:
                status = STATUS_INTELLIGENT
            elif len(viable) > 1:
                status = STATUS_MULTIPLE
            else:
                status = STATUS_UNRESOLVED
            why = (
                "Candidates are discovered by component family + nominal value + footprint, then qualified using every additional engineering requirement explicitly present in the BOM."
                if viable else
                "No Parts Master candidate satisfies the locally available engineering requirements. No provider call made."
            )
            return IntelligentMatch(intake, status, "Attribute-aware Parts Master Index", viable, len(rejected), why)

        return IntelligentMatch(intake, STATUS_UNRESOLVED, "No local matching path", [], 0,
                                "Insufficient identity for current local matching paths.")


def match_source_bom(source_bom: str | Path, index_path: str | Path = "Parts_Master/parts_master_index.json"):
    result, intake = classify_source_bom(source_bom)
    matcher = IntelligentLocalMatcher(index_path)
    return result, intake, [matcher.match(x) for x in intake]
