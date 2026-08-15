# Parts Data Collector (PDC) — v0.2.10

Parts Data Collector (PDC) builds reusable component knowledge from manufacturer and manufacturer-part-number identities. It normalises BOM data, checks existing PDC knowledge, gathers provider evidence for unknown parts, prepares candidate variants for human review, and preserves accepted engineering knowledge for reuse on future BOMs.

PDC is deliberately a **data collection and engineering-review preparation tool**. It removes repetitive research work, but it does not independently approve engineering decisions.

## Current workflow

```text
BOM / Parts Master input
        ↓
Normalisation and identity consolidation
        ↓
Existing PDC knowledge check
        ↓
Provider search for unresolved MFG + MPN identities
        ↓
Candidate generation and engineering justification
        ↓
Human Accept / Reject / Defer review
        ↓
Knowledge History
        ↓
Reusable knowledge for future BOM analysis
```

Generated working outputs are disposable views of the process. They are not the source of engineering truth and should be reproducible from committed inputs, provider evidence and approved knowledge. `output/engineering_review/KNOWLEDGE_HISTORY.csv` is the exception: it is the persistent, human-approved engineering decision history and is never treated as disposable run output.


## Development utilities

Cross-cutting workflow checks live under `tools/` and are run as modules from the repository root. Provider-specific checks remain with their provider under `providers/<provider>/checks/`. New provider discovery/onboarding utilities live under `tools/provider_onboarding/`.

Examples:

```bash
py -m tools.bom_normalization_check "input/gb-mini-board-v0.1-draft2.csv"
py -m tools.parts_master_seed_import_check "input/AIPN Parts Master.xlsx"
py -m tools.knowledge_base_population_check "output/parts_master_staging/AIPN_Parts_Master__STAGING.csv" --limit 10
py -m tools.candidate_review_check "output/provider_results/KB_POPULATION__CANDIDATES.csv"
py -m tools.knowledge_promotion_check "output/provider_results/KB_POPULATION__CANDIDATE_REVIEW.csv"
```

## Supported providers

| Provider | Status |
|---|---|
| DigiKey | Connected |
| Mouser | Connected |
| TME | Connected |

Provider integrations remain independent. PDC uses a provider-neutral part profile so that no single distributor defines the engineering data model.

## Documentation — recommended reading order

1. [`docs/Vision.md`](docs/Vision.md) — what PDC is intended to become and its relationship with PIE.
2. [`docs/Engineering_Principles.md`](docs/Engineering_Principles.md) — rules that govern PDC development and engineering decisions.
3. [`docs/Architecture.md`](docs/Architecture.md) — current system boundaries and data architecture.
4. [`docs/PDCPartProfile.md`](docs/PDCPartProfile.md) — provider-neutral component data model.
5. [`docs/PDC_Parts_Master.md`](docs/PDC_Parts_Master.md) — Parts Master seed/import and governance model.
6. [`docs/BOM_Normalisation.md`](docs/BOM_Normalisation.md) — BOM normalisation and traceability.
7. [`docs/BOM_Intake_Classification.md`](docs/BOM_Intake_Classification.md) — real-BOM intake classification and matching paths.
8. [`docs/Knowledge_Base_Population.md`](docs/Knowledge_Base_Population.md) — provider evidence collection and Knowledge Base population.
9. [`docs/API_Onboarding.md`](docs/API_Onboarding.md) — repeatable process for adding a new provider.
10. [`docs/Workbook_Style_Guide.md`](docs/Workbook_Style_Guide.md) — workbook presentation rules.
11. [`docs/Parking_Lot.md`](docs/Parking_Lot.md) — intentionally deferred ideas and future capability.

Provider-specific implementation notes are under [`docs/providers/`](docs/providers/). Historical sprint/install notes are retained under [`docs/history/`](docs/history/) for traceability but are not part of the normal reading path.

## Installation

Keep your local `.env` file and install dependencies in the active virtual environment:

```powershell
python -m pip install -r requirements.txt
```

## Main application

```powershell
python main.py --input input\AIPN_Input_Template.xlsx --output output\AIPN_Enriched.xlsx
```

Force a live provider refresh where supported:

```powershell
python main.py --input input\AIPN_Input_Template.xlsx --output output\AIPN_Enriched.xlsx --force-refresh
```

Validate input and credentials without retrieving product data:

```powershell
python main.py --input input\AIPN_Input_Template.xlsx --validate-only
```

## Development baseline

Run the complete regression suite with:

```powershell
py -m unittest discover -s tests -v
```

During repository housekeeping and structural refactoring, generated output files must not be used as source information. Tests and smoke checks should regenerate outputs from committed source inputs.

## PDC and PIE

**PDC** collects, normalises, preserves and presents component evidence and approved engineering knowledge.

**PIE** will consume that evidence to perform BOM-level interpretation, risk analysis and recommendations.

Keeping those responsibilities separate allows PDC knowledge to remain reusable across products, customers and future analyses.

### Sprint 4.6.2c — Review Queue

Candidate review history can now be reduced to a current-state engineering review queue and summary using `review_queue.py`. Multiple Accepted candidates for one BOM item are flagged as a conflict rather than automatically resolved.

