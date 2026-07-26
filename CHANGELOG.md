# Changelog

## 0.2.8 - Sprint 4.2.2a TME Connectivity

- Added isolated TME Product API v2 connectivity client.
- Added `tme_connectivity_check.py` with raw JSON capture.
- Added TME environment-variable template and provider README.
- Added initial TME capability-review matrix.
- Added mocked TME connectivity tests; no workbook or Knowledge Base integration.

Added TME Product API connectivity.
- Authentication implemented.
- Product search operational.
- Raw JSON capture added.
- TME connectivity verified.

## [0.2.7] - 2026-07-26

### Added
- Position-based provider dashboard blocks with a reusable ten-colour palette.
- Separate provider Currency columns in Enriched Parts and Review Required.
- Dynamic price-break formatting using the widest quantity and price values in each cell.
- Workbook style guide under `docs/Workbook_Style_Guide.md`.
- Regression tests for provider block layout, price-break alignment and currency separation.

### Changed
- Provider groups are now labelled `Provider #1`, `Provider #2`, and so on rather than using supplier names as workbook structure.
- Each provider block now contains Provider Name, Available, Lead Time, Currency and Price Breaks.
- Price Breaks are right aligned, wrapped, displayed with five decimal places and use at least two spaces between quantity and price.
- Currency symbols were removed from price-break text because currency is now a separate field.
- Providers Queried and Providers Matched are explicitly left aligned and wrapped.
- Workbook layout now separates internal data keys from displayed headings so provider blocks may repeat common headings safely.

### Preserved
- Provider collection, matching, Knowledge Base and raw evidence behaviour are unchanged.
- Provider discovery and `.env`-driven activation remain deferred to the Dynamic Provider Framework sprint.

## [0.2.6] - 2026-07-25

### Added
- Multi-provider component summary records under `Knowledge_Base/Current/Parts`.
- Combined provider identity evidence and engineering confirmation.
- DigiKey and Mouser dashboard blocks on Enriched Parts.
- Future PDC/PIE Knowledge Base Explorer concept to the Parking Lot.

### Changed
- Match Status is now assigned only after all enabled providers have been reviewed.
- Enriched Parts now shows only availability, lead time and price breaks per provider.
- Knowledge Base schema advanced to 1.4.

### Removed
- Attribute Mapping and All Attributes worksheets from the normal workbook output. Raw responses and mapped profiles remain preserved in the Knowledge Base.

## [0.2.5] - Step 3B.2 Mouser response mapping

### Added

- Added a provider-neutral `part_profile` for identity, documentation, lifecycle, compliance and engineering attributes.
- Added Mouser mapping for manufacturer, MPN, Mouser part number, descriptions, URLs, lifecycle, RoHS, package and mounting data.
- Added Mouser commercial mapping for stock, factory stock, lead time, MOQ, pack quantity, packaging, currency and complete price breaks.
- Added Mouser Knowledge Base persistence while retaining the raw API payload as the authoritative captured evidence.
- Added 12 mapping and Knowledge Base regression tests.

### Changed

- Knowledge Base schema advanced to 1.3 and now stores both `part_profile` and `commercial_profile`.
- Commercial profile schema advanced to 1.3 and now supports DigiKey and Mouser response shapes.
- Existing Knowledge Base records without a part profile are upgraded in memory when loaded.

### Preserved

- Mouser is not yet registered in the normal workbook collection flow.
- The workbook layout and visible output remain unchanged.
- Raw DigiKey and Mouser provider responses remain unmodified.

## [0.2.5] - Step 3B.1 Mouser connectivity

### Added

- Added a minimal Mouser Search API client using `MOUSER_API_KEY`.
- Added `MouserProvider` under the common provider contract.
- Added a live connectivity utility: `python mouser_connectivity_check.py <MPN>`.
- Added controlled handling for missing Mouser configuration, HTTP failures and Mouser API error payloads.
- Added mocked unit tests; no live API call is made by the test suite.

### Preserved

- Mouser is not yet registered in the normal workbook collection flow.
- Workbook content and formatting are unchanged in this connectivity-only step.
- Mouser response mapping into the Knowledge Base is deferred to Step 3B.2.

## [0.2.5] - Step 3A: Multi-Provider Execution Contract

### Added

- Added provider-neutral `ProviderResult` and `ProviderStatus` models.
- Added a provider execution boundary that captures provider success and failure without interpreting source data.
- Added explicit provider declarations for required environment variables.
- Added regression tests for provider results, execution isolation and workbook freeze panes.

### Changed

- Existing DigiKey calls now pass through `ProviderManager.execute()` and unwrap their original data.
- Enriched Parts and Review Required now freeze at `E3`, retaining the two header rows and first four review columns while scrolling.
- Updated `.env.example` with grouped placeholders for DigiKey, Mouser, Future Electronics and Arrow.

### Preserved

- DigiKey remains the sole active provider.
- Provider response data, Knowledge Base records and workbook content are unchanged.
- Existing collection failures retain their current user-facing behaviour.

## [0.2.5] - Step 2: Provider Manager

### Added

- Added `ProviderManager` as the central registry and access point for PDC data providers.
- Added deterministic provider registration order and duplicate-name protection.
- Added unit tests for registration, provider ordering, duplicate detection and empty-manager handling.

