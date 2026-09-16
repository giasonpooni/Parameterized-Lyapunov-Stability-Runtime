# Methods

## Plant

The caller supplies a matrix A. For a nonlinear model the linearization
`A = J_f(x*)` is formed in JSPT, or by any other source, and handed
across as an array. This package never estimates a Jacobian.

An affine-parameter plant is

```text
A(theta) = A0 + sum_i theta_i A_i,    theta in [theta_min, theta_max].
```

## Certificate

The first-release certificate is quadratic,

```text
V(x, theta) = x^T P(theta) x,    P(theta) = P0 + sum_i theta_i P_i.
```

P(theta) must be symmetric positive definite at every evaluation site.

## Decrease

Continuous time:

```text
Vdot(x, theta, theta_dot) = x^T ( A(theta)^T P(theta) + P(theta) A(theta) + sum_i theta_dot_i P_i ) x.
```

Discrete time:

```text
Delta V(x, theta) = x^T ( A(theta)^T P(theta) A(theta) - P(theta) ) x.
```

A sample is certified when P is positive definite and the decrease matrix
is negative definite. The origin is certified with V = 0 and decrease = 0.

## Lyapunov equation

For a constant plant the package solves, on the symmetric subspace,

```text
A^T P + P A + Q = 0     (continuous)
A^T P A - P + Q = 0     (discrete)
```

with Q positive definite. A singular operator or a solved P that is not
positive definite is a refusal.

## Charts

For `x' = T x` with invertible T,

```text
P' = T^{-T} P T^{-1},    A' = T A T^{-1}.
```

Then `V'(x') = V(x)` and the scalar decrease is unchanged. Raw
Frobenius norms of P are not invariant. This package does not apply
JSPT's condition cap; a singular T is refused by a failed solve.

## What is not claimed

Vertex checks on an affine plant are a sufficient common-quadratic
test. They are not necessary. Spectral abscissa and spectral radius
are diagnostics. A Hurwitz matrix without a supplied or solved P is
not a certificate. Trajectory finite differences of V are not a
certificate.
