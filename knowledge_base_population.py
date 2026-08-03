"""Populate PDC's Knowledge Base from a staging Parts Master.

Sprint 4.4 Patch 2 deliberately performs collection only. It does not
correlate providers, approve records, allocate AIPNs, or modify the staging
Parts Master.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Protocol

from config import MouserSettings, Settings, TmeSettings
from knowledge_base_manager import KnowledgeBaseManager
from providers.base_provider import ProviderConfigurationError
from providers.digikey import DigiKeyProvider
from providers.digikey.normalizer import build_digikey_pdc_part_profile
from providers.mouser import MouserProvider
from providers.mouser.normalizer import build_mouser_pdc_part_profile
from providers.tme import TmeClient
from providers.tme.normalizer import build_tme_pdc_part_profile


STATUS_DOWNLOADED = "Downloaded"
STATUS_CACHED = "Already Cached"
STATUS_NOT_FOUND = "Not Found"
STATUS_SKIPPED = "Skipped"
STATUS_FAILED = "Failed"


def utc_now_text() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_name(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip()).strip("_") or "Unknown"


def load_staging_records(path: str | Path) -> list[OrderedDict[str, str]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        required = {"Manufacturer", "Manufacturer Part Number"}
        missing = sorted(required.difference(headers))
        if missing:
            raise ValueError(f"Staging Parts Master is missing columns: {', '.join(missing)}")
        return [OrderedDict((key, str(value or "").strip()) for key, value in row.items()) for row in reader]


def _record_document(record: Any) -> dict[str, Any]:
    return {
        "knowledge_base_metadata": dict(record.metadata or {}),
        "provider_response": dict(record.provider_response or {}),
        "commercial_profile": dict(record.commercial_profile or {}),
        "part_profile": dict(record.part_profile or {}),
    }


def _write_profile(profile: Any, output_root: Path, provider: str, manufacturer: str, mpn: str) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / f"{safe_name(provider).upper()}__{safe_name(manufacturer)}__{safe_name(mpn)}.json"
    path.write_text(json.dumps(profile.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _find_cached_path(root: Path, provider: str, endpoint: str, manufacturer: str, mpn: str) -> Path | None:
    direct = root / "Current" / safe_name(provider) / safe_name(endpoint) / f"{safe_name(manufacturer)}__{safe_name(mpn)}.json"
    if direct.exists():
        return direct
    folder = root / "Current" / safe_name(provider) / safe_name(endpoint)
    if not folder.exists():
        return None
    suffix = f"__{safe_name(mpn)}.json".casefold()
    matches = sorted(path for path in folder.glob("*.json") if path.name.casefold().endswith(suffix))
    return matches[0] if matches else None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(slots=True)
class ProviderOutcome:
    record_id: str
    manufacturer: str
    mpn: str
    provider: str
    status: str
    message: str = ""
    knowledge_base_paths: list[str] = field(default_factory=list)
    profile_path: str = ""

    def to_row(self) -> OrderedDict[str, object]:
        return OrderedDict([
            ("Record ID", self.record_id),
            ("Manufacturer", self.manufacturer),
            ("Manufacturer Part Number", self.mpn),
            ("Provider", self.provider),
            ("Status", self.status),
            ("Message", self.message),
            ("Knowledge Base Paths", " | ".join(self.knowledge_base_paths)),
            ("PDCPartProfile Path", self.profile_path),
        ])


class PopulationProvider(Protocol):
    name: str

    def collect(self, record_id: str, manufacturer: str, mpn: str, *, force: bool = False) -> ProviderOutcome:
        ...


class DigiKeyPopulationProvider:
    name = "DigiKey"
    endpoint = "Product_Details"

    def __init__(self, settings: Settings, knowledge_base: KnowledgeBaseManager, profile_root: Path, *, provider: DigiKeyProvider | None = None):
        self.knowledge_base = knowledge_base
        self.profile_root = profile_root
        self.provider = provider or DigiKeyProvider(settings, knowledge_base)

    def collect(self, record_id: str, manufacturer: str, mpn: str, *, force: bool = False) -> ProviderOutcome:
        cached = None if force else _find_cached_path(self.knowledge_base.root, self.name, self.endpoint, manufacturer, mpn)
        if cached:
            document = _load_json(cached)
            status = STATUS_CACHED
        else:
            record = self.provider.details(
                mpn,
                force=force,
                input_manufacturer=manufacturer,
                resolved_manufacturer=manufacturer,
            )
            document = _record_document(record)
            cached = _find_cached_path(self.knowledge_base.root, self.name, self.endpoint, manufacturer, mpn)
            status = STATUS_DOWNLOADED
        profile = build_digikey_pdc_part_profile(
            document,
            raw_references={"product_details": str(cached or "")},
        )
        profile_path = _write_profile(profile, self.profile_root, self.name, manufacturer, mpn)
        return ProviderOutcome(record_id, manufacturer, mpn, self.name, status,
                               knowledge_base_paths=[str(cached or "")], profile_path=str(profile_path))


class MouserPopulationProvider:
    name = "Mouser"
    endpoint = "Part_Number_Search"

    def __init__(self, settings: MouserSettings, knowledge_base: KnowledgeBaseManager, profile_root: Path, *, provider: MouserProvider | None = None):
        self.knowledge_base = knowledge_base
        self.profile_root = profile_root
        self.provider = provider or MouserProvider(settings, knowledge_base)

    def collect(self, record_id: str, manufacturer: str, mpn: str, *, force: bool = False) -> ProviderOutcome:
        cached = None if force else _find_cached_path(self.knowledge_base.root, self.name, self.endpoint, manufacturer, mpn)
        if cached:
            document = _load_json(cached)
            status = STATUS_CACHED
        else:
            record = self.provider.details(
                mpn,
                force=force,
                input_manufacturer=manufacturer,
                resolved_manufacturer=manufacturer,
            )
            document = _record_document(record)
            cached = _find_cached_path(self.knowledge_base.root, self.name, self.endpoint, manufacturer, mpn)
            status = STATUS_DOWNLOADED
        response = document.get("provider_response") or {}
        results = response.get("SearchResults") or response.get("searchResults") or {}
        parts = results.get("Parts") or results.get("parts") or []
        if not parts:
            return ProviderOutcome(record_id, manufacturer, mpn, self.name, STATUS_NOT_FOUND,
                                   message="Mouser returned no parts", knowledge_base_paths=[str(cached or "")])
        profile = build_mouser_pdc_part_profile(
            document,
            raw_references={"part_number_search": str(cached or "")},
        )
        profile_path = _write_profile(profile, self.profile_root, self.name, manufacturer, mpn)
        return ProviderOutcome(record_id, manufacturer, mpn, self.name, status,
                               knowledge_base_paths=[str(cached or "")], profile_path=str(profile_path))


class TmePopulationProvider:
    name = "TME"
    endpoints = ("Product_Search", "Product_Data", "Product_Parameters")

    def __init__(self, settings: TmeSettings, knowledge_base: KnowledgeBaseManager, profile_root: Path, *, client: TmeClient | None = None):
        self.settings = settings
        self.knowledge_base = knowledge_base
        self.profile_root = profile_root
        self.client = client or TmeClient(settings)

    @staticmethod
    def _elements(payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data")
        if isinstance(data, dict):
            products = data.get("products")
            if isinstance(products, dict):
                values = products.get("elements") or products.get("items") or []
                return [item for item in values if isinstance(item, dict)]
            if isinstance(products, list):
                return [item for item in products if isinstance(item, dict)]
        products = payload.get("products")
        return [item for item in products if isinstance(item, dict)] if isinstance(products, list) else []

    def _paths(self, manufacturer: str, mpn: str) -> dict[str, Path | None]:
        return {
            endpoint: _find_cached_path(self.knowledge_base.root, self.name, endpoint, manufacturer, mpn)
            for endpoint in self.endpoints
        }

    def _save(self, endpoint: str, manufacturer: str, mpn: str, payload: dict[str, Any]) -> Path:
        self.knowledge_base.save_raw_provider_response(
            provider=self.name,
            endpoint=endpoint,
            manufacturer=manufacturer or "Unknown",
            mpn=mpn,
            provider_response=payload,
            input_manufacturer=manufacturer,
            locale=f"{self.settings.language}-{self.settings.country}",
            currency=self.settings.currency if endpoint == "Product_Data" else "",
            request_context="customer-linked",
        )
        return self.knowledge_base.current_path(self.name, endpoint, manufacturer or "Unknown", mpn)

    def collect(self, record_id: str, manufacturer: str, mpn: str, *, force: bool = False) -> ProviderOutcome:
        cached = self._paths(manufacturer, mpn)
        if not force and all(cached.values()):
            status = STATUS_CACHED
        else:
            token = self.client._extract_access_token(self.client.obtain_access_token())
            search_payload = self.client.search_products(mpn, access_token=token)
            items = self._elements(search_payload)
            if not items:
                search_path = self._save("Product_Search", manufacturer, mpn, search_payload)
                return ProviderOutcome(record_id, manufacturer, mpn, self.name, STATUS_NOT_FOUND,
                                       message="TME returned no products", knowledge_base_paths=[str(search_path)])
            item = items[0]
            symbol = str(item.get("symbol") or item.get("tmeSymbol") or mpn)
            provider_manufacturer = item.get("manufacturer") or manufacturer
            if isinstance(provider_manufacturer, dict):
                provider_manufacturer = provider_manufacturer.get("name") or manufacturer
            storage_manufacturer = str(provider_manufacturer or manufacturer)
            search_path = self._save("Product_Search", storage_manufacturer, mpn, search_payload)
            data_payload = self.client.get_product_data(symbol, access_token=token)
            data_path = self._save("Product_Data", storage_manufacturer, mpn, data_payload)
            parameters_payload = self.client.get_product_parameters(symbol, access_token=token)
            parameters_path = self._save("Product_Parameters", storage_manufacturer, mpn, parameters_payload)
            cached = {
                "Product_Search": search_path,
                "Product_Data": data_path,
                "Product_Parameters": parameters_path,
            }
            status = STATUS_DOWNLOADED
        documents = {endpoint: _load_json(path) for endpoint, path in cached.items() if path}
        if len(documents) != 3:
            missing = [endpoint for endpoint in self.endpoints if endpoint not in documents]
            raise RuntimeError("TME Knowledge Base capture is incomplete: " + ", ".join(missing))
        raw_refs = {
            "search": str(cached["Product_Search"]),
            "data": str(cached["Product_Data"]),
            "parameters": str(cached["Product_Parameters"]),
        }
        profile = build_tme_pdc_part_profile(
            documents["Product_Search"], documents["Product_Data"], documents["Product_Parameters"],
            raw_references=raw_refs,
        )
        profile_path = _write_profile(profile, self.profile_root, self.name, manufacturer, mpn)
        return ProviderOutcome(record_id, manufacturer, mpn, self.name, status,
                               knowledge_base_paths=[raw_refs["search"], raw_refs["data"], raw_refs["parameters"]],
                               profile_path=str(profile_path))


@dataclass
class PopulationRun:
    source_file: str
    started_at_utc: str
    finished_at_utc: str = ""
    outcomes: list[ProviderOutcome] = field(default_factory=list)
    total_staging_records: int = 0
    selected_records: int = 0

    def summary(self) -> OrderedDict[str, Any]:
        counts = Counter(outcome.status for outcome in self.outcomes)
        provider_counts: dict[str, dict[str, int]] = {}
        for provider in sorted({outcome.provider for outcome in self.outcomes}):
            provider_counts[provider] = dict(Counter(
                outcome.status for outcome in self.outcomes if outcome.provider == provider
            ))
        return OrderedDict([
            ("source_file", self.source_file),
            ("started_at_utc", self.started_at_utc),
            ("finished_at_utc", self.finished_at_utc),
            ("total_staging_records", self.total_staging_records),
            ("selected_records", self.selected_records),
            ("provider_operations", len(self.outcomes)),
            ("status_counts", dict(counts)),
            ("provider_statistics", provider_counts),
        ])


def populate_knowledge_base(
    staging_path: str | Path,
    providers: Iterable[PopulationProvider],
    *,
    force: bool = False,
    limit: int | None = None,
    progress: bool = True,
) -> PopulationRun:
    rows = load_staging_records(staging_path)
    selected = rows if not limit or limit < 1 else rows[:limit]
    provider_list = list(providers)
    run = PopulationRun(
        source_file=str(Path(staging_path)),
        started_at_utc=utc_now_text(),
        total_staging_records=len(rows),
        selected_records=len(selected),
    )
    total = len(selected)
    for index, row in enumerate(selected, start=1):
        record_id = row.get("Record ID", "")
        manufacturer = row.get("Manufacturer", "")
        mpn = row.get("Manufacturer Part Number", "")
        if progress:
            print(f"[{index:>4}/{total}] {manufacturer} | {mpn}")
        if not manufacturer or not mpn:
            for provider in provider_list:
                run.outcomes.append(ProviderOutcome(
                    record_id, manufacturer, mpn, provider.name, STATUS_SKIPPED,
                    message="Incomplete Manufacturer + MPN identity",
                ))
            continue
        for provider in provider_list:
            try:
                outcome = provider.collect(record_id, manufacturer, mpn, force=force)
            except ProviderConfigurationError as error:
                outcome = ProviderOutcome(record_id, manufacturer, mpn, provider.name, STATUS_SKIPPED, str(error))
            except Exception as error:
                outcome = ProviderOutcome(
                    record_id, manufacturer, mpn, provider.name, STATUS_FAILED,
                    f"{type(error).__name__}: {error}",
                )
            run.outcomes.append(outcome)
            if progress:
                print(f"    {provider.name:<10} {outcome.status}{': ' + outcome.message if outcome.message else ''}")
    run.finished_at_utc = utc_now_text()
    return run


def write_population_outputs(run: PopulationRun, output_root: str | Path) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    stem = f"KB_POPULATION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    paths = {
        "results": root / f"{stem}__RESULTS.csv",
        "failures": root / f"{stem}__FAILURES.csv",
        "skipped": root / f"{stem}__SKIPPED.csv",
        "summary": root / f"{stem}__SUMMARY.json",
        "run_log": root / f"{stem}__RUN_LOG.txt",
    }
    rows = [outcome.to_row() for outcome in run.outcomes]
    fieldnames = list(rows[0].keys()) if rows else [
        "Record ID", "Manufacturer", "Manufacturer Part Number", "Provider", "Status",
        "Message", "Knowledge Base Paths", "PDCPartProfile Path",
    ]
    for key, statuses in (("results", None), ("failures", {STATUS_FAILED, STATUS_NOT_FOUND}), ("skipped", {STATUS_SKIPPED})):
        selected = rows if statuses is None else [row for row in rows if row["Status"] in statuses]
        with paths[key].open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(selected)
    summary = run.summary()
    paths["summary"].write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "PDC Knowledge Base Population",
        "=" * 40,
        f"Source              : {summary['source_file']}",
        f"Started UTC         : {summary['started_at_utc']}",
        f"Finished UTC        : {summary['finished_at_utc']}",
        f"Staging records     : {summary['total_staging_records']}",
        f"Selected records    : {summary['selected_records']}",
        f"Provider operations : {summary['provider_operations']}",
        "",
        "Status counts",
        "-" * 40,
    ]
    for status, count in summary["status_counts"].items():
        lines.append(f"{status:<20}: {count}")
    lines.extend(["", "Provider statistics", "-" * 40])
    for provider, counts in summary["provider_statistics"].items():
        lines.append(provider)
        for status, count in counts.items():
            lines.append(f"  {status:<18}: {count}")
    paths["run_log"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return paths


def build_live_providers(
    knowledge_base_root: str | Path = "Knowledge_Base",
    profile_root: str | Path = "output/provider_profiles",
    selected_names: Iterable[str] | None = None,
) -> list[PopulationProvider]:
    selected = {name.casefold() for name in (selected_names or ("DigiKey", "TME", "Mouser"))}
    knowledge_base = KnowledgeBaseManager(knowledge_base_root)
    profiles = Path(profile_root)
    providers: list[PopulationProvider] = []
    if "digikey" in selected:
        try:
            providers.append(DigiKeyPopulationProvider(Settings.from_env(), knowledge_base, profiles))
        except ValueError as error:
            providers.append(_UnavailablePopulationProvider("DigiKey", str(error)))
    if "tme" in selected:
        providers.append(TmePopulationProvider(TmeSettings.from_env(), knowledge_base, profiles))
    if "mouser" in selected:
        providers.append(MouserPopulationProvider(MouserSettings.from_env(), knowledge_base, profiles))
    return providers


class _UnavailablePopulationProvider:
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message

    def collect(self, record_id: str, manufacturer: str, mpn: str, *, force: bool = False) -> ProviderOutcome:
        del force
        raise ProviderConfigurationError(self.message)
