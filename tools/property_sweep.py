#!/usr/bin/env python3
"""Metamorphic sweep of the float64 oracle.

The suite pins the binding laws on fixtures. A fixture shows a law holds
once. These are the same laws stated as relations that must hold for every
admissible input, checked over randomly drawn plants, certificates and
charts:

  chart-invariance   V'(Tx) = V(x) and the scalar decrease is unchanged
  chart-composition  pushing through T1 then T2 equals pushing through T2 T1
  solve-round-trip   a solved P satisfies its own equation, and is PD
  verdict-agreement  verdict() and check_decrease() never disagree
  vertex-sufficiency a constant P is bounded by the corners of the box
  spectrum-consistency a certified plant is Hurwitz / a contraction
  refusal-stability  a refusal does not depend on an irrelevant rescaling

A refusal is a legitimate outcome everywhere: the instrument is allowed to
say no, and the sweep only requires that when it says yes, the relation
holds. Refusal counts are reported so a property that is silently never
exercised cannot look like a pass.

    python tools/property_sweep.py                  # 2000 draws per property
    python tools/property_sweep.py --draws 20000 --seed 7

Exit status is 0 only when every property holds on every draw it reached.
NumPy only, no new dependency.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lyapunov.certificates import quadratic  # noqa: E402
from lyapunov.charts import LinearChart, push_certificate, push_plant  # noqa: E402
from lyapunov.checks import check_decrease, check_vertices  # noqa: E402
from lyapunov.equation import decrease_matrix, solve_lyapunov  # noqa: E402
from lyapunov.plants import affine_box_plant, constant_plant  # noqa: E402
from lyapunov.runtime import evaluate, verdict  # noqa: E402


class Skip(Exception):
    """This draw was refused, which is an allowed outcome."""


def congruence_tolerance(*charts: np.ndarray) -> float:
    """How much relative error a congruence is allowed to lose.

    ``P' = T^-T P T^-1`` has condition number about ``cond(T)**2``, so the
    achievable relative accuracy is ``eps * cond(T)**2`` and a fixed
    threshold is simply wrong. A first run flagged a composition at
    ``cond = 1.2e6`` for a relative difference of 1.0e-5, against an
    expected loss of 3.3e-4 -- the arithmetic was thirty times better than
    the bound, and the threshold was the defect.
    """
    worst = max(float(np.linalg.cond(T)) for T in charts)
    return max(1e-9, 64.0 * float(np.finfo(float).eps) * worst**2)


def spd(rng: np.random.Generator, dim: int) -> np.ndarray:
    root = rng.normal(size=(dim, dim))
    return root @ root.T + dim * np.eye(dim)


def stable(rng: np.random.Generator, dim: int, time: str) -> np.ndarray:
    A = rng.normal(size=(dim, dim))
    eigs = np.linalg.eigvals(A)
    if time == "continuous":
        shift = float(np.max(np.real(eigs))) + rng.uniform(0.1, 2.0)
        return A - shift * np.eye(dim)
    radius = float(np.max(np.abs(eigs)))
    return A * (rng.uniform(0.1, 0.95) / max(radius, 1e-12))


def invertible(rng: np.random.Generator, dim: int) -> np.ndarray:
    scale = 10.0 ** rng.uniform(-4, 4)
    T = rng.normal(size=(dim, dim)) * scale
    if np.linalg.matrix_rank(T) < dim:
        raise Skip
    return T


def prop_chart_invariance(rng: np.random.Generator) -> None:
    dim = int(rng.integers(2, 5))
    time = "continuous" if rng.random() < 0.5 else "discrete"
    plant = constant_plant(stable(rng, dim, time), name="A", time=time)
    cert = quadratic(spd(rng, dim), name="P")
    try:
        chart = LinearChart(name="T", T=invertible(rng, dim))
        moved_plant = push_plant(plant, chart)
        moved_cert = push_certificate(cert, chart)
    except ValueError as exc:
        raise Skip from exc
    x = rng.normal(size=dim)
    here = evaluate(plant, cert, x)
    there = evaluate(moved_plant, moved_cert, chart.T @ x)
    allowed = congruence_tolerance(chart.T)
    # The decrease is x^T (A^T P + P A) x, a difference of comparable terms,
    # so its VALUE can sit arbitrarily close to zero while the form itself is
    # O(1). Dividing by the value would then report a huge relative error for
    # ordinary rounding. Measure against the natural magnitude of the form,
    # ||M|| ||x||^2, which is what the arithmetic actually works with. V needs
    # no such treatment: P is positive definite, so x^T P x does not cancel.
    natural = float(np.max(np.abs(here.decrease_matrix))) * float(x @ x)
    # V is read off one pushed object, P'. The decrease is built from TWO,
    # the similarity A' and the congruence P', each already carrying
    # eps*cond(T)^2, so its bound has to be the looser one. The factor is
    # headroom on the same cond^2 law, not a blanket pass: raising it does
    # not make the property hold at a worse conditioning, only at the same
    # conditioning with a realistic constant.
    for name, a, b, floor, room in (
        ("V", here.value, there.value, 0.0, 1.0),
        ("decrease", here.decrease, there.decrease, natural, 16.0),
    ):
        scale = max(abs(a), abs(b), floor, 1e-300)
        relative = abs(a - b) / scale
        if relative > allowed * room:
            raise AssertionError(
                f"{name} moved by {relative:.2e}, allowed {allowed * room:.2e} "
                f"at cond(T)={float(np.linalg.cond(chart.T)):.2e}"
            )


def prop_chart_composition(rng: np.random.Generator) -> None:
    dim = int(rng.integers(2, 4))
    cert = quadratic(spd(rng, dim), name="P")
    try:
        T1 = invertible(rng, dim)
        T2 = invertible(rng, dim)
        step = push_certificate(push_certificate(cert, LinearChart("T1", T1)), LinearChart("T2", T2))
        direct = push_certificate(cert, LinearChart("T2T1", T2 @ T1))
    except ValueError as exc:
        raise Skip from exc
    x = rng.normal(size=dim)
    moved = (T2 @ T1) @ x
    a, b = float(moved @ step.P @ moved), float(moved @ direct.P @ moved)
    scale = max(abs(a), abs(b), 1e-300)
    relative = abs(a - b) / scale
    allowed = congruence_tolerance(T1, T2, T2 @ T1)
    if relative > allowed:
        raise AssertionError(
            f"T2 after T1 differs from T2 T1 by {relative:.2e}, allowed "
            f"{allowed:.2e} at cond(T2 T1)={float(np.linalg.cond(T2 @ T1)):.2e}"
        )


def prop_solve_round_trip(rng: np.random.Generator) -> None:
    dim = int(rng.integers(1, 6))
    time = "continuous" if rng.random() < 0.5 else "discrete"
    A = stable(rng, dim, time)
    Q = spd(rng, dim)
    try:
        cert = solve_lyapunov(A, Q, time=time)
    except ValueError as exc:
        raise Skip from exc
    if float(np.min(np.linalg.eigvalsh(cert.P))) <= 0.0:
        raise AssertionError("solve returned a P that is not positive definite")
    residual = decrease_matrix(A, cert.P, time=time) + Q
    scale = max(float(np.max(np.abs(Q))), float(np.max(np.abs(cert.P))) * float(np.max(np.abs(A))))
    if float(np.max(np.abs(residual))) / max(scale, 1e-300) > 1e-6:
        raise AssertionError("a solve that was accepted does not satisfy its own equation")


def prop_verdict_agreement(rng: np.random.Generator) -> None:
    dim = int(rng.integers(2, 5))
    time = "continuous" if rng.random() < 0.5 else "discrete"
    A = stable(rng, dim, time) if rng.random() < 0.7 else rng.normal(size=(dim, dim))
    plant = constant_plant(A, name="A", time=time)
    cert = quadratic(spd(rng, dim), name="P")
    ones = np.ones(dim)
    certified = verdict(plant, cert, ones).certified
    passed = check_decrease(plant, cert).passed
    if certified != passed:
        sample = evaluate(plant, cert, ones)
        raise AssertionError(
            f"verdict certified={certified} but check_decrease passed={passed} "
            f"(max eig(M)={sample.max_decrease:.3e})"
        )


def prop_vertex_sufficiency(rng: np.random.Generator) -> None:
    dim = 2
    time = "continuous" if rng.random() < 0.5 else "discrete"
    A0, A1 = rng.normal(size=(dim, dim)), rng.normal(size=(dim, dim))
    lo, hi = 0.0, float(rng.uniform(0.5, 2.0))
    plant = affine_box_plant(A0, [A1], [lo], [hi], name="A(theta)", time=time)
    cert = quadratic(spd(rng, dim), name="P")
    corners = check_vertices(plant, cert, include_rates=False)
    if corners.extra["sufficient_for_box"] != 1.0:
        raise Skip
    worst = corners.extra["worst"]
    for theta in rng.uniform(lo, hi, 24):
        inside = evaluate(plant, cert, np.ones(dim), theta=[float(theta)]).max_decrease
        if inside > worst + 1e-9 * max(1.0, abs(worst)):
            raise AssertionError(
                f"interior theta={theta:.6f} exceeds the corner bound: "
                f"{inside:.6e} > {worst:.6e}, yet sufficient_for_box is 1"
            )


def prop_spectrum_consistency(rng: np.random.Generator) -> None:
    dim = int(rng.integers(2, 5))
    time = "continuous" if rng.random() < 0.5 else "discrete"
    plant = constant_plant(stable(rng, dim, time), name="A", time=time)
    cert = quadratic(spd(rng, dim), name="P")
    if not check_decrease(plant, cert).passed:
        raise Skip
    eigs = np.linalg.eigvals(plant.A)
    if time == "continuous":
        if float(np.max(np.real(eigs))) >= 0.0:
            raise AssertionError("certified in continuous time but not Hurwitz")
    elif float(np.max(np.abs(eigs))) >= 1.0:
        raise AssertionError("certified in discrete time but not a contraction")


def prop_refusal_stability(rng: np.random.Generator) -> None:
    """Certification must not depend on the units the state is written in."""
    dim = int(rng.integers(2, 5))
    time = "continuous" if rng.random() < 0.5 else "discrete"
    plant = constant_plant(stable(rng, dim, time), name="A", time=time)
    cert = quadratic(spd(rng, dim), name="P")
    x = rng.normal(size=dim)
    base = verdict(plant, cert, x)
    scaled = verdict(plant, cert, x * float(10.0 ** rng.uniform(-6, 6)))
    if base.certified != scaled.certified:
        raise AssertionError(
            f"rescaling x changed the verdict: {base.status} -> {scaled.status}"
        )


PROPERTIES = (
    ("chart-invariance", prop_chart_invariance),
    ("chart-composition", prop_chart_composition),
    ("solve-round-trip", prop_solve_round_trip),
    ("verdict-agreement", prop_verdict_agreement),
    ("vertex-sufficiency", prop_vertex_sufficiency),
    ("spectrum-consistency", prop_spectrum_consistency),
    ("refusal-stability", prop_refusal_stability),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260918)
    parser.add_argument("--show", type=int, default=3)
    args = parser.parse_args()

    print(f"{args.draws} draws per property, seed {args.seed}\n")
    failures_total = 0
    for name, check in PROPERTIES:
        rng = np.random.default_rng(args.seed)
        held = skipped = 0
        failures: list[str] = []
        for _ in range(args.draws):
            try:
                check(rng)
                held += 1
            except Skip:
                skipped += 1
            except AssertionError as exc:
                failures.append(str(exc))
        mark = "ok  " if not failures else "FAIL"
        print(f"  {mark} {name:<21} held {held:>6}  refused {skipped:>6}  broken {len(failures):>5}")
        if held == 0:
            print("       every draw was refused; this property proved nothing")
        for message in failures[: args.show]:
            print(f"       {message}")
        failures_total += len(failures)

    print()
    if failures_total:
        print(f"{failures_total} violations")
        return 1
    print("every property held on every draw it reached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
