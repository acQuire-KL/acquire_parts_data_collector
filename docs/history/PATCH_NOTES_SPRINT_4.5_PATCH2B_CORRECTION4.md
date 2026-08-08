# Sprint 4.5 Patch 2b - Correction 4

## Knowledge History conversation-block repair

This correction fixes the presentation of an existing Knowledge History created
by earlier Patch 2b corrections.

### User-facing rule

- `Original Manufacturer` and `Original MPN` are shown once, on the first row
  of each source-part conversation.
- Every following row belongs to that same source MPN until the next populated
  Original MPN begins a new conversation.
- Repeated Original MFG/MPN cells are blanked only for presentation.
- Full source identity remains retained on every knowledge record in the
  right-hand `Source Manufacturer Record` and `Source MPN Record` fields.

### Migration repair

Earlier presentation rewrites could cause a derived Manufacturer Alias row to
inherit the source identity of the preceding conversation. This correction
reconstructs source context from the immutable `Review ID` + `Record ID`
relationship before sorting and displaying the history. Existing Knowledge IDs
are preserved and no history needs to be deleted.

### Scope

No Parts Master changes, no AIPN allocation, no new approvals, and no changes
to engineering knowledge content. This is a presentation/migration correction.
