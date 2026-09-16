from __future__ import annotations

import numpy as np

from lyapunov.certificates import quadratic
from lyapunov.checks import check_decrease, check_vertices
from lyapunov.equation import solve_lyapunov
from lyapunov.reference_plants import two_vertex_lpv


def test_identity_is_a_common_quadratic():
    plant = two_vertex_lpv()
    cert = quadratic(np.eye(2), name="P=I")
    check_decrease(plant, cert, theta=[0.5], theta_dot=[0.0]).raise_for_failure()
    check_vertices(plant, cert, include_rates=False).raise_for_failure()


def test_midpoint_solve_also_covers_vertices():
    plant = two_vertex_lpv()
    cert = solve_lyapunov(plant.matrix([0.5]), time="continuous", name="V-mid")
    check_vertices(plant, cert, include_rates=False).raise_for_failure()
