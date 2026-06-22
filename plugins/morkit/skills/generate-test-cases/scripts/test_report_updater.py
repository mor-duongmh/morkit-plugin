"""Rebuild the Test Report dashboard from the workbook's feature sheets.

The Test Report lists one row per feature (from row 11) and totals them in
row 9. Each row references its feature sheet BY TAB NAME, so the report is
rebuilt from scratch every write: rows are re-wired to the current (renamed)
tab titles in workbook order, stale rows for deleted tabs are cleared, and the
SUM ranges are resized to span exactly the live feature rows.
"""

from __future__ import annotations

import feature_sheet_writer as fsw

TOTAL_ROW = 9
MODULE_COL = 3          # C: module code / display name
ENV_CELL = "E4"
FIRST_MODULE_ROW = 11   # first feature row
DEFAULT_SUM_END = 24    # template SUM(G11:G24)
SUM_COLS = ("G", "H", "I", "J", "K", "L")
WIRE_COLS = (MODULE_COL, 7, 8, 9, 10, 11, 12)


def update(wb, environment: str | None):
    """Rewire every Test Report feature row to current tabs. Returns warnings."""
    warnings = []
    if "Test Report" not in wb.sheetnames:
        return ["Test Report sheet missing; skipped aggregation."]
    tr = wb["Test Report"]
    feats = fsw.feature_sheets(wb)
    n = len(feats)
    end = max(DEFAULT_SUM_END, FIRST_MODULE_ROW + n - 1)

    for i, ws in enumerate(feats):
        row = FIRST_MODULE_ROW + i
        sheet = ws.title  # already sanitized by finalize_sheets
        tr.cell(row, MODULE_COL).value = sheet
        if not tr.cell(row, 2).value:
            tr.cell(row, 2).value = "=ROW()-10"
        for col_letter, col_idx in zip("GHIJ", (7, 8, 9, 10)):
            tr.cell(row, col_idx).value = f"='{sheet}'!{col_letter}5"
        tr.cell(row, 11).value = f"=SUM(G{row}:J{row})"        # K: number of TCs
        tr.cell(row, 12).value = f"='{sheet}'!C2"              # L: total TCs

    # Clear rows for features that no longer exist (deleted/cleaned-up tabs).
    for row in range(FIRST_MODULE_ROW + n, end + 1):
        for col_idx in WIRE_COLS:
            tr.cell(row, col_idx).value = None

    # Resize SUM ranges to span exactly the live feature rows.
    for col in SUM_COLS:
        cell = tr[f"{col}{TOTAL_ROW}"]
        if isinstance(cell.value, str) and cell.value.startswith("=SUM("):
            cell.value = f"=SUM({col}{FIRST_MODULE_ROW}:{col}{end})"

    if FIRST_MODULE_ROW + n - 1 > DEFAULT_SUM_END:
        warnings.append(
            f"Feature count exceeds the template's 14 slots; totals span to row {end}."
        )
    if environment:
        tr[ENV_CELL] = environment

    return warnings
