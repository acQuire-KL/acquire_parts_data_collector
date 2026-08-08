# Sprint 4.4 Patch 3 — Provider Search Qualification and Candidate Capture

## Engineering intent

Improve provider search resolution without allowing an external result to
become approved Parts Master data automatically.

## Changes

- DigiKey exact lookup now uses resolved manufacturer ID plus MPN.
- Controlled manufacturer aliases participate in manufacturer resolution.
- Ambiguous or unresolved DigiKey Product Details requests fall back to an
  MPN-only keyword search.
- Every returned manufacturer and MPN combination is preserved in a candidate
  review report.
- Candidates are ranked by exact MPN, manufacturer equivalence and controlled
  manufacturer-name similarity; ranking is not approval.
- Operational provider failures are separated from legitimate `Not Found` or
  `Multiple Candidates` outcomes.
- Reports now distinguish `Exact Match`, `Alias Match`, `Multiple Candidates`,
  `Not Found`, and `Provider Error`.

## Explicit exclusions

- No staging Parts Master changes.
- No candidate approval.
- No AIPN allocation.
- No correlation engine.
- No workbook or GUI approval workflow.
