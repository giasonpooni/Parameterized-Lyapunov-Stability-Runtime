"""Every refusal path, exercised.

Refusing is the product. A is an input and a non-square one is refused; P is
a declaration and a non-symmetric or indefinite one is refused; a chart that
does not fit is refused; a parameter outside its declared box is refused.
Branch coverage said otherwise: nearly every uncovered line in the package
was a `raise`, so the paths that carry the product were the least exercised
code in it.

These tests do not add a law. They run the refusals the laws already
promise, so that deleting one is visible.
"""

from __future__ import annotations

import numpy as np
import pytest

from lyapunov.certificates import affine_quadratic, quadratic
from lyapunov.charts import LinearChart, push_certificate, push_plant
from lyapunov.equation import decrease_matrix, solve_lyapunov
from lyapunov.plants import affine_box_plant, constant_plant, plant_from_jacobian
from lyapunov.runtime import evaluate


# --- shape and declaration ---


def test_a_state_of_the_wrong_width_is_refused():
    with pytest.raises(ValueError, match="expected dim 2, got 3"):
        quadratic(np.eye(2), name="V").value([1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="expected dim 2, got 3"):
        affine_quadratic(np.eye(2), [np.zeros((2, 2))]).value([1.0, 2.0, 3.0], [0.0])


def test_a_state_that_is_not_a_vector_is_refused():
    with pytest.raises(ValueError, match="must be a 1-D vector"):
        quadratic(np.eye(2)).value(np.ones((2, 2)))


def test_a_non_finite_state_is_refused():
    for bad in (np.nan, np.inf, -np.inf):
        with pytest.raises(ValueError, match="must be finite"):
            quadratic(np.eye(2)).value([bad, 1.0])


def test_a_non_finite_plant_or_certificate_is_refused():
    with pytest.raises(ValueError, match="must be finite"):
        constant_plant([[np.nan, 0.0], [0.0, -1.0]])
    with pytest.raises(ValueError, match="must be finite"):
        quadratic([[np.inf, 0.0], [0.0, 1.0]])


def test_a_non_square_A_is_refused_as_a_plant():
    # docs/DEVELOPMENT.md: do not widen A to accept a 1x3 beam Jacobian.
    with pytest.raises(ValueError, match="nonempty square matrix"):
        plant_from_jacobian([[1.0, 2.0, 3.0]])
    with pytest.raises(ValueError, match="nonempty square matrix"):
        constant_plant(np.zeros((0, 0)))


def test_an_affine_term_that_does_not_match_is_refused():
    with pytest.raises(ValueError, match="every A_i must match A0"):
        affine_box_plant(np.eye(2), [np.eye(3)], [0.0], [1.0])
    with pytest.raises(ValueError, match="every P_i must match P0"):
        affine_quadratic(np.eye(2), [np.eye(3)])


def test_an_unknown_time_is_refused_everywhere_it_is_accepted():
    with pytest.raises(ValueError, match="continuous.*discrete"):
        constant_plant(np.eye(2), time="sideways")
    with pytest.raises(ValueError, match="continuous.*discrete"):
        affine_box_plant(np.eye(2), [np.eye(2)], [0.0], [1.0], time="sideways")
    with pytest.raises(ValueError, match="continuous.*discrete"):
        decrease_matrix(np.eye(2), np.eye(2), time="sideways")
    with pytest.raises(ValueError, match="continuous.*discrete"):
        solve_lyapunov(-np.eye(2), time="sideways")


# --- the declared box ---


def test_a_box_that_is_not_a_box_is_refused():
    with pytest.raises(ValueError, match="theta_max must be at least theta_min"):
        affine_box_plant(np.eye(2), [np.eye(2)], [1.0], [0.0])
    with pytest.raises(ValueError, match="rate_max must be at least rate_min"):
        affine_box_plant(
            np.eye(2), [np.eye(2)], [0.0], [1.0], rate_min=[1.0], rate_max=[0.0]
        )


def test_bounds_that_do_not_match_the_terms_are_refused():
    with pytest.raises(ValueError, match="parameter bounds must match"):
        affine_box_plant(np.eye(2), [np.eye(2)], [0.0, 1.0], [1.0, 2.0])
    with pytest.raises(ValueError, match="rate bounds must match"):
        affine_box_plant(
            np.eye(2), [np.eye(2)], [0.0], [1.0], rate_min=[0.0, 0.0], rate_max=[1.0, 1.0]
        )
    with pytest.raises(ValueError, match="parameter_names length"):
        affine_box_plant(np.eye(2), [np.eye(2)], [0.0], [1.0], parameter_names=("a", "b"))


def test_a_theta_outside_the_declared_box_is_refused():
    plant = affine_box_plant(np.eye(2), [np.eye(2)], [0.0], [1.0])
    for outside in ([-0.5], [1.5]):
        with pytest.raises(ValueError, match="outside the declared box"):
            plant.matrix(outside)


def test_a_rate_outside_the_declared_rate_box_is_refused():
    plant = affine_box_plant(
        np.eye(2), [np.eye(2)], [0.0], [1.0], rate_min=[-0.5], rate_max=[0.5]
    )
    with pytest.raises(ValueError, match="outside the declared rate box"):
        plant.require_rate([0.9])


def test_a_constant_plant_does_not_accept_a_parameter():
    with pytest.raises(ValueError, match="does not accept a parameter"):
        constant_plant(np.eye(2), name="A").matrix([0.5])


def test_a_parameter_of_the_wrong_width_is_refused():
    plant = affine_box_plant(np.eye(2), [np.eye(2)], [0.0], [1.0])
    with pytest.raises(ValueError, match="expected 1 parameters"):
        plant.require_theta([0.1, 0.2])
    with pytest.raises(ValueError, match="expected 1 rates"):
        plant.require_rate([0.1, 0.2])
    with pytest.raises(ValueError, match="expected 1 parameters"):
        affine_quadratic(np.eye(2), [np.zeros((2, 2))]).matrix([0.1, 0.2])


# --- the runtime ---


def test_an_affine_plant_evaluated_without_a_parameter_is_refused():
    plant = affine_box_plant(np.eye(2), [np.eye(2)], [0.0], [1.0])
    with pytest.raises(ValueError, match="requires theta"):
        evaluate(plant, quadratic(np.eye(2)), [1.0, 1.0])


def test_an_affine_certificate_evaluated_without_a_parameter_is_refused():
    plant = constant_plant(-np.eye(2))
    cert = affine_quadratic(np.eye(2), [np.zeros((2, 2))])
    with pytest.raises(ValueError, match="requires theta"):
        evaluate(plant, cert, [1.0, 1.0])


def test_a_rate_that_does_not_match_the_certificate_is_refused():
    plant = affine_box_plant(
        np.eye(2), [np.eye(2)], [0.0], [1.0], rate_min=[-1.0], rate_max=[1.0]
    )
    cert = affine_quadratic(np.eye(2), [np.zeros((2, 2))])
    with pytest.raises(ValueError, match="theta_dot"):
        evaluate(plant, cert, [1.0, 1.0], theta=[0.5], theta_dot=None)


def test_mismatched_certificate_and_plant_dimensions_are_refused():
    with pytest.raises(ValueError, match="dimensions differ"):
        evaluate(constant_plant(np.eye(3)), quadratic(np.eye(2)), [1.0, 1.0])


def test_a_state_that_does_not_match_the_plant_is_refused():
    with pytest.raises(ValueError, match="state dimension"):
        evaluate(constant_plant(-np.eye(2)), quadratic(np.eye(2)), [1.0, 1.0, 1.0])


def test_a_discrete_plant_refuses_a_rate_at_the_runtime_too():
    with pytest.raises(ValueError, match="discrete plants do not take theta_dot"):
        evaluate(
            constant_plant(0.5 * np.eye(2), time="discrete"),
            quadratic(np.eye(2)),
            [1.0, 1.0],
            theta_dot=[0.5],
        )


# --- charts ---


def test_a_chart_that_does_not_fit_is_refused():
    chart = LinearChart(name="T", T=np.eye(2))
    with pytest.raises(ValueError, match="does not match the certificate"):
        push_certificate(quadratic(np.eye(3)), chart)
    with pytest.raises(ValueError, match="does not match the plant"):
        push_plant(constant_plant(np.eye(3)), chart)


def test_scale_factors_must_be_a_vector():
    with pytest.raises(ValueError, match="scale factors must be a 1-D vector"):
        LinearChart.scale([[1.0, 2.0]])


# --- the solve ---


def test_a_Q_that_does_not_match_A_is_refused():
    with pytest.raises(ValueError, match="Q must match A"):
        solve_lyapunov(-np.eye(2), np.eye(3))


def test_a_shape_mismatch_in_the_decrease_form_is_refused():
    with pytest.raises(ValueError, match="A and P must have the same shape"):
        decrease_matrix(np.eye(3), np.eye(2))


def test_a_singular_lyapunov_operator_is_refused():
    # Eigenvalues +1 and -1: lambda_i + lambda_j = 0 in the cross term, so the
    # operator has no unique solution. That is a refusal, not a pseudo-inverse.
    with pytest.raises(ValueError, match="singular|positive definite"):
        solve_lyapunov(np.diag([1.0, -1.0]), time="continuous")


def test_an_indefinite_Q_is_refused():
    with pytest.raises(ValueError, match="positive definite"):
        solve_lyapunov(-np.eye(2), np.diag([1.0, -1.0]))


# --- the invariant that makes two verdict branches unreachable ---


def test_every_evaluated_P_is_positive_definite_by_construction():
    """Why ``verdict``'s "P is not positive definite" branch cannot fire.

    ``QuadraticCertificate`` validates P at construction and stores it
    read-only; ``AffineCertificate.matrix`` calls ``require_spd`` on every
    evaluation. So ``sample.min_P`` is strictly positive whenever a sample
    exists at all, and with a positive definite P, ``V = x^T P x`` is never
    negative. Those two branches in ``verdict`` are defence in depth against
    a future path that skips validation, not live refusals -- and this test
    is what makes that statement checkable rather than assumed.
    """
    rng = np.random.default_rng(11)
    for _ in range(200):
        dim = int(rng.integers(1, 5))
        root = rng.normal(size=(dim, dim))
        cert = quadratic(root @ root.T + dim * np.eye(dim), name="P")
        plant = constant_plant(rng.normal(size=(dim, dim)), name="A")
        sample = evaluate(plant, cert, rng.normal(size=dim))
        assert sample.min_P > 0.0
        assert sample.value >= 0.0


# --- the guest's own refusals ---


def test_the_guest_refuses_a_value_outside_i64():
    from lyapunov.discrete_guest import GuestRefuse, run_v_push

    with pytest.raises(GuestRefuse, match="overflows i64"):
        run_v_push(P=[[1 << 63, 0], [0, 1]], T=[[1, 0], [0, 1]], x=[1, 1])


def test_the_guest_refuses_the_wrong_shape():
    from lyapunov.discrete_guest import GuestRefuse, run_discrete_decrease, run_v_push

    with pytest.raises(GuestRefuse, match="must be 2x2"):
        run_v_push(P=[[1, 0, 0], [0, 1, 0]], T=[[1, 0], [0, 1]], x=[1, 1])
    with pytest.raises(GuestRefuse, match="must have length 2"):
        run_discrete_decrease(A=[[0, 1], [0, 0]], P=[[1, 0], [0, 1]], x=[1, 2, 3])


def test_the_guest_refuses_a_point_that_is_not_a_3_vector():
    from lyapunov.discrete_guest import GuestRefuse, run_developable_defect

    with pytest.raises(GuestRefuse, match="must have length 3"):
        run_developable_defect(
            vertices=[[0, 0], [1, 0], [0, 1], [-1, 0]],
            edges=[[0, 1], [0, 2], [0, 3]],
            center=0,
        )


def test_the_jacobi_twin_refuses_a_curvature_it_does_not_admit():
    from lyapunov.discrete_guest import GuestRefuse, run_jacobi_steps

    with pytest.raises(GuestRefuse, match="K must be 0, 1, or -1"):
        run_jacobi_steps(j0=0, j1=1, k=2, h2=1, steps=4)


def test_the_jacobi_twin_refuses_a_step_count_outside_its_contract():
    from lyapunov.discrete_guest import GuestRefuse, run_jacobi_steps

    for steps in (0, -1, 65, 1000):
        with pytest.raises(GuestRefuse, match="steps must be in 1..64"):
            run_jacobi_steps(j0=0, j1=1, k=0, h2=1, steps=steps)


def test_a_star_outside_3_to_8_spokes_is_refused():
    from lyapunov.discrete_guest import GuestRefuse, run_developable_star

    with pytest.raises(GuestRefuse, match="star must have 3..8 neighbors"):
        run_developable_star(vertex=[0, 0, 0], neighbors=[[1, 0, 0], [0, 1, 0]])
    with pytest.raises(GuestRefuse, match="star must have 3..8 neighbors"):
        run_developable_star(
            vertex=[0, 0, 0], neighbors=[[i, 0, 0] for i in range(1, 11)]
        )


def test_a_star_whose_every_spoke_is_collinear_is_refused():
    from lyapunov.discrete_guest import GuestRefuse, run_developable_star

    with pytest.raises(GuestRefuse, match="every spoke is collinear"):
        run_developable_star(
            vertex=[0, 0, 0], neighbors=[[1, 0, 0], [2, 0, 0], [-3, 0, 0]]
        )


def test_a_panel_graph_with_no_vertices_is_refused():
    from lyapunov.discrete_guest import GuestRefuse, run_developable_defect

    with pytest.raises(GuestRefuse, match="panel graph has no vertices"):
        run_developable_defect(vertices=[], edges=[], center=0)


def test_a_malformed_or_out_of_range_edge_is_refused():
    from lyapunov.discrete_guest import GuestRefuse, run_developable_defect

    vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [-1, 0, 0]]
    with pytest.raises(GuestRefuse, match="must be a pair"):
        run_developable_defect(vertices=vertices, edges=[[0, 1, 2]], center=0)
    with pytest.raises(GuestRefuse, match="index out of range"):
        run_developable_defect(vertices=vertices, edges=[[0, 9]], center=0)
    with pytest.raises(GuestRefuse, match="duplicate spoke"):
        run_developable_defect(
            vertices=vertices, edges=[[0, 1], [1, 0], [0, 2], [0, 3]], center=0
        )


