# BOM Intake & Classification — Sprint 4.6.1

Sprint 4.6 begins the first end-to-end review of a real customer BOM. Patch 4.6.1 deliberately performs **classification only** so that the actual population of the Galenband BOM can be understood before any new matching intelligence is added.

## Source rule

The classifier starts from the original BOM in `input/` and invokes the existing BOM normaliser in memory. It does **not** read an older generated normalised BOM from `output/` as source information.

Every normalised unique BOM item is assigned to exactly one path:

### MFG + MPN

Both Manufacturer and Manufacturer Part Number are present.

Next stage: Parts Master MFG + MPN lookup.

### Value + Footprint

The MPN is blank and both Value and Footprint are available.

Next stage: Parts Master Value + Footprint lookup.

This is a candidate-identification path only. A descriptive match must not become an approved MFG + MPN without engineer review.

### Insufficient Data

The row does not satisfy either current identification path. PDC records why the row cannot yet progress and leaves it for engineer review/additional source information.

An MPN without a Manufacturer is intentionally classified as insufficient rather than guessed into the Value + Footprint path.

## Output

The working output is written to `output/bom_intake/`:

- `<BOM>__BOM_INTAKE.csv` — every normalised BOM item plus classification, reason and next action.
- `<BOM>__BOM_INTAKE_SUMMARY.json` — source/normalised counts and classification totals.

No Parts Master lookup, Knowledge Base lookup, provider call, candidate recommendation, or approval occurs in Sprint 4.6.1.

## Development command

```powershell
py -m tools.bom_intake_classification_check "input\gb-mini-board-v0.1-draft2.csv"
```
