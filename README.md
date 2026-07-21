# AIPN Enricher v0.1.0

Standalone DigiKey Product Information V4 Excel enrichment utility.

## Functions
- Reads Manufacturer + MPN from an XLSX workbook.
- Uses DigiKey two-legged OAuth.
- Retrieves ProductDetails and saves both cached and timestamped raw JSON.
- Creates **Enriched Parts**, **All Attributes**, and **Review Required** sheets.
- Preserves every leaf value from DigiKey's response in All Attributes.
- Does not change the input workbook.

## Setup on Windows
```powershell
cd AIPN_Enricher_v0.1.0
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and enter the client ID and secret from a DigiKey developer application subscribed to Product Information V4.

## Validate the workbook and configuration
```powershell
python main.py --input input\AIPN_Input_Template.xlsx --validate-only
```

## First ten-part run
```powershell
python main.py --input input\AIPN_Master.xlsx --output output\AIPN_Enriched_1-10.xlsx --start-row 2 --max-parts 10
```

## Notes
- Supported headings include Manufacturer/MFG/Mfr and MPN/Manufacturer Part Number.
- Exact MPN results are marked MATCHED; differences and API ambiguity are routed to Review Required.
- Cached responses prevent repeat calls. Use `--force-refresh` only when fresh data is needed.
- ProductDetails can reject an MPN with multiple DigiKey matches. This initial version records the API error rather than guessing. KeywordSearch fallback is the next planned addition after reviewing real responses.
