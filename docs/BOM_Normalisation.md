# BOM Normalisation Outputs

BOM normalisation preserves the source BOM and creates separate engineering and development artefacts.

## Output files

### `__SOURCE.csv`
Unmodified copy of the supplied BOM.

### `__NORMALISED.csv`
Clean engineer-facing output used by later matching and enrichment stages.
It excludes internal grouping and embedded source-data fields.

### `__NORMALISED_DEBUG.csv`
Development view containing the clean columns plus grouping basis, contributing
source-row numbers, and embedded source data.

### `__TRACE.json`
Definitive lossless traceability record linking every source row to exactly one
normalised group.

### `__SUMMARY.json`
Processing statistics and traceability result.

## Principle

PDC may reorganise source BOM data, but every source value must remain recoverable.

## Output ordering

The engineer-facing `NORMALISED.csv` and development `NORMALISED_DEBUG.csv` files are sorted by the first Reference Designator in each grouped row using natural ordering. For example, `C2` appears before `C10`, and a grouped row `R3, R20` is positioned using `R3`. Groups without a Reference Designator are placed last. This ordering affects presentation only; grouping and traceability are unchanged.
