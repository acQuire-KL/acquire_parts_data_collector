# Datasheet Evidence Integration & User-Supplied Evidence — Sprint 4.6.3c

## Objective

Attach datasheet evidence to the actual PDC component knowledge record and expose only a concise active-evidence summary in `parts_master_index.json`. Evidence can be **PDC_ACQUIRED** or **USER_SUPPLIED**. These describe how PDC received the evidence, not who authored it.

## Component JSON

The component JSON keeps `active`, `active_selection_reason`, and append-only `history`. The full evidence history is deliberately not copied into the Parts Master Index.

## User-Supplied Manufacturer Documents

A user can add a manufacturer PDF that PDC could not acquire itself. PDC records the original filename, local archive path, SHA-256, source name, optional Manufacturer Source URL, and whether the user explicitly confirmed it is the manufacturer's document. User confirmation is separate from `manufacturer_url_verified`; PDC does not pretend it independently verified a URL supplied manually.

## Active Evidence Preference

1. Manufacturer Verified
2. Distributor Copy of Manufacturer Document
3. Manufacturer Resolved - Verification Required
4. Distributor Evidence
5. Needs Verification
6. No Datasheet Evidence

A weaker new document does not replace stronger evidence merely because it is newer. Equal-confidence evidence prefers the later retrieval date.

## Parts Master Index Summary

The index receives only: `datasheet_status`, `datasheet_source_type`, `datasheet_active_url`, `datasheet_local_file`, `datasheet_retrieved_date`, `datasheet_sha256`, and `datasheet_evidence_origin`.

## Identity Protection

Association uses Manufacturer + MPN. File-level integration refuses to update unless exactly one matching index record exists.

## Boundary

No PDF technical-attribute extraction, semantic revision comparison, scheduled re-verification, evidence deletion, or candidate approval is performed in 4.6.3c.
