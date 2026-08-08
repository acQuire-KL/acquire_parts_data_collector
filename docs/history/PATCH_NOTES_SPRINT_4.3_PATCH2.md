# Sprint 4.3 Patch 2 — Clean Normalised Output

## Objective

Separate the engineer-facing normalised BOM from development diagnostics.

## Behaviour

`__NORMALISED.csv` now contains only:

- MFG
- MPN
- Value
- Datasheet
- Footprint
- Quantity
- Reference
- DNP

`__NORMALISED_DEBUG.csv` contains the same fields plus:

- Grouping Basis
- Source Rows
- Source Data JSON

`__TRACE.json` remains the authoritative lossless source-row audit trail.

## Scope control

This patch changes output presentation only. Grouping, DNP handling, quantity
summing, reference sorting, fallback identity logic, and traceability are unchanged.
