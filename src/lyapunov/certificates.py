"""Quadratic certificates. This package owns V, not A."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from .linalg import Array, as_vector, immutable, require_spd, require_symmetric


@dataclass(frozen=True)
class QuadraticCertificate:
    """``V(x) = x^T P x`` with a constant symmetric positive-definite P."""

    name: str
    P: Array
    notes: str = ""

    def __post_init__(self) -> None:
        P = require_spd(self.P, "P")
        object.__setattr__(self, "P", immutable(P))

    @property
    def dim(self) -> int:
        return int(self.P.shape[0])

    def matrix(self, theta: ArrayLike | None = None) -> Array:
        # A constant P is the common-quadratic case: theta schedules A, not V.
        return self.P

    def value(self, x: ArrayLike, theta: ArrayLike | None = None) -> float:
        vector = as_vector(x, "x")
        if vector.size != self.dim:
            raise ValueError(f"{self.name}: expected dim {self.dim}, got {vector.size}")
        return float(vector @ self.P @ vector)


@dataclass(frozen=True)
class AffineCertificate:
    """Affine parameter-dependent Lyapunov matrix ``P(theta) = P0 + sum theta_i P_i``.

    Each evaluation ``P(theta)`` must be positive definite. That is checked at
    use sites, not by claiming a global LMI that this package did not solve.
    """

    name: str
    P0: Array
    terms: tuple[Array, ...]
    notes: str = ""

    def __post_init__(self) -> None:
        P0 = require_symmetric(self.P0, "P0")
        terms = tuple(require_symmetric(term, f"P[{i}]") for i, term in enumerate(self.terms))
        n = P0.shape[0]
        for term in terms:
            if term.shape != (n, n):
                raise ValueError("every P_i must match P0")
        object.__setattr__(self, "P0", immutable(P0))
        object.__setattr__(self, "terms", tuple(immutable(term) for term in terms))

    @property
    def dim(self) -> int:
        return int(self.P0.shape[0])

    @property
    def n_parameters(self) -> int:
        return len(self.terms)

    def matrix(self, theta: ArrayLike) -> Array:
        weights = as_vector(theta, "theta")
        if weights.size != self.n_parameters:
            raise ValueError(
                f"{self.name}: expected {self.n_parameters} parameters, got {weights.size}"
            )
        value = self.P0.copy()
        for weight, term in zip(weights, self.terms, strict=True):
            value = value + weight * term
        return require_spd(value, f"P({self.name})")

    def value(self, x: ArrayLike, theta: ArrayLike) -> float:
        vector = as_vector(x, "x")
        if vector.size != self.dim:
            raise ValueError(f"{self.name}: expected dim {self.dim}, got {vector.size}")
        return float(vector @ self.matrix(theta) @ vector)


Certificate = QuadraticCertificate | AffineCertificate


def quadratic(P: ArrayLike, *, name: str = "V", notes: str = "") -> QuadraticCertificate:
    return QuadraticCertificate(name=name, P=np.asarray(P, dtype=float), notes=notes)


def affine_quadratic(
    P0: ArrayLike,
    terms: Sequence[ArrayLike],
    *,
    name: str = "V(theta)",
    notes: str = "",
) -> AffineCertificate:
    return AffineCertificate(
        name=name,
        P0=np.asarray(P0, dtype=float),
        terms=tuple(np.asarray(term, dtype=float) for term in terms),
        notes=notes,
    )
