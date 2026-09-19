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
        '    return _dot2(x[0], Px[0], x[1], Px[1], "quadratic")',
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
        "22",
        "a refusal must mean the maths failed, not that the units are small",
        "src/lyapunov/charts.py",
        "    primed = 0.5 * (primed + primed.T)\n",
        "",
    ),
    Mutation(
        "23",
        "the residual gate measures the solve, not the scale of Q",
        "src/lyapunov/equation.py",
        "    tolerance = min(\n        max(RESIDUAL_FLOOR_RELATIVE * q_scale, backward),\n        RESIDUAL_CAP_RELATIVE * q_scale,\n    )",
        "    tolerance = RESIDUAL_FLOOR_RELATIVE * q_scale",
    ),
    Mutation(
        "24",
        "the residual gate keeps a meaningful forward error",
        "src/lyapunov/equation.py",
        "    tolerance = min(\n        max(RESIDUAL_FLOOR_RELATIVE * q_scale, backward),\n        RESIDUAL_CAP_RELATIVE * q_scale,\n    )",
        "    tolerance = max(RESIDUAL_FLOOR_RELATIVE * q_scale, backward)",
    ),
    Mutation(
        "26",
        "the guest checks every operation, as the Rust twin does",
        "src/lyapunov/discrete_guest.py",
        '    return _add(_mul(a, b, name), _mul(c, d, name), name)',
        '    return _i64(a * b + c * d, name)',
    ),
    Mutation(
        "27",
        "atol must be a real number, not anything float() parses",
        "src/lyapunov/checks.py",
        "    if isinstance(atol, bool) or not isinstance(atol, (int, float, np.floating, np.integer)):\n"
        '        raise ValueError(f"atol must be a real number; got {type(atol).__name__}")\n',
        "",
    ),
    Mutation(
        "28",
        "the spoke order is canonical, not the edge listing order",
        "src/lyapunov/discrete_guest.py",
        "    nbr_idx.sort()\n",
        "",
    ),
    Mutation(
        "29",
        "the normal comes from the first NON-COLLINEAR pair",
        "src/lyapunov/discrete_guest.py",
        "            candidate = _cross(edges[i], edges[j])",
        "            candidate = _cross(edges[0], edges[1])",
    ),
    Mutation(
        "30",
        "a spoke on the centre is degenerate wherever it is listed",
        "src/lyapunov/discrete_guest.py",
        "        if edge == (0, 0, 0):",
        "        if False:",
    ),
    Mutation(
        "31",
        "no tolerance kwarg may loosen a check",
        "src/lyapunov/checks.py",
        '    rtol = _require_no_looser(rtol, DEFAULT_EQUATION_RTOL, "rtol")\n',
        "",
    ),
    Mutation(
        "32",
        "the sp1 host does not mint verified_by_bound_host",
        "guests/discrete-morphisms-v1/sp1-host/src/main.rs",
        '        "proof_status": "NOT_CHECKED",\n        "verified_by_bound_host": false,',
        '        "proof_status": "VERIFIED",\n        "verified_by_bound_host": true,',
    ),
    Mutation(
        "33",
        "a committed pin carries no absolute path",
        "src/lyapunov/host_callback.py",
        '        "guest_manifest": "guests/discrete-morphisms-v1/sp1-program/README.md",',
        '        "guest_manifest": "/home/user/guests/sp1-program/README.md",',
    ),
    Mutation(
        "34",
        "a check cannot carry a claim this instrument cannot make",
        "src/lyapunov/checks.py",
        "    def __post_init__(self) -> None:\n        require_claim(self.claim)",
        "    def __post_init__(self) -> None:\n        pass",
    ),
    Mutation(
        "35",
        "an affine P earns declared samples only, never box sufficiency",
        "src/lyapunov/checks.py",
        "    code = SUFFICIENT_COMMON_QUADRATIC if sufficient else DECLARED_SAMPLES_ONLY",
        "    code = SUFFICIENT_COMMON_QUADRATIC",
    ),
    Mutation(
        "36",
        "a constant P records a zero Pdot, not a silent None",
        "src/lyapunov/runtime.py",
        "        return np.zeros_like(certificate.P)",
        "        return None",
    ),
    Mutation(
        "37",
        "the published report carries the claim code",
        "src/lyapunov/reports.py",
        'lines.append(f"- [{mark}] {check.claim} {check.name}: {check.details}")',
        'lines.append(f"- [{mark}] {check.name}: {check.details}")',
    ),
    # plants.py and certificates.py carried 200 and 82 lines with no mutation
    # at all: the gate proved 37 laws were pinned and said nothing about the
    # modules that own "A is an input" and "P is a declaration".
    Mutation(
        "38",
        "A is an input and must be square",
        "src/lyapunov/plants.py",
        '        A = as_square(self.A, "A")',
        "        A = np.asarray(self.A, dtype=float)",
    ),
    Mutation(
        "39",
        "a theta outside the declared box is refused",
        "src/lyapunov/plants.py",
        "        if np.any(value < self.theta_min - 1e-15) or np.any(value > self.theta_max + 1e-15):",
        "        if False:",
    ),
    Mutation(
        "40",
        "a rate outside the declared rate box is refused",
        "src/lyapunov/plants.py",
        "        if np.any(value < self.rate_min - 1e-15) or np.any(value > self.rate_max + 1e-15):",
        "        if False:",
    ),
    Mutation(
        "41",
        "a box must have theta_max at least theta_min",
        "src/lyapunov/plants.py",
        "        if np.any(theta_max < theta_min):",
        "        if False:",
    ),
    Mutation(
        "42",
        "a declared P is validated positive definite",
        "src/lyapunov/certificates.py",
        '        P = require_spd(self.P, "P")',
        '        P = require_symmetric(self.P, "P")',
    ),
    Mutation(
        "43",
        "every affine P_i is symmetric",
        "src/lyapunov/certificates.py",
        '        terms = tuple(require_symmetric(term, f"P[{i}]") for i, term in enumerate(self.terms))',
        "        terms = tuple(np.asarray(term, dtype=float) for term in self.terms)",
    ),
    Mutation(
        "44",
        "an affine P(theta) is positive definite at every evaluation",
        "src/lyapunov/certificates.py",
        '        return require_spd(value, f"P({self.name})")',
        "        return value",
    ),
    Mutation(
        "45",
        "the jacobi twin bounds its step count",
        "src/lyapunov/discrete_guest.py",
        "    if steps < 1 or steps > 64:",
        "    if False:",
    ),
    Mutation(
        "46",
        "an edge is a spoke whichever way round it is listed",
        "src/lyapunov/discrete_guest.py",
        "        elif j == center and i != center:\n            nbr_idx.append(i)",
        "        elif False:\n            nbr_idx.append(i)",
    ),
    Mutation(
        "47",
        "a receipt naming sp1 without proof bytes is not checked",
        "src/lyapunov/host_callback.py",
        "    if not receipt.proof_bytes_hex or not receipt.verifying_key_digest:",
        "    if False:",
    ),
    Mutation(
        "25",
        "a chart push refusal is reported, not raised, by a check",
        "src/lyapunov/checks.py",
        "    except ValueError as exc:\n        return CheckResult(",
        "    except ZeroDivisionError as exc:\n        return CheckResult(",
    ),
    Mutation(
        "21",
        "a doc cannot give a statement the wrong contract",
        "docs/GATE.md",
        "| `developable-defect-v1` | `i64-sampled-defect-v1` |",
        "| `developable-defect-v1` | `i64-unimodular-v1` |",
    ),
)


