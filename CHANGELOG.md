# Changelog Addition — Sprint 4.3 Patch 2

- Added a clean `__NORMALISED.csv` without development-only trace columns.
- Added `__NORMALISED_DEBUG.csv` retaining Grouping Basis, Source Rows, and Source Data JSON.
- Retained `__TRACE.json` as the formal lossless audit record.
- Added regression tests confirming the clean/debug output separation.
- No grouping or normalisation behaviour changed.

## v0.2.10 - Sprint 4.3 Patch 3
- Sort clean and debug normalised BOM outputs by first Reference Designator.
- Use natural RefDes ordering so numeric suffixes sort as engineers expect.
- Preserve grouping, DNP separation, quantities and lossless traceability.
