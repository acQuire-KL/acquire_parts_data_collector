# PDC Documentation

This folder contains the current design documentation for Parts Data Collector.

## Core reading path

1. **Vision.md** — product purpose and relationship with PIE.
2. **Engineering_Principles.md** — non-negotiable engineering and development rules.
3. **Architecture.md** — current PDC system and data architecture.
4. **PDCPartProfile.md** — provider-neutral component profile.
5. **PDC_Parts_Master.md** — Parts Master import and governance.
6. **BOM_Normalisation.md** — source BOM normalisation and traceability.
7. **BOM_Intake_Classification.md** — Sprint 4.6 real-BOM intake classification and matching paths.
8. **Knowledge_Base_Population.md** — provider evidence collection.
9. **API_Onboarding.md** — repeatable provider onboarding method.
10. **Workbook_Style_Guide.md** — presentation conventions.
11. **Parking_Lot.md** — intentionally deferred work.

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

## Parts Master machine data

- [Parts Master Index](Parts_Master_Index.md) — structured machine-native Parts Master dataset introduced in Sprint 4.6.1.1.
