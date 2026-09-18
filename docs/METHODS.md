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
JSPT's condition cap; a singular T is refused at chart construction by a
rank test, and again downstream by a failed solve or a non-finite `P'`.

The test is rank, not determinant, and that choice is structural rather
than a tuning preference. Invertibility is a *relational* question -- is
`dim(image)` full? -- and a determinant answers it only up to scale, since
`det(cT) = c^n det(T)`. A uniformly small chart therefore underflows to
`det = 0` while its condition number is exactly 1, and the failure grows
with `n` because the scale enters as the n-th power: at `n = 24` a
femto-scale unit chart `1e-15 * I` has `det = 0.0` and is perfectly
invertible. Rank is scale-invariant and does not have that failure.

What rank cannot do is be exact. It is integer-valued and upper
semi-continuous, so it is not a continuous function of the matrix, and
every float64 implementation must choose a threshold. NumPy's is
`smax * n * eps`, the float64 definition of singular -- it tracks machine
epsilon rather than naming a policy number, which is why it is not
JSPT's `MAX_CONDITION_NUMBER`; a chart at condition 1e12 is accepted.

Accepting a chart is not a promise that the pushforward survives. There is
no policy cap, so a chart at condition 1e12 is constructed and pushed; but
`P'` is then computed in float64, and at that conditioning a non-diagonal
chart can produce a `P'` that is not positive definite even though the exact
congruence is. That is refused, because a non-PD `P` is always refused and
there is no nearest-PSD repair. The refusal comes from the arithmetic
running out, not from a threshold anyone chose, and `check_chart_invariance`
reports it as a failed check rather than raising.

So this package makes a **refusal**, never a rank claim. The exact,
threshold-free form of the same question exists in the integer satellite,
where a chart is admitted only if it is unimodular, `det T` in `{+1, -1}`
over the integers. That predicate is total and needs no tolerance, and it
also pins scale, which is exactly the degree of freedom the float64
determinant loses. See [DISCRETE-GUEST-v1.md](DISCRETE-GUEST-v1.md).

## What is claimed, as a code

Every `CheckResult` carries a `claim` from a versioned vocabulary
(`lyapunov.claims`, `claim-codes-v1`), and the published reports print it.
A bare `passed=True` invites the reader to supply the claim, and the one
they supply is usually larger than the one the instrument made.

| code | what passing it means |
| --- | --- |
| `SUFFICIENT_COMMON_QUADRATIC` | a common quadratic held at every declared corner, and the corners bound the box |
| `DECLARED_SAMPLES_ONLY` | the declared sites held; nothing was shown about the rest of the box |
| `SAMPLE_DECREASE` | the decrease form was negative definite at one declared sample |
| `EQUATION_RESIDUAL` | a supplied P satisfies the equation against a declared Q |
| `CHART_INVARIANCE` | V and the scalar decrease survived a change of coordinates |
| `CHART_PUSH_REFUSED` | the chart was accepted, the pushforward left float64 |
| `SPECTRUM_DIAGNOSTIC` | the spectrum is consistent with the certificate |

`LPV_STABLE`, `STABLE`, `CERTIFIED_STABLE`, `NECESSARY`, `VERIFIED`, `SAFE`
and `AUTHORIZED` are listed in `claims.FORBIDDEN_CLAIMS` and refused by the
`CheckResult` constructor, so the prohibition is executable and not only
written down here.

## The parameter rate

`CertificateSample.P_rate` records the `Pdot` that actually entered the
decrease form: the affine sum for an `AffineCertificate`, the zero matrix
for a constant `P`, and `None` in discrete time, where the law admits no
rate term. A constant `P` has `Pdot = 0` because `P` does not depend on
`theta`, not because a declared rate was ignored, and a plant may declare
a `theta_dot` box that therefore never enters the arithmetic.
`check_vertices` says so in its details rather than leaving the bound
looking used.

## What is not claimed

Vertex checks on an affine plant are a sufficient common-quadratic
test. They are not necessary. Spectral abscissa and spectral radius
are diagnostics. A Hurwitz matrix without a supplied or solved P is
not a certificate. Trajectory finite differences of V are not a
certificate.
