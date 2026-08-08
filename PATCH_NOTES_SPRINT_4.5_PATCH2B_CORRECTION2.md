# Sprint 4.5 Patch 2b – Correction 2

## Knowledge History schema refresh on no-change reruns

This correction fixes a presentation migration issue found while retesting the
engineer-first Knowledge History column order.

Previously, when a Candidate Review contained no new knowledge events, PDC
correctly appended zero records but also skipped rewriting the existing
`__KNOWLEDGE_HISTORY.csv`.  As a result an older Knowledge History file retained
its previous column order even though the run summary was refreshed.

The Knowledge History is now always rewritten using the current schema and
column order after it is read and merged.  Existing knowledge rows are preserved;
no user deletion or reset is required.

This does **not** change the immutable-history principle.  Knowledge records are
still never deleted or edited as engineering decisions.  Only the CSV
representation/schema is refreshed.
