# Sprint 4.7.2 — BOM Identity Recovery & Variant Discovery

## Purpose
Sprint 4.7.2 makes operational BOM review tolerant of incomplete and imperfect manufacturer part-number data without allowing PDC to silently change engineering data.

## Principles
- The BOM remains the source input. PDC does not rewrite the BOM MPN.
- A recovered or near MPN is a **candidate**, not an approval.
- Ordering suffix differences such as `T`, `R` and `TR` are no longer assumed harmless.
- Candidate package and BOM footprint evidence are retained where available.
- Manufacturer/provider datasheet links are retained with candidate evidence.
- All legitimate variants discovered in provider search results can be retained for later engineering review.
- Parts Master/AIPN allocation remains a controlled downstream action.
- PIE remains responsible for deciding whether an alternative/orderable variant is desirable for the design; PDC establishes what candidates and variants exist.

## BOM identity recovery
When the MPN cell is blank, PDC inspects BOM context in this order:
1. BOM Value
2. BOM Description

A value is considered only when it plausibly resembles an MPN. Common engineering values such as `10k`, `100nF` and `3.3V` are deliberately rejected.

If a candidate is found, providers are queried using the candidate while the original `Requested MPN` remains blank. The row therefore remains a review item.

Example:

- Manufacturer: Hirose
- MPN: blank
- BOM Value: `DF13A-2P-1.25H(20)`

PDC may search `DF13A-2P-1.25H(20)` and report it as `Recovered MPN candidate`, but it does not insert it into the BOM.

## Variant discovery
Provider-returned order codes are compared with the BOM/search MPN and classified as:
- Exact identity
- Orderable suffix variant candidate
- Truncated suffix candidate
- Near MPN candidate
- Different variant candidate

Only exact normalised MPN identity can contribute an automatic provider identity match. A suffix candidate remains review-required until its meaning and engineering fit are supported by evidence.

## Identity Candidates worksheet
The operational output now includes an `Identity Candidates` worksheet with:
- Source Row
- Input Manufacturer
- Input MPN
- BOM Value
- BOM Footprint
- Candidate Manufacturer
- Candidate MPN
- Relationship
- Evidence Sources
- Candidate Package / Case
- Footprint Check
- Datasheet URL
- Status
- Notes

The same candidate discovered by multiple providers is consolidated into one row with all evidence-source names retained.

## Footprint checking
Sprint 4.7.2 uses deliberately conservative footprint checks:
- Strong positive evidence can be reported as `Consistent`.
- Lack of terminology overlap is reported as `Not assessed`, not as a conflict.

This avoids treating distributor package terminology and CAD footprint naming as equivalent when the evidence is not strong enough.

## Provider candidate sources
- DigiKey: Product Details plus keyword-search fallback when exact identity is not confirmed.
- Mouser: complete part-number search results, including alternate packaging/order-code entries when returned.
- TME: product search manufacturer symbols/order codes.

Raw provider evidence continues to be preserved in the Knowledge Base.
