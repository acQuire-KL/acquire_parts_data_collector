## Sprint 4.7.2e — Console-First Identity Resolution

- Added `--console-only` mode so live identity/provider logic can be validated without generating a workbook.
- Added explicit Hirose manufacturer alias handling (`Hirose` ↔ `Hirose Electric Co Ltd`) through the auditable manufacturer alias table.
- DigiKey manufacturer-resolution uncertainty no longer immediately becomes a provider error when keyword discovery remains available.
- DigiKey keyword discovery can now contribute identity evidence when the returned MPN is alphanumeric-equivalent to the source search text.
- Provider-returned formatting is preferred over raw BOM punctuation when the alphanumeric manufacturer order code is identical.
- Manufacturer-defined alphanumeric characters remain strict: Hirose `6DS` and `6DP` are distinct identities and are never normalised together.
- Two independent provider identity confirmations stop further normalisation/family broadening and suppress a third-provider coverage/error gap from `Review Required`.
- Corrected the Review Required filter so `No immediate review exception identified` does not itself trigger review.
- Family broadening remains capped at 25% and is not entered once two-provider consensus is reached.
- Housekeeping performed before packaging.

## Sprint 4.7.2d corrective logic patch

- DigiKey keyword-search results that are alphanumeric-equivalent to the source search text are now retained as formatting-normalised identity candidates instead of being discarded as redundant exact identities.
- Two independent provider identity matches now stop discovery regardless of harmless provider manufacturer-name spelling differences.
- This prevents Abracon 2-of-3 matches from entering normalisation and allows DigiKey search to surface corrected Hirose punctuation/order-code formatting.

# Changelog

## Sprint 4.7.2d — Evidence-Led Identity Resolution

- Identity resolution now stops when two or more active providers independently confirm the same Manufacturer + MPN.
- Normalisation/family discovery is therefore not run for already-resolved identities.
- Blank-MPN BOM context can be resolved when two independent providers return the same formatting-equivalent Manufacturer + MPN.
- Provider retry success now replaces stale first-pass no-match/error evidence in final Provider Results.
- Family discovery is a last resort and is capped at 25% right-side reduction; short MPNs are not broadened.
- `not listed` remains a normal provider coverage state, distinct from provider errors.
- A resolved recovered identity does not enter Review Required merely because candidate evidence exists.
- No automatic engineering approval and no BOM rewrite.

# Changelog

## Sprint 4.7.2c — Identity Search Correction & Exception Review Queue

- Provider coverage wording corrected: a successful provider lookup with no product listing is reported as `not listed`, not an error. `error` is reserved for genuine API/authentication/network/processing failures.
- Corrects the identity-recovery search state machine using the Hirose/Abracon two-part regression fixture.
- DigiKey keyword discovery now tries the exact source search text as well as the alphanumeric search key.
- A returned same-manufacturer MPN with the same alphanumeric identity is treated as a strong formatting-normalised candidate.
- Family truncation is suppressed once a strong formatting-equivalent candidate is found.
- Failed providers are retried using the stronger properly formatted MPN discovered by another provider/search path.
- Clean exact matches such as Abracon `AOTA-N160808S-2R2MT` remain matched even when another provider has no listing.
- `Review Required` is redesigned as a concise exception queue rather than a near-duplicate of `Enriched Parts`.
- Adds a permanent two-line Hirose + Abracon regression BOM fixture.
- No automatic engineering approval, BOM substitution, Parts Master mutation or AIPN allocation.

# Changelog

## Sprint 4.7.2b — Search Normalisation & Multi-Pass Identity Resolution

- Preserves the exact source MPN / BOM field used to initiate identity discovery.
- Adds a punctuation-free alphanumeric search key for internal/provider discovery.
- Adds controlled progressive right-side truncation for manufacturer-family discovery.
- Stops family broadening when a useful manufacturer-family result level is found.
- Adds cross-provider retry: a stronger MPN discovered by one provider is retried against providers that did not confirm the first pass.
- Family-search results remain candidates and require manufacturer-document/order-table verification; they never silently alter the BOM.
- Provider candidate evidence records discovery source and relationship.
- Provider lead-time dashboard headings are now `Lead Time (Weeks)`; duration values are numeric whole weeks rounded up.
- Calendar week notation remains interpreted as a delivery week, not a duration.
- Lead-time cells are centre aligned.
- All output workbook cells use word wrap for readability.
- No automatic engineering approval, BOM substitution, Parts Master mutation or AIPN allocation.
# Sprint 4.7.2a — Operational Provider Presentation, Lead-Time Normalisation & Performance

