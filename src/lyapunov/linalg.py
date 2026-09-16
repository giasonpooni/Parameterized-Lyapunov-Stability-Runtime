"""Shared array checks. No condition-number cap lives here."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .constitution import SYMMETRY_ATOL

Array = NDArray[np.floating]


def as_vector(value: ArrayLike, name: str = "x") -> Array:
    array = np.asarray(value, dtype=float)
    if array.ndim == 0:
        return array.reshape(1)
    if array.ndim != 1:
        raise ValueError(f"{name} must be a 1-D vector, got shape {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array


def as_square(value: ArrayLike, name: str) -> Array:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[0] != array.shape[1] or array.shape[0] < 1:
        raise ValueError(f"{name} must be a nonempty square matrix, got shape {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array


def require_symmetric(value: ArrayLike, name: str) -> Array:
    array = as_square(value, name)
    skew = array - array.T
    if float(np.max(np.abs(skew))) > SYMMETRY_ATOL:
        raise ValueError(f"{name} must be symmetric within {SYMMETRY_ATOL}")
    return 0.5 * (array + array.T)


def require_spd(value: ArrayLike, name: str) -> Array:
    array = require_symmetric(value, name)
    eigvals = np.linalg.eigvalsh(array)
    if float(np.min(eigvals)) <= 0.0:
        raise ValueError(f"{name} must be positive definite; min eigenvalue={float(np.min(eigvals)):.3e}")
    return array


def hermitian_eigvals(value: ArrayLike) -> Array:
    return np.linalg.eigvalsh(require_symmetric(value, "matrix"))


def immutable(value: Array) -> Array:
    return np.frombuffer(value.tobytes(order="C"), dtype=value.dtype).reshape(value.shape)