def test_an_edge_listed_the_other_way_round_is_still_a_spoke():
    # (j, center) has to be read as a spoke exactly as (center, j) is, or the
    # statement would depend on how each edge happens to be oriented.
    from lyapunov.discrete_guest import run_developable_defect

    vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [-1, 0, 0]]
    forward = run_developable_defect(
        vertices=vertices, edges=[[0, 1], [0, 2], [0, 3]], center=0
    )
    reversed_ = run_developable_defect(
        vertices=vertices, edges=[[1, 0], [2, 0], [3, 0]], center=0
    )
    assert forward.held == reversed_.held is True
    assert forward.outputs == reversed_.outputs


# --- paths that carry a claim, and were never run ---


def test_sp1_named_without_proof_bytes_is_not_checked():
    from lyapunov.discrete_guest import FIXTURE_V_PUSH, run_v_push
    from lyapunov.host_callback import Receipt, attach

    statement = run_v_push(**FIXTURE_V_PUSH)
    for absent in ("proof_bytes_hex", "verifying_key_digest"):
        fields = {
            "statement_digest": statement.digest(),
            "claim_scope": "computational-integrity-only",
            "backend": "sp1",
            "verifying_key_digest": "vk",
            "proof_bytes_hex": "ab",
            "verified_by_bound_host": True,
        }
        fields[absent] = None
        receipt = Receipt(**fields)
        result = attach(statement, receipt)
        assert result.proof_status == "NOT_CHECKED"
        assert result.to_dict()["may_authorize"] is False


