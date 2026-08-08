# Sprint 4.5 Patch 2b - Correction 6

## Remove redundant Manufacturer Alias history rows

Knowledge History now stores one row per actual candidate review decision. A separate
`Manufacturer Alias` row is no longer written when an accepted candidate uses a
different manufacturer name.

The alias is not lost. PDC derives it from the approved relationship already present
on the part row:

- Original Manufacturer -> Candidate Manufacturer
- Review Decision = Accept

Existing legacy `Manufacturer Alias` rows created by earlier Patch 2b corrections are
removed during the next schema rewrite. This is a migration of redundant derived rows,
not deletion of an engineering decision: the originating accepted part decision remains
unchanged and continues to provide the alias relationship.

No Parts Master changes and no AIPNs are allocated.
