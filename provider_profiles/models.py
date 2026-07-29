"""Provider-neutral Provider Part Profile.

A ProviderPartProfile is the normalised view of one provider's evidence for one
manufacturer part. It is deliberately separate from the later correlated
Knowledge Base Part Profile, which may combine evidence from several providers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PROVIDER_PART_PROFILE_SCHEMA_VERSION = "0.1"


@dataclass(slots=True)
class AttributeEvidence:
    """Traceability for one normalised attribute."""

    provider: str
    endpoint: str
    raw_name: str
    raw_value: Any
    normalised_value: Any
    unit: str = ""
    captured_at_utc: str = ""


@dataclass(slots=True)
class IdentityProfile:
    manufacturer: str = ""
    manufacturer_part_number: str = ""
    provider_part_number: str = ""
    description: str = ""
    detailed_description: str = ""
    category: str = ""
    product_status: list[str] = field(default_factory=list)
    ean: str = ""


@dataclass(slots=True)
class TechnicalProfile:
    component_type: str = ""
    regulator_type: list[str] = field(default_factory=list)
    manufacturer_series: str = ""
    package: str = ""
    mounting_type: str = ""
    output_voltage_v: float | None = None
    output_current_a: float | None = None
    input_voltage_min_v: float | None = None
    input_voltage_max_v: float | None = None
    operating_temperature_min_c: float | None = None
    operating_temperature_max_c: float | None = None
    tolerance_percent: float | None = None
    channel_count: int | None = None
    additional_attributes: dict[str, list[str]] = field(default_factory=dict)


@dataclass(slots=True)
class CommercialProfile:
    currency: str = ""
    price_type: str = ""
    tax_type: str = ""
    tax_rate_percent: float | None = None
    supplier_moq: int | float | None = None
    order_multiple: int | float | None = None
    stock_quantity: int | float | None = None
    price_breaks: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class LogisticsProfile:
    sales_unit: str = ""
    listed_pack_quantity: int | float | None = None
    manufacturer_standard_pack_quantity: int | float | None = None
    pack_formats: list[str] = field(default_factory=list)
    weight_value: float | None = None
    weight_unit: str = ""
    deliveries: Any = None


@dataclass(slots=True)
class MediaProfile:
    primary_image_url: str = ""
    thumbnail_url: str = ""
    high_resolution_image_url: str = ""
    datasheet_url: str = ""
    product_url: str = ""


@dataclass(slots=True)
class ProviderMetadata:
    provider: str = ""
    locale: str = ""
    currency: str = ""
    request_context: str = ""
    captured_at_utc: str = ""
    source_endpoints: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProviderPartProfile:
    schema_version: str = PROVIDER_PART_PROFILE_SCHEMA_VERSION
    identity: IdentityProfile = field(default_factory=IdentityProfile)
    technical: TechnicalProfile = field(default_factory=TechnicalProfile)
    commercial: CommercialProfile = field(default_factory=CommercialProfile)
    logistics: LogisticsProfile = field(default_factory=LogisticsProfile)
    media: MediaProfile = field(default_factory=MediaProfile)
    provider_metadata: ProviderMetadata = field(default_factory=ProviderMetadata)
    provenance: dict[str, AttributeEvidence] = field(default_factory=dict)
    raw_references: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return asdict(self)
