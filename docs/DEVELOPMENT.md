# Development status

This repository is **in development**. A green local pytest run and a
written `results/` file are not confirmation that the runtime is out of
development.

## What "out of development" would require

- The NumPy certificate identities below pinned by tests on `main`, and
  every one of them proved load-bearing by `tools/mutation_check.py`.
- Cross-reference cases regenerated from declared sibling matrices,
  with JSON and markdown in `results/` matching the runner.
- A decision, recorded in HANDOFF, that no further first-release
  identity will change.
- No CUDA, no local condition cap, no import of `sensitivity`.

Until that decision exists, treat every PASS as a development sample.

## Current first-release identities (still under refinement)

- A is an input matrix. Non-square J from JSPT is refused as A.
- V is quadratic. Decrease is A^T P + P A + Pdot or A^T P A - P.
- Solve on the symmetric subspace, dim <= 24.
- Charts push P by solves. Singular T is refused by a rank test, which is
  scale invariant; there is no 1e12 cap here. Accepting a chart is not a
  promise that the pushforward survives float64.
- `verdict` certifies only a negative definite decrease form. A negative
  semidefinite one is not a certificate away from the origin.
- Tolerances may only tighten a test. A negative `atol` is refused.
- Vertex corners are a sufficient box test for a common quadratic only; an
  affine `P(theta)` reports `sufficient_for_box = 0`.
- The Lyapunov residual gate measures the solve, not the scale of `Q`. Its
  three constants are in `docs/KERNEL.md`.
- The i64 guest refuses every operation that leaves the range, matching the
  Rust twin operation for operation. A twin disagreement is a refuse.
- Every check reports a claim code from `claim-codes-v1`. A vertex sweep
  earns `SUFFICIENT_COMMON_QUADRATIC` at best, never a statement about the
  plant being stable.
- `Pdot` is recorded, not implied. A constant `P` records the zero matrix,
  so a declared `theta_dot` box cannot look as though it entered.

## Mutation gate

A green suite proves the tests ran. It does not prove they are load
bearing. `tools/mutation_check.py` applies, one at a time, the exact change
each law forbids, and requires the suite to go red:

```bash
uv run --python 3.13 --dev python tools/mutation_check.py
uv run --python 3.13 --dev python tools/mutation_check.py --list
uv run --python 3.13 --dev python tools/mutation_check.py --working-tree
```

Exit status is 0 only when every mutation is caught. Each mutation runs in
a throwaway copy of the tree; the script never writes inside the
repository, and it refuses to report anything unless the copy's baseline is
green, because a red baseline makes every result noise.

The list covers the code laws, the pins and the documents. `docs/GATE.md`
went stale at "three discrete identities" because no test read it, so
mutations 17 to 21 hand-edit a pin, restore the stale count, and rename,
reorder and mis-contract a registry table.

Two rules when a mutation escapes:

- Do not delete the mutation. An escaped mutation is an unpinned law;
  write the test that catches it. Two escapes were found this way. One
  test claimed to pin the guest's `i64` range check but its input
  overflowed in an inner helper whose own guard fired first. Another
  claimed to pin the statement registry but only asked whether an id
  appeared somewhere in the file, so a renamed table row slipped past.
- A mutation that no longer applies is reported as stale and counts as an
  escape. Update the mutation to match the code; do not drop it.
- A mutation that breaks collection is reported as `UNUSABLE`, not as an
  escape. Deleting the body of a block leaves an `IndentationError`, pytest
  then emits no `FAILED` lines, and "no test noticed" would read exactly
  like "nothing was pinned" when in fact nothing was measured. Rewrite the
  mutation so the tree stays valid -- negate a condition rather than delete
  a block.

Mutations that delete the same text leave the file at an identical size,
so `__pycache__` is purged and `PYTHONDONTWRITEBYTECODE` is set on every
run. Without that, CPython's `(mtime, size)` cache key can match across two
mutations written in the same mtime tick and the run silently tests the
previous mutation's code, which reports an escaped law as caught.

## Coverage, and what the last percent is

Branch coverage runs in CI with a floor in `pyproject.toml`. It is a
ratchet: raise it when coverage rises, never lower it so a change fits.

It was added because the shape of the misses was damning. At 90% nearly
every uncovered line in the package was a `raise` -- the refusal paths,
which are the product, were its least exercised code. Writing
`tests/test_refusals.py` took it to 98.88%.

What remains is defensive code that cannot fire, and is listed here so the
gap is accounted for rather than mysterious:

- `runtime.py` "P is not positive definite" and "V is negative". Every
  certificate validates P at construction or at each evaluation, so
  `min_P` is strictly positive whenever a sample exists, and `x^T P x` is
  then never negative. `test_every_evaluated_P_is_positive_definite_by_construction`
  pins the invariant that makes them unreachable.
- `runtime.py` "theta_dot does not match the certificate". The plant checks
  the rate against its own parameter count first, and the certificate
  matrix is built from `theta` before the rate is assembled, so every route
  to that mismatch is intercepted earlier.
- `charts.py` the two `LinAlgError` handlers. The rank test at construction
  refuses anything `np.linalg.solve` would reject.
- `discrete_guest.py` "held and defect==0 must agree", an internal
  consistency assertion between two values computed from the same triples.
- `benchmarks.py` "unexpected: non-square J was accepted as A", which fires
  only if the law it records has already been broken.

Keeping these is deliberate: they are cheap insurance against a future
path that skips a validation. Deleting them to reach 100% would trade a
guard for a number.

## Recursive benchmark rule

1. Read a published sibling matrix or result number.
2. Copy it into a declared case in `lyapunov.benchmarks`.
3. Run `examples/cross_reference.py`.
4. Commit the JSON and markdown that the run wrote.
5. Do not hand-edit those numbers.

JSPT observation Jacobians that are not square plants must remain
refusals. Do not widen A to accept a 1x3 beam Jacobian so a row turns
green.
