# Changelog Addition — Sprint 4.4 Patch 2

- Added cache-aware Knowledge Base population from the staging Parts Master.
- Added batch collection through DigiKey, TME and Mouser with isolated provider failures.
- Added PDCPartProfile generation and operational results, failures, skipped and summary reports.
- Added a ten-record default safety limit; use `--limit 0` to process all staging records.
- No correlation, approval, AIPN allocation, manifest or refresh-policy work is included.

# Changelog Addition — Sprint 4.3 Patch 2

- Added a clean `__NORMALISED.csv` without development-only trace columns.
- Added `__NORMALISED_DEBUG.csv` retaining Grouping Basis, Source Rows, and Source Data JSON.
- Retained `__TRACE.json` as the formal lossless audit record.
- Added regression tests confirming the clean/debug output separation.
- No grouping or normalisation behaviour changed.

## v0.2.10 - Sprint 4.3 Patch 3
- Sort clean and debug normalised BOM outputs by first Reference Designator.
- Use natural RefDes ordering so numeric suffixes sort as engineers expect.
- Preserve grouping, DNP separation, quantities and lossless traceability.

## v0.2.10 Sprint 4.4 Patch 1

- Added lossless legacy AIPN Parts Master seed import.
- Added staging, duplicate, issue, alias, trace and summary outputs.
- Enforced pending-verification status with zero automatic approvals or AIPN allocation.

## v0.2.10 Sprint 4.4 Patch 3
- Added DigiKey Manufacturer + MPN search qualification.
- Added MPN-only candidate capture for ambiguous/unresolved searches.
- Added candidate ranking and separate provider-error reporting.

## v0.2.10 — Sprint 4.5 Patch 2
- Added Knowledge Promotion from completed candidate reviews.
- Added manufacturer-alias, procurement-variant, approved-addition and review-history artefacts.
- Added validation and governance summary outputs.
- No Parts Master modification or AIPN allocation.

## v0.2.10 — Sprint 4.5 Patch 2a
- Consolidated promoted manufacturer-alias, procurement-variant and approved-addition records into one `__PROMOTED_KNOWLEDGE.csv` output.
- Added stable Knowledge IDs and lifecycle fields for future superseding/withdrawal without deleting history.
- Kept `__REVIEW_HISTORY.csv` as an append-only engineering audit trail; identical reruns do not duplicate history entries.
- `__VALIDATION.csv` is now created only when warnings are present.
- Added explicit Engineering Knowledge immutability principle to project documentation.
- No Parts Master modification or AIPN allocation.

## v0.2.10 — Sprint 4.5 Patch 2b

- Consolidated Knowledge Promotion into one immutable `KNOWLEDGE_HISTORY` event store.
- Removed duplicate storage of accepted MFG+MPN records as both Procurement Variant and Approved Addition.
- Added derived current-state helpers for Approved Parts and Manufacturer Aliases.
- Added append-only supersession links so later decisions can replace earlier knowledge without deleting or editing the earlier event.
- Preserved Accept, Reject and Defer engineer comments for future review learning.
- Added Review Comment Learning to the Parking Lot.
- Added Engineering Principles for store-once/derive-views and PDC removing legwork without removing human approval.

## v0.2.10 — Sprint 4.5 Repository Housekeeping Step 1

Documentation-only housekeeping following completion of Sprint 4.5 Patch 2b.

- Rewrote the root README to describe the current PDC workflow and v0.2.10 state.
- Added a defined documentation reading order.
- Moved provider-specific notes into `docs/providers/`.
- Moved historical sprint installation and patch notes into `docs/history/`.
- Archived superseded cleanup/placement instruction files out of the project root.
- Added documentation indexes for current, provider-specific and historical material.
- No Python modules, runtime behaviour, provider integrations, inputs, outputs or Knowledge Base data changed in this step.

## v0.2.10 — Sprint 4.5 Repository Housekeeping Steps 2–5

