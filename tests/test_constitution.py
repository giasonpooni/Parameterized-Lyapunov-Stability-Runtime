from __future__ import annotations

import numpy as np
import pytest

from lyapunov.certificates import quadratic
from lyapunov.charts import LinearChart, push_certificate
from lyapunov.constitution import MAX_KRONECKER_DIM, MIN_DECREASE_MARGIN, SYMMETRY_ATOL
from lyapunov.equation import solve_lyapunov
from lyapunov.plants import plant_from_jacobian


def test_constitution_values_are_frozen():
    assert SYMMETRY_ATOL == 1e-12
    assert MIN_DECREASE_MARGIN == 0.0
    assert MAX_KRONECKER_DIM == 24


def test_no_local_condition_cap_on_scale_charts():
    chart = LinearChart.scale([1e-6, 1e6], name="extreme-scale")
    cert = quadratic([[2.0, 0.1], [0.1, 3.0]])
    pushed = push_certificate(cert, chart)
    x = np.array([0.4, -1.2])
    assert abs(float(x @ cert.P @ x) - float((chart.T @ x) @ pushed.P @ (chart.T @ x))) < 1e-10


def test_singular_chart_is_refused_without_a_cap():
    with pytest.raises(ValueError, match="invertible"):
        LinearChart(name="singular", T=[[1.0, 0.0], [2.0, 0.0]])


def test_nonsymmetric_P_is_refused():
    with pytest.raises(ValueError, match="symmetric"):
        quadratic([[1.0, 2.0], [0.0, 1.0]])


def test_jacobian_callable_is_refused():
    with pytest.raises(TypeError, match="matrix"):
        plant_from_jacobian(lambda x: np.eye(2))


def test_unstable_solve_is_refused():
    with pytest.raises(ValueError):
        solve_lyapunov([[0.2, 1.0], [0.0, 0.3]], time="continuous")
