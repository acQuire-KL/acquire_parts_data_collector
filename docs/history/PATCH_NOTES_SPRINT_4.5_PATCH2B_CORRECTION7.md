# Sprint 4.5 Patch 2b – Correction 7

## Candidate variant restoration

This correction fixes a migration/presentation defect introduced while simplifying the Knowledge History.

### Behaviour

- The **Original MFG + Original MPN** define the review conversation.
- Every provider candidate returned for that original part remains a distinct **Candidate MFG + Candidate MPN** row.
- Procurement/ordering variants such as `ADS1232IPW`, `ADS1232IPWR`, `ADS1232IPWRG4`, and `ADS1232IPWG4` therefore remain visible candidates for individual user Accept / Reject / Defer decisions.
- Re-running an existing review repairs blank Candidate Manufacturer / Candidate MPN fields in older Knowledge History rows by matching the immutable Knowledge ID to the current review event.
- No new engineering approval is created during this repair and no existing Knowledge ID is replaced.
- Redundant standalone Manufacturer Alias rows remain removed; aliases are derived from accepted Original Manufacturer -> Candidate Manufacturer relationships.

### Governance

The correction preserves the Patch 2b principles:

- no automatic engineering approvals;
- never delete historical decisions;
- later decisions supersede earlier decisions;
- original source identity remains traceable on every record.
