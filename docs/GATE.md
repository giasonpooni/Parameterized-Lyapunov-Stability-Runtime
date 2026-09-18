# Compiled stack

Do not implement CUDA or a local condition-number cap here.
Linearization A = J belongs to JSPT. Certificates belong here.

NumPy PLSR is the development oracle for V. A later Rust gate may
seal the certificate identities. CUDA and C++ are backends behind
that gate if they ever exist. They are not a second constitution.

## Law that must survive the gate

- V is a declared quadratic form. It is not a finite difference of a
  trajectory and not a spectral radius lookup.
- A is an input matrix. This package does not form J_f(x*).
- P is symmetric; a non-symmetric declaration is refused.
- P that is not positive definite is refused. No clip, no nearest-PSD.
- Continuous decrease is A^T P + P A + Pdot. Discrete decrease is A^T P A - P.
- Charts push P by solves, not inverses. A singular T is refused.
  There is no MAX_CONDITION_NUMBER in this repository.
- Spectrum is a diagnostic. It does not replace V.

No backend may expose those identities as kwargs that change the law.

## Binding slice

A scaled-integer satellite exists: `lyapunov.discrete_guest` and
`guests/discrete-morphisms-v1`. It seals four discrete identities in
`i64`, each under its own named numeric contract:

| statement_id | numeric contract |
| --- | --- |
| `V-push-v1` | `i64-unimodular-v1` |
| `discrete-decrease-v1` | `i64-unimodular-v1` |
| `jacobi-step-v1` | `i64-unimodular-v1` |
| `developable-defect-v1` | `i64-sampled-defect-v1` |

There is no suite-level contract. `developable-star-v1` under
`i64-coplanar-star-v1` is a helper, not a suite member; prefer
`developable-defect-v1`.

A guest may commit only `statement_id`, `held`, `statement_digest`.
Coordinates and outputs stay in the host-oracle inputs.

Exactness is part of the contract: a result outside `i64` is refused on
both sides rather than returned as a Python bignum or a wrapped Rust
`i64`, because a twin disagreement is a refuse, not a repair.

The host callback is `lyapunov.host_callback.attach`.
SP1 guest source lives in `guests/discrete-morphisms-v1/sp1-program`
and is not a CI dependency. Missing cargo-prove or opaque proof bytes
keep `proof_status=NOT_CHECKED`. Do not import into `gat`. Do not
report VERIFIED without a bound verifier.

Wire a new statement kind into the SP1 program only once `cargo prove`
exists. Until then the count above is the registry, and
`tests/test_registry_coherence.py` holds this document to it.

## Refusal

Do not add CuPy, JAX-as-runtime, cvxpy as a hidden constitution, or a
local copy of JSPT's 1e12 cap.