- Grouped operational DigiKey, Mouser and TME code/checks under provider-specific folders.
- Moved cross-cutting workflow checks under `tools/` and added the generic `tools/provider_onboarding/` toolkit.
- Cleaned root-level development artefacts while retaining active runtime modules.
- Changed Knowledge Base Population to one current working set rather than accumulating timestamped report copies.
- Renamed the provider working-output folder to `output/provider_results/`.
- Moved persistent human-approved Knowledge History to `output/engineering_review/KNOWLEDGE_HISTORY.csv`.
- Added migration support for earlier nested Patch 2b Knowledge History files without duplicating Knowledge IDs.
- Retained `Knowledge_Base/` as the provider/source evidence store and deliberately retained legacy `cache/` and `raw_responses/` until their remaining dependencies can be removed safely.
- Final Step 5 regression suite: 126 tests PASS; deterministic BOM and Parts Master baselines unchanged.

## v0.2.10 — Sprint 4.6.1 BOM Intake & Classification

- Added the first real-BOM review intake stage using the committed Galenband BOM.
- Fresh-normalises the original source BOM in memory rather than using prior generated outputs as source information.
- Classifies every normalised unique item as `MFG + MPN`, `Value + Footprint`, or `Insufficient Data`.
- Adds a clear classification reason and next action for each item.
- Performs no Parts Master lookup, provider lookup, candidate recommendation or automatic approval in this patch.
- Adds a concise BOM-intake CSV and classification summary under `output/bom_intake/`.

## Sprint 4.6.2 — Existing Knowledge Matching
- Added local Parts Master and Knowledge Base matching before provider calls.
- Added conservative Value + Footprint matching; all descriptive matches require Engineering approval.
- Explicitly treats DNP as assembly context, not an exclusion criterion.
- Added fresh-source BOM local-match check and regression coverage.

## Sprint 4.6.1.1 — Parts Master Index Foundation

- Added machine-native `Parts_Master/parts_master_index.json` generation.
- One index record is created per unique Manufacturer + MPN identity.
- AIPN is optional; records without AIPN remain valid and use MFG+MPN as their identity basis.
- Preserves source-row traceability and reports duplicate-source attribute conflicts.
- No provider calls, automatic approvals, free-text attribute inference, or AIPN allocation.

## v0.2.10 — Sprint 4.6.2c Review Queue & Candidate Decision Summary

- Added a deterministic current-state review queue derived from the immutable 4.6.2b review history.
- Added BOM-item status and attention handling for Pending, Needs Verification, Accepted, Rejected and No Suitable Candidate outcomes.
- Added explicit conflict detection when more than one candidate is currently Accepted for one BOM item; PDC never silently selects one.
- Added current-state summary counts and flat queue rows for later console, CSV, workbook or GUI presentation.
- Added Static Datasheet / Specification Evidence Archive to the Parking Lot for future PDC collection/evidence work.
- No Parts Master, BOM, AVL, AIPN, ECO/concession/deviation or provider/API behaviour is changed by this sprint.

## v0.2.10 — Sprint 4.6.2d Controlled Engineering Action Handoff

- Added controlled handoff from current Accepted candidate reviews to proposed engineering actions.
- Added conservative action classification for AVL addition, BOM change, temporary concession/deviation, reference-only and unclassified cases.
- Added append-only engineering action proposal evidence.
- Added protection against handing off stale historical Accepted decisions.
- Preserved review evidence, warnings, score and justification in each proposal.
- No Parts Master, BOM, AVL, AIPN, ECO, concession/deviation or production authorisation is executed by this sprint.



## Sprint 4.6.3a Datasheet Evidence Model, Manufacturer Source Resolution & Local Archive

- Added Static Evidence Copy + Active Source URL model.
- Added manufacturer source resolution and verification state.
- Added MFG/DISTI/DISTI_COPY_OF_MFG classification and SHA-256 archive/change foundation.

## v0.2.10 — Sprint 4.6.3b Datasheet Acquisition & Manufacturer Source Verification

- Added live datasheet acquisition flow using the 4.6.3a evidence model.
- Added redirect/final-URL handling and manufacturer-domain candidate discovery.
- Added independent Manufacturer Source URL fetch/verification before promoting a source to verified MFG evidence.
- Added PDF-content validation to avoid archiving HTML/product pages as datasheets.
- Added preference for verified manufacturer evidence while retaining distributor evidence when no verified manufacturer source is available.
- Added structured acquisition failure handling suitable for future batch processing.
- Kept regression tests deterministic through injected/mock HTTP fetchers.
- No bulk parts_master_index.json mutation or semantic PDF change analysis is performed by this sprint.

