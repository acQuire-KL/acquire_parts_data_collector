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

Reports are written to `output/provider_results` as one **current working set**. A new population run replaces these files rather than creating another timestamped copy:

- `KB_POPULATION__RESULTS.csv` — one row per part/provider operation.
- `KB_POPULATION__FAILURES.csv` — not-found and multiple-candidate results requiring attention.
- `KB_POPULATION__SKIPPED.csv` — missing configuration or incomplete identity.
- `KB_POPULATION__CANDIDATES.csv` — candidate MFG+MPN combinations returned for engineering review.
- `KB_POPULATION__PROVIDER_ERRORS.csv` — connection, API, quota or runtime errors.
- `KB_POPULATION__SUMMARY.json` — machine-readable counts by provider and status.
- `KB_POPULATION__RUN_LOG.txt` — concise human-readable run summary.

The timestamps that describe the run remain inside the summary and run log; they are no longer encoded into every filename. Older timestamped population reports are removed automatically on the next population run. Human-edited `__CANDIDATE_REVIEW.csv` files are **not** removed automatically, because they may contain engineering decisions that have not yet been promoted.

The staging Parts Master is read-only throughout the operation.

## Downstream review

Candidate review remains a separate human decision stage:

```bash
py -m tools.candidate_review_check "output/provider_results/KB_POPULATION__CANDIDATES.csv"
```

Completed decisions are promoted into the persistent engineering review history:

```bash
py -m tools.knowledge_promotion_check "output/provider_results/KB_POPULATION__CANDIDATE_REVIEW.csv"
```

Knowledge Promotion writes the permanent decision history to `output/engineering_review/KNOWLEDGE_HISTORY.csv`. It is intentionally separate from the current provider working set.
