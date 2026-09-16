"""Small declared plants used by the first-release examples and tests."""

from __future__ import annotations

import numpy as np

from .plants import AffinePlant, LinearPlant, affine_box_plant, constant_plant


def hurwitz2() -> LinearPlant:
    return constant_plant(
        [[-1.0, 2.0], [0.0, -3.0]],
        name="hurwitz2",
        time="continuous",
        notes="Strictly Hurwitz; a quadratic certificate exists.",
    )


def unstable2() -> LinearPlant:
    return constant_plant(
        [[0.2, 1.0], [0.0, 0.3]],
        name="unstable2",
        time="continuous",
        notes="Positive eigenvalues; the Lyapunov solve must refuse a PD P.",
    )


def discrete_contract() -> LinearPlant:
    angle = np.pi / 7.0
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=float,
    )
    return constant_plant(
        0.6 * rotation,
        name="discrete-contract",
        time="discrete",
        notes="Spectral radius 0.6; a discrete quadratic certificate exists.",
    )


def two_vertex_lpv() -> AffinePlant:
    """Hurwitz pair with an affine off-diagonal coupling.

    ``A(theta) = [[-1, theta], [0, -2]]`` on ``theta in [0, 1]``. A common
    quadratic ``P = I`` is a certificate at both vertices.
    """
    A0 = np.array([[-1.0, 0.0], [0.0, -2.0]], dtype=float)
    A1 = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=float)
    return affine_box_plant(
        A0,
        [A1],
        [0.0],
        [1.0],
        name="two-vertex-lpv",
        time="continuous",
        rate_min=[-0.5],
        rate_max=[0.5],
        parameter_names=("coupling",),
        notes="A(theta)=[[-1, theta],[0, -2]] on theta in [0,1] with |theta_dot|<=0.5.",
    )


def reference_catalogue() -> dict[str, LinearPlant | AffinePlant]:
    return {
        "hurwitz2": hurwitz2(),
        "unstable2": unstable2(),
        "discrete-contract": discrete_contract(),
        "two-vertex-lpv": two_vertex_lpv(),
    }
