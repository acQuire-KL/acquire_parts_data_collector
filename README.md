# Parts Data Collector (PDC) — v0.2.7 development

PDC reads Manufacturer + MPN rows from Excel, resolves the manufacturer, retrieves DigiKey Product Information V4 data, and writes an enriched workbook.

## Project direction

PDC is being developed to automate the multi-source data-gathering workflow of an experienced component engineer. It collects and preserves source data; the Parts Intelligence Engine (PIE) will later compare, interpret and present that data for reviewed decisions.

The architectural principles are documented in:

- `docs/Vision.md`
- `docs/Architecture.md`
- `docs/Engineering_Principles.md`
- `docs/Parking_Lot.md`

The v0.2.4a documentation foundation does not yet change Python behaviour or workbook output.


## v0.2.2: Workbook review usability

- `Enriched Parts` now uses Match Status as its sole user-facing match indicator.
- Match Status cells use green, yellow, orange and red review colours.
- Detailed reasons remain available on `Review Required`.
- Filters and frozen headers are applied only to the two review-oriented worksheets.
- Excel presentation logic has moved into `excel_formatter.py`.

## v0.2.1: Static technical attributes

The enriched workbook now groups and exposes technical attributes already present in the Knowledge Base. The `Attribute Mapping` worksheet records the source JSON path and a real sample value for each mapped field.

The first phase focuses on identity, documentation, compliance, physical and broadly applicable electrical data. Existing commercial fields remain available, but further commercial-data work is deferred.

## v0.2.0: Knowledge Base foundation

PDC now stores provider data in a persistent, provider-aware Knowledge Base:

```text
Knowledge_Base/
├── Current/
│   └── DigiKey/
│       ├── Product_Details/
│       └── Reference_Data/
├── History/
│   └── DigiKey/
│       └── Product_Details/
└── Manifest.json
```

- `Current` contains the latest known response for fast reuse.
- `History` contains an immutable dated JSON snapshot for each fresh live API capture.
- Every JSON contains a capture timestamp and source metadata.
- `Manifest.json` records provider and record counts and reserves a section for later staggered refresh planning.
- Existing v0.1.x `cache/` files are migrated automatically when first used.

A Knowledge Base read does **not** create a new history snapshot. A new history snapshot is created only following a fresh API request, such as when `--force-refresh` is used.

## Installation

Keep your existing `.env` file. Install dependencies in your virtual environment:

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py --input input\AIPN_Input_Template.xlsx --output output\AIPN_Enriched.xlsx
```

Force a live refresh and create a new historical snapshot:

```powershell
python main.py --input input\AIPN_Input_Template.xlsx --output output\AIPN_Enriched.xlsx --force-refresh
```

Validate input and credentials without retrieving product data:

```powershell
python main.py --input input\AIPN_Input_Template.xlsx --validate-only
```

## Important data distinction

PDC collects and preserves source data. PIE will later interpret lifecycle risk, PCNs, LTB/LCS dates, replacement suitability, and approval into the Parts Master.

## Commercial Profile (v0.2.3 Phase 1)

PDC now derives a provider-neutral commercial profile from each captured DigiKey product response while preserving the original response unchanged.

The profile contains:

- original provider currency and capture timestamp;
- product-level availability, unit price and manufacturer lead time;
- every DigiKey product variation;
- provider part number;
- raw package type and normalised pack format;
- MOQ and pack quantity;
- package-specific availability;
- complete standard and customer price ladders, sorted by break quantity.

This phase prepares the data model for the Enriched Parts price-break summary and the long-form Commercial Analysis output planned for Phase 2.

## Commercial Output (v0.2.3)

PDC now presents commercial data in two complementary forms:

- `Enriched Parts` contains the primary purchasing offer and a multiline price-break summary for engineering review.
- `Commercial Analysis` contains one row per packaging offer and price break for BOM costing, Power Query and later PIE what-if analysis.

The commercial model preserves the provider currency, complete standard price ladder, packaging option and fixed additional charges. Digi-Reel service fees are kept separate from unit prices so later costing can calculate true effective cost without altering the provider's quoted price.
