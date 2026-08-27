# Sprint 4.7.1a — Operational BOM Review Corrective Patch

This patch addresses issues found while running a real engineering BOM through Sprint 4.7.1.

## Corrections

- CSV input is accepted directly and converted in memory into the same review path used by Excel workbooks.
- `MF` is accepted as a Manufacturer header alias, alongside MFG/MFR/Manufacturer variants.
- BOM `Value` and `Footprint` are preserved explicitly in the Enriched and Review Required sheets.
- Rows with a blank MPN are identified before provider lookup; DigiKey, Mouser and TME calls are skipped and the review observation states that the MPN is missing.
- Runtime progress is flushed immediately and shows provider-by-provider progress for every BOM row.
- Raw API payloads are no longer exposed in the workbook `Providers Queried` field.
- Provider status text is reduced to review-friendly states such as `success`, `not found`, `provider error`, `authentication error`, `rate limited`, and `skipped - MPN missing`.
- HTTP 404 / explicit not-found responses are treated as `no_match` for operational review rather than as provider-system failure.
- Common terminal tape/reel ordering suffixes are handled conservatively for identity matching. Examples covered by regression tests include `TPS628438YKA` vs `TPS628438YKAR` and `MAX40203ANS` vs `MAX40203ANS+T`.
- Arbitrary prefix matching remains prohibited.

## Raw diagnostics

Concise status is a workbook presentation rule only. ProviderEvidence retains the provider message so the Knowledge Base/provider history can preserve detailed diagnostic information.

## Regression

`python -m unittest discover -s tests -v`

Expected result for this patch: **226 tests OK**.
