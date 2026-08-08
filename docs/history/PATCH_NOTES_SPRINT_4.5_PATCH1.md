# Sprint 4.5 Patch 1 — Candidate Review Workflow

Introduces a deterministic, file-based review artefact for provider candidates.

## Added

- Stable review group IDs.
- Candidate rows grouped by staging record, provider and source MPN.
- Rank-preserving review output.
- Human-editable decision and final identity fields.
- Evidence text derived only from the candidate search result.
- Optional procurement-variant grouping field for later governance work.

## Governance

The review generator never changes the candidate file, staging Parts Master or
approved Parts Master. Blank decision fields are intentional. Engineering
approval remains a separate future stage.
