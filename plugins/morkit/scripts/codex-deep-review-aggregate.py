#!/usr/bin/env python3
"""
morkit deep-review aggregator — Codex CLI mode.

Reads N specialist output files (each containing a YAML-Markdown findings block),
merges and dedupes findings, applies severity calibration, ranks, and renders
either Markdown or JSON.

Used by scripts/codex-deep-review.sh — not intended for standalone invocation
(but works standalone given proper workdir).
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Info"]
SEVERITY_WEIGHT = {"Critical": 100, "High": 50, "Medium": 20, "Low": 5, "Info": 0}

# ---------- YAML parsing (minimal, no external deps) ----------

YAML_BLOCK_RE = re.compile(r"```ya?ml\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def extract_yaml_blocks(text: str) -> list[str]:
    """Return all ```yaml ...``` block contents from a markdown text."""
    return YAML_BLOCK_RE.findall(text)


def parse_findings_yaml(yaml_text: str) -> list[dict]:
    """
    Minimal YAML parser tailored to our findings schema:

        findings:
          - id: S1
            category: Security
            severity: High
            file: path/to/x
            line: 42
            title: ...
            detail: ...
            source: OWASP:A03
            suggested_fix: ...
            confidence: 90

    Returns [] if no findings list found.
    """
    findings: list[dict] = []
    in_findings = False
    current: dict | None = None
    multiline_key: str | None = None
    multiline_indent = 0

    for raw in yaml_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Multiline collection (for fields like detail/suggested_fix using |-)
        if multiline_key and indent > multiline_indent and current is not None:
            current[multiline_key] = (current.get(multiline_key, "") + "\n" + stripped).strip()
            continue
        elif multiline_key:
            multiline_key = None

        if stripped.startswith("findings:"):
            in_findings = True
            continue
        if not in_findings:
            continue

        if stripped.startswith("- "):
            if current is not None:
                findings.append(current)
            current = {}
            stripped = stripped[2:]
            indent += 2

        if ":" in stripped and current is not None:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value in ("|", "|-", ">", ">-"):
                multiline_key = key
                multiline_indent = indent
                current[key] = ""
            else:
                # Strip surrounding quotes if any
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                current[key] = value

    if current is not None:
        findings.append(current)

    return findings


# ---------- Aggregation ----------


def dedupe(findings: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for f in findings:
        key = (f.get("file", ""), str(f.get("line", "")), f.get("title", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def normalize_severity(s: str) -> str:
    s_low = (s or "").strip().lower()
    for canon in SEVERITY_ORDER:
        if canon.lower() == s_low:
            return canon
    return "Info"


def coerce_int(v, default=0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def compute_score(f: dict) -> int:
    sev = normalize_severity(f.get("severity"))
    conf = coerce_int(f.get("confidence"), 50)
    return SEVERITY_WEIGHT[sev] + (conf // 10)


def rank(findings: list[dict]) -> list[dict]:
    for f in findings:
        f["severity"] = normalize_severity(f.get("severity"))
        f["confidence"] = coerce_int(f.get("confidence"), 50)
        f["score"] = compute_score(f)
    findings.sort(
        key=lambda f: (SEVERITY_ORDER.index(f["severity"]), -f["score"], f.get("file", ""))
    )
    return findings


def overall_summary(findings: list[dict]) -> dict:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for f in findings:
        counts[f["severity"]] += 1

    if counts["Critical"] >= 2:
        risk = "CRITICAL"
    elif counts["Critical"] >= 1:
        risk = "CRITICAL"
    elif counts["High"] >= 1:
        risk = "HIGH"
    elif counts["Medium"] >= 1:
        risk = "MEDIUM"
    elif counts["Low"] >= 1:
        risk = "LOW"
    else:
        risk = "INFO"

    if counts["Critical"] >= 1:
        decision = "BLOCK"
    elif counts["High"] >= 1:
        decision = "APPROVE_WITH_CHANGES"
    else:
        decision = "APPROVE"

    if findings:
        avg_conf = sum(f["confidence"] for f in findings) // len(findings)
    else:
        avg_conf = 100

    return {
        "risk": risk,
        "decision": decision,
        "confidence": avg_conf,
        "counts": counts,
    }


# ---------- Rendering ----------


def render_markdown(findings: list[dict], summary: dict, meta: dict) -> str:
    decision_emoji = {"BLOCK": "🛑", "APPROVE_WITH_CHANGES": "⚠️", "APPROVE": "✅"}[summary["decision"]]
    lines = [
        f"# morkit deep-review — {meta['target']}",
        "",
        f"_Generated by Codex CLI parallel wrapper · {meta['timestamp']}_",
        "",
        "## Executive Summary",
        "",
        f"- **Overall Risk**: `{summary['risk']}`",
        f"- **Decision**: {decision_emoji} `{summary['decision']}`",
        f"- **Confidence**: {summary['confidence']}%",
        f"- **Specialists run**: {', '.join(meta['agents'])}",
        "",
        "### Severity counts",
        "",
        "| Severity | Count |",
        "| --- | --- |",
    ]
    for sev in SEVERITY_ORDER:
        lines.append(f"| {sev} | {summary['counts'][sev]} |")

    lines += ["", "## Findings", ""]
    if not findings:
        lines.append("_No findings._")
    else:
        for f in findings:
            lines += [
                f"### [{f['severity']}] {f.get('id', '?')} — {f.get('title', '(no title)')}",
                "",
                f"- **File**: `{f.get('file', '?')}:{f.get('line', '?')}`",
                f"- **Category**: {f.get('category', '?')}",
                f"- **Source**: {f.get('source', '?')}",
                f"- **Confidence**: {f.get('confidence', '?')}%",
                "",
                f"{f.get('detail', '(no detail)')}",
                "",
                "**Suggested fix:**",
                "",
                "```",
                f"{f.get('suggested_fix', '(none)')}",
                "```",
                "",
            ]

    # Next step
    next_step = {
        "BLOCK": "Fix Critical findings, push fix commit, then re-run deep-review.",
        "APPROVE_WITH_CHANGES": "Address High findings (or defer with justification), push, then merge.",
        "APPROVE": "Ready to merge.",
    }[summary["decision"]]
    lines += ["## Next step", "", next_step, ""]

    return "\n".join(lines)


def render_json(findings: list[dict], summary: dict, meta: dict) -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "target": meta["target"],
            "timestamp": meta["timestamp"],
            "mode": "codex-parallel",
            "agents": meta["agents"],
            "overall": {
                "risk": summary["risk"],
                "decision": summary["decision"],
                "confidence": summary["confidence"],
                "counts": summary["counts"],
            },
            "findings": findings,
        },
        indent=2,
        ensure_ascii=False,
    )


# ---------- Main ----------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True, help="Directory with <agent>.out files")
    ap.add_argument("--agents", required=True, help="Comma-separated specialist names")
    ap.add_argument("--target", required=True, help="Target string for report header")
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = ap.parse_args()

    workdir = Path(args.workdir)
    agents = args.agents.split(",")

    all_findings: list[dict] = []
    succeeded: list[str] = []
    for agent in agents:
        out = workdir / f"{agent}.out"
        if not out.exists():
            continue
        text = out.read_text(encoding="utf-8", errors="replace")
        blocks = extract_yaml_blocks(text)
        if not blocks:
            # tolerate: maybe the specialist emitted raw YAML without fences
            blocks = [text]
        agent_findings = []
        for block in blocks:
            agent_findings.extend(parse_findings_yaml(block))
        if agent_findings:
            succeeded.append(agent)
            all_findings.extend(agent_findings)
        else:
            # specialist returned no findings — still counts as succeeded
            succeeded.append(agent)

    findings = rank(dedupe(all_findings))
    summary = overall_summary(findings)
    meta = {
        "target": args.target,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agents": succeeded,
    }

    if args.format == "json":
        sys.stdout.write(render_json(findings, summary, meta))
    else:
        sys.stdout.write(render_markdown(findings, summary, meta))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
