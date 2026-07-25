from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from providers.base_provider import BaseProvider
from providers.provider_result import ProviderResult, ProviderStatus


class ProviderManager:
    """Registry and provider-neutral execution boundary for PDC providers."""

    def __init__(self, providers: Iterable[BaseProvider] | None = None):
        self._providers: list[BaseProvider] = []
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

    def execute(self, provider: BaseProvider, operation: str, *args, **kwargs) -> ProviderResult:
        """Execute one provider method and isolate provider-level failures.

        Step 3A returns the raw provider data unchanged inside ProviderResult.
        Later multi-provider steps can continue after one provider fails without
        teaching the manager any DigiKey-, Mouser- or supplier-specific rules.
        """
        if provider not in self._providers:
            raise ValueError(f"Provider is not registered: {provider.name}")

        method = getattr(provider, operation, None)
        if method is None or not callable(method):
            raise AttributeError(f"Provider {provider.name} has no operation {operation!r}")

        try:
            data: Any = method(*args, **kwargs)
        except Exception as error:
            return ProviderResult(
                provider_name=provider.name,
                status=ProviderStatus.ERROR,
                message=str(error),
                exception=error,
            )

        return ProviderResult(
            provider_name=provider.name,
            status=ProviderStatus.SUCCESS,
            data=data,
        )
