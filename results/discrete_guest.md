# Discrete guest fixtures

Integer twins only. `proof_status: NOT_CHECKED`.
claim_scope: `computational-integrity-only`
numeric_contracts: `i64-sampled-defect-v1`, `i64-unimodular-v1`

Each statement carries its own contract; the suite spans more than one.

| statement | contract | held | reported value |
| --- | --- | --- | --- |
| `V-push-v1` | `i64-unimodular-v1` | True | V = 14 |
| `discrete-decrease-v1` | `i64-unimodular-v1` | True | delta_V = -4 |
| `jacobi-step-v1` | `i64-unimodular-v1` | True | j_final = 5 |
| `developable-defect-v1` | `i64-sampled-defect-v1` | True | defect = 0 |

Not a stamp. Not SI-traceable. Do not import into `gat`.
