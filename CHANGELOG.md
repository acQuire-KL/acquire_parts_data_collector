# Changelog

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
