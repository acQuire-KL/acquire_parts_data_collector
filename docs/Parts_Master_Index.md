# Parts Master Index — Sprint 4.6.1.1

## Purpose

`Parts_Master/parts_master_index.json` is PDC's first machine-native structured view of the Parts Master.

It contains one record per unique **Manufacturer + Manufacturer Part Number** identity. An AIPN is useful but is **not required** to create a record. Until an AIPN is allocated, Manufacturer + MPN remains the external identity.

The index is generated from the current Parts Master source workbook. Excel is therefore the migration/source input at this stage; the JSON index is the dataset intended for PDC's local matching logic. Longer term, Excel should be treated as a human review/export format rather than PDC's database.

## What Sprint 4.6.1.1 does

- Reads `input/AIPN Parts Master.xlsx` from scratch.
- Groups duplicate source rows by Manufacturer + MPN.
- Creates one structured component record per identity.
- Preserves source-row traceability.
- Surfaces conflicting values from duplicate source rows instead of silently discarding them.
- Allows `AIPN: null` where an AIPN has not yet been allocated.

## What it deliberately does not do

- No provider/API calls.
- No automatic engineering approvals.
- No AIPN allocation.
- No free-text description parsing or inferred engineering attributes yet.
- No Value + Footprint-only component records; those remain BOM requirements until an actual MFG+MPN is approved.

## Build command

```bash
py -m tools.parts_master_index_check "input\AIPN Parts Master.xlsx"
```

Default output:

```text
Parts_Master/parts_master_index.json
```

The current migration baseline is 263 source rows consolidated to 260 unique MFG+MPN records.
