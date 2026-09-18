"""Acceptance tests for certificate structure, not derivative estimates."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from .certificates import AffineCertificate, Certificate, QuadraticCertificate
from .charts import LinearChart, push_certificate, push_plant
from .constitution import MIN_DECREASE_MARGIN
from .equation import decrease_matrix
from .linalg import hermitian_eigvals
from .plants import AffinePlant, LinearPlant, Plant
from .runtime import evaluate


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    residual: float
    details: str
    extra: dict[str, float]

    def raise_for_failure(self) -> None:
        if not self.passed:
            raise AssertionError(f"{self.name} failed: {self.details}")


def _require_tightening(atol: float) -> float:
    """``atol`` may only tighten a test, never loosen one.

    GATE.md: no backend may expose the identities as kwargs that change the
    law. A negative ``atol`` would turn a refusal into a pass, so it is
    refused rather than clipped.
    """
    if isinstance(atol, bool) or not isinstance(atol, (int, float, np.floating, np.integer)):
        raise ValueError(f"atol must be a real number; got {type(atol).__name__}")
    value = float(atol)
    if not np.isfinite(value) or value < 0.0:
        raise ValueError(f"atol must be finite and non-negative; got {atol!r}")
    return value


DEFAULT_EQUATION_ATOL = 1e-8
DEFAULT_EQUATION_RTOL = 1e-8
DEFAULT_CHART_ATOL = 1e-10
DEFAULT_CHART_RTOL = 1e-9


def _require_no_looser(value: float, default: float, name: str) -> float:
    """A tolerance may be made stricter, never weaker than its declared default.

    ``check_equation_residual(..., rtol=1e300)`` would otherwise report
    passed=True for any P at all, which is a kwarg that changes the law.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float, np.floating, np.integer)):
        raise ValueError(f"{name} must be a real number; got {type(value).__name__}")
    number = float(value)
    if not np.isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be finite and non-negative; got {value!r}")
    if number > default:
        raise ValueError(
            f"{name}={number:.3e} is looser than the declared {default:.3e}; "
            "a tolerance may only tighten a test"
        )
    return number


def check_decrease(
    plant: Plant,
    certificate: Certificate,
    *,
    theta: ArrayLike | None = None,
    theta_dot: ArrayLike | None = None,
    atol: float = 0.0,
) -> CheckResult:
    """Require the decrease matrix to be negative definite at one parameter.

    ``atol`` only tightens the margin. A negative ``atol`` is refused.
    """
    atol = _require_tightening(atol)
    dummy = np.ones(plant.dim)
    sample = evaluate(plant, certificate, dummy, theta=theta, theta_dot=theta_dot)
    residual = sample.max_decrease + atol
    passed = sample.min_P > 0.0 and sample.max_decrease < -MIN_DECREASE_MARGIN - atol
    return CheckResult(
        name=f"decrease:{plant.name}:{certificate.name}",
        passed=passed,
        residual=residual,
        details=(
            f"min eig(P)={sample.min_P:.3e}, max eig(M)={sample.max_decrease:.3e}"
        ),
        extra={"min_P": sample.min_P, "max_decrease": sample.max_decrease},
    )


def check_vertices(
    plant: AffinePlant,
    certificate: Certificate,
    *,
    include_rates: bool = True,
    atol: float = 0.0,
) -> CheckResult:
    """Evaluate positivity and decrease at every declared (theta, theta_dot) corner.

    With a constant ``P`` the largest eigenvalue of the decrease family is
    convex in ``theta``, so it attains its box maximum at a corner and the
    corners are a sufficient common-quadratic test. That holds in discrete
    time too, where the form is quadratic in ``theta`` but the maximum is
    still a maximum of convex functions -- the degree in ``theta`` is not
    what decides it. With an ``AffineCertificate`` the convexity is lost and
    the corners are only the declared sample set, not a sufficient test for
    the box. That limit is reported, never hidden.
    """
    atol = _require_tightening(atol)
    worst = -np.inf
    worst_label = ""
    failures = 0
    checked = 0
    for theta in plant.vertices():
        rates: tuple[ArrayLike | None, ...]
        if plant.time == "continuous" and include_rates and isinstance(certificate, AffineCertificate):
            rates = plant.rate_vertices()
        else:
            rates = (None,)
        for theta_dot in rates:
            checked += 1
            result = check_decrease(
                plant,
                certificate,
                theta=theta,
                theta_dot=theta_dot,
                atol=atol,
            )
            if result.extra["max_decrease"] > worst:
                worst = result.extra["max_decrease"]
                worst_label = f"theta={np.asarray(theta).tolist()} rate={None if theta_dot is None else np.asarray(theta_dot).tolist()}"
            if not result.passed:
                failures += 1
    passed = failures == 0 and checked > 0
    sufficient = isinstance(certificate, QuadraticCertificate)
    claim = (
        "sufficient common-quadratic test on the declared box"
        if sufficient
        else "declared corners only; NOT sufficient for the box (P(theta) makes the "
        "decrease form quadratic in theta)"
    )
    return CheckResult(
        name=f"vertices:{plant.name}:{certificate.name}",
        passed=passed,
        residual=worst,
        details=(
            f"{checked} corners, {failures} failed; worst {worst_label} "
            f"max eig(M)={worst:.3e}; {claim}"
        ),
        extra={
            "corners": float(checked),
            "failures": float(failures),
            "worst": worst,
            "sufficient_for_box": float(sufficient),
        },
    )


