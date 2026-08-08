# Sprint 4.5 Patch 2b - Correction 5

## Knowledge History user-facing simplification

This correction removes the two redundant columns from `__KNOWLEDGE_HISTORY.csv`:

- `Standard Manufacturer Name`
- `Manufacturer Part Number`

The engineer-facing identity is now deliberately limited to:

1. `Original Manufacturer`
2. `Original MPN`
3. `Candidate Manufacturer`
4. `Candidate MPN`

followed by the decision, justification and engineer comment.

The accepted candidate remains represented by `Decision = Accept`; the same MPN is no longer repeated in a second manufacturer-part-number column.

Manufacturer-alias knowledge now uses the candidate manufacturer as the approved/standardised manufacturer side of the alias relationship, while the source alias remains in `Manufacturer Alias` and the full original source identity remains in the right-hand traceability fields.

Existing Knowledge History files are migrated in place on the next run. No Knowledge IDs or historical decisions need to be deleted first.

## Behaviour unchanged

- Knowledge remains append-only.
- Existing Knowledge IDs are preserved.
- Superseding remains supported.
- Conversation-block presentation remains unchanged.
- No Parts Master is modified.
- No AIPN is allocated.

## Regression

Full suite: 122 tests passing.
