# Sprint 4.4 Patch 1 — PDC Parts Master Seed Import

Introduces a lossless XLSX seed importer for the legacy AIPN Parts Master.

## Included

- Manufacturer + MPN staging identity.
- Permanent staging Record IDs.
- Pending-verification status for every imported record.
- Legacy AIPN, description, family and datasheet preservation.
- Duplicate identity report.
- Conservative manufacturer alias report.
- Missing-identity issues report.
- Full source-row traceability and summary.
- Regression tests.

## Excluded

- Provider lookups.
- Automatic approval.
- New AIPN allocation.
- Parts Master matching.
- Source workbook modification.
