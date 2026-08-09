# PDC Documentation

This folder contains the current design documentation for Parts Data Collector.

## Core reading path

1. **Vision.md** — product purpose and relationship with PIE.
2. **Engineering_Principles.md** — non-negotiable engineering and development rules.
3. **Architecture.md** — current PDC system and data architecture.
4. **PDCPartProfile.md** — provider-neutral component profile.
5. **PDC_Parts_Master.md** — Parts Master import and governance.
6. **BOM_Normalisation.md** — source BOM normalisation and traceability.
7. **Knowledge_Base_Population.md** — provider evidence collection.
8. **API_Onboarding.md** — repeatable provider onboarding method.
9. **Workbook_Style_Guide.md** — presentation conventions.
10. **Parking_Lot.md** — intentionally deferred work.

## Supporting documentation

- `providers/` contains provider-specific implementation and capability notes.
- `history/` contains superseded sprint, patch, installation and cleanup notes retained only for project traceability.

Historical documentation should not be used to determine current PDC behaviour when a current core document covers the same subject.

- `../tools/` contains cross-cutting workflow checks and the generic provider onboarding toolkit.

## Repository data folders

Three similarly important concepts are deliberately named differently:

- `../Knowledge_Base/` — retained provider/source evidence.
- `../output/provider_results/` — current provider-search and candidate working results.
- `../output/engineering_review/` — persistent human-reviewed engineering decision history.

This separation avoids using generated provider output as the source of engineering truth.