def check_chart_invariance(
    plant: LinearPlant,
    certificate: QuadraticCertificate,
    chart: LinearChart,
    x: ArrayLike,
    *,
    atol: float = DEFAULT_CHART_ATOL,
    rtol: float = DEFAULT_CHART_RTOL,
) -> CheckResult:
    """V and the scalar decrease must be invariant under x' = T x.

    A chart this package accepts can still push a certificate out of float64:
    at a high condition number the computed ``P'`` may not be positive
    definite even though the exact congruence is. That is a refusal, and it
    is reported here as a failed check rather than raised, so a caller
    sweeping charts sees it the same way as any other failure. The refusal
    itself still stands in ``push_certificate``.
    """
    atol = _require_no_looser(atol, DEFAULT_CHART_ATOL, "atol")
    rtol = _require_no_looser(rtol, DEFAULT_CHART_RTOL, "rtol")
    sample = evaluate(plant, certificate, x)
    try:
        primed_plant = push_plant(plant, chart)
        primed_cert = push_certificate(certificate, chart)
    except ValueError as exc:
        return CheckResult(
            name=f"chart:{plant.name}:{chart.name}",
            passed=False,
            residual=float("inf"),
            details=f"chart push refused: {exc}",
            extra={
                "value_gap": float("inf"),
                "decrease_gap": float("inf"),
                "P_frobenius_ratio": float("nan"),
            },
        )
    x_prime = chart.T @ np.asarray(x, dtype=float)
    primed = evaluate(primed_plant, primed_cert, x_prime)
    value_gap = abs(sample.value - primed.value)
    decrease_gap = abs(sample.decrease - primed.decrease)
    residual = max(value_gap, decrease_gap)
    scale = max(abs(sample.value), abs(sample.decrease), 1e-16)
    passed = residual <= atol + rtol * scale
    return CheckResult(
        name=f"chart:{plant.name}:{chart.name}",
        passed=passed,
        residual=residual,
        details=(
            f"V gap={value_gap:.3e}, decrease gap={decrease_gap:.3e}; "
            f"unscaled ||P||_F={float(np.linalg.norm(certificate.P, 'fro')):.3e} "
            f"vs ||P'||_F={float(np.linalg.norm(primed_cert.P, 'fro')):.3e}"
        ),
        extra={
            "value_gap": value_gap,
            "decrease_gap": decrease_gap,
            "P_frobenius_ratio": float(
                np.linalg.norm(primed_cert.P, "fro")
                / max(np.linalg.norm(certificate.P, "fro"), 1e-16)
            ),
        },
    )


def check_equation_residual(
    plant: LinearPlant,
    certificate: QuadraticCertificate,
    Q: ArrayLike,
    *,
    atol: float = DEFAULT_EQUATION_ATOL,
    rtol: float = DEFAULT_EQUATION_RTOL,
) -> CheckResult:
    atol = _require_no_looser(atol, DEFAULT_EQUATION_ATOL, "atol")
    rtol = _require_no_looser(rtol, DEFAULT_EQUATION_RTOL, "rtol")
    Q_mat = np.asarray(Q, dtype=float)
    residual_matrix = decrease_matrix(plant.A, certificate.P, time=plant.time) + Q_mat
    residual = float(np.max(np.abs(residual_matrix)))
    scale = max(float(np.max(np.abs(Q_mat))), 1e-16)
    passed = residual <= atol + rtol * scale
    return CheckResult(
        name=f"equation:{plant.name}:{certificate.name}",
        passed=passed,
        residual=residual,
        details=f"max |A-form + Q|={residual:.3e}",
        extra={"relative": residual / scale},
    )


def spectral_radius(A: ArrayLike) -> float:
    return float(np.max(np.abs(np.linalg.eigvals(np.asarray(A, dtype=float)))))


def spectral_abscissa(A: ArrayLike) -> float:
    return float(np.max(np.real(np.linalg.eigvals(np.asarray(A, dtype=float)))))


def check_spectrum_agrees_with_certificate(
    plant: LinearPlant,
    certificate: QuadraticCertificate,
) -> CheckResult:
    """Spectrum is a diagnostic. The certificate is the claim.

    A certified continuous plant must have negative spectral abscissa.
    A certified discrete plant must have spectral radius < 1. The
    converse is not checked: a Hurwitz A without a supplied P is not a
    certificate.
    """
    form = decrease_matrix(plant.A, certificate.P, time=plant.time)
    max_decrease = float(np.max(hermitian_eigvals(form)))
    if plant.time == "continuous":
        diagnostic = spectral_abscissa(plant.A)
        consistent = not (max_decrease < 0.0 and diagnostic >= 0.0)
        details = f"abscissa={diagnostic:.3e}, max eig(M)={max_decrease:.3e}"
    else:
        diagnostic = spectral_radius(plant.A)
        consistent = not (max_decrease < 0.0 and diagnostic >= 1.0)
        details = f"radius={diagnostic:.3e}, max eig(M)={max_decrease:.3e}"
    return CheckResult(
        name=f"spectrum:{plant.name}",
        passed=consistent,
        residual=diagnostic,
        details=details,
        extra={"diagnostic": diagnostic, "max_decrease": max_decrease},
    )
