from __future__ import annotations

import numpy as np
import pytest

from lyapunov.charts import LinearChart
from lyapunov.checks import check_chart_invariance
from lyapunov.equation import certificate_for_plant
from lyapunov.reference_plants import hurwitz2


def test_value_and_decrease_are_chart_invariant():
    plant = hurwitz2()
    cert = certificate_for_plant(plant)
    chart = LinearChart.scale([1000.0, 0.01], name="milli")
    check_chart_invariance(plant, cert, chart, [0.3, -1.1]).raise_for_failure()


def test_frobenius_of_P_is_not_invariant():
    plant = hurwitz2()
    cert = certificate_for_plant(plant)
    chart = LinearChart.scale([1000.0, 0.01], name="milli")
    from lyapunov.charts import push_certificate

    pushed = push_certificate(cert, chart)
    assert not np.isclose(
        np.linalg.norm(cert.P, "fro"),
        np.linalg.norm(pushed.P, "fro"),
    )


def test_offset_free_first_release():
    with pytest.raises(ValueError):
        LinearChart(name="bad", T=np.ones((2, 3)))
