# Changelog Addition — Sprint 4.4 Patch 2

- Added cache-aware Knowledge Base population from the staging Parts Master.
- Added batch collection through DigiKey, TME and Mouser with isolated provider failures.
- Added PDCPartProfile generation and operational results, failures, skipped and summary reports.
- Added a ten-record default safety limit; use `--limit 0` to process all staging records.
- No correlation, approval, AIPN allocation, manifest or refresh-policy work is included.

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

## v0.2.10 Sprint 4.4 Patch 1

- Added lossless legacy AIPN Parts Master seed import.
- Added staging, duplicate, issue, alias, trace and summary outputs.
- Enforced pending-verification status with zero automatic approvals or AIPN allocation.

## v0.2.10 Sprint 4.4 Patch 3
- Added DigiKey Manufacturer + MPN search qualification.
- Added MPN-only candidate capture for ambiguous/unresolved searches.
- Added candidate ranking and separate provider-error reporting.
