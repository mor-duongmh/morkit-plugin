"""Entry point: fill an Excel workbook with test cases from cases.json.

Deterministic — writes only what cases.json contains; never invents content.
Emits a JSON result on stdout for the SKILL.md to parse. On failure, prints a
plain-language message (no traceback) and exits non-zero; the original output
and its .bak are preserved.

Usage:
  python write_test_cases.py --cases cases.json --template <tpl.xlsx> \
      --out <out.xlsx> [--sheet-conflict append|new|overwrite]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import feature_sheet_writer as fsw
import test_report_updater as report
import workbook_resolver as wbres

REQUIRED_TOP = ("feature", "sections")


def _validate(data: dict):
    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        raise ValueError(f"cases.json missing required key(s): {', '.join(missing)}")
    if not data["sections"]:
        raise ValueError("cases.json has no sections to write.")
    for s in data["sections"]:
        if not s.get("name"):
            raise ValueError("Every section needs a name.")
        for c in s.get("cases", []):
            if not c.get("description"):
                raise ValueError("Every case needs a description.")
            for row in c.get("rows", []):
                if not row.get("expected"):
                    raise ValueError(
                        f"Case '{c['description']}' has a row with no expected output "
                        "(required — the auto ID column depends on it)."
                    )


def run(args) -> dict:
    with open(args.cases, encoding="utf-8") as f:
        data = json.load(f)
    _validate(data)

    wb, existed = wbres.load_or_init(args.template, args.out)
    ws, cloned, had_feature = fsw.find_or_make_sheet(
        wb, data["feature"], args.sheet_conflict
    )

    # Re-running an existing feature: honor the conflict policy.
    append = existed and had_feature and args.sheet_conflict == "append"
    if had_feature and args.sheet_conflict == "overwrite":
        append = False  # write_feature clears the region when not appending

    last_row, count = fsw.write_feature(ws, data, append=append)
    # Name the tab after the feature and drop any unused placeholder tabs,
    # then rebuild the Test Report against the resulting tab names.
    fsw.finalize_sheets(wb, ws, data["feature"])
    warnings = report.update(wb, data.get("environment"))
    backup = wbres.save(wb, args.out)

    return {
        "ok": True,
        "output": os.path.abspath(args.out),
        "sheet": ws.title,
        "feature": data["feature"],
        "rows_written": count,
        "last_row": last_row,
        "cloned_new_sheet": cloned,
        "appended": append,
        "backup": backup,
        "warnings": warnings,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Write test cases into an Excel template.")
    p.add_argument("--cases", required=True)
    p.add_argument("--template", required=True)
    p.add_argument("--out", required=True)
    p.add_argument(
        "--sheet-conflict",
        choices=["append", "new", "overwrite"],
        default="append",
        help="What to do if the feature already has a sheet.",
    )
    args = p.parse_args(argv)

    try:
        result = run(args)
    except Exception as exc:  # plain-language surface for non-tech testers
        print(json.dumps({
            "ok": False,
            "error": str(exc),
            "hint": "Nothing was overwritten unsafely; any previous output is kept "
                    "(plus a .bak copy if it already existed).",
        }))
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
