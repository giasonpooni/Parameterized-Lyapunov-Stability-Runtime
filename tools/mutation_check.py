#!/usr/bin/env python3
"""Mutation gate for the certificate laws.

A green test suite proves the tests run. It does not prove they are load
bearing. This applies, one at a time, the exact change each law forbids and
requires the suite to go red. A mutation nothing catches is a law nothing
pins -- report it, do not paper over it.

docs/GATE.md went stale at "three discrete identities" precisely because no
test read it. The doc and pin mutations below exist so that cannot recur.

Every mutation runs in a throwaway copy of the tree. This script never
writes inside the repository.

    python tools/mutation_check.py                 # against HEAD
    python tools/mutation_check.py --working-tree  # including uncommitted work
    python tools/mutation_check.py --list
    python tools/mutation_check.py --only 01,09,18

Exit status is 0 only when every mutation is caught.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Mutation:
    """One forbidden change, and the law it is forbidden by."""

    ident: str
    law: str
    path: str
    old: str
    new: str

    def label(self) -> str:
        return f"{self.ident} {self.law}"


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        "01",
        "verdict must not certify a merely semidefinite decrease",
        "src/lyapunov/runtime.py",
        "    if sample.max_decrease >= -MIN_DECREASE_MARGIN:",
        "    if sample.max_decrease > -MIN_DECREASE_MARGIN:",
    ),
    Mutation(
        "02",
        "atol may only tighten check_decrease",
        "src/lyapunov/checks.py",
        "    atol = _require_tightening(atol)\n    dummy = np.ones(plant.dim)",
        "    dummy = np.ones(plant.dim)",
    ),
    Mutation(
        "03",
        "atol may only tighten check_vertices",
        "src/lyapunov/checks.py",
        "    atol = _require_tightening(atol)\n    worst = -np.inf",
        "    worst = -np.inf",
    ),
    Mutation(
        "04",
        "corners are sufficient for a common quadratic only",
        "src/lyapunov/checks.py",
        "    sufficient = isinstance(certificate, QuadraticCertificate)",
        "    sufficient = True",
    ),
    Mutation(
        "05",
        "a non-PD P is refused, never repaired",
        "src/lyapunov/linalg.py",
        '    if float(np.min(eigvals)) <= 0.0:\n'
        '        raise ValueError(f"{name} must be positive definite; '
        'min eigenvalue={float(np.min(eigvals)):.3e}")\n'
        "    return array",
        "    if float(np.min(eigvals)) <= 0.0:\n"
        "        w, Q = np.linalg.eigh(array)\n"
        "        return Q @ np.diag(np.clip(w, 1e-12, None)) @ Q.T\n"
        "    return array",
    ),
    Mutation(
        "06",
        "Pdot is never copied onto discrete time",
        "src/lyapunov/equation.py",
        '        if P_rate is not None:\n'
        '            raise ValueError("discrete certificates do not take a parameter rate")\n'
        "        form = A_mat.T @ P_mat @ A_mat - P_mat",
        '        form = A_mat.T @ P_mat @ A_mat - P_mat\n'
        "        if P_rate is not None:\n"
        '            form = form + require_symmetric(P_rate, "P_rate")',
    ),
    Mutation(
        "07",
        "charts push P by solves, not inverses",
        "src/lyapunov/charts.py",
        "        Y = np.linalg.solve(chart.T.T, certificate.P)\n"
        "        primed = np.linalg.solve(chart.T.T, Y.T).T",
        "        Ti = np.linalg.inv(chart.T)\n"
        "        primed = Ti.T @ certificate.P @ Ti",
    ),
    Mutation(
        "08",
        "an accepted chart cannot be mutated afterwards",
        "src/lyapunov/charts.py",
        '        object.__setattr__(self, "T", immutable(T))',
        '        object.__setattr__(self, "T", T)',
    ),
    Mutation(
        "09",
        "invertibility is decided by rank, which is scale invariant",
        "src/lyapunov/charts.py",
        "        if np.linalg.matrix_rank(T) < T.shape[0]:",
        "        if abs(float(np.linalg.det(T))) == 0.0:",
    ),
    Mutation(
        "10",
        "only the sp1 backend is admitted",
        "src/lyapunov/host_callback.py",
        '    if receipt.backend != "sp1":\n'
        '        raise GuestRefuse(f"unsupported backend {receipt.backend!r}")\n',
        "",
    ),
    Mutation(
        "11",
        "VERIFIED only from a bound host",
        "src/lyapunov/host_callback.py",
        "    if receipt.verified_by_bound_host:",
        "    if True:",
    ),
    Mutation(
        "12",
        "every guest kernel range checks its own result",
        "src/lyapunov/discrete_guest.py",
        '    return _i64(x[0] * Px[0] + x[1] * Px[1], "quadratic")',
        "    return x[0] * Px[0] + x[1] * Px[1]",
    ),
    Mutation(
        "13",
        "guest kernels gate P as the Rust twin does",
        "src/lyapunov/discrete_guest.py",
        "    _require_pd(P)\n    Tinv = inv_unimodular(T)",
        "    Tinv = inv_unimodular(T)",
    ),
    Mutation(
        "14",
        "public commit is id, held and digest only",
        "src/lyapunov/discrete_guest.py",
        '            "statement_digest": self.digest(),\n        }',
        '            "statement_digest": self.digest(),\n'
        '            "inputs": self.inputs,\n        }',
    ),
    Mutation(
        "15",
        "the registry ids are fixed",
        "src/lyapunov/discrete_guest.py",
        'STATEMENT_DEFECT = "developable-defect-v1"',
        'STATEMENT_DEFECT = "defect-v2"',
    ),
    Mutation(
        "16",
        "a new statement cannot land without updating docs and pins",
        "src/lyapunov/discrete_guest.py",
        "        run_developable_defect(**FIXTURE_DEFECT),\n    ]",
        "        run_developable_defect(**FIXTURE_DEFECT),\n"
        "        run_developable_star(**FIXTURE_DEVELOPABLE),\n    ]",
    ),
    Mutation(
        "17",
        "results pins are regenerated, never hand-edited",
        "results/discrete_guest.md",
        "V = 14",
        "V = 99",
    ),
    Mutation(
        "18",
        "no doc states a stale statement count",
        "docs/GATE.md",
        "It seals four discrete identities in",
        "It seals three discrete identities in",
    ),
    Mutation(
        "19",
        "a registry table row cannot be renamed",
        "docs/DISCRETE-GUEST-v1.md",
        "| `developable-defect-v1` | `i64-sampled-defect-v1` | sampled defect",
        "| `REMOVED` | `i64-sampled-defect-v1` | sampled defect",
    ),
    Mutation(
        "20",
        "a registry table cannot be reordered",
        "docs/GATE.md",
        "| `V-push-v1` | `i64-unimodular-v1` |\n"
        "| `discrete-decrease-v1` | `i64-unimodular-v1` |",
        "| `discrete-decrease-v1` | `i64-unimodular-v1` |\n"
        "| `V-push-v1` | `i64-unimodular-v1` |",
    ),
    Mutation(
        "21",
        "a doc cannot give a statement the wrong contract",
        "docs/GATE.md",
        "| `developable-defect-v1` | `i64-sampled-defect-v1` |",
        "| `developable-defect-v1` | `i64-unimodular-v1` |",
    ),
)


def _populate(target: Path, working_tree: bool) -> None:
    """Copy the tree into ``target`` without touching the repository."""
    if working_tree:
        listing = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT, capture_output=True, check=True, text=True,
        ).stdout
        for name in filter(None, listing.split("\0")):
            source = ROOT / name
            if not source.is_file():
                continue
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return
    archive = subprocess.run(
        ["git", "archive", "HEAD"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)


def _purge_bytecode(sandbox: Path) -> None:
    """Remove every __pycache__ under the sandbox.

    Two mutations that delete the same string leave the file at an identical
    SIZE. Written within one mtime granularity, CPython's (mtime, size) cache
    key then matches, and the previous mutation's .pyc is reused for the next
    mutation's source -- so the run silently tests the wrong code and can
    report an escaped law as caught. Belt and braces with
    PYTHONDONTWRITEBYTECODE below.
    """
    for cache in sandbox.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _failures(sandbox: Path) -> list[str]:
    """Test ids that failed, running the sandbox against the sandbox."""
    _purge_bytecode(sandbox)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no", "--no-header",
         "-p", "no:cacheprovider", str(sandbox / "tests")],
        cwd=str(sandbox), capture_output=True, text=True,
        env={**os.environ,
             "PYTHONPATH": str(sandbox / "src"),
             "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return sorted(
        {
            line.split("::")[1].split()[0]
            for line in result.stdout.splitlines()
            if line.startswith("FAILED") and "::" in line
        }
    )


def _confirm_sandbox_is_active(sandbox: Path) -> None:
    """A sandbox that imports the installed package would prove nothing."""
    probe = subprocess.run(
        [sys.executable, "-c",
         "import lyapunov.runtime as r; print(r.__file__)"],
        cwd=str(sandbox), capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(sandbox / "src")},
    )
    resolved = probe.stdout.strip()
    if not resolved.startswith(str(sandbox)):
        raise SystemExit(
            f"sandbox is not active: lyapunov resolved to {resolved!r}, "
            f"expected a path under {sandbox}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-tree", action="store_true",
                        help="mutate the working tree copy, not HEAD")
    parser.add_argument("--only", default="",
                        help="comma separated mutation ids, e.g. 01,09")
    parser.add_argument("--list", action="store_true",
                        help="print the mutations and exit")
    args = parser.parse_args()

    selected = MUTATIONS
    if args.only:
        wanted = {token.strip() for token in args.only.split(",") if token.strip()}
        unknown = wanted - {m.ident for m in MUTATIONS}
        if unknown:
            raise SystemExit(f"unknown mutation ids: {sorted(unknown)}")
        selected = tuple(m for m in MUTATIONS if m.ident in wanted)

    if args.list:
        for mutation in selected:
            print(f"{mutation.ident}  {mutation.path:<36} {mutation.law}")
        return 0

    sandbox = Path(tempfile.mkdtemp(prefix="plsr-mutation-"))
    try:
        _populate(sandbox, args.working_tree)
        _confirm_sandbox_is_active(sandbox)

        baseline = _failures(sandbox)
        source = "the working tree" if args.working_tree else "HEAD"
        if baseline:
            print(f"baseline from {source} is not green: {baseline}")
            print("every result would be noise; fix the suite first.")
            return 2
        print(f"baseline from {source} is green; {len(selected)} mutations\n")

        escaped: list[Mutation] = []
        for mutation in selected:
            path = sandbox / mutation.path
            original = path.read_text(encoding="utf-8")
            if original.count(mutation.old) != 1:
                print(f"  SKIPPED  {mutation.label()}")
                print(f"           pattern occurs {original.count(mutation.old)} times "
                      f"in {mutation.path}; the mutation is stale")
                escaped.append(mutation)
                continue
            path.write_text(original.replace(mutation.old, mutation.new, 1), encoding="utf-8")
            try:
                caught = [name for name in _failures(sandbox) if name not in baseline]
            finally:
                path.write_text(original, encoding="utf-8")
            if caught:
                shown = ", ".join(caught[:4])
                if len(caught) > 4:
                    shown += f" (+{len(caught) - 4} more)"
                print(f"  caught   {mutation.label()}")
                print(f"           {shown}")
            else:
                print(f"  ESCAPED  {mutation.label()}")
                print(f"           nothing failed; this law is not pinned")
                escaped.append(mutation)

        print(f"\n{len(selected) - len(escaped)}/{len(selected)} mutations caught")
        if escaped:
            print("\nunpinned laws:")
            for mutation in escaped:
                print(f"  {mutation.ident}  {mutation.law}")
            return 1
        return 0
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
