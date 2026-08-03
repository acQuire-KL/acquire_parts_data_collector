# Sprint 4.2.5 Patch 2 — Mouser PDCPartProfile

This patch adds a Mouser normaliser that targets the same `PDCPartProfile` as TME and DigiKey.

It preserves:

- identity and catalogue classification;
- live stock, MOQ and order multiple;
- factory lead time normalised to weeks;
- all returned price breaks;
- advertised Reel, Cut Tape and MouseReel formats;
- MouseReel service charge and its raw provider wording;
- manufacturer standard pack quantity;
- weight normalised to grams;
- RoHS, ECCN, US HTS and country of origin;
- additional compliance classifications;
- datasheet, image and product links;
- provenance and raw Knowledge Base references.

The patch adds `lifecycle.suggested_replacement` as a provider-neutral field. Missing Mouser technical parameters remain empty rather than being inferred from descriptive text.