### Changed

- `main.py` now obtains the active DigiKey provider through `ProviderManager` rather than constructing and using it directly.
- Console startup output now lists the registered provider names.

### Preserved

- DigiKey remains the sole active provider.
- Collection, Knowledge Base and workbook behaviour are unchanged.

# Changelog

## [0.2.5] - Unreleased

### Provider framework — Step 1

- Added a common `BaseProvider` contract for provider-specific collection implementations.
- Added a `DigiKeyProvider` adapter around the existing DigiKey API client.
- Updated the application entry point to use the provider abstraction instead of importing the DigiKey client directly.
- Preserved DigiKey collection, Knowledge Base and workbook behaviour.
- Added provider framework regression tests.
- Added the future Regression Test Library to the Parking Lot.

## [0.2.4a] - Unreleased

### Documentation and architecture foundation

- Defined PDC as an exhaustive, multi-source component data collector that reproduces the research workflow of an experienced component engineer.
- Clarified the responsibility boundary: PDC collects and preserves data; PIE converts that data into information, comparisons and reviewed decisions.
- Defined the Knowledge Base as the persistent, source-aware interface between PDC and PIE rather than a temporary cache.
- Established that collection should continue when primary commercial data is unavailable but other source information exists.
- Established that all commercial offers, delivery formats, price ladders and additional charges must be preserved.
- Defined the planned Enriched Parts review order as Status, Identity, Engineering, Commercial, Traceability, Documentation and Compliance.
- Added `docs/Vision.md`, `docs/Architecture.md` and `docs/Engineering_Principles.md`.
- Expanded the Parking Lot with deferred presentation, multi-source, commercial-history and future PIE-analysis items.

### Scope note

This step changes documentation only. Python behaviour and workbook output are unchanged until the following v0.2.4a implementation steps.


## [0.2.3] - Commercial output phase

### Added

- Commercial fields in `Enriched Parts` using the primary purchasing offer.
- Multiline price-break summary with one quantity/price pair per line.
- `Commercial Analysis` worksheet with one row per packaging offer and price break.
- Generic additional-charge records, including Digi-Reel service fees when returned by DigiKey.
- Parking Lot item for future rich-text price-break colours and central palette refinement.

### Preserved

- Original provider currency and provider prices.
- Every packaging offer and complete standard price ladder.
- Fixed charges separately from unit prices.


### v0.2.2 formatting update
- Added central field-format definitions in `excel_formats.py`.
- Explicitly defined formatting for every current Enriched Parts and Review Required field.
- MOQ, pack quantity and availability quantities use numeric `#,##0` formatting and right alignment.
- Lead-time fields are numeric and centre aligned.
- Unit-price and break-price fields are prepared for `#,##0.00000` formatting.
- All identifiers and text fields, including MPNs, are left aligned and retained as text.


## 0.2.2 - 2026-07-24

- Removed the Reason column from Enriched Parts.
- Retained detailed diagnostic reasons on Review Required.
- Added four-colour Match Status formatting: Matched, Review Required, Multiple Matches and Not Found.
- Limited auto-filtering and freeze panes to Enriched Parts and Review Required.
- Added `excel_formatter.py` so Excel presentation is separated from collection and matching logic.
- Kept the remaining worksheets structurally independent for possible future CSV export.

## 0.2.1 - 2026-07-23

- Grouped workbook fields into Input & Match, Identity, Documentation, Compliance, Physical, Electrical, Commercial and Traceability.
- Added Description and Detailed Description as separate fields.
- Added Product Image URL and retained Datasheet URL as live references.
- Added exact mappings for DigiKey classifications, including RoHS, REACH, MSL, ECCN and HTSUS.
- Added Product Family using the deepest DigiKey category returned.
- Added selected static physical and broadly applicable electrical attributes.
- Added an Attribute Mapping worksheet containing JSON paths and real sample values for validation.
- Retained the existing commercial fields without expanding commercial-data handling.
- Normalised protocol-relative datasheet URLs to HTTPS.

## 0.2.0 - 2026-07-22

- Added provider-aware `Knowledge_Base` storage.
- Added `Current` and immutable `History` records.
- Added capture timestamps and provider metadata inside JSON files.
- Added `Manifest.json` with provider and record statistics.
- Added automatic migration of legacy v0.1.x DigiKey cache files.
- Added output columns for capture timestamp and data source mode.
- Preserved manufacturer normalisation and concise review messaging from v0.1.2.
- Reserved manifest configuration for a later staggered refresh schedule.

## v0.2.3 - Commercial Profile Phase 1

- Added a provider-neutral `commercial_profile.py` normalisation layer.
- Preserved the complete DigiKey provider response as the source record.
- Captured every product variation and its provider part number, packaging, MOQ, pack quantity, availability and complete standard/customer price ladders.
- Preserved original provider currency and capture timestamp.
- Added a normalised pack format while retaining the original provider package description.
- Updated Knowledge Base schema to 1.1 and embedded the commercial profile in new and migrated product records.
- Existing Knowledge Base records remain compatible; their commercial profile is derived in memory when absent.
