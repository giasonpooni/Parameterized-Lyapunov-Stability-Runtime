"""Attach the host callback to the fixture suite and write a pin."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lyapunov.host_callback import attach_fixture_suite  # noqa: E402
from lyapunov.reports import format_host_callbacks, write_report  # noqa: E402


def main() -> None:
    body = attach_fixture_suite()
    json_path = ROOT / "results" / "host_callback.json"
    md_path = ROOT / "results" / "host_callback.md"
    write_report(json_path, json.dumps(body, indent=2) + "\n")
    write_report(md_path, format_host_callbacks(body))
    print(json_path)
    print(md_path)
    print("cargo_prove_available", body["cargo_prove_available"])
    print("proof_status", body["proof_status"])


if __name__ == "__main__":
    main()
