# Sprint 4.5 Patch 2b - Correction 3

## Knowledge History conversation grouping

This correction changes only the human-readable presentation/order of Knowledge History.

A source MFG+MPN now starts a review conversation block. The source identity is displayed once; related candidate, procurement-variant and manufacturer-alias rows follow beneath it until the next source MPN starts a new block.

Within each source-part block:

1. the candidate matching the original MPN is shown first when present;
2. other approved procurement variants follow;
3. derived manufacturer-alias knowledge follows last.

The visible repeated source cells are suppressed for readability, but the full source Manufacturer and MPN remain retained on every knowledge record in the right-hand `Source Manufacturer Record` and `Source MPN Record` fields. This preserves traceability and allows the grouped presentation to be safely reread on later runs.

No knowledge is deleted or overwritten. Existing history is migrated/re-rendered using the new presentation when the same review is rerun.
