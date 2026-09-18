"""Lyapunov equations. Certificates are constructed here; A is given."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .certificates import QuadraticCertificate
from .constitution import (
    MAX_KRONECKER_DIM,
    RESIDUAL_BACKWARD_FACTOR,
    RESIDUAL_CAP_RELATIVE,
    RESIDUAL_FLOOR_RELATIVE,
)
from .linalg import Array, as_square, require_spd, require_symmetric
from .plants import LinearPlant


def _half_vector_basis(dim: int) -> tuple[list[tuple[int, int]], int]:
    pairs = [(i, j) for i in range(dim) for j in range(i, dim)]
    return pairs, len(pairs)


def _pack_symmetric(matrix: Array) -> Array:
    dim = matrix.shape[0]
    pairs, count = _half_vector_basis(dim)
    packed = np.empty(count, dtype=float)
    for index, (i, j) in enumerate(pairs):
        packed[index] = matrix[i, j]
    return packed


def _unpack_symmetric(packed: Array, dim: int) -> Array:
    pairs, _ = _half_vector_basis(dim)
    matrix = np.zeros((dim, dim), dtype=float)
    for value, (i, j) in zip(packed, pairs, strict=True):
        matrix[i, j] = value
        matrix[j, i] = value
    return matrix


def _continuous_operator(A: Array) -> Array:
    dim = A.shape[0]
    pairs, count = _half_vector_basis(dim)
    operator = np.zeros((count, count), dtype=float)
    for col, (p, q) in enumerate(pairs):
        basis = np.zeros((dim, dim), dtype=float)
        basis[p, q] = 1.0
        basis[q, p] = 1.0
        image = A.T @ basis + basis @ A
        for row, (i, j) in enumerate(pairs):
            operator[row, col] = image[i, j]
    return operator


def _discrete_operator(A: Array) -> Array:
    dim = A.shape[0]
    pairs, count = _half_vector_basis(dim)
    operator = np.zeros((count, count), dtype=float)
    for col, (p, q) in enumerate(pairs):
        basis = np.zeros((dim, dim), dtype=float)
        basis[p, q] = 1.0
        basis[q, p] = 1.0
        image = A.T @ basis @ A - basis
        for row, (i, j) in enumerate(pairs):
            operator[row, col] = image[i, j]
    return operator


def decrease_matrix(
    A: ArrayLike,
    P: ArrayLike,
    *,
    time: str = "continuous",
    P_rate: ArrayLike | None = None,
) -> Array:
    """Return the quadratic form matrix of Vdot or Delta V.

    Continuous: A^T P + P A + P_rate.
    Discrete: A^T P A - P. Discrete certificates do not take a P_rate.
    """
    A_mat = as_square(A, "A")
    P_mat = require_symmetric(P, "P")
    if A_mat.shape != P_mat.shape:
        raise ValueError("A and P must have the same shape")
    if time == "continuous":
        form = A_mat.T @ P_mat + P_mat @ A_mat
        if P_rate is not None:
            form = form + require_symmetric(P_rate, "P_rate")
        return 0.5 * (form + form.T)
    if time == "discrete":
        if P_rate is not None:
            raise ValueError("discrete certificates do not take a parameter rate")
        form = A_mat.T @ P_mat @ A_mat - P_mat
        return 0.5 * (form + form.T)
    raise ValueError("time must be 'continuous' or 'discrete'")


def solve_lyapunov(
    A: ArrayLike,
    Q: ArrayLike | None = None,
    *,
    time: str = "continuous",
    name: str = "V",
) -> QuadraticCertificate:
    """Solve the Lyapunov equation for a constant quadratic certificate.

    Continuous: A^T P + P A + Q = 0.
    Discrete: A^T P A - P + Q = 0.

    Q defaults to I. The solve is on the symmetric subspace.
    Failure to produce a positive-definite P is a refused certificate,
    not a repaired one.
    """
    A_mat = as_square(A, "A")
    dim = A_mat.shape[0]
    if dim > MAX_KRONECKER_DIM:
        raise ValueError(
            f"Lyapunov solve is limited to dim <= {MAX_KRONECKER_DIM}; got {dim}"
        )
    if Q is None:
        Q_mat = np.eye(dim)
    else:
        Q_mat = require_spd(Q, "Q")
        if Q_mat.shape != (dim, dim):
            raise ValueError("Q must match A")
    if time == "continuous":
        operator = _continuous_operator(A_mat)
    elif time == "discrete":
        operator = _discrete_operator(A_mat)
    else:
        raise ValueError("time must be 'continuous' or 'discrete'")
    rhs = -_pack_symmetric(Q_mat)
    try:
        packed = np.linalg.solve(operator, rhs)
    except np.linalg.LinAlgError as exc:
        raise ValueError("Lyapunov operator is singular; no unique certificate") from exc
    P = _unpack_symmetric(packed, dim)
    P = require_spd(P, "solved P")
    residual = decrease_matrix(A_mat, P, time=time) + Q_mat
    residual_max = float(np.max(np.abs(residual)))
    # This gate asks one question: did the linear solve actually resolve the
    # equation? A backward-stable solve leaves a residual of order
    # eps * ||operator|| * ||P||, so the tolerance has to carry that term.
    # Scaling by ||Q|| alone refuses correct certificates on badly scaled but
    # perfectly stable plants: A = [[-1e-5, 1], [0, -1e-5]] gives a positive
    # definite P with a RELATIVE residual of 5e-12 and an absolute one of
    # 1e-7, which the old gate called a failure.
    # The backward term alone is not enough. For an ill-conditioned operator
    # it grows without bound, and a residual that large says nothing: the
    # equation is A^T P + P A = -Q, so once the residual approaches ||Q|| the
    # identity is not recovered at all. Cap the tolerance at recovering Q to
    # six digits. Between the two, this is never tighter than the old gate,
    # so no solve accepted before is refused now, and never looser than a
    # meaningful forward error.
    q_scale = max(1.0, float(np.max(np.abs(Q_mat))))
    backward = (
        RESIDUAL_BACKWARD_FACTOR
        * float(np.finfo(float).eps)
        * float(np.max(np.abs(operator)))
        * float(np.max(np.abs(P)))
    )
    # Clamped, so in practice the floor binds for well-scaled plants, the
    # backward term binds for ||P|| roughly 1e5 to 1e7, and the cap binds
    # beyond that.
    tolerance = min(
        max(RESIDUAL_FLOOR_RELATIVE * q_scale, backward),
        RESIDUAL_CAP_RELATIVE * q_scale,
    )
    if residual_max > tolerance:
        raise ValueError(
            f"Lyapunov residual {residual_max:.3e} exceeds tolerance "
            f"{tolerance:.3e}; the equation is not resolvable in float64 at "
            "this scale"
        )
    return QuadraticCertificate(
        name=name,
        P=P,
        notes=f"solved {time} Lyapunov equation against declared Q",
    )


def certificate_for_plant(
    plant: LinearPlant,
    Q: ArrayLike | None = None,
    *,
    name: str | None = None,
) -> QuadraticCertificate:
    return solve_lyapunov(
        plant.A,
        Q,
        time=plant.time,
        name=name or f"V[{plant.name}]",
    )
