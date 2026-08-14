"""Sprint 4.6.2 local BOM matching.

Uses only local source data: freshly normalised BOM, Parts Master, and the
current PDC Knowledge Base.  No provider/API calls and no automatic approval.
DNP rows are processed exactly like fitted rows; DNP remains assembly context.
"""
from __future__ import annotations
import json, math, re
from collections import OrderedDict, Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bom_intake_classifier import classify_source_bom, CLASS_MFG_MPN, CLASS_VALUE_FOOTPRINT
from parts_master_seed_importer import read_xlsx_rows, clean_text
from manufacturer_resolver import resolve_manufacturer

STATUS_EXACT_PM = "Parts Master Match"
STATUS_KB = "Knowledge Base Match"
STATUS_VALUE_UNIQUE = "Value + Footprint Candidate"
STATUS_VALUE_MULTIPLE = "Multiple Value + Footprint Candidates"
STATUS_UNRESOLVED = "Unresolved"


def _key(v): return clean_text(v).casefold()
def _mpn(v): return _key(v)

def _package_key(text: object) -> str:
    s=clean_text(text).upper()
    # KiCad standard footprints include both imperial and metric sizes.
    m=re.search(r'(?:^|[_:\-])(0201|0402|0603|0805|1206|1210|1812)(?:[_:\-]|$)', s)
    if m: return m.group(1)
    # Parts Master cases normally contain the package directly.
    m=re.search(r'\b(0201|0402|0603|0805|1206|1210|1812)\b', s)
    return m.group(1) if m else _key(s)


def _engineering_value(text: object, reference: str="") -> float | str | None:
    """Conservative value parser for resistor/capacitor descriptive matching."""
    raw=clean_text(text).replace('Ω','R').replace('ohm','R').replace('Ohm','R')
    if not raw: return None
    ref=clean_text(reference).upper()
    kind='C' if ref.startswith('C') else 'R' if ref.startswith('R') else ''
    s=raw.strip()
    try:
        return float(s)
    except ValueError: pass
    if kind=='C':
        m=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*([pPnNuUµmM])F?',s)
        if m:
            factors={'p':1e-12,'n':1e-9,'u':1e-6,'µ':1e-6,'m':1e-3}
            return float(m.group(1))*factors[m.group(2).lower()]
    if kind=='R':
        # 4K7, 2R2, 15.4k, 500M etc.
        m=re.fullmatch(r'([0-9]+)([RrKkMm])([0-9]+)',s)
        if m:
            f={'r':1,'k':1e3,'m':1e6}[m.group(2).lower()]
            return (float(m.group(1))+float('0.'+m.group(3)))*f
        m=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*([RrKkMm])?',s)
        if m:
            f={'':1,'r':1,'k':1e3,'m':1e6}[m.group(2).lower() if m.group(2) else '']
            return float(m.group(1))*f
    return _key(raw)


def _value_equal(a,b)->bool:
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-15)
    return a is not None and b is not None and a==b

@dataclass
class MatchRecord:
    intake: object
    status: str
    method: str
    candidates: list[dict]
    justification: str
    process_disposition: str = "Process"
    disposition_reason: str = "Normal component processing; DNP state does not alter identification processing."

    def output_rows(self):
        base=self.intake.as_output_record()
        cands=self.candidates or [{}]
        for i,c in enumerate(cands,1):
            out=OrderedDict()
            for k in ("Classification","Classification Reason","Next Action"):
                out[k]=base.get(k,"")
            out["Process Disposition"]=self.process_disposition
            out["Disposition Reason"]=self.disposition_reason
            out["Match Status"]=self.status
            out["Match Method"]=self.method
            out["Candidate Count"]=len(self.candidates)
            out["Candidate #"]=i if self.candidates else ""
            out["Matched AIPN"]=c.get("AIPN","")
            out["Legacy AIPN"]=c.get("AIPN - OLD","")
            out["Candidate Manufacturer"]=c.get("Manufacturer Name",c.get("manufacturer",""))
            out["Candidate MPN"]=c.get("Manufacturer Part Number",c.get("mpn",""))
            out["Candidate Description"]=c.get("Description","")
            out["PDC Justification"]=self.justification
            for k in ("MFG","MPN","Value","Datasheet","Footprint","Quantity","Reference","DNP"):
                out[k]=base.get(k,"")
            yield out

