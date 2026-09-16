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
- Reference plants: Hurwitz pair, unstable pair (solve must refuse),
  discrete contraction, two-vertex affine coupling LPV.

## Not delivered

- SOS / polynomial V, SDP synthesis of P, CLF-to-u, hybrid certificates,
  Rust / CUDA gate, JSPT import, PLC/SCADA, BIM kernels.

## Run

```
uv run --python 3.13 python examples/quickstart.py
uv run --python 3.13 --dev pytest
```
