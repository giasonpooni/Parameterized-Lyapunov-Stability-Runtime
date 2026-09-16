# Development status

This repository is **in development**. A green local pytest run and a
written `results/` file are not confirmation that the runtime is out of
development.

## What "out of development" would require

- The NumPy certificate identities below pinned by tests on `main`.
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
- Charts push P by solves. Singular T is refused. No 1e12 cap here.

## Recursive benchmark rule

1. Read a published sibling matrix or result number.
2. Copy it into a declared case in `lyapunov.benchmarks`.
3. Run `examples/cross_reference.py`.
4. Commit the JSON and markdown that the run wrote.
5. Do not hand-edit those numbers.

JSPT observation Jacobians that are not square plants must remain
refusals. Do not widen A to accept a 1x3 beam Jacobian so a row turns
green.
