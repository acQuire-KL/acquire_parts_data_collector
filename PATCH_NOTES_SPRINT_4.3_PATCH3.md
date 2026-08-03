# Sprint 4.3 Patch 3 - Natural Reference Sorting

## Objective
Improve engineering readability by sorting the clean and debug normalised BOM outputs by the first Reference Designator in each grouped row.

## Behaviour
- Natural ordering is used: `C2` precedes `C10`, and `R2` precedes `R10`.
- A grouped row such as `R3, R20` is positioned using `R3`.
- Rows without a Reference Designator are placed after referenced rows.
- No grouping, matching, provider lookup, recommendation or Parts Master behaviour is changed.

## Traceability
All source data remains available in `SOURCE.csv`, `NORMALISED_DEBUG.csv` and `TRACE.json`.
