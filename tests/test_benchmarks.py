from __future__ import annotations

from lyapunov.benchmarks import (
    chart_invariance_on_companion,
    jspt_affine2,
    jspt_beam_jacobian_refused_as_A,
    jspt_scaled_rotation_discrete,
    jspt_storage_as_dynamics,
    run_suite,
    two_tank_leak_companion,
)


def test_jspt_expanding_maps_are_refused():
    assert jspt_affine2().outcome == "refused"
    assert jspt_scaled_rotation_discrete().outcome == "refused"
    assert jspt_storage_as_dynamics().outcome == "refused"


def test_beam_observation_jacobian_is_not_a_plant():
    result = jspt_beam_jacobian_refused_as_A()
    assert result.outcome == "refused"
    assert result.numbers["rows"] == 1.0
    assert result.numbers["cols"] == 3.0


def test_leak_companion_and_chart_are_samples_not_a_release():
    leak = two_tank_leak_companion()
    chart = chart_invariance_on_companion()
    assert leak.outcome == "certified-sample"
    assert chart.outcome == "certified-sample"
    assert chart.numbers["V_gap"] < 1e-12


def test_suite_keeps_refusals_and_samples():
    outcomes = {case.name: case.outcome for case in run_suite()}
    assert outcomes["jspt-affine2"] == "refused"
    assert outcomes["jspt-beam-J-as-A"] == "refused"
    assert outcomes["two-tank-leak-companion"] == "certified-sample"
