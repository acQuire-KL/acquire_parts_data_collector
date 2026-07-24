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
