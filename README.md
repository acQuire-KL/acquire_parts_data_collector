# Parts Data Collector (PDC) — v0.2.10

Parts Data Collector (PDC) builds reusable component knowledge from manufacturer and manufacturer-part-number identities. It normalises BOM data, checks existing PDC knowledge, gathers provider evidence for unknown parts, prepares candidate variants for human review, and preserves accepted engineering knowledge for reuse on future BOMs.

PDC is deliberately a **data collection and engineering-review preparation tool**. It removes repetitive research work, but it does not independently approve engineering decisions.

## Sprint 4.7.2a — Operational Provider Presentation, Lead-Time Normalisation & Performance

Operational provider blocks are now filled only by providers that returned useful commercial data for that BOM row. Lead time is reported consistently in whole weeks (rounded up), including safe handling of `0 Days`, quote-required values and ISO calendar delivery weeks. Provider detail calls run concurrently per BOM row, TME authentication is reused across its product endpoints, and run diagnostics expose provider activity and cumulative timing.

## Sprint 4.7.2 — BOM Identity Recovery & Variant Discovery

Operational BOM review can now recover a plausible missing MPN from BOM context, discover provider-returned orderable variants, and retain them in an `Identity Candidates` worksheet. Variant suffixes are candidates only; PDC no longer assumes `T`, `R` or `TR` is harmless without supporting evidence. See `docs/BOM_Identity_Recovery_Variant_Discovery.md`.

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



### Sprint 4.6.2d — Controlled Engineering Action Handoff

Current Accepted candidate reviews can now be converted into traceable
engineering-action proposals without modifying Parts Master, BOM, AVL or
production-authorisation data. Ambiguous cases are deliberately returned as
`Needs Engineering Classification`.


### Sprint 4.6.3a — Datasheet Evidence

PDC now retains a Static Evidence Copy and Active Source URL with manufacturer-source resolution and SHA-256 change foundations.


### Sprint 4.6.3b — Datasheet Acquisition

PDC can now follow a discovered datasheet URL, validate the returned document,
independently verify a Manufacturer Source URL where possible, prefer the
manufacturer document, and archive the resulting Static Evidence Copy using
the 4.6.3a provenance/hash model.

### Sprint 4.6.3c — Datasheet Evidence Integration

Datasheet evidence can now be attached to the correct component JSON and summarised into `parts_master_index.json`. PDC-acquired and user-supplied manufacturer specifications are both supported with distinct provenance.

### Sprint 4.7.1 — Operational BOM Review

PDC now connects the accumulated local knowledge, Parts Master context and all three provider paths (DigiKey, Mouser and TME) into a practical BOM-review workbook. The output preserves BOM context, shows each provider independently, surfaces datasheet/local evidence and adds a concise review summary without making automatic engineering approvals.


### Sprint 4.7.1a — Operational BOM Review Corrective Patch

Real-BOM testing now supports direct CSV input, common `MF` Manufacturer headings, explicit BOM Value/Footprint preservation, blank-MPN pre-checks, concise provider statuses and visible provider-by-provider runtime progress. Common terminal ordering-code suffixes are handled conservatively for identity matching.


## Sprint 4.7.2b

Identity recovery now uses traceable search representations: source text, alphanumeric search key, controlled family-prefix discovery, and cross-provider retry using a stronger manufacturer MPN discovered elsewhere. Search relaxation is discovery-only. The source BOM identity is never overwritten and family results remain review candidates until supported by manufacturer evidence.

Operational workbook presentation also uses numeric `Lead Time (Weeks)` values and wraps all cells.


## Sprint 4.7.2c

The operational identity workflow now exhausts exact and alphanumeric discovery before family broadening. DigiKey keyword discovery explicitly searches both the source BOM text and the alphanumeric key. Strong formatting-equivalent candidates stop family truncation and can be used to retry providers that failed the first pass.

`Review Required` is now an exception-oriented engineering queue rather than a duplicate of the Enriched sheet. A two-line Hirose/Abracon BOM is included under `tests/fixtures` for focused regression.


## Sprint 4.7.2d

Identity search is now evidence-led. With the current three active providers, two independent provider confirmations stop further normalisation and family broadening. If the BOM MPN is blank, two providers returning the same formatting-equivalent order code can resolve the identity without creating a Review Required exception. Family discovery is retained only as a conservative last resort and is capped at 25% right-side reduction.


## Sprint 4.7.2e console-only validation

For identity/debug validation without creating `output/AIPN_Enriched.xlsx`:

```bash
py main.py --input "input/gb-mini-board-v0.1-draft3 - 2part.csv" --console-only
```

The console reports each provider result, any discovery-returned MPN, consensus count, resolved identity and whether review is required. Two independent provider identity matches stop further broadening.


## Sprint 4.7.2f

TME provider coverage semantics are now explicit: a successful Product Search with zero returned products is `not listed`. Product Data and Product Parameters are not called in that state. API/authentication/network failures remain `provider error`.

Independent provider discovery remains the first pass. A resolved MPN from another provider is used only as a later cross-provider confirmation fallback when independent evidence is insufficient.


## Sprint 4.7.2g — DigiKey independent-first search

DigiKey identity discovery now begins with Keyword Search using only the source/BOM-derived MPN. Mouser and TME perform their own independent first-pass lookups in parallel. Provider results are compared only after those independent calls.

When DigiKey returns an alphanumeric-equivalent order code, PDC records that as independent DigiKey identity evidence and, where a DigiKey manufacturer ID is available, requests Product Details using DigiKey's own returned MPN. Cross-provider seeding remains a fallback only when independent consensus is insufficient.

Console validation remains:

```bash
py main.py --input "input/gb-mini-board-v0.1-draft3 - 2part.csv" --console-only
```