def test_a_vertex_check_reports_the_corners_that_failed():
    from lyapunov.checks import check_vertices

    # Unstable at both corners, so the failure counter is exercised.
    plant = affine_box_plant(
        np.array([[0.2, 1.0], [0.0, 0.3]]), [np.zeros((2, 2))], [0.0], [1.0]
    )
    result = check_vertices(plant, quadratic(np.eye(2), name="P=I"), include_rates=False)
    assert result.passed is False
    assert result.extra["failures"] == result.extra["corners"] > 0


def test_an_inconclusive_verdict_is_reported_as_such():
    from lyapunov.runtime import verdict

    # A^T P + P A = diag(-2, 0) with P = I: negative SEMI-definite, so the
    # matrix cannot certify. At x = [1, 0] the scalar is strictly negative,
    # so it is not a violation either. That is the third outcome, and it is
    # the honest one: this sample decreases, the certificate does not cover
    # the whole space, and the instrument says neither yes nor no.
    plant = constant_plant(np.diag([-1.0, 0.0]), name="semidefinite")
    sample_result = verdict(plant, quadratic(np.eye(2), name="P=I"), [1.0, 0.0])
    assert sample_result.sample.max_decrease == pytest.approx(0.0)
    assert sample_result.sample.decrease < 0.0
    assert sample_result.status == "inconclusive"
    assert not sample_result.certified
    # and in the kernel of that same form it IS a violation, not a pass
    kernel = verdict(plant, quadratic(np.eye(2), name="P=I"), [0.0, 1.0])
    assert kernel.status == "violated"


