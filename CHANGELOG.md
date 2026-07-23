# Changelog

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
