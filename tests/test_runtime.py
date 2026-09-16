from __future__ import annotations

import numpy as np
import pytest

from lyapunov.certificates import affine_quadratic
from lyapunov.equation import certificate_for_plant
from lyapunov.reference_plants import hurwitz2, two_vertex_lpv
from lyapunov.runtime import evaluate, verdict


def test_equilibrium_is_certified():
    plant = hurwitz2()
    cert = certificate_for_plant(plant)
    result = verdict(plant, cert, [0.0, 0.0])
    assert result.status == "certified"
    assert result.sample.value == 0.0
    assert result.sample.decrease == 0.0


def test_off_equilibrium_decrease_is_negative():
    plant = hurwitz2()
    cert = certificate_for_plant(plant)
    sample = evaluate(plant, cert, [0.8, -0.3])
    assert sample.value > 0.0
    assert sample.decrease < 0.0
    assert verdict(plant, cert, [0.8, -0.3]).certified


def test_level_set_exclusion():
    plant = hurwitz2()
    cert = certificate_for_plant(plant)
    sample = evaluate(plant, cert, [1.0, 1.0])
    result = verdict(plant, cert, [1.0, 1.0], level=0.1 * sample.value)
    assert result.status == "outside-level"


def test_affine_certificate_needs_rate_in_continuous_time():
    plant = two_vertex_lpv()
    cert = affine_quadratic(np.eye(2), [np.zeros((2, 2))])
    with pytest.raises(ValueError, match="theta_dot"):
        evaluate(plant, cert, [0.2, -0.1], theta=[0.4])
