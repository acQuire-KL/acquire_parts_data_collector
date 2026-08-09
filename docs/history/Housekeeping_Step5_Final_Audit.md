# Repository Housekeeping Step 5 — Final Audit

This audit closes the Sprint 4.5 repository-housekeeping sequence.

## Final data-folder roles

- `Knowledge_Base/` — retained provider/source evidence and current source captures.
- `output/provider_results/` — current provider-search working set. These files are regenerated and are not engineering history.
- `output/engineering_review/` — persistent human-reviewed engineering decision history. `KNOWLEDGE_HISTORY.csv` is never treated as disposable run output.
- `output/parts_master_staging/` — staging view generated from the legacy AIPN Parts Master.
- `output/normalised_boms/` — normalised BOM working outputs.
- `output/provider_profiles/` — provider-neutral profiles generated from provider evidence.

## Retained legacy folders

`cache/` and `raw_responses/` are retained for now. Existing tests and legacy provenance references still use them. They should not be deleted merely for cosmetic cleanup; a later migration can retire them once those dependencies have been removed and the Knowledge Base is confirmed as the sole evidence store.

## Removed / retired clutter

The final cleanup removes completed housekeeping instruction/test files from the root, obsolete sample workbook outputs, and generated `__pycache__` directories. Historical sprint/install notes remain under `docs/history/` rather than the project root.

## Knowledge History migration

The final six-row Sprint 4.5 Patch 2b Knowledge History is moved from the old nested `output/knowledge_base_population/knowledge_promotion/` location to:

`output/engineering_review/KNOWLEDGE_HISTORY.csv`

Future Knowledge Promotion runs use this fixed history filename and append/supersede knowledge without deleting earlier decisions.

## Test baseline

Step 5 was tested with 126 unit/regression tests. The deterministic local baseline remains:

- BOM source rows: 163
- Normalised BOM rows: 75
- Rows consolidated: 88
- BOM traceability: PASS
- Parts Master source rows: 263
- Staging records: 260
- Duplicate identity groups: 3
- Manufacturer alias groups: 4
- Automatic approvals: 0
- New AIPNs allocated: 0
- Parts Master traceability: PASS
