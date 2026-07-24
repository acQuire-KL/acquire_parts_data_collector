from __future__ import annotations

from collections.abc import Iterable

from providers.base_provider import BaseProvider


class ProviderManager:
    """Registry and access point for PDC data providers.

    Step 2 deliberately keeps collection behaviour unchanged: the first
    registered provider remains the active provider used by the existing
    single-provider workflow. Later steps can iterate over ``providers``
    without changing application-level registration code.
    """

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