class LocalKnowledgeMatcher:
    def __init__(self, parts_master_path, knowledge_base_dir="Knowledge_Base/Current/Parts"):
        _,self.pm=read_xlsx_rows(parts_master_path)
        self.kb_dir=Path(knowledge_base_dir)
        self.pm_mpn={}
        for r in self.pm:
            if clean_text(r.get("Manufacturer Part Number")):
                self.pm_mpn.setdefault(_mpn(r["Manufacturer Part Number"]),[]).append(r)
        self.manufacturers=sorted({clean_text(r.get("Manufacturer Name")) for r in self.pm if clean_text(r.get("Manufacturer Name"))})
        self.kb={}
        if self.kb_dir.exists():
            for p in self.kb_dir.glob("*.json"):
                try:
                    d=json.loads(p.read_text(encoding="utf-8"))
                    m=d.get("requested_manufacturer",""); n=d.get("requested_mpn","")
                    if n: self.kb.setdefault(_mpn(n),[]).append((m,n,d,p))
                except (OSError,json.JSONDecodeError):
                    continue

    def _manufacturer_compatible(self, bom_mfg, candidate_mfg):
        if _key(bom_mfg)==_key(candidate_mfg): return True,"exact manufacturer"
        # Resolve BOM name against all PM manufacturers; only accept a resolved unique name.
        res=resolve_manufacturer(bom_mfg,self.manufacturers)
        return bool(res.status=="RESOLVED" and _key(res.standard_name)==_key(candidate_mfg)), res.reason

    def match(self,intake):
        b=intake.normalised_record; cls=intake.classification
        if cls==CLASS_MFG_MPN:
            mpn=clean_text(b.get("MPN")); mfg=clean_text(b.get("MFG"))
            pm=[]
            for r in self.pm_mpn.get(_mpn(mpn),[]):
                ok,_=self._manufacturer_compatible(mfg,r.get("Manufacturer Name",""))
                if ok: pm.append(r)
            if pm:
                return MatchRecord(intake,STATUS_EXACT_PM,"Local Parts Master MFG + MPN",pm,
                    "Exact MPN found locally and manufacturer identity is compatible. Engineering review remains available; no provider call made.")
            kb=[]
            for km,kn,d,p in self.kb.get(_mpn(mpn),[]):
                if _key(km)==_key(mfg):
                    kb.append({"manufacturer":km,"mpn":kn,"Description":"","AIPN":"","AIPN - OLD":""})
            if kb:
                return MatchRecord(intake,STATUS_KB,"Local Knowledge Base MFG + MPN",kb,
                    "Exact requested MFG + MPN exists in the local Knowledge Base. No provider call made.")
            return MatchRecord(intake,STATUS_UNRESOLVED,"Local MFG + MPN lookup",[],
                "No compatible local Parts Master or Knowledge Base identity found. Eligible for provider search in a later stage.")
        if cls==CLASS_VALUE_FOOTPRINT:
            val=_engineering_value(b.get("Value"),b.get("Reference","")); pkg=_package_key(b.get("Footprint",""))
            found=[]
            for r in self.pm:
                if _package_key(r.get("Case",""))!=pkg: continue
                pmval=_engineering_value(r.get("Value",""),b.get("Reference",""))
                if _value_equal(val,pmval): found.append(r)
            if len(found)==1:
                return MatchRecord(intake,STATUS_VALUE_UNIQUE,"Local Parts Master Value + Footprint",found,
                    "One Parts Master record has the same normalised Value + Footprint. This is a candidate only and requires Engineering approval.")
            if len(found)>1:
                return MatchRecord(intake,STATUS_VALUE_MULTIPLE,"Local Parts Master Value + Footprint",found,
                    f"{len(found)} Parts Master records have the same normalised Value + Footprint. All remain Engineering-review candidates.")
            return MatchRecord(intake,STATUS_UNRESOLVED,"Local Value + Footprint lookup",[],
                "No exact Value + Footprint match found in the Parts Master. No provider call made.")
        return MatchRecord(intake,STATUS_UNRESOLVED,"No local matching path",[],"Insufficient identity for current local matching paths.")

def match_source_bom(source_bom,parts_master):
    result,intake=classify_source_bom(source_bom)
    matcher=LocalKnowledgeMatcher(parts_master)
    return result,intake,[matcher.match(x) for x in intake]
