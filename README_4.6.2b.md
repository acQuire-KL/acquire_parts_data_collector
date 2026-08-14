# PDC Sprint 4.6.2b — Candidate Review & Decision Handling

## Purpose

Sprint 4.6.2b adds a controlled human-review layer above the Sprint 4.6.2a
Intelligent Local Candidate Matching output.

It deliberately does **not** change candidate matching, scoring, Parts Master
content, AVL data, or provider/API behaviour.

## Files

- `candidate_review.py` — review projection, decision model and append-only JSONL store.
- `tests/test_candidate_review.py` — deterministic unittest coverage.
- `integration_example.py` — minimal example showing how a 4.6.2a result is handed to 4.6.2b.

## Review decisions

- Pending
- Accepted
- Rejected
- Needs Verification
- No Suitable Candidate

`No Suitable Candidate` is recorded against the BOM item, not against an
individual candidate.

## Traceability model

Every reviewer action appends a new JSONL record. A changed decision does not
overwrite history. The latest record for a BOM-item/candidate pair is its
current review state.

The candidate supplied by 4.6.2a is snapshotted in the record, including its
raw candidate dictionary. This preserves the evidence that was presented to
the reviewer at that point in time.

## Important boundary

An **Accepted** 4.6.2b result means the reviewer accepted the candidate
proposal for the review being performed. It does not automatically:

- add an AVL entry;
- alter an AIPN;
- update the Parts Master;
- revise a BOM;
- issue an ECO/concession/deviation;
- approve use in production.

Those are later governance actions.

## Suggested repo placement

Because the exact 4.6.2a source tree was not available in the current File
Library, this sprint is intentionally loosely coupled.

Place `candidate_review.py` beside the existing matching module initially, or
move it into the existing PDC module/package naming convention if 4.6.2a
already established one. The tests only require the module to be importable.

## Test

From the repository root:

```bash
python -m unittest tests.test_candidate_review -v
```

## Acceptance criteria

4.6.2b is complete when:

1. 4.6.2a candidates can be projected for review without mutation.
2. Reviewer decisions are constrained to the approved state set.
3. Candidate decisions are traceable to a BOM item and candidate.
4. Decision changes retain history.
5. `No Suitable Candidate` is supported at BOM-item level.
6. No matching score is recalculated by 4.6.2b.
7. No Parts Master/provider/API write or call is performed.
8. Deterministic tests pass.
