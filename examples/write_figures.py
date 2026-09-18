"""Write the discrete-guest fixture SVG from the live i64 twins.

The figure only repeats numbers the guest just produced (docs/FIGURES.md).
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lyapunov.reports import render_guest_figure, write_report  # noqa: E402


def main() -> None:
    out = ROOT / "results" / "discrete_guest_fixture.svg"
    write_report(out, render_guest_figure())
    print(out)


if __name__ == "__main__":
    main()
