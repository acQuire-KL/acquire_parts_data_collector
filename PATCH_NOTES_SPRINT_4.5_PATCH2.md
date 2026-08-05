# Sprint 4.5 Patch 2 — Knowledge Promotion

## Objective
Convert completed candidate-review decisions into traceable, reusable engineering knowledge artefacts.

## Added
- `knowledge_promotion.py`
- `knowledge_promotion_check.py`
- `tests/test_knowledge_promotion.py`

## Outputs
- `__MANUFACTURER_ALIASES.csv`
- `__PROCUREMENT_VARIANTS.csv`
- `__APPROVED_ADDITIONS.csv`
- `__REVIEW_HISTORY.csv`
- `__VALIDATION.csv`
- `__SUMMARY.json`

## Governance
- The review file is never modified.
- The Staging Parts Master is never modified.
- No Approved Parts Master is generated yet.
- No AIPNs are allocated.
- Every promoted item remains linked to its Review ID and source record.
- The project term is **Standard Manufacturer Name**, not “canonical”.
