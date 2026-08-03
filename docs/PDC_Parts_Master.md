# PDC Parts Master

## Purpose

The PDC Parts Master is the engineering-controlled catalogue used for trusted BOM matching. It is not an automatically populated cache of provider responses.

## Seed import workflow

Sprint 4.4 Patch 1 imports the existing AIPN Parts Master into a staging area:

```text
Legacy AIPN Parts Master
        ↓
PDC Parts Master – Staging
        ↓ human review (future sprint)
PDC Parts Master – Approved
```

Every imported record begins as **Imported - Pending Verification**. The importer does not allocate AIPNs, query providers, or approve records.

## Identity

The staging identity is Manufacturer + Manufacturer Part Number. Existing AIPNs remain legacy evidence while the internal numbering rules are reviewed.

## Governance

- No record is added to the Approved Parts Master without human acceptance.
- Provider matches are candidates, not approvals.
- Duplicate source identities are consolidated only in staging and retain every original row in the trace output.
- Manufacturer spelling, case and diacritic variants may be proposed as aliases, but abbreviations and corporate-name differences require review.
- Missing Manufacturer or MPN rows remain in the import-issues output and are never silently discarded.
- The legacy workbook is never overwritten.

## Outputs

- `__STAGING.csv` — clean pending-verification records.
- `__STAGING_DEBUG.csv` — staging records with source-row detail.
- `__IMPORT_ISSUES.csv` — rows missing Manufacturer or MPN.
- `__DUPLICATES.csv` — repeated MFG+MPN identities.
- `__MANUFACTURER_ALIASES.csv` — conservative alias proposals requiring review.
- `__TRACE.json` — complete source evidence.
- `__SUMMARY.json` — import statistics and governance checks.
