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


def check_decrease(
    plant: Plant,
    certificate: Certificate,
    *,
    theta: ArrayLike | None = None,
    theta_dot: ArrayLike | None = None,
    atol: float = 0.0,
) -> CheckResult:
    """Require the decrease matrix to be negative definite at one parameter."""
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
    """Evaluate positivity and decrease at every declared (theta, theta_dot) corner."""
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
    return CheckResult(
        name=f"vertices:{plant.name}:{certificate.name}",
        passed=passed,
        residual=worst,
        details=f"{checked} corners, {failures} failed; worst {worst_label} max eig(M)={worst:.3e}",
        extra={"corners": float(checked), "failures": float(failures), "worst": worst},
    )


def check_chart_invariance(
    plant: LinearPlant,
    certificate: QuadraticCertificate,
    chart: LinearChart,
    x: ArrayLike,
    *,
    atol: float = 1e-10,
    rtol: float = 1e-9,
) -> CheckResult:
    """V and the scalar decrease must be invariant under x' = T x."""
    sample = evaluate(plant, certificate, x)
    primed_plant = push_plant(plant, chart)
    primed_cert = push_certificate(certificate, chart)
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
    atol: float = 1e-8,
    rtol: float = 1e-8,
) -> CheckResult:
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
