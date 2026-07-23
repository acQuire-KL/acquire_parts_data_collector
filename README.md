# Parts Data Collector (PDC) v0.2.1

PDC reads Manufacturer + MPN rows from Excel, resolves the manufacturer, retrieves DigiKey Product Information V4 data, and writes an enriched workbook.


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