def test_the_certificate_value_methods_return_the_quadratic_form():
    P = np.array([[2.0, 0.5], [0.5, 3.0]])
    x = np.array([1.0, -2.0])
    assert quadratic(P, name="V").value(x) == pytest.approx(float(x @ P @ x))
    affine = affine_quadratic(P, [np.diag([1.0, 1.0])], name="V(theta)")
    expected = float(x @ (P + 0.25 * np.eye(2)) @ x)
    assert affine.value(x, [0.25]) == pytest.approx(expected)


def test_a_scalar_state_is_accepted_as_a_one_vector():
    assert quadratic([[4.0]], name="V").value(3.0) == pytest.approx(36.0)


def test_the_reference_catalogue_is_reachable_and_declares_its_plants():
    from lyapunov.reference_plants import reference_catalogue

    catalogue = reference_catalogue()
    assert set(catalogue) == {"hurwitz2", "unstable2", "discrete-contract", "two-vertex-lpv"}
    for name, plant in catalogue.items():
        assert plant.dim == 2, name


def test_the_plant_dataclass_validates_A_itself_not_only_its_helper():
    # constant_plant calls as_square before constructing LinearPlant, so a
    # test that only goes through the helper leaves the dataclass's own guard
    # unexercised. A caller can build the dataclass directly.
    from lyapunov.plants import AffinePlant, LinearPlant

    with pytest.raises(ValueError, match="nonempty square matrix"):
        LinearPlant(name="direct", A=[[1.0, 2.0, 3.0]])
    with pytest.raises(ValueError, match="nonempty square matrix"):
        AffinePlant(
            name="direct",
            A0=[[1.0, 2.0, 3.0]],
            terms=(),
            theta_min=[],
            theta_max=[],
            rate_min=[],
            rate_max=[],
        )


