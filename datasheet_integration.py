from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any, Mapping
from datasheet_evidence import DatasheetEvidence, DatasheetSourceType, archive_datasheet, sha256_file

EVIDENCE_STATUS_MFG_VERIFIED = "Manufacturer Verified"
EVIDENCE_STATUS_MFG_RESOLVED = "Manufacturer Resolved - Verification Required"
EVIDENCE_STATUS_DISTI_COPY_MFG = "Distributor Copy of Manufacturer Document"
EVIDENCE_STATUS_DISTI = "Distributor Evidence"
EVIDENCE_STATUS_NEEDS_VERIFICATION = "Needs Verification"
EVIDENCE_STATUS_NONE = "No Datasheet Evidence"

@dataclass(frozen=True)
class EvidenceIntegrationResult:
    status: str
    manufacturer: str
    mpn: str
    component_updated: bool
    index_updated: bool
    active_selection_reason: str
    error: str = ""

def integrate_acquired_evidence(*, component_record: Mapping[str, Any], evidence: DatasheetEvidence, manufacturer: str, mpn: str) -> dict[str, Any]:
    _assert_component_identity(component_record, manufacturer, mpn)
    updated=deepcopy(dict(component_record)); block=deepcopy(updated.get('datasheet_evidence') or {}); history=list(block.get('history') or [])
    entry=_history_from_evidence(evidence=evidence,evidence_origin='PDC_ACQUIRED',original_filename=Path(evidence.local_file).name,user_confirmation=False)
    history=_append_history_deduplicated(history,entry)
    selected,reason=_select_active_evidence(block.get('active'),entry)
    block['active']=selected; block['active_selection_reason']=reason; block['history']=history; updated['datasheet_evidence']=block
    return updated

def integrate_user_supplied_evidence(*, component_record: Mapping[str, Any], supplied_file: str|Path, archive_root: str|Path, manufacturer: str, mpn: str, supplied_source_name: str, added_date: str|date, manufacturer_document_confirmed: bool, manufacturer_source_url: str='', document_name: str='datasheet') -> dict[str, Any]:
    _assert_component_identity(component_record,manufacturer,mpn)
    source=Path(supplied_file)
    if not source.is_file(): raise FileNotFoundError(source)
    source_type=DatasheetSourceType.MFG if manufacturer_document_confirmed else DatasheetSourceType.UNKNOWN
    archived=archive_datasheet(downloaded_file=source,archive_root=archive_root,manufacturer_name=manufacturer,mpn=mpn,source_type=source_type,source_name=supplied_source_name,retrieved_date=added_date,document_name=document_name)
    added=added_date.isoformat() if isinstance(added_date,date) else str(added_date)
    status=EVIDENCE_STATUS_MFG_VERIFIED if manufacturer_document_confirmed else EVIDENCE_STATUS_NEEDS_VERIFICATION
    entry={'evidence_origin':'USER_SUPPLIED','document_source_type':source_type.value,'source_name':str(supplied_source_name or ''),'active_source_url':str(manufacturer_source_url or '').strip(),'manufacturer_source_url':str(manufacturer_source_url or '').strip(),'local_file':str(archived),'sha256':sha256_file(archived),'retrieved_date':added,'original_filename':source.name,'manufacturer_url_verified':False,'manufacturer_document_confirmed':bool(manufacturer_document_confirmed),'verification_status':status,'notes':("User confirmed this file is the manufacturer's specification." if manufacturer_document_confirmed else 'User-supplied document requires provenance verification.')}
    updated=deepcopy(dict(component_record)); block=deepcopy(updated.get('datasheet_evidence') or {}); history=list(block.get('history') or []); history=_append_history_deduplicated(history,entry)
    selected,reason=_select_active_evidence(block.get('active'),entry)
    block['active']=selected; block['active_selection_reason']=reason; block['history']=history; updated['datasheet_evidence']=block
    return updated

