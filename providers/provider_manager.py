from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from threading import Lock
from time import perf_counter
from typing import Any

from providers.base_provider import BaseProvider, ProviderConfigurationError
from providers.provider_result import ProviderResult, ProviderStatus


class ProviderManager:
    """Registry and provider-neutral execution boundary for PDC providers.

    Sprint 4.7.2a also records lightweight execution diagnostics.  The timing
    counters are thread-safe so independent providers can be queried
    concurrently without changing result interpretation.
    """

    def __init__(self, providers: Iterable[BaseProvider] | None = None):
        self._providers: list[BaseProvider] = []
        self._stats_lock = Lock()
        self._stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "elapsed": 0.0, "success": 0, "error": 0, "skipped": 0, "no_match": 0,
                     "knowledge_base_hits": 0, "live_results": 0}
        )
        for provider in providers or ():
            self.register(provider)

    @property
    def providers(self) -> tuple[BaseProvider, ...]:
        """Return registered providers in deterministic registration order."""
        return tuple(self._providers)

    @property
    def names(self) -> tuple[str, ...]:
        """Return the names of all registered providers."""
        return tuple(provider.name for provider in self._providers)

    def register(self, provider: BaseProvider) -> None:
        """Register one provider, rejecting duplicate provider names."""
        if not isinstance(provider, BaseProvider):
            raise TypeError("provider must implement BaseProvider")

        normalised_name = provider.name.strip().casefold()
        if any(existing.name.strip().casefold() == normalised_name for existing in self._providers):
            raise ValueError(f"Provider already registered: {provider.name}")

        self._providers.append(provider)

    @property
    def primary(self) -> BaseProvider:
        """Return the active provider for the current single-provider workflow."""
        if not self._providers:
            raise RuntimeError("No data providers are registered")
        return self._providers[0]

    def _record(self, provider_name: str, result: ProviderResult, elapsed: float) -> None:
        source_mode = ""
        data = result.data
        if data is not None:
            source_mode = str(getattr(data, "source_mode", "") or "")
            if not source_mode and isinstance(data, dict):
                source_mode = str(data.get("source_mode") or "")
        with self._stats_lock:
            stats = self._stats[provider_name]
            stats["calls"] += 1
            stats["elapsed"] += elapsed
            stats[result.status.value] = stats.get(result.status.value, 0) + 1
            if source_mode == "knowledge_base_current":
                stats["knowledge_base_hits"] += 1
            elif source_mode.startswith("live_api"):
                stats["live_results"] += 1

    def execute(self, provider: BaseProvider, operation: str, *args, **kwargs) -> ProviderResult:
        """Execute one provider method and isolate provider-level failures."""
        if provider not in self._providers:
            raise ValueError(f"Provider is not registered: {provider.name}")

        method = getattr(provider, operation, None)
        if method is None or not callable(method):
            raise AttributeError(f"Provider {provider.name} has no operation {operation!r}")

        started = perf_counter()
        try:
            data: Any = method(*args, **kwargs)
        except ProviderConfigurationError as error:
            result = ProviderResult(
                provider_name=provider.name,
                status=ProviderStatus.SKIPPED,
                message=str(error),
                exception=error,
            )
        except Exception as error:
            result = ProviderResult(
                provider_name=provider.name,
                status=ProviderStatus.ERROR,
                message=str(error),
                exception=error,
            )
        else:
            result = ProviderResult(
                provider_name=provider.name,
                status=ProviderStatus.SUCCESS,
                data=data,
            )
        self._record(provider.name, result, perf_counter() - started)
        return result

    def stats_snapshot(self) -> dict[str, dict[str, Any]]:
        with self._stats_lock:
            return {name: dict(values) for name, values in self._stats.items()}

    def diagnostic_rows(self) -> list[tuple[str, str]]:
        """Compact provider timing/request diagnostics for console/workbook."""
        snapshot = self.stats_snapshot()
        rows: list[tuple[str, str]] = []
        total_calls = 0
        total_kb = 0
        total_live = 0
        for provider in self.names:
            stats = snapshot.get(provider, {})
            calls = int(stats.get("calls", 0))
            total_calls += calls
            total_kb += int(stats.get("knowledge_base_hits", 0))
            total_live += int(stats.get("live_results", 0))
            rows.append((
                f"{provider} provider activity",
                f"{calls} calls; {float(stats.get('elapsed', 0.0)):.1f} s cumulative; "
                f"{int(stats.get('error', 0))} errors; {int(stats.get('skipped', 0))} skipped",
            ))
        rows.append(("Provider operations", str(total_calls)))
        rows.append(("Knowledge Base results", str(total_kb)))
        rows.append(("Live API results", str(total_live)))
        rows.append(("Timing note", "Provider times are cumulative and may overlap because providers are queried concurrently."))
        return rows
