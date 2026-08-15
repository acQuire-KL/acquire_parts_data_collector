from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse, parse_qsl, unquote, urlencode, urlunparse
import hashlib, re, shutil

class DatasheetSourceType(str, Enum):
    MFG = "MFG"
    DISTI = "DISTI"
    DISTI_COPY_OF_MFG = "DISTI_COPY_OF_MFG"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class SourceResolution:
    discovery_url: str
    resolved_url: str
    manufacturer_source_url: str
    active_source_url: str
    document_source_type: DatasheetSourceType
    source_resolution_status: str
    manufacturer_url_verified: bool
    notes: str = ""

@dataclass(frozen=True)
class DatasheetEvidence:
    discovered_via: str
    discovery_source_type: str
    discovery_url: str
    resolved_url: str
    manufacturer_source_url: str
    active_source_url: str
    document_source_type: str
    document_source_name: str
    local_file: str
    retrieved_date: str
    sha256: str
    file_size_bytes: int
    content_type: str = "application/pdf"
    source_resolution_status: str = "Unresolved"
    manufacturer_url_verified: bool = False
    notes: str = ""
    schema_version: str = "1.0"
    def to_dict(self) -> dict[str, Any]: return asdict(self)

def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def documents_match(a,b): return sha256_file(a)==sha256_file(b)

def normalise_active_url(url: str) -> str:
    text=str(url or '').strip()
    if not text: return ''
    p=urlparse(text)
    if p.scheme not in {'http','https'} or not p.netloc: return text
    drop={'ref','referrer','source','campaign','tracking','trk'}
    kept=[]
    for k,v in parse_qsl(p.query, keep_blank_values=True):
        low=k.casefold()
        if low.startswith('utm_') or low in drop: continue
        kept.append((k,v))
    return urlunparse((p.scheme.lower(),p.netloc.lower(),p.path,p.params,urlencode(kept,doseq=True),''))

def extract_embedded_urls(url: str) -> list[str]:
    out=[]
    for _,v in parse_qsl(urlparse(str(url or '')).query, keep_blank_values=False):
        c=unquote(v).strip()
        if c.startswith(('http://','https://')): out.append(c)
    return list(dict.fromkeys(out))

def host_matches_domain(url, domain):
    host=(urlparse(str(url or '')).hostname or '').casefold().rstrip('.')
    d=str(domain or '').casefold().strip().lstrip('.').rstrip('.')
    return bool(host and d) and (host==d or host.endswith('.'+d))

def resolve_datasheet_source(*, discovery_url, resolved_url, manufacturer_domains: Iterable[str], independently_verified_url='', downloaded_distributor_file=None, downloaded_manufacturer_file=None):
    domains=tuple(str(d).strip() for d in manufacturer_domains if str(d).strip())
    discovery=normalise_active_url(discovery_url)
    resolved=normalise_active_url(resolved_url)
    candidate=''
    if any(host_matches_domain(resolved,d) for d in domains): candidate=resolved
    else:
        for c in extract_embedded_urls(discovery_url):
            c=normalise_active_url(c)
            if any(host_matches_domain(c,d) for d in domains): candidate=c; break
    verified_url=normalise_active_url(independently_verified_url)
    verified=bool(verified_url and any(host_matches_domain(verified_url,d) for d in domains))
    if verified:
        mfg=verified_url; active=verified_url; typ=DatasheetSourceType.MFG
        status='Manufacturer Source Verified'; notes='Direct manufacturer source URL independently verified.'
    elif candidate:
        mfg=candidate; active=candidate; typ=DatasheetSourceType.MFG
        status='Manufacturer Source Resolved - Verification Required'; notes='URL resolves to a recognised manufacturer domain.'
    else:
        mfg=''; active=resolved or discovery; typ=DatasheetSourceType.DISTI
        status='Distributor Source'; notes='No independently verified manufacturer source URL available.'
    if downloaded_distributor_file and downloaded_manufacturer_file:
        if documents_match(downloaded_distributor_file, downloaded_manufacturer_file):
            if not verified:
                typ=DatasheetSourceType.DISTI_COPY_OF_MFG; status='Distributor Copy Matches Manufacturer Document'
            notes += ' Distributor and manufacturer downloads have identical SHA-256.'
        else:
            notes += ' Distributor and manufacturer downloads differ; review required.'
    return SourceResolution(discovery,resolved,mfg,active,typ,status,verified,notes.strip())

def _safe(v):
    t=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',str(v or '').strip())
    t=re.sub(r'\s+','_',t); t=re.sub(r'_+','_',t)
    return t.strip('._') or 'unknown'

def make_archive_filename(*, mpn, source_type, source_name, retrieved_date, document_name='datasheet', extension='.pdf'):
    st=source_type.value if isinstance(source_type,DatasheetSourceType) else str(source_type)
    dt=retrieved_date.isoformat() if isinstance(retrieved_date,date) else str(retrieved_date)
    ext=extension if str(extension).startswith('.') else '.'+str(extension)
    return '__'.join(map(_safe,[dt,mpn,st,source_name,document_name]))+ext.lower()

def archive_datasheet(*, downloaded_file, archive_root, manufacturer_name, mpn, source_type, source_name, retrieved_date, document_name='datasheet'):
    src=Path(downloaded_file)
    if not src.is_file(): raise FileNotFoundError(src)
    destdir=Path(archive_root)/_safe(manufacturer_name)/_safe(mpn); destdir.mkdir(parents=True,exist_ok=True)
    dest=destdir/make_archive_filename(mpn=mpn,source_type=source_type,source_name=source_name,retrieved_date=retrieved_date,document_name=document_name,extension=src.suffix or '.pdf')
    h=sha256_file(src)
    if dest.exists():
        if sha256_file(dest)==h: return dest
        dest=dest.with_name(dest.stem+'__'+h[:12]+dest.suffix)
    shutil.copyfile(src,dest); return dest

def build_evidence_record(*, archived_file, resolution, discovered_via, discovery_source_type, document_source_name, retrieved_date, archive_root=None, notes=''):
    p=Path(archived_file)
    if not p.is_file(): raise FileNotFoundError(p)
    dt=retrieved_date.isoformat() if isinstance(retrieved_date,date) else str(retrieved_date)
    local=str(p)
    if archive_root is not None:
        try: local=str(p.relative_to(Path(archive_root)))
        except ValueError: pass
    combined=' '.join(x for x in [resolution.notes,str(notes or '').strip()] if x)
    return DatasheetEvidence(str(discovered_via or ''),str(discovery_source_type or ''),resolution.discovery_url,resolution.resolved_url,resolution.manufacturer_source_url,resolution.active_source_url,resolution.document_source_type.value,str(document_source_name or ''),local,dt,sha256_file(p),p.stat().st_size,source_resolution_status=resolution.source_resolution_status,manufacturer_url_verified=resolution.manufacturer_url_verified,notes=combined)

def compare_active_to_static(*, static_file, current_download):
    a=sha256_file(static_file); b=sha256_file(current_download); changed=a!=b
    return {'static_sha256':a,'current_sha256':b,'changed':changed,'status':'Changed' if changed else 'No Change'}
