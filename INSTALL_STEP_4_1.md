# PDC v0.2.4a — Step 4.1 Installation

## Purpose

Improve readability of multi-offer commercial fields on **Enriched Parts** and other formatted output sheets.

## Replace

Copy these files into the project root, replacing the existing versions:

- `excel_formats.py`
- `excel_formatter.py`

Copy this file into the project's `tests` folder:

- `tests/test_wrapped_commercial_cells.py`

## Test

Run:

```bash
python -m unittest discover -s tests -v
```

Expected result with Steps 1–4 installed:

```text
Ran 12 tests
OK
```

Then run PDC normally and inspect **Enriched Parts**.

Multi-offer values should display on separate lines, including:

- Provider Part Number
- Pack Format
- Packaging Code
- Minimum Order Quantity
- Pack Quantity
- Quantity Available
- Additional Charge
- Additional Charge Description
- Price Breaks

Rows containing three offers should expand to show at least three lines.

## Commit

```bash
git add excel_formats.py excel_formatter.py tests/test_wrapped_commercial_cells.py
git commit -m "Wrap multi-offer commercial fields in workbook"
```
