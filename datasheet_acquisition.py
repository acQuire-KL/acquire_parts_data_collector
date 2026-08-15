from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import mimetypes
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

from datasheet_evidence import (
    DatasheetEvidence,
    DatasheetSourceType,
    archive_datasheet,
    build_evidence_record,
    extract_embedded_urls,
    host_matches_domain,
    normalise_active_url,
    resolve_datasheet_source,
    sha256_file,
)


DEFAULT_USER_AGENT = "acQuire-PDC/4.6.3b Datasheet Acquisition"


@dataclass(frozen=True)
class HttpFetchResult:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str
    content_disposition: str
    body: bytes
    redirect_chain: tuple[str, ...] = ()


@dataclass(frozen=True)
class DatasheetAcquisitionResult:
    status: str
    evidence: DatasheetEvidence | None
    discovery_url: str
    final_url: str
    manufacturer_source_url: str
    archive_file: str
    error: str = ""
    attempts: tuple[str, ...] = ()


def fetch_url(
    url: str,
    *,
    timeout: float = 20.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> HttpFetchResult:
    """
    Fetch a document using urllib while recording the final URL.

    Live network behaviour is isolated here so unit tests can inject a fetcher.
    """
    redirect_chain: list[str] = []

    class RecordingRedirectHandler(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            redirect_chain.append(newurl)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = build_opener(RecordingRedirectHandler())
    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.5",
        },
    )

    with opener.open(request, timeout=timeout) as response:
        body = response.read()
        headers = response.headers
        return HttpFetchResult(
            requested_url=url,
            final_url=response.geturl(),
            status_code=getattr(response, "status", 200),
            content_type=(headers.get_content_type() if headers else ""),
            content_disposition=(headers.get("Content-Disposition", "") if headers else ""),
            body=body,
            redirect_chain=tuple(redirect_chain),
        )


def looks_like_pdf(fetch: HttpFetchResult) -> bool:
    """Reject HTML/error pages masquerading as datasheet links."""
    content_type = (fetch.content_type or "").casefold()
    disposition = (fetch.content_disposition or "").casefold()

    if fetch.body.startswith(b"%PDF-"):
        return True
    if "application/pdf" in content_type:
        return True
    if ".pdf" in disposition:
        return True
    return False


def candidate_manufacturer_urls(
    *,
    discovery_url: str,
    final_url: str,
    manufacturer_domains: Iterable[str],
) -> list[str]:
    """
    Return manufacturer-domain URL candidates discovered without guessing.

    Candidates can come from:
      * the HTTP final URL; or
      * embedded redirect/proxy parameters in the original distributor URL.
    """
    domains = tuple(manufacturer_domains)
    candidates: list[str] = []

    normalised_final = normalise_active_url(final_url)
    if any(host_matches_domain(normalised_final, domain) for domain in domains):
        candidates.append(normalised_final)

    for embedded in extract_embedded_urls(discovery_url):
        normalised = normalise_active_url(embedded)
        if any(host_matches_domain(normalised, domain) for domain in domains):
            candidates.append(normalised)

    return list(dict.fromkeys(candidates))


def verify_manufacturer_url(
    url: str,
    *,
    manufacturer_domains: Iterable[str],
    fetcher: Callable[..., HttpFetchResult] = fetch_url,
    timeout: float = 20.0,
) -> HttpFetchResult | None:
    """
    Independently test a manufacturer URL.

    Verification requires:
      * URL/final URL on a recognised manufacturer domain;
      * successful fetch; and
      * returned content that looks like a PDF.
    """
    domains = tuple(manufacturer_domains)
    if not any(host_matches_domain(url, domain) for domain in domains):
        return None

    try:
        result = fetcher(url, timeout=timeout)
    except (HTTPError, URLError, TimeoutError, OSError):
        return None

    if result.status_code < 200 or result.status_code >= 300:
        return None

    final_url = normalise_active_url(result.final_url)
    if not any(host_matches_domain(final_url, domain) for domain in domains):
        return None

    if not looks_like_pdf(result):
        return None

    return result


