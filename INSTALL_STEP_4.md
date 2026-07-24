# PDC v0.2.4a — Step 4 Installation

## Purpose

Step 4 exposes every captured commercial offer in the workbook instead of showing only one selected DigiKey packaging option.

For parts such as `MCP1711T-25I/OT`, Enriched Parts now preserves Cut Tape, Digi-Reel and Reel information. Commercial Analysis continues to provide one row per offer and price break.

## Files to replace

Copy these files into the project, preserving their paths:

- `main.py`
- `workbook_layout.py`
- `tests/test_multiple_commercial_offers.py`

## Test

Run:

```bash
python -m unittest discover -s tests -v
```

Expected result with Steps 1–4 installed:

```text
Ran 10 tests
OK
```

Then run PDC normally using the sample BOM containing `MCP1711T-25I/OT`.

## Workbook checks

On **Enriched Parts**, confirm the MCP1711 row shows:

- Offer Count = 3
- Cut Tape, DigiReel and Reel in the commercial fields
- all three DigiKey provider part numbers
- separate price-ladder blocks for each packaging option

On **Commercial Analysis**, confirm there are separate rows for each packaging offer and each available price break.

## Commit

```bash
git add main.py workbook_layout.py tests/test_multiple_commercial_offers.py
git commit -m "Expose multiple commercial offers in workbook"
```
