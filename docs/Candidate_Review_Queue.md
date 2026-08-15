# Review Queue & Candidate Decision Summary — Sprint 4.6.2c

Sprint 4.6.2c turns the append-only review decisions created by Sprint 4.6.2b
into a deterministic **current-state engineering review queue**.

## Purpose

The queue answers practical review questions without changing any engineering
master data:

- Which BOM items still need attention?
- Which candidates are Pending or Need Verification?
- Which candidate has been Accepted or Rejected?
- Has the reviewer declared No Suitable Candidate?
- Has more than one candidate been Accepted for the same BOM item?

## Current-State Derivation

The 4.6.2b JSONL review history remains immutable. 4.6.2c derives current
state by using only the latest event for each BOM-item/candidate `review_key`.

Earlier events remain available as review history and are never deleted or
edited.

## Item Status

A BOM item is presented with one of these derived states:

- `Conflict - Multiple Accepted`
- `Pending`
- `Needs Verification`
- `No Suitable Candidate`
- `Accepted`
- `All Candidates Rejected`
- `No Review Candidates`
- `Reviewed`

A multiple-acceptance condition is deliberately treated as a conflict. PDC
must not silently choose between two human-accepted candidates.

## Queue Ordering

The current queue is ordered:

1. multiple-acceptance conflicts;
2. other items needing attention;
3. resolved items.

Candidate ordering within each BOM item prioritises Pending and Needs
Verification entries, followed by Accepted and Rejected entries. Score is used
only as a secondary display-order aid; 4.6.2c never changes the 4.6.2a score.

## Summary

`build_review_summary()` reports current-state counts including:

- total BOM items;
- total candidate proposals;
- BOM items needing attention;
- multiple-acceptance conflicts;
- No Suitable Candidate items;
- item-status counts;
- candidate-decision counts.

## Boundary

Sprint 4.6.2c is a read/derive/report layer. It does not:

- re-run or alter candidate matching;
- modify Parts Master;
- modify a BOM;
- modify an AVL;
- allocate an AIPN;
- create an ECO, concession or deviation;
- call a distributor or manufacturer API;
- convert Accepted into production authorisation.

Those remain later engineering-governance steps.
