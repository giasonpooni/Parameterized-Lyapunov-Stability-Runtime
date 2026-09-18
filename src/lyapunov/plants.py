"""Declared linear plants. A is an input, never formed here."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from .linalg import Array, as_square, as_vector, immutable


@dataclass(frozen=True)
class LinearPlant:
    """Time-invariant linear plant ``dx/dt = A x`` or ``x+ = A x``.

    ``A`` is supplied by the caller. This package does not differentiate
    a nonlinear ``f`` and does not own ``J_f(x*)``.
    """

    name: str
    A: Array
    time: str = "continuous"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.time not in {"continuous", "discrete"}:
            raise ValueError("time must be 'continuous' or 'discrete'")
        A = as_square(self.A, "A")
        object.__setattr__(self, "A", immutable(A))

    @property
    def dim(self) -> int:
        return int(self.A.shape[0])

    def matrix(self, theta: ArrayLike | None = None) -> Array:
        if theta is not None and np.asarray(theta).size:
            raise ValueError(f"{self.name} does not accept a parameter")
        return self.A


@dataclass(frozen=True)
class AffinePlant:
    """Affine-parameter plant ``A(theta) = A0 + sum theta_i A_i``.

    ``theta`` lives in a declared box. For a common quadratic (constant P)
    the corners are a sufficient test of the box, because the decrease form
    is then affine in ``theta``. For an affine ``P(theta)`` the form is
    quadratic in ``theta`` and the corners are evaluation sites only, not a
    box certificate. Rate bounds, when present, bound ``theta_dot`` for
    continuous-time PDLFs; the rate corners do bound the rate box.
    """

    name: str
    A0: Array
    terms: tuple[Array, ...]
    theta_min: Array
    theta_max: Array
    rate_min: Array
    rate_max: Array
    time: str = "continuous"
    parameter_names: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if self.time not in {"continuous", "discrete"}:
            raise ValueError("time must be 'continuous' or 'discrete'")
        A0 = as_square(self.A0, "A0")
        n = A0.shape[0]
        terms = tuple(as_square(term, f"A[{i}]") for i, term in enumerate(self.terms))
        for term in terms:
            if term.shape != (n, n):
                raise ValueError("every A_i must match A0")
        p = len(terms)
        theta_min = as_vector(self.theta_min, "theta_min")
        theta_max = as_vector(self.theta_max, "theta_max")
        rate_min = as_vector(self.rate_min, "rate_min")
        rate_max = as_vector(self.rate_max, "rate_max")
        if theta_min.size != p or theta_max.size != p:
            raise ValueError("parameter bounds must match the number of terms")
        if np.any(theta_max < theta_min):
            raise ValueError("theta_max must be at least theta_min")
        if rate_min.size != p or rate_max.size != p:
            raise ValueError("rate bounds must match the number of terms")
        if np.any(rate_max < rate_min):
            raise ValueError("rate_max must be at least rate_min")
        if self.parameter_names and len(self.parameter_names) != p:
            raise ValueError("parameter_names length must match the number of terms")
        object.__setattr__(self, "A0", immutable(A0))
        object.__setattr__(self, "terms", tuple(immutable(term) for term in terms))
        object.__setattr__(self, "theta_min", immutable(theta_min))
        object.__setattr__(self, "theta_max", immutable(theta_max))
        object.__setattr__(self, "rate_min", immutable(rate_min))
        object.__setattr__(self, "rate_max", immutable(rate_max))

    @property
    def dim(self) -> int:
        return int(self.A0.shape[0])

    @property
    def n_parameters(self) -> int:
        return len(self.terms)

    def require_theta(self, theta: ArrayLike) -> Array:
        value = as_vector(theta, "theta")
        if value.size != self.n_parameters:
            raise ValueError(
                f"{self.name}: expected {self.n_parameters} parameters, got {value.size}"
            )
        if np.any(value < self.theta_min - 1e-15) or np.any(value > self.theta_max + 1e-15):
            raise ValueError(f"{self.name}: theta is outside the declared box")
        return value

    def require_rate(self, theta_dot: ArrayLike) -> Array:
        value = as_vector(theta_dot, "theta_dot")
        if value.size != self.n_parameters:
            raise ValueError(
                f"{self.name}: expected {self.n_parameters} rates, got {value.size}"
            )
        if np.any(value < self.rate_min - 1e-15) or np.any(value > self.rate_max + 1e-15):
            raise ValueError(f"{self.name}: theta_dot is outside the declared rate box")
        return value

    def matrix(self, theta: ArrayLike) -> Array:
        weights = self.require_theta(theta)
        value = self.A0.copy()
        for weight, term in zip(weights, self.terms, strict=True):
            value = value + weight * term
        return value

    def vertices(self) -> tuple[Array, ...]:
        p = self.n_parameters
        corners: list[Array] = []

        def walk(index: int, acc: list[float]) -> None:
            if index == p:
                corners.append(np.asarray(acc, dtype=float))
                return
            walk(index + 1, acc + [float(self.theta_min[index])])
            if float(self.theta_max[index]) != float(self.theta_min[index]):
                walk(index + 1, acc + [float(self.theta_max[index])])

        walk(0, [])
        return tuple(corners)

    def rate_vertices(self) -> tuple[Array, ...]:
        p = self.n_parameters
        corners: list[Array] = []

        def walk(index: int, acc: list[float]) -> None:
            if index == p:
                corners.append(np.asarray(acc, dtype=float))
                return
            walk(index + 1, acc + [float(self.rate_min[index])])
            if float(self.rate_max[index]) != float(self.rate_min[index]):
                walk(index + 1, acc + [float(self.rate_max[index])])

        walk(0, [])
        return tuple(corners)


Plant = LinearPlant | AffinePlant


def constant_plant(
    A: ArrayLike,
    *,
    name: str = "A",
    time: str = "continuous",
    notes: str = "",
) -> LinearPlant:
    return LinearPlant(name=name, A=as_square(A, "A"), time=time, notes=notes)


def affine_box_plant(
    A0: ArrayLike,
    terms: Sequence[ArrayLike],
    theta_min: ArrayLike,
    theta_max: ArrayLike,
    *,
    name: str = "A(theta)",
    time: str = "continuous",
    rate_min: ArrayLike | None = None,
    rate_max: ArrayLike | None = None,
    parameter_names: tuple[str, ...] = (),
    notes: str = "",
) -> AffinePlant:
    packed = tuple(np.asarray(term, dtype=float) for term in terms)
    p = len(packed)
    if rate_min is None:
        rate_min = np.zeros(p)
    if rate_max is None:
        rate_max = np.zeros(p)
    return AffinePlant(
        name=name,
        A0=np.asarray(A0, dtype=float),
        terms=packed,
        theta_min=np.asarray(theta_min, dtype=float),
        theta_max=np.asarray(theta_max, dtype=float),
        rate_min=np.asarray(rate_min, dtype=float),
        rate_max=np.asarray(rate_max, dtype=float),
        time=time,
        parameter_names=parameter_names,
        notes=notes,
    )


def plant_from_jacobian(
    jacobian_at_equilibrium: ArrayLike,
    *,
    name: str = "A=J(x*)",
    time: str = "continuous",
    notes: str = "A supplied as J_f(x*); formed outside this package.",
) -> LinearPlant:
    """Accept ``A = J_f(x*)`` from JSPT or any other source.

    The Jacobian is not computed here. Passing a callable is refused so
    this package cannot become a second finite-difference helper.
    """
    if isinstance(jacobian_at_equilibrium, Mapping) or callable(jacobian_at_equilibrium):
        raise TypeError("pass the matrix A = J_f(x*), not a model or a callable")
    return constant_plant(
        jacobian_at_equilibrium,
        name=name,
        time=time,
        notes=notes,
    )
