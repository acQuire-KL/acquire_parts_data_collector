"""Excel-only presentation helpers for PDC workbook outputs."""

from __future__ import annotations

from datetime import datetime
import re

from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from excel_formats import format_for_heading

GROUP_COLOURS = {
    "Input & Match": "5B9BD5",
    "Identity": "4472C4",
    "Documentation": "70AD47",
    "Compliance": "8064A2",
    "Physical": "A5A5A5",
    "Electrical": "ED7D31",
    "Commercial (Existing)": "FFC000",
    "Commercial": "FFC000",
    "Traceability": "264478",
}

STATUS_FILLS = {
    "Matched": "C6EFCE",             # green
    "Review Required": "FFEB9C",     # yellow
    "Multiple Matches": "F4B183",    # orange
    "Not Found": "FFC7CE",           # red
}

STATUS_FONTS = {
    "Matched": "006100",
    "Review Required": "9C6500",
    "Multiple Matches": "9C5700",
    "Not Found": "9C0006",
}

_NUMERIC_TEXT = re.compile(r"^[+-]?(?:\d+(?:,\d{3})*|\d*)(?:\.\d+)?$")


def add_group_headers(ws, columns) -> None:
    """Add the merged top-level group row used by review-oriented sheets."""
    column_index = 1
    while column_index <= len(columns):
        group = columns[column_index - 1][0]
        start = column_index
        while column_index <= len(columns) and columns[column_index - 1][0] == group:
            column_index += 1
        end = column_index - 1
        ws.merge_cells(start_row=1, start_column=start, end_row=1, end_column=end)
        cell = ws.cell(1, start, group)
        cell.fill = PatternFill("solid", fgColor=GROUP_COLOURS.get(group, "1F4E78"))
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _coerce_numeric(value):
    """Convert clean numeric strings to numbers without touching identifiers."""
    if value in (None, "") or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value

    text = str(value).strip()
    if not text or not _NUMERIC_TEXT.fullmatch(text):
        return value

    number = float(text.replace(",", ""))
    return int(number) if number.is_integer() else number


def _coerce_date(value):
    """Convert ISO-style date text when possible; otherwise preserve the source."""
    if value in (None, "") or isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return value
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return value


def _set_column_widths(ws, header_row: int) -> None:
    for column in range(1, ws.max_column + 1):
        heading = str(ws.cell(header_row, column).value or "")
        field_format = format_for_heading(heading)

        if field_format.width is not None:
            width = field_format.width
        else:
            max_length = 0
            for row in range(header_row, ws.max_row + 1):
                max_length = max(max_length, len(str(ws.cell(row, column).value or "")))
            width = min(max(max_length + 2, 10), 40)

        ws.column_dimensions[get_column_letter(column)].width = width


def _apply_field_formats(ws, headings: list[str], first_data_row: int) -> None:
    for column, heading in enumerate(headings, 1):
        field_format = format_for_heading(heading)

        for row_number in range(first_data_row, ws.max_row + 1):
            cell = ws.cell(row_number, column)

            if field_format.coerce_numeric:
                cell.value = _coerce_numeric(cell.value)
            elif field_format.number_format in {"yyyy-mm-dd", "yyyy-mm-dd hh:mm:ss"}:
                cell.value = _coerce_date(cell.value)

            cell.number_format = field_format.number_format
            cell.alignment = Alignment(
                horizontal=field_format.horizontal,
                vertical=field_format.vertical,
                wrap_text=field_format.wrap_text,
            )

            if field_format.hyperlink and str(cell.value or "").startswith("http"):
                cell.hyperlink = str(cell.value)
                cell.style = "Hyperlink"
                # Reapply alignment because the Hyperlink named style can alter it.
                cell.alignment = Alignment(
                    horizontal=field_format.horizontal,
                    vertical=field_format.vertical,
                    wrap_text=field_format.wrap_text,
                )


def _apply_status_colours(ws, headings: list[str], first_data_row: int) -> None:
    if "Match Status" not in headings:
        return
    status_column = headings.index("Match Status") + 1
    for row_number in range(first_data_row, ws.max_row + 1):
        cell = ws.cell(row_number, status_column)
        status = str(cell.value or "")
        fill_colour = STATUS_FILLS.get(status)
        if fill_colour:
            cell.fill = PatternFill("solid", fgColor=fill_colour)
            cell.font = Font(color=STATUS_FONTS[status], bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="top")


def format_review_sheet(ws, headings: list[str]) -> None:
    """Format Enriched Parts or Review Required for interactive review."""
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:{get_column_letter(ws.max_column)}{ws.max_row}"

    for cell in ws[2]:
        group = ws.cell(1, cell.column).value
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = PatternFill("solid", fgColor=GROUP_COLOURS.get(group, "1F4E78"))
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.row_dimensions[1].height = 22
    ws.row_dimensions[2].height = 36

    _apply_field_formats(ws, headings, first_data_row=3)
    _set_column_widths(ws, header_row=2)
    _apply_status_colours(ws, headings, first_data_row=3)


def format_reference_sheet(ws) -> None:
    """Apply basic presentation without filters or frozen panes."""
    headings = [str(cell.value or "") for cell in ws[1]]

    for cell in ws[1]:
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    _apply_field_formats(ws, headings, first_data_row=2)
    _set_column_widths(ws, header_row=1)
