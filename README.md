# Parameterized Lyapunov Stability Runtime

A computational runtime for evaluating quadratic Lyapunov certificates
on declared linear plants, including affine-parameter (LPV) plants, with
explicit limits on what a certificate is and is not.

Short name **PLSR**. The reusable library import is `lyapunov`.

This is not a second Jacobian package and not a GPU stack. Linearization
`A = J_f(x*)` is formed in
[Jacobian-Sensitivity-Propagation-Testbed](https://github.com/giasonpooni/Jacobian-Sensitivity-Propagation-Testbed)
or supplied by the caller. This repository owns the certificate
structure `V`.

**In development.** Result files are development samples. They do not
confirm the runtime is out of development. See
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

The central question is:

> Given A and a quadratic V, does V decrease in the Lyapunov sense at
> the declared samples, and does that scalar claim survive a linear
> change of coordinates?

## What is in the first slice

| Responsibility | What the runtime demonstrates |
| --- | --- |
| Certificate structure | `V(x, theta) = x^T P(theta) x` with constant or affine `P`. |
| Lyapunov equation | Solve `A^T P + P A + Q = 0` or `A^T P A - P + Q = 0` on small dense plants. |
| Runtime evaluation | Return `V` and the decrease form at a live `(x, theta, theta_dot)`. |
| Vertex checks | Test a common quadratic at every corner of a declared parameter box. |
| Chart invariance | `V'(Tx) = V(x)` after pushing `P` by solves, not inverses. |
| Sibling cross-reference | Copy published JSPT matrices; record refuse or sample. |

Spectrum is a diagnostic. A Hurwitz matrix without a P is not a
certificate. Trajectory finite differences of V are not a certificate.

## Install and run

Python 3.12 or 3.13 and NumPy are required. [uv](https://docs.astral.sh/uv/)
is the supported runner; a plain virtual environment also works.

```bash
git clone https://github.com/giasonpooni/Parameterized-Lyapunov-Stability-Runtime.git
cd Parameterized-Lyapunov-Stability-Runtime
uv run --python 3.13 python examples/quickstart.py
uv run --python 3.13 python examples/cross_reference.py
uv run --python 3.13 --with pytest pytest -q
```

The quickstart writes `results/quickstart.md`. The cross-reference
runner writes `results/cross_reference.json` and
`results/cross_reference.md`.

## Scope and limits

Quadratic certificates on explicit linear and affine-parameter plants.
No SOS, no SDP synthesis of P, no CLF-to-input formula, no CUDA, and
no local copy of JSPT's condition-number cap.

A vertex check of a common quadratic is a sufficient LPV test. It is
conservative. See [docs/SCOPE.md](docs/SCOPE.md),
[docs/METHODS.md](docs/METHODS.md), and
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## License

MIT. See [LICENSE](LICENSE).