def build_index_datasheet_summary(component_record: Mapping[str, Any]) -> dict[str, Any]:
    block=component_record.get('datasheet_evidence') or {}; active=block.get('active') or {}
    if not active:
        return {'datasheet_status':EVIDENCE_STATUS_NONE,'datasheet_source_type':'','datasheet_active_url':'','datasheet_local_file':'','datasheet_retrieved_date':'','datasheet_sha256':'','datasheet_evidence_origin':''}
    return {'datasheet_status':active.get('verification_status',EVIDENCE_STATUS_NEEDS_VERIFICATION),'datasheet_source_type':active.get('document_source_type',''),'datasheet_active_url':active.get('active_source_url',''),'datasheet_local_file':active.get('local_file',''),'datasheet_retrieved_date':active.get('retrieved_date',''),'datasheet_sha256':active.get('sha256',''),'datasheet_evidence_origin':active.get('evidence_origin','')}

def update_parts_master_index_record(*, index_record: Mapping[str, Any], component_record: Mapping[str, Any], manufacturer: str, mpn: str) -> dict[str, Any]:
    _assert_record_identity(index_record,manufacturer,mpn); updated=deepcopy(dict(index_record)); updated.update(build_index_datasheet_summary(component_record)); return updated

def integrate_evidence_files(*, component_json_path: str|Path, parts_master_index_path: str|Path, manufacturer: str, mpn: str, evidence: DatasheetEvidence|None=None, user_supplied_file: str|Path|None=None, archive_root: str|Path|None=None, supplied_source_name: str='', added_date: str|date|None=None, manufacturer_document_confirmed: bool=False, manufacturer_source_url: str='') -> EvidenceIntegrationResult:
    cp=Path(component_json_path); ip=Path(parts_master_index_path); component=json.loads(cp.read_text(encoding='utf-8')); index_data=json.loads(ip.read_text(encoding='utf-8'))
    try: _assert_component_identity(component,manufacturer,mpn)
    except ValueError as exc: return EvidenceIntegrationResult('Component Match Required',manufacturer,mpn,False,False,'',str(exc))
    records,wrapper=_index_records(index_data); matches=[i for i,r in enumerate(records) if _identity_matches(r,manufacturer,mpn)]
    if len(matches)!=1: return EvidenceIntegrationResult('Index Match Required',manufacturer,mpn,False,False,'',f'Expected one index match for {manufacturer} / {mpn}; found {len(matches)}.')
    if evidence is not None and user_supplied_file is not None: raise ValueError('Supply either acquired evidence or a user-supplied file, not both.')
    if evidence is None and user_supplied_file is None: raise ValueError('No evidence supplied.')
    if evidence is not None:
        updated_component=integrate_acquired_evidence(component_record=component,evidence=evidence,manufacturer=manufacturer,mpn=mpn)
    else:
        if archive_root is None or added_date is None: raise ValueError('archive_root and added_date are required for user-supplied evidence.')
        updated_component=integrate_user_supplied_evidence(component_record=component,supplied_file=user_supplied_file,archive_root=archive_root,manufacturer=manufacturer,mpn=mpn,supplied_source_name=supplied_source_name,added_date=added_date,manufacturer_document_confirmed=manufacturer_document_confirmed,manufacturer_source_url=manufacturer_source_url)
    idx=matches[0]; records[idx]=update_parts_master_index_record(index_record=records[idx],component_record=updated_component,manufacturer=manufacturer,mpn=mpn)
    cp.write_text(json.dumps(updated_component,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if wrapper is None: out=records
    else: out=deepcopy(index_data); out[wrapper]=records
    ip.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    block=updated_component.get('datasheet_evidence') or {}
    return EvidenceIntegrationResult('Integrated',manufacturer,mpn,True,True,block.get('active_selection_reason',''))

def _history_from_evidence(*, evidence: DatasheetEvidence, evidence_origin: str, original_filename: str, user_confirmation: bool) -> dict[str, Any]:
    return {'evidence_origin':evidence_origin,'document_source_type':evidence.document_source_type,'source_name':evidence.document_source_name,'active_source_url':evidence.active_source_url,'manufacturer_source_url':evidence.manufacturer_source_url,'local_file':evidence.local_file,'sha256':evidence.sha256,'retrieved_date':evidence.retrieved_date,'original_filename':original_filename,'manufacturer_url_verified':evidence.manufacturer_url_verified,'manufacturer_document_confirmed':bool(user_confirmation),'verification_status':_verification_status_from_evidence(evidence),'notes':evidence.notes}

def _verification_status_from_evidence(evidence: DatasheetEvidence) -> str:
    if evidence.document_source_type==DatasheetSourceType.MFG.value: return EVIDENCE_STATUS_MFG_VERIFIED if evidence.manufacturer_url_verified else EVIDENCE_STATUS_MFG_RESOLVED
    if evidence.document_source_type==DatasheetSourceType.DISTI_COPY_OF_MFG.value: return EVIDENCE_STATUS_DISTI_COPY_MFG
    if evidence.document_source_type==DatasheetSourceType.DISTI.value: return EVIDENCE_STATUS_DISTI
    return EVIDENCE_STATUS_NEEDS_VERIFICATION

def _select_active_evidence(current: Mapping[str, Any]|None,candidate: Mapping[str, Any]) -> tuple[dict[str, Any],str]:
    if not current: return dict(candidate),'First datasheet evidence available'
    cq=_quality_rank(current); nq=_quality_rank(candidate)
    if nq>cq: return dict(candidate),_selection_reason(candidate)
    if nq<cq: return dict(current),'Existing higher-confidence evidence retained'
    cd=str(current.get('retrieved_date') or ''); nd=str(candidate.get('retrieved_date') or '')
    return (dict(candidate),'Equal-confidence evidence; most recent retained') if nd>=cd else (dict(current),'Equal-confidence evidence; existing newer evidence retained')

def _selection_reason(e):
    s=e.get('verification_status','')
    if s==EVIDENCE_STATUS_MFG_VERIFIED: return 'Verified manufacturer evidence preferred'
    if s==EVIDENCE_STATUS_DISTI_COPY_MFG: return 'Distributor copy proven to match manufacturer document'
    if s==EVIDENCE_STATUS_DISTI: return 'No stronger manufacturer evidence available'
    return 'Best available evidence retained'

def _quality_rank(e):
    return {EVIDENCE_STATUS_MFG_VERIFIED:50,EVIDENCE_STATUS_DISTI_COPY_MFG:40,EVIDENCE_STATUS_MFG_RESOLVED:30,EVIDENCE_STATUS_DISTI:20,EVIDENCE_STATUS_NEEDS_VERIFICATION:10,EVIDENCE_STATUS_NONE:0}.get(e.get('verification_status',''),0)

def _append_history_deduplicated(history,entry):
    result=[dict(x) for x in history]; fp=(entry.get('sha256'),entry.get('local_file'),entry.get('evidence_origin'))
    if any((x.get('sha256'),x.get('local_file'),x.get('evidence_origin'))==fp for x in result): return result
    result.append(dict(entry)); return result

def _assert_component_identity(record,manufacturer,mpn):
    if not _identity_matches(record,manufacturer,mpn): raise ValueError(f'Component identity mismatch for {manufacturer} / {mpn}.')

def _assert_record_identity(record,manufacturer,mpn):
    if not _identity_matches(record,manufacturer,mpn): raise ValueError(f'Index identity mismatch for {manufacturer} / {mpn}.')

def _identity_matches(record,manufacturer,mpn):
    rm=_pick(record,'manufacturer','manufacturer_name','mfg','Manufacturer','MFG'); rp=_pick(record,'mpn','manufacturer_part_number','part_number','MPN','Manufacturer Part Number')
    return rm.casefold()==str(manufacturer or '').strip().casefold() and rp.casefold()==str(mpn or '').strip().casefold()

def _pick(record,*keys):
    for k in keys:
        v=record.get(k)
        if v is not None and str(v).strip(): return str(v).strip()
    return ''

def _index_records(data):
    if isinstance(data,list): return [dict(x) for x in data],None
    if isinstance(data,dict):
        for k in ('parts','records','components','items'):
            if isinstance(data.get(k),list): return [dict(x) for x in data[k]],k
    raise ValueError('Unsupported parts_master_index.json structure.')
