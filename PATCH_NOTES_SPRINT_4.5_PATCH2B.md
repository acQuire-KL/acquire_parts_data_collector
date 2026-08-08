# PDC v0.2.10 — Sprint 4.5 Patch 2b

## Knowledge History Consolidation

Patch 2b simplifies the Knowledge Promotion model after review of the Patch 2a outputs showed that `PROMOTED_KNOWLEDGE` and `REVIEW_HISTORY` still duplicated much of the same information.

### Main change

Engineering knowledge is now stored in one permanent event file:

- `__KNOWLEDGE_HISTORY.csv`

A clean run therefore produces only:

- `__KNOWLEDGE_HISTORY.csv`
- `__SUMMARY.json`

`__VALIDATION.csv` is created only when warnings exist.

### Store once, derive views

The Knowledge History is the single stored record. PDC derives current views such as:

- Approved Parts
- Manufacturer Aliases
- Procurement Variant groups
- Current review state

Those views are not written as overlapping permanent CSV files.

### MPN duplication removed

An accepted MFG+MPN is stored once as an `Approved Part` event. It is no longer duplicated as both a `Procurement Variant` and an `Approved Addition`.

The procurement-variant relationship is carried on the Approved Part record through `Relationship Type` and `Relationship Group`.

Manufacturer aliases remain separate relationship knowledge, but alias rows do not repeat the MPN.

### Immutable history and superseding

Existing events are never deleted or overwritten. If a later decision changes an earlier one, the new event is appended and its `Supersedes` field points to the earlier Knowledge ID. Current state is derived from the supersession chain.

This preserves the timescale of engineering decisions for later impact analysis.

### Engineer comments

`Engineer Notes` are stored as `Engineer Comment` for all Accept, Reject and Defer decisions. Rejected and deferred candidates remain in Knowledge History as `Candidate Review` events rather than disappearing.

A future **Review Comment Learning** capability has been added to `docs/Parking_Lot.md`. Historical comments may later help candidate ranking and explanations, but they will never constitute manufacturer engineering evidence or independently approve a part.

### Governance unchanged

Patch 2b does not:

- modify a Parts Master;
- allocate an AIPN;
- automatically approve a component;
- treat provider/commercial data as manufacturer engineering evidence.
