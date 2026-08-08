# PDC v0.2.10 — Sprint 4.5 Patch 2b Correction

## Purpose

Make `__KNOWLEDGE_HISTORY.csv` easier for an engineer to read without changing the underlying immutable knowledge model.

## Changes

- Moves source/BOM identity to the left of Knowledge History:
  1. Original Manufacturer
  2. Original MPN
  3. Candidate Manufacturer
  4. Candidate MPN
- Places the approved/standard identity, decision, justification, engineer comment, datasheet/product link and provider next.
- Moves Knowledge IDs, Review IDs, lifecycle dates and supersession fields to the right.
- Preserves the Original MFG+MPN even when it is identical to the accepted candidate; this is intentional review traceability rather than duplicate knowledge.
- Persists Candidate Manufacturer and Candidate MPN in Knowledge History so the original proposal remains visible years later.

## Unchanged

- One permanent Knowledge History file.
- Never delete / never overwrite; later decisions supersede earlier knowledge.
- No Parts Master update.
- No AIPN allocation.
- No automatic engineering approval.
