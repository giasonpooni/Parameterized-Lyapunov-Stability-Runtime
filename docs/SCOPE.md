# Scope

The first release answers one question:

> Given a declared linear plant A (possibly affine in a parameter) and
> a quadratic certificate V, does V decrease in the Lyapunov sense at
> the declared samples, and is that claim invariant under a linear
> chart?

It does **not** claim to be a general LMI toolbox or a nonlinear
CLF synthesizer.

## In scope

- Constant and affine-parameter linear plants supplied as matrices.
- Accepting `A = J_f(x*)` from JSPT as a matrix, not computing it.
- Constant and affine quadratic certificates `V(x) = x^T P(theta) x`.
- Continuous and discrete Lyapunov equations on small dense plants.
- Runtime evaluation of V and the decrease form at `(x, theta, theta_dot)`.
- Vertex checks on a declared parameter box.
- Chart invariance of the scalar V and the scalar decrease.

## Out of scope until implemented and tested

- Forming A by finite differences or AD.
- SOS / polynomial certificates and nonlinear V construction.
- SDP synthesis of P (cvxpy, MOSEK, and friends).
- Control-Lyapunov formulas that emit an input u.
- Hybrid switching, resets, and dwell-time certificates.
- A compiled Rust or CUDA gate.
- Importing `sensitivity` and becoming a second Jacobian package.

A common quadratic that holds at every vertex of an affine plant is a
sufficient LPV test. It is conservative. The first release reports
that test; it does not pretend to have solved the infinite-dimensional
PDLF LMI.
