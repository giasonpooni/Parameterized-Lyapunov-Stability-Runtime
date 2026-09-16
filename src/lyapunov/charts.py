"""How a quadratic certificate transforms under a linear chart.

JSPT owns charts, k2(T), and the 1e12 cap. This module only pushes P
through an already-accepted invertible T so that V is invariant:

    x' = T x,    P' T = Y  with  T^T Y = P,    V'(x') = V(x).

A singular T is refused by a failed solve. There is no local condition
cap and no nearest-PSD repair.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from .certificates import QuadraticCertificate
from .linalg import Array, as_square, require_spd
from .plants import LinearPlant


@dataclass(frozen=True)
class LinearChart:
    name: str
    T: Array

    def __post_init__(self) -> None:
        T = as_square(self.T, "T")
        if abs(float(np.linalg.det(T))) == 0.0 or np.linalg.matrix_rank(T) < T.shape[0]:
            raise ValueError("T must be invertible")
        object.__setattr__(self, "T", T)

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
