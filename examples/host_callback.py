"""Attach the host callback to the fixture suite and write a pin."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lyapunov.host_callback import attach_fixture_suite  # noqa: E402


def main() -> None:
    body = attach_fixture_suite()
    out = ROOT / "results" / "host_callback.json"
    out.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    md = ROOT / "results" / "host_callback.md"
    lines = [
        "# Host callback",
        "",
        f"proof_status: `{body['proof_status']}`",
        f"cargo_prove_available: `{body['cargo_prove_available']}`",
        f"claim_scope: `{body['claim_scope']}`",
        "",
        "| statement | held | callback |",
        "| --- | --- | --- |",
    ]
    for cb in body["callbacks"]:
        sid = cb["statement"]["statement_id"]
        held = cb["statement"]["held"]
        lines.append(f"| `{sid}` | {held} | {cb['proof_status']} |")
    lines.extend(["", "Not a stamp. Not verified. Do not import into gat.", ""])
    md.write_text("\n".join(lines), encoding="utf-8")
    print(out)
    print("cargo_prove_available", body["cargo_prove_available"])
    print("proof_status", body["proof_status"])


if __name__ == "__main__":
    main()
