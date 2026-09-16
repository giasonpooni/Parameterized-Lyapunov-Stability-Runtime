"""Run declared sibling-matrix cases and write real result files.

This does not import JSPT, FSRT, or GAT. It copies published matrices
and records solve / refuse outcomes. Passing cases does not take the
runtime out of development.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lyapunov.benchmarks import JSPT_REPO, JSPT_SHA, run_suite
from lyapunov.reports import write_report


def main() -> None:
    cases = run_suite()
    payload = {
        "status": "in-development",
        "confirmed_out_of_development": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jspt_pin": {"repo": JSPT_REPO, "sha": JSPT_SHA},
        "cases": [case.as_dict() for case in cases],
    }
    root = Path(__file__).resolve().parents[1]
    json_target = root / "results" / "cross_reference.json"
    json_target.parent.mkdir(parents=True, exist_ok=True)
    json_target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Cross-reference benchmarks",
        "",
        "Status: **in development**. `confirmed_out_of_development: false`.",
        "",
        f"JSPT pin: `{JSPT_REPO}@{JSPT_SHA}`.",
        "",
        "Matrices below are copied from sibling reference models or result",
        "files. This package does not import `sensitivity`. A refusal is a",
        "recorded outcome. These numbers are not a release certificate.",
        "",
        "| case | outcome | details |",
        "| --- | --- | --- |",
    ]
    for case in cases:
        details = case.details.replace("|", "\\|")
        lines.append(f"| `{case.name}` | {case.outcome} | {details} |")
    lines.extend(["", "## Numbers", ""])
    for case in cases:
        lines.append(f"### {case.name}")
        lines.append("")
        lines.append(f"Source: {case.source}")
        lines.append("")
        for key, value in case.numbers.items():
            lines.append(f"- `{key}` = {value:.12g}")
        lines.append("")
    md_target = root / "results" / "cross_reference.md"
    write_report(md_target, "\n".join(lines))
    print(f"Wrote {json_target}")
    print(f"Wrote {md_target}")
    for case in cases:
        print(f"[{case.outcome}] {case.name}: {case.details}")


if __name__ == "__main__":
    main()
