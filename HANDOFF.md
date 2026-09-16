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
- Discrete guest satellite: `V-push-v1`, `discrete-decrease-v1`,
  `jacobi-step-v1` as exact i64 maps. Host callback attached;
  SP1 prover not bound. Status `NOT_CHECKED`.
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

## Run

```
uv run --python 3.13 python examples/quickstart.py
uv run --python 3.13 python examples/cross_reference.py
uv run --python 3.13 python examples/discrete_guest.py
uv run --python 3.13 python examples/host_callback.py
uv run --python 3.13 --dev pytest
```
