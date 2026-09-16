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

Not opened. Do not add a PyO3 crate, a Julia wrapper, or a GPU kernel
until the NumPy identities above have tests and a handoff.

## Refusal

Do not add CuPy, JAX-as-runtime, cvxpy as a hidden constitution, or a
local copy of JSPT's 1e12 cap.
