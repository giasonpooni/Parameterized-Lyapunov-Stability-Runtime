# Kernel and drift ledger

PLSR owns certificate structure. JSPT owns A2-A5 as local maps.
Domain repos wrap types; they do not fork either law.

## Ownership

| Object | Owner | Notes |
| --- | --- | --- |
| `A = J_f(x*)` | JSPT | Passed in as an array through `plant_from_jacobian`. |
| Chart cap `k2(T) <= 1e12` | JSPT | Not copied here. |
| `V = x^T P(theta) x` | PLSR | Quadratic first release. |
| Decrease form | PLSR | Continuous `A^T P + P A + Pdot`, discrete `A^T P A - P`. |
| Lyapunov solve | PLSR | Symmetric-subspace dense solve. |
| Site / IFC / tank id | domain repos | Not shared. |

If a function needs a Jacobian of a nonlinear `f`, it does not go here.
If a function only needs a chart condition cap, it stays in JSPT.

## Frozen names

`LinearPlant`, `AffinePlant`, `QuadraticCertificate`, `AffineCertificate`,
`solve_lyapunov`, `decrease_matrix`, `evaluate`, `verdict`,
`push_certificate`, `plant_from_jacobian`

Add freely behind them. Do not rename to sound like JSPT or FSRT.

## Constitution

- `SYMMETRY_ATOL = 1e-12`
- `MIN_DECREASE_MARGIN = 0.0`
- `MAX_KRONECKER_DIM = 24` for the dense solve only
- solve, do not invert
- no clip / nearest-PSD
- no local condition-number cap

## Ledger

| law | module | consumers |
| --- | --- | --- |
| `A` is an input | `plants.py` | examples, later FSRT observer |
| `A^T P + P A + Pdot < 0` | `equation.py`, `runtime.py` | checks, examples |
| `V'(Tx)=V(x)` | `charts.py` | tests |
| spectrum is diagnostic | `checks.py` | quickstart |

## What this repo is not

JSPT does not live here. A fluid tank report does not live here.
An IFC verdict does not live here. PLSR takes matrices and a certificate.