def test_an_affine_P_term_that_is_not_symmetric_is_refused():
    # The shape check alone would let a same-shape asymmetric term through,
    # and P(theta) would then be asymmetric at every theta but zero.
    with pytest.raises(ValueError, match="must be symmetric"):
        affine_quadratic(np.eye(2), [np.array([[0.0, 1.0], [0.0, 0.0]])])


def test_the_looseness_guard_also_requires_a_real_number():
    # _require_tightening and _require_no_looser are separate guards; a test
    # of the first leaves the second's type check unexercised.
    from lyapunov.checks import check_equation_residual

    plant = constant_plant(-np.eye(2))
    cert = quadratic(np.eye(2))
    for bad in ("1e-9", None, [1e-9]):
        with pytest.raises(ValueError, match="must be a real number"):
            check_equation_residual(plant, cert, np.eye(2), rtol=bad)


def test_a_rate_of_the_wrong_width_is_refused_before_the_certificate_sees_it():
    """The plant guards the rate first, so the certificate's own check cannot fire.

    ``evaluate`` validates ``theta_dot`` against the PLANT's parameter count
    before the certificate is consulted, and the certificate matrix is built
    from ``theta`` before the rate is assembled. Every route to a mismatch
    between ``theta_dot`` and ``certificate.n_parameters`` is therefore
    intercepted earlier, which is why ``runtime.py``'s "theta_dot does not
    match the certificate" is defence in depth rather than a live refusal.
    """
    plant = affine_box_plant(
        np.eye(2), [np.eye(2)], [0.0], [1.0], rate_min=[-1.0], rate_max=[1.0]
    )
    cert = affine_quadratic(np.eye(2), [np.zeros((2, 2))])
    with pytest.raises(ValueError, match="expected 1 rates, got 2"):
        evaluate(plant, cert, [1.0, 1.0], theta=[0.5], theta_dot=[0.1, 0.2])
    # and a theta of the wrong width is caught by the certificate matrix
    two = affine_box_plant(
        np.eye(2), [np.eye(2), np.eye(2)], [0.0, 0.0], [1.0, 1.0],
        rate_min=[0.0, 0.0], rate_max=[0.0, 0.0],
    )
    with pytest.raises(ValueError, match="expected 1 parameters, got 2"):
        evaluate(two, cert, [1.0, 1.0], theta=[0.1, 0.2], theta_dot=[0.0, 0.0])


