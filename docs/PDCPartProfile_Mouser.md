# PDCPartProfile — Mouser mapping

Sprint 4.2.5 Patch 2 maps Mouser Part Number Search data into the same `PDCPartProfile` used by TME and DigiKey.

## Mapping principles

- The profile grows additively; useful information is not removed to make providers look identical.
- No provider is authoritative.
- Provider-specific field names remain confined to the Mouser normaliser, provenance, and raw JSON.
- Commercial differences are preserved rather than correlated as if they were technical attributes.

## Mouser contributions

The current Mouser response contributes identity, catalogue classification, live stock, MOQ, order multiple, factory lead time, price breaks, available packaging formats, MouseReel service charges, standard pack quantity, weight, lifecycle/replacement information, RoHS, tariff/export classifications, country of origin, and media links.

Mouser's current Part Number Search response does not provide the same detailed parametric engineering block as the TME Parameters endpoint or DigiKey Product Details. Missing technical fields remain empty; they are not inferred from descriptive text.
