"""Exercise the first-release certificate runtime on declared plants."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from lyapunov.certificates import quadratic
from lyapunov.charts import LinearChart
from lyapunov.checks import (
    check_chart_invariance,
    check_decrease,
    check_equation_residual,
    check_spectrum_agrees_with_certificate,
    check_vertices,
)
from lyapunov.equation import certificate_for_plant
from lyapunov.plants import plant_from_jacobian
from lyapunov.reference_plants import discrete_contract, hurwitz2, two_vertex_lpv
from lyapunov.reports import format_checks, format_verdicts, write_report
from lyapunov.runtime import verdict


def main() -> None:
    continuous = hurwitz2()
    discrete = discrete_contract()
    lpv = two_vertex_lpv()
    supplied = plant_from_jacobian(continuous.A, name="A=J(x*)")

    Q = np.eye(2)
    v_cont = certificate_for_plant(continuous, Q, name="V-hurwitz")
    v_disc = certificate_for_plant(discrete, Q, name="V-discrete")
    v_supplied = certificate_for_plant(supplied, Q, name="V-from-J")
    v_lpv = quadratic(np.eye(2), name="V-lpv")

    checks = [
        check_equation_residual(continuous, v_cont, Q),
        check_equation_residual(discrete, v_disc, Q),
        check_spectrum_agrees_with_certificate(continuous, v_cont),
        check_spectrum_agrees_with_certificate(discrete, v_disc),
        check_decrease(supplied, v_supplied),
        check_chart_invariance(
            continuous,
            v_cont,
            LinearChart.scale([1000.0, 0.01], name="milli"),
            [0.5, -0.2],
        ),
        check_vertices(lpv, v_lpv, include_rates=False),
    ]

    print("Parameterized Lyapunov Stability Runtime")
    print("Certificates on declared A. A is not formed here.\n")
    for check in checks:
        mark = "PASS" if check.passed else "FAIL"
        print(f"[{mark}] {check.name}")
        print(f"       {check.details}")

    samples = [
        verdict(continuous, v_cont, [0.0, 0.0]),
        verdict(continuous, v_cont, [0.8, -0.3]),
        verdict(lpv, v_lpv, [0.4, -0.2], theta=[0.0]),
        verdict(lpv, v_lpv, [0.4, -0.2], theta=[1.0]),
    ]
    print("\nRuntime samples:")
    for item in samples:
        print(f"  {item.status:12s} {item.details}")

    report = format_checks("Quickstart checks", checks) + format_verdicts(
        "Runtime samples", samples
    )
    target = Path(__file__).resolve().parents[1] / "results" / "quickstart.md"
    write_report(target, report)
    print(f"\nWrote {target}")

    if any(not check.passed for check in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