def test_a_degenerate_box_has_one_corner_not_two():
    # theta_max == theta_min collapses that axis: the corner walk must not
    # emit the same corner twice.
    plant = affine_box_plant(
        np.eye(2), [np.eye(2)], [0.5], [0.5], rate_min=[0.0], rate_max=[0.0]
    )
    assert len(plant.vertices()) == 1
    assert len(plant.rate_vertices()) == 1
    wide = affine_box_plant(
        np.eye(2), [np.eye(2)], [0.0], [1.0], rate_min=[-1.0], rate_max=[1.0]
    )
    assert len(wide.vertices()) == 2
    assert len(wide.rate_vertices()) == 2


def test_write_report_creates_the_directory_it_needs(tmp_path):
    from lyapunov.reports import write_report

    target = tmp_path / "nested" / "deeper" / "report.md"
    write_report(target, "# written\n")
    assert target.read_text(encoding="utf-8") == "# written\n"


def test_a_statement_with_no_known_summary_key_is_refused_not_blanked():
    # reports._summary would otherwise print an empty cell for a statement
    # whose outputs the formatter does not know how to summarise.
    from lyapunov.reports import format_guest_suite

    suite = {
        "claim_scope": "computational-integrity-only",
        "numeric_contracts": ["i64-unimodular-v1"],
        "statements": [
            {
                "statement_id": "mystery-v1",
                "numeric_contract": "i64-unimodular-v1",
                "held": True,
                "outputs": {"something_else": 1},
            }
        ],
    }
    with pytest.raises(ValueError, match="no known summary key"):
        format_guest_suite(suite)
