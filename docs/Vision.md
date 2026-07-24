# Parts Data Collector — Vision

## Purpose

The Parts Data Collector (PDC) automates the data-gathering work normally performed by an experienced electronics component engineer or procurement specialist.

A manual component investigation often starts with DigiKey or FindChips, continues through other distributors and the manufacturer, and may finish with a general web search when the expected information is not immediately available. PDC should progressively reproduce that workflow.

PDC is therefore not merely a distributor API client or a BOM-enrichment script. It is the collection layer for a reusable component knowledge platform.

## Core Vision

> PDC should collect as much relevant source data as is reasonably available before concluding that the information cannot be found.

When one source is incomplete, PDC should eventually continue through other appropriate sources rather than treating the first incomplete response as the end of the investigation.

The long-term collection path may include:

1. Existing Knowledge Base records.
2. Manufacturer websites and manufacturer documentation.
3. Authorised distributors.
4. Aggregators such as FindChips.
5. Specialist or regional distributors.
6. Marketplace listings, clearly identified as such.
7. General web search for the MPN, description, documentation, notices and possible alternatives.

The order and availability of sources will evolve, but the principle remains constant: collect first, interpret later.

## Relationship with PIE

PDC and the Parts Intelligence Engine (PIE) have different responsibilities.

### PDC

PDC collects and preserves data, including:

- manufacturer and part identity;
- descriptions and classifications;
- technical attributes;
- documentation links and local document references;
- compliance and lifecycle statements;
- commercial offers from all available providers;
- packaging and delivery formats;
- stock, lead time, MOQ and complete price ladders;
- additional commercial charges;
- marketplace listings;
- similar-part and replacement references;
- provider, source and capture metadata.

PDC may identify that values differ between sources, but it does not decide which value should be approved.

### PIE

PIE converts collected data into useful information and decisions, including:

- preferred purchasing source;
- BOM costing and quantity what-if analysis;
- availability and supply-risk assessment;
- lifecycle and compliance risk;
- comparison of conflicting source values;
- identification and assessment of alternatives;
- AVL recommendations;
- approval workflows and change proposals.

PIE must not silently change approved data. Engineering and procurement decisions remain subject to user review.

## Knowledge Base

The Knowledge Base is the persistent interface between collection and analysis.

```text
Data Sources
     │
     ▼
    PDC
     │
     ▼
Knowledge Base
     │
     ▼
    PIE
     │
     ▼
Information, comparisons and reviewed decisions
```

PDC writes rich, source-aware records. PIE reads and analyses those records. The original source data remains available so future analysis is not limited by the first workbook layout or the first set of requirements.

## Success Criteria

PDC is successful when it can perform the majority of the repetitive component-research work that would otherwise require manually visiting numerous websites, while retaining enough traceability for the user to verify every important result.

A successful PDC record should answer, where the sources allow:

- Is this the intended manufacturer and MPN?
- What is the component and what are its relevant technical attributes?
- What documentation and compliance information is available?
- Who carries it?
- Is it in stock?
- In which packaging and delivery formats?
- At what MOQ, quantity breaks and additional charges?
- What other information did the source provide when normal commercial data was unavailable?
- Where and when was each item of data collected?
