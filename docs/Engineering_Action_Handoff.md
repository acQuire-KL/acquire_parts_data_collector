# Controlled Engineering Action Handoff — Sprint 4.6.2d

## Purpose

Sprint 4.6.2d creates a controlled handoff between an **Accepted** candidate
review and the engineering-governance process that may eventually change an
AVL, BOM or production authorisation.

The output is a **proposal**, not an executed engineering change.

## Permitted Proposed Actions

- `Propose AVL Addition`
- `Propose BOM Change`
- `Temporary Concession/Deviation Required`
- `No Action / Reference Only`
- `Needs Engineering Classification`

## Conservative Classification

PDC may classify a handoff automatically only when explicit context is
provided:

| Context | Proposed action |
| --- | --- |
| `reference_only = true` | No Action / Reference Only |
| `temporary_use = true` | Temporary Concession/Deviation Required |
| `existing_bom_mpn_replacement = true` | Propose BOM Change |
| `add_to_existing_avl = true` | Propose AVL Addition |
| none/ambiguous | Needs Engineering Classification |

PDC deliberately does not infer an AVL/BOM/governance action merely because a
candidate was Accepted.

## Traceability

Each proposal preserves:

- source BOM-item identity;
- candidate identity, MFG, MPN and AIPN where present;
- 4.6.2a match score;
- 4.6.2b review ID and Accepted decision;
- reviewer and review comment;
- candidate warnings and justification;
- proposed engineering action;
- engineering-action reason and explicit context;
- UTC creation time.

Proposal persistence is append-only JSONL.

## Current-State Protection

Bulk handoff uses only the **latest** 4.6.2b review state for each candidate.
A historical Accepted decision that was subsequently changed to Rejected or
Needs Verification is not handed off.

## Governance Boundary

4.6.2d does **not**:

- modify the Parts Master;
- add or remove an AVL entry;
- revise a BOM;
- allocate/change an AIPN;
- issue or approve an ECO;
- issue or approve a concession/deviation;
- authorise production use;
- call manufacturer/distributor APIs.

A later governance sprint may consume these proposals, but must preserve the
distinction between *proposal* and *authorised change*.
