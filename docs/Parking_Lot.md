# PDC Parking Lot

This document captures future enhancements identified during development.

The purpose of the Parking Lot is to record worthwhile ideas without distracting from the current development sprint.

Only features that have a clear objective and measurable benefit should be added.

---

# Multi-Source Attribute Validation

**Priority:** Medium

## Objective

Validate technical attributes collected from multiple data providers and identify discrepancies before presenting them to the user.

## Proposed Source Hierarchy

1. Manufacturer Datasheet / Manufacturer Website
2. Distributor-hosted Manufacturer Datasheet
3. Distributor Product Data

## Future Behaviour

- Preserve every collected value.
- Record the source of every attribute.
- Record capture date and time.
- Compare equivalent attributes from multiple providers.
- Highlight disagreements.
- Never automatically overwrite an approved value.
- Allow PIE to present differences for engineering review.

Engineering approval always remains a manual decision.

---

# Local Datasheet Repository

**Priority:** Medium

## Objective

Maintain a local repository of manufacturer datasheets used during product development.

## Benefits

- Offline access
- Engineering traceability
- Protection against broken URLs
- Historical document archive
- ECO support
- Future document comparison

## Notes

The live Datasheet URL should also be retained.

The URL itself provides useful information if:

- a newer revision has been published;
- the manufacturer has moved the document;
- the distributor has updated the linked document;
- the document is no longer available.

The locally stored copy represents the document that engineering approved during product development.

---

# Local Product Image Repository

**Priority:** Low

## Objective

Maintain local copies of product images.

## Benefits

- Offline operation
- Faster UI
- Engineering Parts Catalogue
- Improved user experience within PIE

Initially only the Product Image URL will be stored.

---

# Datasheet Version Tracking

**Priority:** Medium

## Objective

Detect when manufacturers publish a newer datasheet revision.

## Possible Behaviour

- Compare latest available revision against the locally stored revision.
- Notify when newer revisions exist.
- Link previous and latest revisions.
- Assist engineering review.
- No automatic acceptance of newer revisions.

Engineering disposition always remains a manual decision.

---

# Commercial Data Refresh

**Priority:** Medium

## Objective

Refresh commercial information independently from technical information.

Examples include:

- Distributor Stock
- Factory Stock
- Lead Time
- MOQ
- Price Breaks
- Packaging Options

Technical attributes generally change infrequently, while commercial information changes regularly.

---

# Incremental Knowledge Base Refresh

**Priority:** Low

## Objective

Refresh the Knowledge Base incrementally rather than attempting to refresh every component simultaneously.

Possible future strategies include:

- Daily rotation
- Weekly rotation
- Lifecycle-based priority
- Frequently-used components first
- User-requested refresh

This approach reduces API usage while keeping the Knowledge Base current.

---

# Manufacturer PCN Integration

**Priority:** Medium

## Objective

Capture and associate Product Change Notices (PCNs) with components held within the Knowledge Base.

## Future Behaviour

- Record PCNs alongside the affected component.
- Link PCNs to datasheet revisions where applicable.
- Allow PIE to notify users when an approved component has an outstanding PCN.
- Support engineering review and ECO decisions.

PDC collects and preserves the information.

PIE presents the information.

Engineering decides the appropriate action.

---

# Future Engineering Parts Catalogue

**Priority:** Low

## Objective

Provide a visual component catalogue for engineers and procurement.

Possible features include:

- Product image
- Manufacturer
- MPN
- Description
- Package
- Lifecycle
- Datasheet
- Search by attribute
- Search by image/category
- Links into PIE and the Knowledge Base

This would become another view of the Knowledge Base rather than a separate database.
---

# Interactive Review GUI

**Priority:** Medium

## Objective

Replace the temporary Excel `User Action` review workflow with an interactive GUI in which the user can select proposed matches, correct source information, defer custom parts and approve candidate records.

The GUI must retain the principle that PDC prepares data but does not automatically add records to the Knowledge Base.

---

# Automated Currency Tracker

**Priority:** Medium

## Objective

Replace the development exchange-rate table with an automatically maintained currency-rate provider or tracker.

Future behaviour should include:

- EUR conversion rates for USD, GBP and RON, with scope to add more currencies.
- Original provider currency and original prices always retained.
- Rate source and retrieval timestamp stored.
- Historical rates retained so past commercial snapshots can be reproduced.
- Cached rates used when the external provider is unavailable.

---

# Persistent Manual Review Queue

**Priority:** Low

## Objective

Consider a persistent queue for repeatedly unresolved items after experience with the normal rerun workflow.

Possible future behaviour includes retry counts, a configurable three-strikes rule, deferred custom parts and assignment to a manual review session. A Review ID should only be introduced if persistent cross-run tracking proves necessary.

---

# Price-Break Colour Palette and Rich-Text Formatting

**Priority:** Low

## Objective

Improve the multiline `Price Breaks` summary in `Enriched Parts` after the core commercial workflow is complete.

## Proposed Presentation

- Quantity in blue.
- `@` separator in black.
- Unit price in green.
- One price break per line.
- Quantities padded so the `@` symbols align vertically.
- Workbook colours held in one central palette so they can be adjusted after visual review.

## Notes

