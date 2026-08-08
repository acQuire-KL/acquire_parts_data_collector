# Knowledge Base Population

Sprint 4.4 Patch 2 populates the PDC Knowledge Base from the staging Parts Master created by Sprint 4.4 Patch 1.

## Scope

For each valid Manufacturer + Manufacturer Part Number record, PDC checks the current Knowledge Base and queries DigiKey, TME and Mouser only when current data is absent. Raw provider responses remain in the existing Knowledge Base structure and a provider-specific `PDCPartProfile` is written under `output/provider_profiles`.

This patch does **not** correlate providers, approve records, allocate AIPNs, update the staging Parts Master, or create a final workbook.

## Safe initial run

The command defaults to ten staging records so API behaviour and credentials can be confirmed before a full population run:

```bash
py -m tools.knowledge_base_population_check "output/parts_master_staging/AIPN_Parts_Master__STAGING.csv"
```

Process all staging records only after reviewing the initial reports:

```bash
py -m tools.knowledge_base_population_check "output/parts_master_staging/AIPN_Parts_Master__STAGING.csv" --limit 0
```

Select one or more providers with repeated `--provider` arguments. Existing current captures are reused unless `--force` is supplied.

## Outputs

Reports are written to `output/knowledge_base_population`:

- `__RESULTS.csv` — one row per part/provider operation.
- `__FAILURES.csv` — API errors and provider not-found results.
- `__SKIPPED.csv` — missing configuration or incomplete identity.
- `__SUMMARY.json` — machine-readable counts by provider and status.
- `__RUN_LOG.txt` — concise human-readable progress summary.

The staging Parts Master is read-only throughout the operation.
