"""How a quadratic certificate transforms under a linear chart.

JSPT owns charts, k2(T), and the 1e12 cap. This module only pushes P
through an already-accepted invertible T so that V is invariant:

    x' = T x,    P' T = Y  with  T^T Y = P,    V'(x') = V(x).

A singular T is refused at construction by a rank test, and again by a
failed solve or a non-finite P' downstream. This is a refusal, not a rank
claim. There is no local condition cap and no nearest-PSD repair.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from .certificates import QuadraticCertificate
from .linalg import Array, as_square, immutable, require_spd
from .plants import LinearPlant


@dataclass(frozen=True)
class LinearChart:
    name: str
    T: Array

    def __post_init__(self) -> None:
        T = as_square(self.T, "T")
        # Rank, not determinant. det is scale-COVARIANT: det(cT) = c**n det(T),
        # so it underflows to 0.0 for a uniformly small T whose condition
        # number is exactly 1 -- and the worse the larger n is, because the
        # scale enters as the n-th power. At n=24 (MAX_KRONECKER_DIM) a
        # femto-scale unit chart 1e-15*I has det 0.0 and is perfectly
        # invertible. Rank is scale-INVARIANT and is the relational question
        # actually being asked: is dim(image) full? A search over exactly
        # rank-deficient matrices found no case the det clause caught that the
        # rank test did not, and many well-conditioned charts it refused.
        #
        # numpy's rank tolerance is smax*n*eps, the float64 definition of
        # singular, tracking machine epsilon. It is not a policy number and
        # not JSPT's 1e12 MAX_CONDITION_NUMBER; no such constant exists here
        # and a chart at condition 1e12 is accepted (tests/test_constitution).
        # This is a REFUSAL, not a rank measurement: no float64 predicate can
        # report a rank, because rank is integer-valued and upper
        # semi-continuous, so every implementation must pick a threshold. The
        # exact, threshold-free version of this question lives in the i64
        # guest as unimodularity, det T in {+1,-1}.
        if np.linalg.matrix_rank(T) < T.shape[0]:
            raise ValueError("T must be invertible")
        object.__setattr__(self, "T", immutable(T))

    @property
    def dim(self) -> int:
        return int(self.T.shape[0])

    @classmethod
    def scale(cls, factors: ArrayLike, *, name: str = "scale") -> LinearChart:
        diag = np.asarray(factors, dtype=float)
        if diag.ndim != 1:
            raise ValueError("scale factors must be a 1-D vector")
        return cls(name=name, T=np.diag(diag))


def push_certificate(certificate: QuadraticCertificate, chart: LinearChart) -> QuadraticCertificate:
    if certificate.dim != chart.dim:
        raise ValueError("chart T does not match the certificate")
    # T^T Y = P, then P' T = Y  =>  P' = T^{-T} P T^{-1} without forming inverses.
    try:
        Y = np.linalg.solve(chart.T.T, certificate.P)
        primed = np.linalg.solve(chart.T.T, Y.T).T
    except np.linalg.LinAlgError as exc:
        raise ValueError("T is not invertible; refused without a condition cap") from exc
    # P' = T^-T P T^-1 is exactly symmetric whenever P is, and certificate.P
    # was already required symmetric when the certificate was declared. So any
    # skew here is roundoff from the two solves, of order eps*||P'||. That
    # grows with the UNIT SCALE of T and not with its conditioning: a chart at
    # condition 2.3 is refused by an absolute SYMMETRY_ATOL once T is small
    # enough that P' reaches ~1e12. SYMMETRY_ATOL guards a P the caller
    # DECLARED; this congruence is one this package just computed, so project
    # the roundoff skew out, exactly as decrease_matrix already does for the
    # forms it builds. This is not a repair of an input.
    primed = 0.5 * (primed + primed.T)
    primed = require_spd(primed, "P'")
    return QuadraticCertificate(
        name=f"{certificate.name}[{chart.name}]",
        P=primed,
        notes=f"pushed through {chart.name}",
    )


def push_plant(plant: LinearPlant, chart: LinearChart) -> LinearPlant:
    if plant.dim != chart.dim:
        raise ValueError("chart T does not match the plant")
    try:
        # A' = T A T^{-1}
        primed = chart.T @ np.linalg.solve(chart.T.T, plant.A.T).T
    except np.linalg.LinAlgError as exc:
        raise ValueError("T is not invertible; refused without a condition cap") from exc
    return LinearPlant(
        name=f"{plant.name}[{chart.name}]",
        A=primed,
        time=plant.time,
        notes=f"similarity through {chart.name}",
    )
