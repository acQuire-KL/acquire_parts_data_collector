# Changelog

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