Partial-cell formatting requires Excel rich-text runs and may not be reliably supported by the current workbook-writing library. The plain multiline output should remain the functional fallback.

---

# Multi-Provider Collection Workflow

**Priority:** High

## Objective

Progressively reproduce the manual sourcing workflow used when a component cannot be fully researched from one distributor.

## Candidate Sources

- Existing Knowledge Base
- Manufacturer website and documentation
- DigiKey
- Mouser
- Farnell / element14 / Newark
- RS
- Arrow
- Avnet
- TME
- LCSC
- FindChips and similar aggregators
- Specialist and regional distributors
- General web search

## Notes

The source order should eventually be configurable and may differ by region, component category or information type. PDC collects the evidence; PIE later compares and ranks it.

---

# Marketplace Offer Capture

**Priority:** Medium

## Objective

Capture marketplace offers exposed by providers when authorised distribution offers are unavailable or incomplete.

## Requirements

- Clearly identify the offer as marketplace data.
- Retain seller, provider, stock, price, MOQ, location and timestamps where available.
- Do not present a marketplace seller as an authorised distributor.
- Do not automatically recommend or approve the offer.

---

# Similar-Part and Replacement Reference Capture

**Priority:** Medium

## Objective

Collect similar-part, replacement, alternate-packaging and related-product references exposed by source websites.

## Notes

PDC should retain the references and their source context without asserting equivalence. PIE may later compare specifications and propose alternatives for user review.

---

# Commercial Offer Summary Presentation

**Priority:** Medium

## Objective

Improve how all provider delivery formats are summarised on `Enriched Parts` while retaining one component row.

## Options to Evaluate

- One wrapped cell containing a clearly separated block for every offer.
- A small group of commercial summary columns containing multiline values.
- One Enriched Parts row per delivery format, with identity fields repeated.
- A configurable choice between component view and offer view.

## Notes

The long-form `Commercial Analysis` worksheet remains the canonical tabular output with one row per offer and price break.

---

# Historical Commercial Snapshots

**Priority:** Medium

## Objective

Retain dated commercial snapshots so PIE can analyse changes in price, stock, MOQ and lead time.

## Future Behaviour

- Record provider and capture timestamp.
- Preserve the original currency and price ladder.
- Compare current and previous snapshots.
- Avoid creating false history entries when records are merely read from the Knowledge Base.

---

# Provider Confidence and Source Quality

**Priority:** Low — Future PIE

## Objective

Allow PIE to assess the relevance and confidence of different source types without changing the collected source data.

Potential factors include:

- manufacturer versus distributor statement;
- authorised versus marketplace source;
- freshness;
- completeness;
- agreement with other sources;
- design registration or customer-specific data.

PDC records the facts required for the assessment. PIE performs the assessment.

---

# Commercial Offer Ranking

**Priority:** Low — Future PIE

## Objective

Allow PIE to rank purchasing offers for a defined demand quantity and user constraints.

Potential factors include:

- effective unit cost;
- MOQ and excess quantity;
- fixed charges;
- stock and lead time;
- authorised-distributor status;
- pack format;
- currency and landed-cost assumptions;
- approved supplier and AVL status.

No offer should be selected automatically without a transparent rule and user review.

---

# Workbook Colour Palette

**Priority:** Low

## Objective

Hold workbook colours, fills and fonts in one configurable palette so presentation can be refined without changing workbook logic.

This item complements the existing rich-text price-break formatting item.

---

# Release Checklist

**Priority:** Low

## Objective

Introduce a concise, repeatable checklist before merging a release branch into `main`.

Suggested checks:

- Version updated.
- Changelog updated.
- Documentation updated.
- Application run completed.
- Regression samples passed.
- Sample workbook reviewed.
- Release branch merged.
- Tag created and pushed.

---

# Regression Test Library

**Priority:** Medium

## Objective

Build a representative library of real-world BOM inputs and lightweight expected-behaviour checks for repeatable regression testing.

## Initial Approach

- Retain suitable sample BOMs as they are encountered.
- Record concise manual checks for important workbook behaviours.
- Avoid storing generated workbooks unless a specific comparison requires them.
- Continue using unit tests for deterministic code-level checks.

## Future Automation

Selected checks may later be automated, including:

- workbook generation;
- worksheet names and order;
- enriched-part counts;
- offer and price-break counts;
- expected provider records;
- hyperlink and field-presence checks.

Visual workbook review remains a manual engineering check where appropriate.

## Future GUI / Knowledge Base Explorer

Develop a GUI presentation layer after the multi-provider Knowledge Base and provider coverage are mature.

Possible later modes:

- **PDC Explorer** — browse every component in the Knowledge Base and view all provider identity, engineering, commercial and raw-evidence records on one screen.
- **PIE Explorer** — use a BOM as the component filter, then add analysis, risk assessment and recommendations without changing the provider evidence captured by PDC.

The GUI must remain a view over the Knowledge Base rather than becoming an independent data store.

## Deferred provider investigation — Mouser technical parameters

The current documented Mouser Search API response does not expose the detailed technical parameter set visible on the product webpage. Revisit when Mouser changes its API, another supported endpoint is identified, or a commercial need justifies further investigation.
