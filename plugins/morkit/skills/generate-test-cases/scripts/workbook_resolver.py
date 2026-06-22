"""Resolve, back up, and atomically save the output workbook.

The user's template is NEVER mutated. First run copies the template to the
output path (byte copy, preserving all formatting). Later runs open the
existing output and append. Saves go through a temp file + os.replace so a
crash mid-write cannot corrupt an existing workbook; the prior output is kept
as a `.bak` sibling.
"""

from __future__ import annotations

import os
import shutil
import tempfile

import openpyxl


def load_or_init(template_path: str, out_path: str):
    """Return (workbook, append_mode).

    append_mode is True when out_path already existed (we opened it to add a
    feature), False when we freshly copied the template.
    """
    if os.path.exists(out_path):
        wb = openpyxl.load_workbook(out_path)
        return wb, True

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(template_path, out_path)  # byte copy keeps styles/formulas
    wb = openpyxl.load_workbook(out_path)
    return wb, False


def save(wb, out_path: str) -> str | None:
    """Atomically save wb to out_path. Returns the .bak path if one was made.

    Existing output is copied to out_path + '.bak' first, then the new
    workbook is written to a temp file in the same directory and atomically
    moved into place.
    """
    out_path = os.path.abspath(out_path)
    out_dir = os.path.dirname(out_path)
    backup = None

    if os.path.exists(out_path):
        backup = out_path + ".bak"
        shutil.copyfile(out_path, backup)

    fd, tmp = tempfile.mkstemp(suffix=".xlsx", dir=out_dir)
    os.close(fd)
    try:
        wb.save(tmp)
        os.replace(tmp, out_path)  # atomic on same volume, cross-platform
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    return backup
