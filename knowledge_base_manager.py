from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


KNOWLEDGE_BASE_SCHEMA_VERSION = "1.0"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_text(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat().replace("+00:00", "Z")


def safe_name(value: str, max_length: int = 120) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip())
    text = re.sub(r"_+", "_", text).strip("_.")
    return (text or "unknown")[:max_length]


@dataclass(frozen=True)
class KnowledgeRecord:
    provider_response: dict[str, Any]
    metadata: dict[str, Any]

    @property
    def captured_at_utc(self) -> str:
        return str(self.metadata.get("captured_at_utc", ""))

    @property
    def source_mode(self) -> str:
        return str(self.metadata.get("source_mode", ""))


class KnowledgeBaseManager:
    """Owns PDC's provider-independent current knowledge and history."""

    def __init__(self, root: str | Path = "Knowledge_Base") -> None:
        self.root = Path(root)
        self.current_root = self.root / "Current"
        self.history_root = self.root / "History"
        self.manifest_path = self.root / "Manifest.json"
        self.current_root.mkdir(parents=True, exist_ok=True)
        self.history_root.mkdir(parents=True, exist_ok=True)
        self._ensure_manifest()

    def _folder(self, provider: str, endpoint: str, history: bool = False) -> Path:
        root = self.history_root if history else self.current_root
        folder = root / safe_name(provider) / safe_name(endpoint)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _part_key(self, manufacturer: str, mpn: str) -> str:
        return f"{safe_name(manufacturer)}__{safe_name(mpn)}"

    def current_path(self, provider: str, endpoint: str, manufacturer: str, mpn: str) -> Path:
        return self._folder(provider, endpoint) / f"{self._part_key(manufacturer, mpn)}.json"

    def load_current(self, provider: str, endpoint: str, manufacturer: str, mpn: str) -> KnowledgeRecord | None:
        path = self.current_path(provider, endpoint, manufacturer, mpn)
        if not path.exists():
            return None
        document = json.loads(path.read_text(encoding="utf-8"))
        metadata = dict(document.get("knowledge_base_metadata") or {})
        metadata["source_mode"] = "knowledge_base_current"
        return KnowledgeRecord(dict(document.get("provider_response") or {}), metadata)

    def save_live_response(
        self,
        *,
        provider: str,
        endpoint: str,
        manufacturer: str,
        mpn: str,
        provider_response: dict[str, Any],
        input_manufacturer: str,
        resolved_manufacturer: str,
        manufacturer_id: int | str | None,
        locale: str,
        currency: str,
        rate_limit: dict[str, Any] | None = None,
    ) -> KnowledgeRecord:
        captured = utc_now()
        metadata = {
            "knowledge_base_schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
            "provider": provider,
            "endpoint": endpoint,
            "captured_at_utc": utc_text(captured),
            "source_mode": "live_api",
            "input_manufacturer": input_manufacturer,
            "input_mpn": mpn,
            "resolved_manufacturer": resolved_manufacturer,
            "provider_manufacturer_id": manufacturer_id,
            "locale": locale,
            "currency": currency,
            "rate_limit": rate_limit or {},
        }
        document = {
            "knowledge_base_metadata": metadata,
            "provider_response": provider_response,
        }
        text = json.dumps(document, indent=2, ensure_ascii=False)

        current_path = self.current_path(provider, endpoint, manufacturer, mpn)
        current_path.write_text(text, encoding="utf-8")

        history_folder = self._folder(provider, endpoint, history=True) / self._part_key(manufacturer, mpn)
        history_folder.mkdir(parents=True, exist_ok=True)
        stamp = captured.strftime("%Y-%m-%dT%H%M%SZ")
        history_path = history_folder / f"{stamp}.json"
        suffix = 1
        while history_path.exists():
            history_path = history_folder / f"{stamp}_{suffix}.json"
            suffix += 1
        history_path.write_text(text, encoding="utf-8")

        self._update_manifest(provider, captured)
        return KnowledgeRecord(provider_response, metadata)

    def save_reference_data(
        self,
        *,
        provider: str,
        dataset: str,
        provider_response: dict[str, Any],
        locale: str,
        currency: str,
        rate_limit: dict[str, Any] | None = None,
    ) -> KnowledgeRecord:
        captured = utc_now()
        metadata = {
            "knowledge_base_schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
            "provider": provider,
            "endpoint": "Reference_Data",
            "dataset": dataset,
            "captured_at_utc": utc_text(captured),
            "source_mode": "live_api",
            "locale": locale,
            "currency": currency,
            "rate_limit": rate_limit or {},
        }
        document = {"knowledge_base_metadata": metadata, "provider_response": provider_response}
        path = self._folder(provider, "Reference_Data") / f"{safe_name(dataset)}.json"
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
        self._update_manifest(provider, captured)
        return KnowledgeRecord(provider_response, metadata)

    def load_reference_data(self, provider: str, dataset: str) -> KnowledgeRecord | None:
        path = self._folder(provider, "Reference_Data") / f"{safe_name(dataset)}.json"
        if not path.exists():
            return None
        document = json.loads(path.read_text(encoding="utf-8"))
        metadata = dict(document.get("knowledge_base_metadata") or {})
        metadata["source_mode"] = "knowledge_base_current"
        return KnowledgeRecord(dict(document.get("provider_response") or {}), metadata)

    def migrate_legacy_file(
        self,
        legacy_path: Path,
        *,
        provider: str,
        endpoint: str,
        manufacturer: str,
        mpn: str,
        input_manufacturer: str,
        resolved_manufacturer: str,
        manufacturer_id: int | str | None,
        locale: str,
        currency: str,
    ) -> KnowledgeRecord | None:
        if not legacy_path.exists():
            return None
        response = json.loads(legacy_path.read_text(encoding="utf-8"))
        captured = datetime.fromtimestamp(legacy_path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0)
        metadata = {
            "knowledge_base_schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
            "provider": provider,
            "endpoint": endpoint,
            "captured_at_utc": utc_text(captured),
            "source_mode": "legacy_cache_migration",
            "input_manufacturer": input_manufacturer,
            "input_mpn": mpn,
            "resolved_manufacturer": resolved_manufacturer,
            "provider_manufacturer_id": manufacturer_id,
            "locale": locale,
            "currency": currency,
            "legacy_source_file": str(legacy_path),
            "rate_limit": {},
        }
        document = {"knowledge_base_metadata": metadata, "provider_response": response}
        current_path = self.current_path(provider, endpoint, manufacturer, mpn)
        current_path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
        self._update_manifest(provider, captured)
        return KnowledgeRecord(response, metadata)

    def _ensure_manifest(self) -> None:
        if self.manifest_path.exists():
            return
        now = utc_text()
        manifest = {
            "knowledge_base_version": "0.2.0",
            "schema_version": KNOWLEDGE_BASE_SCHEMA_VERSION,
            "created_at_utc": now,
            "last_updated_at_utc": now,
            "providers": {},
            "refresh_planning": {
                "enabled": False,
                "description": "Reserved for staggered periodic refresh scheduling in a later release."
            },
        }
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def _update_manifest(self, provider: str, captured: datetime) -> None:
        self._ensure_manifest()
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        providers = manifest.setdefault("providers", {})
        entry = providers.setdefault(provider, {})
        entry["last_capture_at_utc"] = utc_text(captured)
        entry["current_records"] = self._count_json(self.current_root / safe_name(provider))
        entry["history_records"] = self._count_json(self.history_root / safe_name(provider))
        manifest["last_updated_at_utc"] = utc_text(captured)
        manifest["total_current_records"] = self._count_json(self.current_root)
        manifest["total_history_records"] = self._count_json(self.history_root)
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    @staticmethod
    def _count_json(folder: Path) -> int:
        return sum(1 for _ in folder.rglob("*.json")) if folder.exists() else 0
