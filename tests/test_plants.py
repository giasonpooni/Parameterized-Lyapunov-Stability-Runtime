from __future__ import annotations

import numpy as np
import pytest

from lyapunov.plants import affine_box_plant, plant_from_jacobian
from lyapunov.reference_plants import hurwitz2, two_vertex_lpv


def test_plant_from_jacobian_accepts_a_matrix():
    plant = plant_from_jacobian(hurwitz2().A, name="from-jspt")
    assert plant.dim == 2
    np.testing.assert_allclose(plant.A, hurwitz2().A)


def test_affine_vertices_are_the_box_corners():
    plant = two_vertex_lpv()
    corners = plant.vertices()
    assert len(corners) == 2
    np.testing.assert_allclose(corners[0], [0.0])
    np.testing.assert_allclose(corners[1], [1.0])


def test_theta_outside_box_is_refused():
    plant = two_vertex_lpv()
    with pytest.raises(ValueError, match="outside"):
        plant.matrix([1.2])


def test_rate_outside_box_is_refused():
    plant = two_vertex_lpv()
    with pytest.raises(ValueError, match="rate"):
        plant.require_rate([0.9])


def test_mismatched_bounds_are_refused():
    with pytest.raises(ValueError):
        affine_box_plant(np.eye(2), [np.eye(2)], [0.0, 1.0], [1.0])
