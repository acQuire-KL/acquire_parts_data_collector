# Sprint 4.7.1b — Attribute Normalisation & Exceptions-Based Reporting

## Purpose
Make the operational BOM review easier to read as provider coverage grows. PDC continues to collect provider evidence independently, but the workbook reports normal agreement compactly and makes exceptions prominent.

## Provider Results
The two Status columns `Providers Queried` and `Providers Matched` are replaced by `Provider Results`.

Examples:
- `3 matched`
- `12 matched; 3 not found; 1 error`
- `1 matched; 8 not found; 4 error`

A provider returning part data without confirmed manufacturer + MPN identity is counted as `unconfirmed`. Skipped providers remain visible as a count.

## Attribute normalisation
Provider values are normalised conservatively for comparison. The source evidence itself is not rewritten.

Example agreement:
- DigiKey: `-55°C ~ 125°C`
- TME: `-55.0 to 125.0 C`

Workbook result:
- `-55°C to 125°C`

Example disagreement:
- DigiKey: `-55°C ~ 125°C`
- TME: `-40 to 125 C`

Workbook result:
- `EXCEPTION — DigiKey: -55°C ~ 125°C; TME: -40 to 125 C`

## Principle
Collect comprehensively. Normalise conservatively. Compress agreement. Report exceptions. Preserve evidence.