def acquire_datasheet(
    *,
    discovery_url: str,
    discovered_via: str,
    discovery_source_type: str,
    manufacturer_name: str,
    manufacturer_domains: Iterable[str],
    mpn: str,
    archive_root: str | Path,
    retrieved_date: str | date,
    document_name: str = "datasheet",
    fetcher: Callable[..., HttpFetchResult] = fetch_url,
    timeout: float = 20.0,
) -> DatasheetAcquisitionResult:
    """
    Acquire one datasheet and archive engineering evidence.

    Flow:
      1. Fetch the discovery URL and follow redirects.
      2. Reject non-PDF responses.
      3. Inspect final/embedded URLs for manufacturer-domain candidates.
      4. Independently fetch manufacturer candidates where possible.
      5. Prefer the independently verified manufacturer document.
      6. Otherwise archive the distributor/final document.
      7. Build a 4.6.3a DatasheetEvidence record.

    No component JSON/index update is performed here; the caller can decide
    when to persist the returned evidence record.
    """
    attempts: list[str] = [discovery_url]

    try:
        discovery_fetch = fetcher(discovery_url, timeout=timeout)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return DatasheetAcquisitionResult(
            status="Acquisition Failed",
            evidence=None,
            discovery_url=discovery_url,
            final_url="",
            manufacturer_source_url="",
            archive_file="",
            error=str(exc),
            attempts=tuple(attempts),
        )

    if discovery_fetch.status_code < 200 or discovery_fetch.status_code >= 300:
        return DatasheetAcquisitionResult(
            status="Acquisition Failed",
            evidence=None,
            discovery_url=discovery_url,
            final_url=discovery_fetch.final_url,
            manufacturer_source_url="",
            archive_file="",
            error=f"HTTP {discovery_fetch.status_code}",
            attempts=tuple(attempts),
        )

    if not looks_like_pdf(discovery_fetch):
        return DatasheetAcquisitionResult(
            status="Not a PDF",
            evidence=None,
            discovery_url=discovery_url,
            final_url=discovery_fetch.final_url,
            manufacturer_source_url="",
            archive_file="",
            error="Resolved content is not recognised as a PDF.",
            attempts=tuple(attempts),
        )

    mfg_candidates = candidate_manufacturer_urls(
        discovery_url=discovery_url,
        final_url=discovery_fetch.final_url,
        manufacturer_domains=manufacturer_domains,
    )

    verified_mfg_fetch: HttpFetchResult | None = None
    verified_mfg_url = ""

    for candidate in mfg_candidates:
        attempts.append(candidate)
        result = verify_manufacturer_url(
            candidate,
            manufacturer_domains=manufacturer_domains,
            fetcher=fetcher,
            timeout=timeout,
        )
        if result is not None:
            verified_mfg_fetch = result
            verified_mfg_url = normalise_active_url(result.final_url)
            break

    # If the discovery fetch itself ended directly on MFG and is a valid PDF,
    # it is still independently retested above. Only that retest sets verified.
    selected_fetch = verified_mfg_fetch or discovery_fetch

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        discovery_file = tmp_dir / "discovery.pdf"
        discovery_file.write_bytes(discovery_fetch.body)

        manufacturer_file = None
        if verified_mfg_fetch is not None:
            manufacturer_file = tmp_dir / "manufacturer.pdf"
            manufacturer_file.write_bytes(verified_mfg_fetch.body)

        resolution = resolve_datasheet_source(
            discovery_url=discovery_url,
            resolved_url=discovery_fetch.final_url,
            manufacturer_domains=manufacturer_domains,
            independently_verified_url=verified_mfg_url,
            downloaded_distributor_file=(
                discovery_file
                if discovery_source_type.casefold() == "disti"
                else None
            ),
            downloaded_manufacturer_file=manufacturer_file,
        )

        selected_file = tmp_dir / "selected.pdf"
        selected_file.write_bytes(selected_fetch.body)

        source_type = (
            DatasheetSourceType.MFG
            if verified_mfg_fetch is not None
            else resolution.document_source_type
        )
        source_name = (
            manufacturer_name
            if source_type == DatasheetSourceType.MFG
            else discovered_via
        )

        archived = archive_datasheet(
            downloaded_file=selected_file,
            archive_root=archive_root,
            manufacturer_name=manufacturer_name,
            mpn=mpn,
            source_type=source_type,
            source_name=source_name,
            retrieved_date=retrieved_date,
            document_name=document_name,
        )

    evidence = build_evidence_record(
        archived_file=archived,
        resolution=resolution,
        discovered_via=discovered_via,
        discovery_source_type=discovery_source_type,
        document_source_name=(
            manufacturer_name
            if source_type == DatasheetSourceType.MFG
            else discovered_via
        ),
        retrieved_date=retrieved_date,
        archive_root=archive_root,
    )

    status = (
        "Manufacturer Evidence Archived"
        if evidence.manufacturer_url_verified
        else "Evidence Archived"
    )

    return DatasheetAcquisitionResult(
        status=status,
        evidence=evidence,
        discovery_url=normalise_active_url(discovery_url),
        final_url=normalise_active_url(discovery_fetch.final_url),
        manufacturer_source_url=evidence.manufacturer_source_url,
        archive_file=str(archived),
        attempts=tuple(attempts),
    )


def acquisition_result_to_dict(
    result: DatasheetAcquisitionResult,
) -> dict[str, Any]:
    return {
        "status": result.status,
        "discovery_url": result.discovery_url,
        "final_url": result.final_url,
        "manufacturer_source_url": result.manufacturer_source_url,
        "archive_file": result.archive_file,
        "error": result.error,
        "attempts": list(result.attempts),
        "evidence": result.evidence.to_dict() if result.evidence else None,
    }
