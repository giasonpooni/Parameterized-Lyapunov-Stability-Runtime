#!/usr/bin/env python3
"""Differential test of the two i64 twins.

docs/DISCRETE-GUEST-v1.md makes the twins referees for each other:
"disagreement with the integer twin is a refuse, not a repair". Until now
that agreement was checked on four hand-written fixtures. This generates
cases, runs them through `lyapunov.discrete_guest` and through the Rust
binary in `guests/discrete-morphisms-v1`, and requires the two to agree on
the outcome AND on which refusal fired.

Cases are drawn towards the boundaries, because that is where the twins
have actually diverged: the i64 edges, values that overflow only in an
intermediate, matrices that are symmetric but not definite, charts with
determinant just off +-1, and stars that are degenerate in each of the
ways the contract names.

    python tools/differential_twins.py                 # 2000 cases
    python tools/differential_twins.py --cases 20000
    python tools/differential_twins.py --seed 7

Exit status is 0 only when every case agrees. This needs `cargo` but not
`cargo-prove`: the crate has no dependencies and builds offline.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRATE = ROOT / "guests" / "discrete-morphisms-v1"

sys.path.insert(0, str(ROOT / "src"))

from lyapunov.discrete_guest import (  # noqa: E402
    GuestRefuse,
    run_developable_defect,
    run_discrete_decrease,
    run_jacobi_steps,
    run_v_push,
)

I64_MIN, I64_MAX = -(1 << 63), (1 << 63) - 1

#: Python raises one exception type with a message; Rust returns a variant.
#: Map the message onto the variant name so the two are comparable.
REFUSAL_KINDS = (
    ("overflows i64", "Overflow"),
    ("must be symmetric", "NotSymmetric"),
    ("positive definite", "NotPd"),
    ("unimodular", "NotUnimodular"),
    ("K must be", "BadK"),
    ("steps must be", "BadSteps"),
    ("star must have", "BadStar"),
    ("coincides with the centre", "DegenerateStar"),
    ("every spoke is collinear", "DegenerateStar"),
    ("panel graph has no vertices", "EmptyGraph"),
    ("center index out of range", "CenterOutOfRange"),
    ("index out of range", "EdgeOutOfRange"),
    ("must be a pair", "Parse"),
    ("duplicate spoke", "DuplicateSpoke"),
)


def classify(message: str) -> str:
    for needle, name in REFUSAL_KINDS:
        if needle in message:
            return name
    return f"Unclassified({message[:40]})"


@dataclass(frozen=True)
class Case:
    op: str
    line: str
    run: object

    def python(self) -> str:
        try:
            statement = self.run()
        except GuestRefuse as exc:
            return f"ERR {classify(str(exc))}"
        out = statement.outputs
        held = int(statement.held)
        if self.op == "VPUSH":
            pp = out["P_prime"]
            return (
                f"OK {held} {out['V']} {out['V_prime']} {out['x_prime'][0]} "
                f"{out['x_prime'][1]} {pp[0][0]} {pp[0][1]} {pp[1][0]} {pp[1][1]}"
            )
        if self.op == "DEC":
            return f"OK {held} {out['delta_V']}"
        if self.op == "JAC":
            return f"OK {held} {out['j_final']}"
        normal = out["normal"]
        return f"OK {held} {out['defect']} {normal[0]} {normal[1]} {normal[2]}"


def scalar(rng: random.Random) -> int:
    """A value drawn towards the places the twins can disagree."""
    bucket = rng.random()
    if bucket < 0.40:
        return rng.randint(-4, 4)
    if bucket < 0.60:
        return rng.choice([0, 1, -1, 2, -2, 3, -3])
    if bucket < 0.85:
        shift = rng.choice([15, 16, 31, 32, 40, 46, 47, 61, 62])
        return _clamp(rng.choice([1, -1]) * (1 << shift) + rng.randint(-2, 2))
    if bucket < 0.95:
        return rng.choice([I64_MIN, I64_MAX, I64_MIN + 1, I64_MAX - 1, 1 << 62, -(1 << 62)])
    return rng.randint(I64_MIN, I64_MAX)


def _clamp(value: int) -> int:
    """Keep a generated value inside i64.

    An input outside i64 is not a twin disagreement: Python refuses it in
    _as_i64 and the Rust harness cannot even parse it. abs(I64_MIN) leaves
    the range, which is how the first run produced 50 such cases.
    """
    return max(I64_MIN, min(I64_MAX, value))


def symmetric_pair(rng: random.Random) -> list[list[int]]:
    a, d, b = scalar(rng), scalar(rng), scalar(rng)
    if rng.random() < 0.25:  # deliberately non-symmetric
        return [[a, b], [scalar(rng), d]]
    if rng.random() < 0.35:  # deliberately easy to be PD
        a, d, b = _clamp(abs(a) + 1), _clamp(abs(d) + 1), rng.randint(-1, 1)
    return [[a, b], [b, d]]


def chart(rng: random.Random) -> list[list[int]]:
    if rng.random() < 0.45:  # unimodular by construction
        k, m = rng.randint(-3, 3), rng.randint(-3, 3)
        base = [[1, k], [0, 1]] if rng.random() < 0.5 else [[1, 0], [m, 1]]
        if rng.random() < 0.3:
            base = [[base[0][0], base[0][1]], [-base[1][0], -base[1][1]]]
        return base
    return [[scalar(rng), scalar(rng)], [scalar(rng), scalar(rng)]]


def star(rng: random.Random) -> tuple[list[list[int]], list[list[int]], int]:
    count = rng.randint(2, 6)
    coordinate = lambda: rng.randint(-6, 6) if rng.random() < 0.85 else scalar(rng)
    centre = [coordinate() for _ in range(3)]
    vertices = [centre]
    planar = rng.random() < 0.5
    for _ in range(count):
        point = [_clamp(centre[0] + coordinate()), _clamp(centre[1] + coordinate()), centre[2]]
        if not planar:
            point[2] = _clamp(centre[2] + coordinate())
        if rng.random() < 0.08:  # coincident with the centre
            point = list(centre)
        vertices.append(point)
    edges = [[0, i] for i in range(1, count + 1)]
    if rng.random() < 0.12:
        edges.append(list(rng.choice(edges)))  # duplicate spoke
    if rng.random() < 0.10:
        edges.append([0, rng.choice([-1, len(vertices) + 3])])  # out of range
    rng.shuffle(edges)
    centre_index = 0 if rng.random() < 0.9 else rng.choice([-1, len(vertices) + 2])
    return vertices, edges, centre_index


def build(rng: random.Random) -> Case:
    which = rng.choice(["VPUSH", "DEC", "JAC", "DEFECT"])
    if which == "VPUSH":
        P, T = symmetric_pair(rng), chart(rng)
        x = [scalar(rng), scalar(rng)]
        line = "VPUSH " + " ".join(
            map(str, [P[0][0], P[0][1], P[1][0], P[1][1], T[0][0], T[0][1], T[1][0], T[1][1], *x])
        )
        return Case(which, line, lambda: run_v_push(P=P, T=T, x=x))
    if which == "DEC":
        A = [[scalar(rng), scalar(rng)], [scalar(rng), scalar(rng)]]
        P = symmetric_pair(rng)
        x = [scalar(rng), scalar(rng)]
        line = "DEC " + " ".join(
            map(str, [A[0][0], A[0][1], A[1][0], A[1][1], P[0][0], P[0][1], P[1][0], P[1][1], *x])
        )
        return Case(which, line, lambda: run_discrete_decrease(A=A, P=P, x=x))
    if which == "JAC":
        j0, j1 = scalar(rng), scalar(rng)
        k = rng.choice([0, 1, -1, 2, -5])
        h2 = scalar(rng) if rng.random() < 0.4 else rng.randint(-3, 3)
        steps = rng.choice([1, 2, 4, 8, 64, 65, 0])
        line = f"JAC {j0} {j1} {k} {h2} {steps}"
        return Case(which, line, lambda: run_jacobi_steps(j0=j0, j1=j1, k=k, h2=h2, steps=steps))
    vertices, edges, centre = star(rng)
    flat: list[int] = [len(vertices)]
    for point in vertices:
        flat.extend(point)
    flat.append(len(edges))
    for edge in edges:
        flat.extend(edge)
    flat.append(centre)
    line = "DEFECT " + " ".join(map(str, flat))
    return Case(
        which,
        line,
        lambda: run_developable_defect(vertices=vertices, edges=edges, center=centre),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260918)
    parser.add_argument("--show", type=int, default=12, help="divergences to print")
    args = parser.parse_args()

    build_result = subprocess.run(
        ["cargo", "build", "--locked", "--offline", "--quiet", "--bin", "differential"],
        cwd=CRATE, capture_output=True, text=True,
    )
    if build_result.returncode != 0:
        print(build_result.stderr.strip() or "cargo build failed")
        return 2

    rng = random.Random(args.seed)
    cases = [build(rng) for _ in range(args.cases)]

    rust = subprocess.run(
        ["cargo", "run", "--locked", "--offline", "--quiet", "--bin", "differential"],
        cwd=CRATE, input="\n".join(c.line for c in cases) + "\n",
        capture_output=True, text=True,
    )
    if rust.returncode != 0:
        print(rust.stderr.strip() or "cargo run failed")
        return 2
    answers = rust.stdout.splitlines()
    if len(answers) != len(cases):
        print(f"protocol desync: {len(answers)} answers for {len(cases)} cases")
        return 2

    divergences: list[tuple[Case, str, str]] = []
    agreed: dict[str, int] = {}
    for case, theirs in zip(cases, answers):
        mine = case.python()
        if mine != theirs:
            divergences.append((case, mine, theirs))
        else:
            agreed[case.op] = agreed.get(case.op, 0) + 1

    print(f"{args.cases} cases, seed {args.seed}")
    for op in sorted(set(c.op for c in cases)):
        total = sum(1 for c in cases if c.op == op)
        print(f"  {op:<7} {agreed.get(op, 0):>5}/{total:<5} agreed")
    if not divergences:
        print("\nthe twins agree on every case")
        return 0

    print(f"\n{len(divergences)} DIVERGENCES -- a disagreement is a refuse, not a repair:\n")
    for case, mine, theirs in divergences[: args.show]:
        print(f"  {case.line}")
        print(f"    python {mine}")
        print(f"    rust   {theirs}")
    if len(divergences) > args.show:
        print(f"  ... and {len(divergences) - args.show} more")
    shapes: dict[tuple[str, str], int] = {}
    for case, mine, theirs in divergences:
        shapes[(mine.split()[0] + ":" + mine.split()[1] if mine.startswith("ERR") else "OK",
                theirs.split()[0] + ":" + theirs.split()[1] if theirs.startswith("ERR") else "OK")] = (
            shapes.get((mine.split()[0] + ":" + mine.split()[1] if mine.startswith("ERR") else "OK",
                        theirs.split()[0] + ":" + theirs.split()[1] if theirs.startswith("ERR") else "OK"), 0) + 1
        )
    print("\n  shapes (python -> rust):")
    for (mine, theirs), count in sorted(shapes.items(), key=lambda kv: -kv[1]):
        print(f"    x{count:<5} {mine}  vs  {theirs}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
