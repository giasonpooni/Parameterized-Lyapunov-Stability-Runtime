"""Run the integer guest fixtures and write results/*.json.

Does not invoke SP1. proof_status stays NOT_CHECKED.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lyapunov.discrete_guest import run_fixture_suite  # noqa: E402
from lyapunov.reports import format_guest_suite, write_report  # noqa: E402


def main() -> None:
    suite = run_fixture_suite()
    json_path = ROOT / "results" / "discrete_guest.json"
    md_path = ROOT / "results" / "discrete_guest.md"
    write_report(json_path, json.dumps(suite, indent=2) + "\n")
    write_report(md_path, format_guest_suite(suite))
    print(json_path)
    print(md_path)
    for stmt in suite["statements"]:
        print(stmt["statement_id"], "held=", stmt["held"], "digest=", stmt["statement_digest"][:16])


if __name__ == "__main__":
    main()