def _warn_about_untracked(working_tree: bool) -> None:
    """Refuse to measure a tree that is missing files the author just wrote.

    --working-tree copies TRACKED files, so a new module or a new test file
    that has not been `git add`ed is simply absent from the sandbox. That
    does not fail loudly: the suite runs without those tests and every
    mutation they would have caught is reported as an unpinned law. It has
    happened twice. Untracked source or test files are now a hard stop.
    """
    if not working_tree:
        return
    listed = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "src", "tests", "tools"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    relevant = [name for name in listed if name.endswith(".py")]
    if relevant:
        raise SystemExit(
            "untracked files under src/, tests/ or tools/ would be MISSING from "
            "the sandbox, so any law they pin would be reported as unpinned:\n  "
            + "\n  ".join(relevant)
            + "\n`git add` them, or run without --working-tree to measure HEAD."
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


class MutationUnusable(RuntimeError):
    """The mutated tree could not run its tests at all.

    A mutation that breaks collection -- an IndentationError from deleting
    the body of a block, say -- produces no FAILED lines. Read naively that
    is indistinguishable from "no test noticed", so it would be reported as
    an unpinned law. It is the opposite: nothing was measured. Say so.
    """


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
    failed = sorted(
        {
            line.split("::")[1].split()[0]
            for line in result.stdout.splitlines()
            if line.startswith("FAILED") and "::" in line
        }
    )
    # pytest: 0 all passed, 1 tests failed. Anything else is collection
    # interrupted, internal error, usage error or nothing collected.
    if result.returncode not in (0, 1) and not failed:
        detail = next(
            (
                line
                for line in reversed(result.stdout.splitlines())
                if "error" in line.lower()
            ),
            f"pytest exit {result.returncode}",
        )
        raise MutationUnusable(detail.strip())
    return failed


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
        detail = probe.stderr.strip().splitlines()[-1:] or ["no stderr"]
        hint = ""
        if "--working-tree" in " ".join(sys.argv) and "ModuleNotFoundError" in probe.stderr:
            hint = (
                "\n  --working-tree copies TRACKED files only, so a new module "
                "that has not been `git add`ed is missing from the sandbox."
            )
        raise SystemExit(
            f"sandbox is not active: lyapunov resolved to {resolved!r}, "
            f"expected a path under {sandbox}\n  {detail[0]}{hint}"
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

    _warn_about_untracked(args.working_tree)
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
            except MutationUnusable as exc:
                print(f"  UNUSABLE {mutation.label()}")
                print(f"           the mutated tree cannot run its tests: {exc}")
                print("           nothing was measured; rewrite the mutation so it stays valid")
                escaped.append(mutation)
                continue
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
