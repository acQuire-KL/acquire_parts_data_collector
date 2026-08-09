# PDC Tools

This folder contains development and validation utilities that operate across the PDC workflow.

These utilities are intentionally separate from production modules. Run them as Python modules from the repository root so imports resolve consistently.

## Current workflow checks

```bash
py -m tools.bom_normalization_check "input/gb-mini-board-v0.1-draft2.csv"
py -m tools.parts_master_seed_import_check "input/AIPN Parts Master.xlsx"
py -m tools.knowledge_base_population_check "output/parts_master_staging/AIPN_Parts_Master__STAGING.csv" --limit 10
py -m tools.candidate_review_check "output/knowledge_base_population/KB_POPULATION__CANDIDATES.csv"
py -m tools.knowledge_promotion_check "path/to/__CANDIDATE_REVIEW.csv"
```

Provider-specific checks do **not** live here. They belong with the operational provider under `providers/<provider>/checks/`.

## New provider onboarding

`provider_onboarding/` contains the provider-neutral onboarding method and helper utilities used before a new integration is promoted into `providers/<provider>/`.
