# Parts Data Collector — Engineering Principles

## 1. Collect Data; Do Not Make the Decision

PDC gathers facts and preserves evidence. PIE analyses those facts. The user approves engineering and procurement decisions.

## 2. Exhaust Readily Available Source Data

PDC should continue collecting while a source or subsequent source exposes relevant information. Missing primary commercial data does not justify discarding marketplace, similar-part, replacement, lifecycle or documentation information.

## 3. Never Discard Data Because the Current Report Does Not Use It

The current workbook is only one view of the Knowledge Base. Data that is not displayed today may support future costing, risk, comparison or audit functions.

## 4. Preserve Provider-Native Records

Original provider responses, terminology, identifiers, currency, URLs and timestamps must be retained. Provider-neutral fields are derived views and must not replace the source evidence.

## 5. Commercial Offers Are Plural

A component may have multiple providers, provider part numbers, packaging formats, MOQs, price ladders and additional charges. The data model must preserve all valid offers rather than arbitrarily selecting the first one.

## 6. Keep Additional Charges Separate from Unit Price

Fixed charges such as a re-reeling service fee are not component unit prices. Store them separately with their amount, currency, description and application basis so later costing can calculate effective cost transparently.

## 7. Separate Collection Logic from Presentation

Provider access, source normalisation, Knowledge Base storage, workbook construction and Excel formatting should remain separate modules wherever practical. A presentation change should not require changing collection logic.

## 8. Prefer Configuration Over Repeated Hard-Coding

Workbook section order, field definitions, formats and provider mappings should be defined centrally. This reduces inconsistent behaviour and makes future changes auditable.

## 9. Retain Traceability

Important values should retain enough context to identify:

- provider or source;
- source URL or provider identifier where available;
- capture date and time;
- locale and currency where relevant;
- whether the value came from current storage, migrated storage or a fresh request.

## 10. Do Not Infer When a Fact Can Be Collected

PDC should prefer explicit source statements over assumptions. Derived values must be clearly identifiable and reproducible from retained source data.

## 11. Highlight Conflicts; Do Not Silently Resolve Them

When sources disagree, preserve each value and its source. PIE or the user may later determine which value is appropriate.

## 12. Maintain Backward Compatibility Deliberately

Knowledge Base schema changes should be incremental. Existing records should remain usable through compatible readers, in-memory derivation or explicit migration rather than being silently abandoned.

## 13. Keep `main` Releasable

Development takes place on a branch. Changes are merged into `main` only after the application runs, regression checks pass, documentation is updated and a sample workbook has been reviewed.

## 14. Deliver in Testable Increments

Large changes should be divided into coherent steps that leave the project runnable. Each step should have a clear objective, replacement files, a test method and a meaningful commit.

## 15. Keep Deferred Work in the Parking Lot

Worthwhile ideas that are outside the current sprint should be recorded in `docs/Parking_Lot.md`. They should not rely on conversational memory.
## 16. Preserve Provider Independence

All provider-specific authentication, request construction, response parsing and mapping must remain inside the provider package or common provider framework. The core PDC application should treat every provider through the same contract. Adding a new provider should not require provider-specific changes to workbook, Knowledge Base or orchestration code.

## 17. Make Provider Onboarding Repeatable

A newly connected provider should use the common raw-response capture path before provider-neutral mapping is introduced. Provider folders, metadata, current/history storage and test expectations should be created by shared infrastructure rather than duplicated provider code.

## 18. Normalise Once, Consume Everywhere

Provider-specific terminology, units and formats shall be translated into a common internal representation within PDC. The Knowledge Base, workbook and PIE shall consume the normalised representation and shall not duplicate provider-specific parsing or mapping logic. Raw provider values must remain available as evidence.

## 19. Validate Before Publishing to PIE

PDC owns the heavy lifting required to collect, normalise, correlate and validate data attributes before they become the trusted Knowledge Base record used by PIE. PIE may analyse and make recommendations from that record, but should not need to reinterpret provider-native formats or determine whether equivalent technical values mean the same thing.


## PDCPartProfile grows additively

Useful attributes discovered from any provider are added to the provider-neutral PDCPartProfile. Existing useful attributes are not deleted because another provider does not expose them, and no provider is treated as authoritative.

## 20. Human Approval Controls the Parts Master

PDC may import, enrich and recommend Parts Master records, but no record may enter the Approved Parts Master without explicit human acceptance. Provider data and automated proposals remain staging evidence until approved. The source workbook must remain unchanged and every imported value must remain traceable.

## 21. Engineering Knowledge Is Immutable

Once engineering knowledge has been approved and promoted, it is never edited or deleted. A later engineering review may supersede or withdraw an earlier decision, but the earlier record and its evidence remain part of the permanent history.

Knowledge records therefore carry lifecycle fields that allow PDC to determine when a decision was effective and what later decision replaced it. This preserves the timescale of engineering decisions so later impact analysis can determine which products, BOMs or builds may have relied on knowledge that was subsequently changed.

## 22. Store Knowledge Once; Derive Views When Needed

PDC should avoid storing the same engineering decision in multiple overlapping operational files. Permanent engineering knowledge is recorded once in the immutable Knowledge History. Current Approved Parts, Manufacturer Aliases, Procurement Variant groups and review views are derived from that history when required.

This reduces duplicate data while preserving complete traceability.

## 23. PDC Removes Legwork, Not Engineering Approval

PDC should complete as much deterministic work as possible before asking the user to review a component: normalise duplicate BOM rows, apply known aliases, identify existing approved parts, gather candidate evidence and rank proposals. The user should only be asked to decide genuinely new or unresolved engineering knowledge.

PDC may make the approval workflow easy and repetitive, but it must not silently approve a new component or engineering relationship on the user's behalf.
