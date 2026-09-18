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
from lyapunov.reports import format_cross_reference, write_report


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

    md_target = root / "results" / "cross_reference.md"
    write_report(md_target, format_cross_reference(cases, JSPT_REPO, JSPT_SHA))
    print(f"Wrote {json_target}")
    print(f"Wrote {md_target}")
    for case in cases:
        print(f"[{case.outcome}] {case.name}: {case.details}")


if __name__ == "__main__":
    main()
