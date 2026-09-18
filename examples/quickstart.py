"""Exercise the first-release certificate runtime on declared plants."""

from __future__ import annotations

from pathlib import Path

from lyapunov.reports import format_quickstart, quickstart_scenario, write_report


def main() -> None:
    checks, samples = quickstart_scenario()

    print("Parameterized Lyapunov Stability Runtime")
    print("Certificates on declared A. A is not formed here.\n")
    for check in checks:
        mark = "PASS" if check.passed else "FAIL"
        print(f"[{mark}] {check.name}")
        print(f"       {check.details}")

    print("\nRuntime samples:")
    for item in samples:
        print(f"  {item.status:12s} {item.details}")

    target = Path(__file__).resolve().parents[1] / "results" / "quickstart.md"
    write_report(target, format_quickstart())
    print(f"\nWrote {target}")

    if any(not check.passed for check in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
