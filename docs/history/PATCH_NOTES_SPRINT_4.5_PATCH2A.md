# Sprint 4.5 Patch 2a — Knowledge Promotion Consolidation

## Objective

Reduce duplicate Knowledge Promotion outputs while preserving complete engineering traceability and the ability to supersede decisions months or years later.

## Output simplification

Patch 2 generated separate Manufacturer Alias, Procurement Variant and Approved Addition files. Patch 2a combines these into one operational file:

`__PROMOTED_KNOWLEDGE.csv`

Each row is distinguished by `Knowledge Category`:

- Manufacturer Alias
- Procurement Variant
- Approved Addition

The permanent review audit trail remains separate in `__REVIEW_HISTORY.csv`.

## Stable knowledge identity

Promoted rows now carry deterministic Knowledge IDs:

- `MA-...` — Manufacturer Alias
- `PV-...` — Procurement Variant
- `PA-...` — Approved Addition

The same approved relationship produces the same Knowledge ID when reprocessed.

## Engineering knowledge lifecycle

Every promoted record includes:

- Status
- Effective From
- Effective To
- Supersedes
- Superseded By

Patch 2a creates new promoted knowledge as `Active`. It does not yet execute a supersede workflow; the fields establish the stable structure required for that future review action.

## Never delete; supersede

Review History is treated as immutable engineering history. Re-running the same review does not duplicate identical history entries. If a later review changes the engineering decision, it creates a new History ID and is appended rather than replacing the earlier event.

This preserves the time period during which an engineering decision was in force for future impact analysis.

## Validation

`__VALIDATION.csv` is only produced when warnings exist. Blocking errors still prevent promotion.

## Out of scope

Patch 2a does not:

- update or generate the Approved Parts Master;
- allocate AIPNs;
- automatically supersede knowledge;
- delete or modify earlier engineering decisions;
- add provider or BOM functionality.
