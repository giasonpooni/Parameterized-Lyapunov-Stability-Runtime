# HANDOFF

Public siblings: Fluid-State-Reconstruction-Testbed,
Construction-State-Estimator-for-BIM,
Jacobian-Sensitivity-Propagation-Testbed,
Geodesic-Flow-and-Jacobi-Field-Testbed.
This repository is the certificate slice. It does not import those
packages and does not absorb their domains.

## Delivered

- `lyapunov` package: declared linear / affine plants, quadratic /
  affine certificates, continuous and discrete Lyapunov solves,
  runtime evaluation of V and the decrease form, vertex checks,
  chart push of P by solves.
- A is accepted as a matrix through `plant_from_jacobian`. Callables
  and models are refused.
- No local condition-number cap. Singular T is refused by a failed
  solve. No nearest-PSD repair of P.
- Discrete guest satellite: four exact i64 statements -- `V-push-v1`,
  `discrete-decrease-v1` and `jacobi-step-v1` under `i64-unimodular-v1`,
  and `developable-defect-v1` under `i64-sampled-defect-v1`. There is no
  suite-level contract; each statement carries its own.
  `developable-star-v1` under `i64-coplanar-star-v1` is a helper, not a
  suite member. A result outside `i64` is refused on both the Python and
  the Rust side rather than returned as a bignum or wrapped. Public
  commit is `statement_id`, `held`, `statement_digest` only. Host
  callback attached; SP1 prover not bound. Status `NOT_CHECKED`.
- Reference plants: Hurwitz pair, unstable pair (solve must refuse),
  discrete contraction, two-vertex affine coupling LPV.
- Cross-reference runner against JSPT published matrices
  (`examples/cross_reference.py`). Refusals are recorded outcomes.

## Development status

In development. `results/cross_reference.json` records
`confirmed_out_of_development: false`. Do not treat a green pytest
  or a written results file as a release.

## Not delivered

- SOS / polynomial V, SDP synthesis of P, CLF-to-u, hybrid certificates,
  bound SP1 verifier / receipt, CUDA, JSPT import, PLC/SCADA, BIM kernels.

## Known gap, deliberately not closed here

The SP1 guest at `guests/discrete-morphisms-v1/sp1-program` commits
`(kind, held, a, b)` and never commits `statement_digest`, so a receipt
carries no binding to the statement it came from: `attach` compares a
digest the host wrote into the receipt JSON, not one the proof covers.
Closing this means changing the guest's committed public values to
`statement_id`, `held`, `statement_digest` and re-deriving the verifying
key, which needs `cargo prove`. Until that toolchain exists the honest
position is the one the code already takes: `proof_status` stays
`NOT_CHECKED`, and nothing in this repository may set
`verified_by_bound_host` from that program. Do not wire a new statement
kind before then.

## Run

```
uv run --python 3.13 python examples/quickstart.py
uv run --python 3.13 python examples/cross_reference.py
uv run --python 3.13 python examples/discrete_guest.py
uv run --python 3.13 python examples/host_callback.py
uv run --python 3.13 python examples/write_figures.py
uv run --python 3.13 --dev pytest -q
```

The Rust twin needs no `cargo-prove`, and CI runs it in a dedicated
`i64 guest twin` job. The SP1 packages under `sp1-program/` and
`sp1-host/` remain out of CI:

```
cd guests/discrete-morphisms-v1 && cargo test && cargo run
```

The mutation gate proves the law tests are load bearing. It never writes
inside the repository:

```
uv run --python 3.13 --dev python tools/mutation_check.py
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). An escaped mutation is an
unpinned law: write the test, do not delete the mutation.
