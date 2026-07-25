from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProviderStatus(str, Enum):
    """Provider-level execution states used by PDC orchestration."""

    SUCCESS = "success"
    NO_MATCH = "no_match"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass(frozen=True)
class ProviderResult:
    """Outcome from one provider operation.

    The payload remains provider-neutral: orchestration can report success,
    absence or failure without interpreting the provider's source data.
    """

    provider_name: str
    status: ProviderStatus
    data: Any = None
    matches_found: int = 0
    offers_found: int = 0
    message: str | None = None
    exception: Exception | None = None

    @property
    def succeeded(self) -> bool:
        return self.status is ProviderStatus.SUCCESS

    def require_data(self) -> Any:
        """Return collected data or re-raise the original provider error.

        Existing PDC call sites use this during Step 3A so collection behaviour
        remains unchanged while execution results become available to later
        multi-provider orchestration.
        """
        if self.succeeded:
            return self.data
        if self.exception is not None:
            raise self.exception
        raise RuntimeError(self.message or f"{self.provider_name} returned {self.status.value}")
