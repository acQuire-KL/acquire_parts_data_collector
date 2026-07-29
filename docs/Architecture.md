# Parts Data Collector — Architecture

## 1. Architectural Objective

PDC is designed as a provider-aware collection system rather than a single-provider workbook script.

The architecture must allow new sources to be added without redesigning the workbook, the Knowledge Base or PIE. Provider-specific response structures belong inside provider adapters and normalisation layers. Shared records should use provider-neutral concepts while retaining the provider-native values from which they were derived.

## 2. System Boundary

```text
Input BOM / MPN List
        │
        ▼
Input Validation and Normalisation
        │
        ▼
Collection Orchestration
        │
        ├── Knowledge Base
        ├── Manufacturer Sources
        ├── Distributor Providers
        ├── Aggregators
        └── General Web Sources
        │
        ▼
Provider-Native Source Records
        │
        ▼
Provider-Neutral Profiles and Indexes
        │
        ▼
Knowledge Base
        │
        ├── PDC Workbook and Exports
        └── PIE Analysis
```

PDC owns collection, normalisation, storage and factual presentation. PIE owns comparison, ranking, risk assessment, recommendations and approval workflows.

## 3. Collection Behaviour

PDC should not stop solely because a primary commercial offer is unavailable.

For each requested component, the collection process should eventually attempt to gather all readily available categories of information, including:

- exact and candidate identity matches;
- technical and classification data;
- documentation and compliance data;
- standard distributor offers;
- every packaging and delivery format;
- complete price ladders;
- fixed and variable additional charges;
- marketplace offers;
- alternate packaging references;
- similar-part references;
- replacement, lifecycle or discontinuation notices;
- manufacturer stock or direct-buy information where available;
- source metadata and timestamps.

A missing field is not necessarily the end of the collection path. The collector should continue when the source exposes other relevant data.

## 4. Provider Separation

Provider-specific code should be isolated behind a provider interface or adapter.

A provider adapter is responsible for:

- authentication and request construction;
- provider-specific searching and pagination;
- preserving the raw provider response;
- translating provider fields into shared profiles;
- retaining provider terminology, identifiers and URLs;
- recording capture time, locale, currency and request context.

Shared application logic should not assume DigiKey field names, packaging descriptions or response layout.

## 5. Knowledge Base Structure

The Knowledge Base is not merely a temporary cache. It is the persistent source-aware data store shared by PDC and PIE.

A component record may contain:

```text
Component Record
├── Identity
├── Engineering / Technical Profiles
├── Documentation
├── Compliance and Lifecycle Statements
├── Commercial Profiles
│   ├── Provider
│   │   ├── Offer / Delivery Format
│   │   │   ├── MOQ and Pack Quantity
│   │   │   ├── Availability and Lead Time
│   │   │   ├── Price Ladder
│   │   │   └── Additional Charges
│   │   └── Additional Offers
│   └── Additional Providers
├── Marketplace Records
├── Similar and Replacement References
└── Source and Capture Metadata
```

The precise schema will evolve incrementally. Existing source records must remain readable wherever practical, with derived profiles created in memory or through controlled migration.

## 6. Raw and Normalised Data

PDC should retain both:

1. **Provider-native source data** — the original factual response, preserved without reinterpretation.
2. **Provider-neutral profiles** — normalised records that allow equivalent concepts from different sources to be presented and compared.

Normalisation must not erase the original value. For example, a provider's packaging description may be mapped to a common pack format, but the original packaging text must also remain available.

## 7. Commercial Model

Commercial information is plural by design.

A component can have:

- multiple providers;
- multiple provider part numbers;
- multiple packaging or delivery formats;
- different MOQ and pack quantities;
- different stock quantities and lead times;
- different standard and customer price ladders;
- fixed service or packaging charges;
- marketplace and non-authorised offers.

No single offer should be treated as the complete commercial record. Workbook summary views may condense the data, but the long-form commercial output and Knowledge Base must preserve all offers.

## 8. Workbook Role

The workbook is a review and export view of the Knowledge Base; it is not the master data store.

The principal review flow should follow the user's sourcing workflow:

```text
Status → Identity → Engineering → Commercial → Traceability → Documentation → Compliance
```

Commercial information should be visible early enough for practical BOM review. Documentation and compliance remain available but are positioned later in the Enriched Parts worksheet to reduce unnecessary horizontal scrolling.

Long-form worksheets such as Commercial Analysis should remain structurally suitable for filtering, Power Query, PivotTables, CSV export and later PIE ingestion.

## 9. Match and Availability Status

Internal facts should remain distinct even when the workbook presents a simplified status.

For example:

```text
Engineering Match = true
Commercial Data Available = false
```

may be displayed as a yellow `Matched` status rather than creating a separate user-facing match category.

The workbook status is a presentation rule. The underlying factual states should remain separately available for later analysis.

## 10. Non-Automation Rule

PDC may collect candidates and evidence, but it must not automatically:

- approve an alternative;
- overwrite an approved part;
- select a preferred provider;
- resolve conflicting technical values;
- infer compliance or lifecycle status not stated by a source;
- convert a marketplace listing into an authorised source;
- alter quoted provider prices by embedding fees into unit prices.

Those actions belong to PIE or to explicit user review.

## Multi-Provider Evidence Model

PDC queries every enabled provider independently and preserves each provider response as peer evidence. The provider-neutral component summary is created only after provider execution has completed. It may confirm identity and engineering agreement, but it must not rank providers, choose suppliers or make sourcing recommendations; those responsibilities belong to PIE.

The workbook is a review dashboard over the Knowledge Base. Detailed commercial offers remain in Commercial Analysis, while raw responses and common profiles remain in the Knowledge Base.

## 11. Provider Part Profile

Each provider normaliser targets the same internal contract:

```text
Provider 1 ─┐
Provider 2 ─┼──> Provider Part Profile
Provider 3 ─┤
Provider n ─┘
```

A Provider Part Profile represents one provider's normalised evidence for one manufacturer part. It contains provider-neutral Identity, Technical, Commercial, Logistics and Media sections, together with provider metadata, provenance and references to the retained raw records.

The profile is not yet the final correlated Knowledge Base Part Profile. The later validation and correlation stage combines several Provider Part Profiles, preserves disagreements and assigns evidence confidence before publishing the trusted record consumed by PIE.

```text
Provider-native responses
        │
        ▼
Provider-specific normaliser
        │
        ▼
Provider Part Profile
        │
        ▼
Validation and correlation (PDC)
        │
        ▼
Validated Knowledge Base Part Profile
        │
        ▼
PIE
```

The model must evolve from provider evidence rather than from one provider's field names. TME is the first implementation; DigiKey and Mouser will be refactored to the same contract before the profile is declared stable.

