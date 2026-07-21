# acquire_parts_data_collector v0.1.1

Standalone DigiKey Product Information V4 Excel enrichment utility.

## What changed in v0.1.1

The collector now resolves the input Manufacturer to DigiKey's manufacturer ID before
requesting ProductDetails. The request therefore uses **Manufacturer + MPN**, which
handles generic part numbers such as `SS14` that are sold by several manufacturers.

The resolver:

1. Downloads and caches DigiKey's manufacturer catalogue.
2. Normalises common legal suffixes and known naming variations.
3. Resolves one unique DigiKey manufacturer ID.
4. Calls ProductDetails with both the MPN and `manufacturerId`.
5. Accepts the result only when the returned MPN and manufacturer ID both match.
6. Routes uncertain manufacturer names to Review Required instead of guessing.

## Functions

- Reads Manufacturer + MPN from an XLSX workbook.
- Uses DigiKey two-legged OAuth.
- Retrieves ProductDetails and saves both cached and timestamped raw JSON.
- Creates **Enriched Parts**, **All Attributes**, and **Review Required** sheets.
- Preserves every leaf value from DigiKey's response in All Attributes.
- Does not change the input workbook.

## Setup on Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and enter the client ID and secret from a DigiKey developer application
subscribed to Product Information V4.

## Validate

```powershell
python main.py --input input\AIPN_Input_Template.xlsx --validate-only
```

## Ten-part run

```powershell
python main.py --input input\AIPN_Master.xlsx --output output\AIPN_Enriched_1-10.xlsx --start-row 2 --max-parts 10
```

## Cache change

Product cache filenames now contain the DigiKey manufacturer ID, for example:

```text
SS14_MFG_1049.json
```

This prevents an earlier MPN-only result from being reused for a different manufacturer.
`_manufacturers.json` stores the DigiKey manufacturer catalogue.

Use `--force-refresh` only when fresh source data is required.
