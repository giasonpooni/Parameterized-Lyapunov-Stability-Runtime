"""Evaluate a certificate at a live (x, theta, theta_dot). This is the runtime."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from .certificates import AffineCertificate, Certificate, QuadraticCertificate
from .constitution import MIN_DECREASE_MARGIN
from .equation import decrease_matrix
from .linalg import Array, as_vector, hermitian_eigvals
from .plants import AffinePlant, LinearPlant, Plant


@dataclass(frozen=True)
class CertificateSample:
    value: float
    decrease: float
    decrease_matrix: Array
    P: Array
    A: Array
    theta: Array | None
    theta_dot: Array | None
    min_P: float
    max_decrease: float


@dataclass(frozen=True)
class Verdict:
    status: str
    sample: CertificateSample
    details: str

    @property
    def certified(self) -> bool:
        return self.status == "certified"


def _plant_matrix(plant: Plant, theta: ArrayLike | None) -> Array:
    if isinstance(plant, LinearPlant):
        return plant.matrix(theta)
    if theta is None:
        raise ValueError(f"{plant.name} requires theta")
    return plant.matrix(theta)


def _certificate_matrix(certificate: Certificate, theta: ArrayLike | None) -> Array:
    if isinstance(certificate, QuadraticCertificate):
        return certificate.matrix(theta)
    if theta is None:
        raise ValueError(f"{certificate.name} requires theta")
    return certificate.matrix(theta)


def _parameter_rate(certificate: Certificate, theta_dot: ArrayLike | None) -> Array | None:
    if isinstance(certificate, QuadraticCertificate):
        # Common quadratic: Pdot = 0 even if the plant has a rate bound.
        return None
    if theta_dot is None:
        raise ValueError(f"{certificate.name} requires theta_dot in continuous time")
    rate = as_vector(theta_dot, "theta_dot")
    if rate.size != certificate.n_parameters:
        raise ValueError("theta_dot does not match the certificate")
    total = np.zeros_like(certificate.P0)
    for weight, term in zip(rate, certificate.terms, strict=True):
        total = total + weight * term
    return total


def evaluate(
    plant: Plant,
    certificate: Certificate,
    x: ArrayLike,
    *,
    theta: ArrayLike | None = None,
    theta_dot: ArrayLike | None = None,
) -> CertificateSample:
    """Return V and the quadratic decrease form at one sample.

    The decrease is the certificate form, not a finite difference of V
    along a simulated trajectory.
    """
    if certificate.dim != plant.dim:
        raise ValueError("certificate and plant dimensions differ")
    state = as_vector(x, "x")
    if state.size != plant.dim:
        raise ValueError("state dimension does not match the plant")
    if isinstance(plant, AffinePlant) and theta is not None:
        plant.require_theta(theta)
        if theta_dot is not None:
            plant.require_rate(theta_dot)
    A = _plant_matrix(plant, theta)
    P = _certificate_matrix(certificate, theta)
    P_rate = None
    if plant.time == "continuous":
        P_rate = _parameter_rate(certificate, theta_dot)
    elif theta_dot is not None and np.asarray(theta_dot).size:
        raise ValueError("discrete plants do not take theta_dot")
    form = decrease_matrix(A, P, time=plant.time, P_rate=P_rate)
    value = float(state @ P @ state)
    decrease = float(state @ form @ state)
    theta_vec = None if theta is None else as_vector(theta, "theta")
    rate_vec = None if theta_dot is None else as_vector(theta_dot, "theta_dot")
    return CertificateSample(
        value=value,
        decrease=decrease,
        decrease_matrix=form,
        P=P,
        A=A,
        theta=theta_vec,
        theta_dot=rate_vec,
        min_P=float(np.min(hermitian_eigvals(P))),
        max_decrease=float(np.max(hermitian_eigvals(form))),
    )


def verdict(
    plant: Plant,
    certificate: Certificate,
    x: ArrayLike,
    *,
    theta: ArrayLike | None = None,
    theta_dot: ArrayLike | None = None,
    level: float | None = None,
) -> Verdict:
    """Classify one sample against the certificate inequalities.

    certified means this sample is inside the claimed decrease and
    positivity. It is not a global proof unless the sample set is the
    declared vertex set of an affine problem whose inequalities are
    jointly convex in the usual LPV sense.
    """
    sample = evaluate(plant, certificate, x, theta=theta, theta_dot=theta_dot)
    if sample.min_P <= 0.0:
        return Verdict("violated", sample, f"P is not positive definite; min eig={sample.min_P:.3e}")
    if sample.value < 0.0:
        return Verdict("violated", sample, f"V={sample.value:.3e} is negative")
    if level is not None and sample.value > level:
        return Verdict(
            "outside-level",
            sample,
            f"V={sample.value:.3e} exceeds level {level:.3e}",
        )
    if sample.max_decrease > -MIN_DECREASE_MARGIN:
        if abs(sample.max_decrease) <= 1e-14 and np.allclose(x, 0.0):
            return Verdict("certified", sample, "equilibrium sample; V=0 and decrease=0")
        if sample.decrease >= 0.0 and not np.allclose(x, 0.0):
            return Verdict(
                "violated",
                sample,
                f"decrease form is not negative; max eig={sample.max_decrease:.3e}, "
                f"x^T M x={sample.decrease:.3e}",
            )
        return Verdict(
            "inconclusive",
            sample,
            f"decrease matrix is not negative definite; max eig={sample.max_decrease:.3e}",
        )
    return Verdict(
        "certified",
        sample,
        f"V={sample.value:.3e}, decrease={sample.decrease:.3e}, "
        f"max eig(M)={sample.max_decrease:.3e}",
    )