- Provider dashboard blocks are now result-driven per BOM row; providers with no useful commercial data no longer consume Provider #1/#2/#3 positions.
- Provider order remains neutral for now: useful results retain provider registration order until a later configurable/commercial ranking policy is introduced.
- Lead time is normalised to whole calendar weeks and always rounded up in operational workbook views.
- Zero/negative lead time is reported conservatively as `Request Delivery Quote`, never as immediate availability.
- ISO calendar delivery notation such as `Week 45` is detected and converted to a duration from the run date rather than being misread as 45 weeks.
- DigiKey, Mouser and TME detail collection is now concurrent per BOM row.
- TME reuses one access token across Search, Data and Parameters instead of authenticating separately for each endpoint.
- Added provider operation/timing diagnostics to the console and BOM Review Summary.
- Knowledge Base manifest updates are thread-safe for concurrent provider collection.
- Added 10 regression tests; full suite now 253 tests OK.

# Sprint 4.7.2 — BOM Identity Recovery & Variant Discovery

- Added conservative recovery of missing MPNs from BOM Value/Description without rewriting the BOM.
- Removed automatic identity acceptance of T/R/TR suffix differences; these are now variant candidates requiring evidence.
- Added provider-backed variant discovery from DigiKey keyword search, Mouser search/alternate packaging data and TME manufacturer symbols.
- Added conservative BOM Footprint consistency evidence for candidates.
- Added `Identity Candidates` worksheet to operational BOM review output.
- Consolidates the same candidate across providers while retaining evidence-source names, package and datasheet context.
- Stores identity-candidate evidence in the Knowledge Base summary without allocating an AIPN or modifying Parts Master.
- Added 12 regression tests; full suite now 243 tests OK.

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

## v0.2.10 — Sprint 4.6.3c Datasheet Evidence Integration & User-Supplied Evidence

- Added component JSON evidence history and active selection.
- Added lightweight parts_master_index.json datasheet evidence summary.
- Added user-supplied manufacturer PDF support with explicit provenance.
- Added Manufacturer + MPN identity protection and ambiguous-index rejection.

## v0.2.10 — Sprint 4.7.1 End-to-End Operational BOM Review

- Connected DigiKey, Mouser and TME into one operational BOM-review path with no distributor preference.
- Added operational TME provider adapter using the existing TME client and provider-neutral normaliser.
- Added BOM Description, Quantity and DNP context to the review workbook; DNP remains reviewable assembly context.
- Added read-only Parts Master Index context including AIPN, lifecycle and datasheet evidence.
- Added Review Observation and BOM Review Summary outputs.
- Added third provider dashboard block for TME and retained detailed commercial offers in Commercial Analysis.
- Kept engineering approval, BOM/AVL mutation and AIPN allocation outside PDC review.


## v0.2.10 — Sprint 4.7.1a Operational BOM Review Corrective Patch

- Added direct CSV BOM intake for the operational review path.
- Added `MF` Manufacturer header alias support.
- Added explicit BOM Value and Footprint columns to review output.
- Added pre-provider blank-MPN handling and explicit review messaging.
- Added immediate flushed runtime/progress output with provider-by-provider status.
- Replaced raw API payloads in `Providers Queried` with concise engineering-review statuses.
- Mapped provider 404/not-found responses to operational `no_match` while retaining raw diagnostics outside the workbook display.
- Added conservative terminal ordering-suffix identity handling for common R/T/TR variants.

## Sprint 4.7.1b — Attribute Normalisation & Exceptions-Based Reporting

- Replaced `Providers Queried` and `Providers Matched` workbook columns with one compact `Provider Results` count, e.g. `12 matched; 3 not found; 1 error`.
- Added conservative engineering-attribute normalisation before cross-provider comparison.
- Equivalent formatting such as `-55°C ~ 125°C` and `-55.0 to 125.0 C` now collapses to one clean value: `-55°C to 125°C`.
- Genuine provider attribute disagreement remains explicit and is prefixed `EXCEPTION —` with source-labelled values.
- Added weak-consensus review observation when only one provider matches while other provider outcomes exist.
- Raw provider evidence is unchanged and remains available for diagnostics/Knowledge Base evidence.
- Regression suite: 231 tests passing.
