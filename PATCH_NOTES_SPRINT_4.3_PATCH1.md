# Sprint 4.3 Patch 1 — BOM Normalisation

This patch introduces a deterministic, lossless preprocessing stage before matching,
provider searches, recommendations, or Parts Master updates.

## Key rules

- Source BOM is copied unchanged.
- One source row contributes to exactly one normalised group.
- MFG + MPN + DNP is the primary grouping identity.
- Blank-MPN rows use MFG + Value + Footprint + DNP as a conservative temporary identity.
- Fitted and DNP occurrences are never merged.
- References are combined and naturally sorted.
- Quantities are summed exactly as supplied.
- Complete source rows remain embedded in the normalised output and trace JSON.
- No MFG/MPN is invented and no Parts Master record is created.

## Galenband validation result

Using `gb-mini-board-v0.1-draft2.csv`:

- Source rows: 163
- Normalised rows: 75
- Rows consolidated: 88
- Groups with MPN: 30
- Groups without MPN: 45
- DNP groups: 2
- Lossless traceability check: PASS
