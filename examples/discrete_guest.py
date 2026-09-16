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


def main() -> None:
    suite = run_fixture_suite()
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    json_path = out_dir / "discrete_guest.json"
    md_path = out_dir / "discrete_guest.md"
    json_path.write_text(json.dumps(suite, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Discrete guest fixtures",
        "",
        "Integer twins only. `proof_status: NOT_CHECKED`.",
        f"claim_scope: `{suite['claim_scope']}`",
        f"numeric_contract: `{suite['numeric_contract']}`",
        "",
        "| statement | held | V / \u0394V / j_final |",
        "| --- | --- | --- |",
    ]
    for stmt in suite["statements"]:
        out = stmt["outputs"]
        summary = out.get("V", out.get("delta_V", out.get("j_final")))
        lines.append(f"| `{stmt['statement_id']}` | {stmt['held']} | {summary} |")
    lines.extend(
        [
            "",
            "Not a stamp. Not SI-traceable. Do not import into `gat`.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(json_path)
    print(md_path)
    for stmt in suite["statements"]:
        print(stmt["statement_id"], "held=", stmt["held"], "digest=", stmt["statement_digest"][:16])


if __name__ == "__main__":
    main()
