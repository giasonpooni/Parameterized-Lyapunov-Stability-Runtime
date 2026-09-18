"""One test per bullet of the binding law list in docs/GATE.md.

These pin laws that already hold. They add no new law. Each test is written
so that deleting the guard it protects turns it red.
"""

from __future__ import annotations

import numpy as np
import pytest

from lyapunov.certificates import affine_quadratic, quadratic
from lyapunov.charts import LinearChart, push_certificate
from lyapunov.checks import check_decrease, check_vertices
from lyapunov.discrete_guest import (
    GuestRefuse,
    det2,
    discrete_decrease_form,
    jacobi_step,
    mul2,
    push_P,
    quadratic as guest_quadratic,
    run_discrete_decrease,
    run_v_push,
)
from lyapunov.equation import decrease_matrix, solve_lyapunov
from lyapunov.host_callback import Receipt, attach
from lyapunov.plants import constant_plant
from lyapunov.reference_plants import hurwitz2, two_vertex_lpv, unstable2
from lyapunov.runtime import verdict


# --- "P that is not positive definite is refused. No clip, no nearest-PSD." ---


def test_indefinite_P_is_refused_not_repaired():
    with pytest.raises(ValueError, match="positive definite"):
        quadratic([[1.0, 0.0], [0.0, -1.0]])


def test_singular_P_on_the_boundary_is_refused():
    # A nearest-PSD repair would nudge the zero eigenvalue and accept this.
    with pytest.raises(ValueError, match="positive definite"):
        quadratic([[1.0, 1.0], [1.0, 1.0]])


def test_affine_P_is_refused_at_the_theta_where_it_stops_being_PD():
    cert = affine_quadratic(np.eye(2), [np.diag([-1.0, 0.0])])
    assert cert.matrix([0.5])[0, 0] == pytest.approx(0.5)
    with pytest.raises(ValueError, match="positive definite"):
        cert.matrix([1.0])


# --- "Discrete decrease is A^T P A - P." Pdot must not be copied onto it. ---


def test_discrete_time_refuses_a_parameter_rate():
    with pytest.raises(ValueError, match="rate"):
        decrease_matrix(np.eye(2), np.eye(2), time="discrete", P_rate=np.eye(2))


def test_discrete_decrease_is_AtPA_minus_P():
    A = np.array([[0.5, 0.2], [0.0, 0.3]])
    P = np.array([[2.0, 0.1], [0.1, 3.0]])
    np.testing.assert_allclose(
        decrease_matrix(A, P, time="discrete"), A.T @ P @ A - P, atol=1e-15
    )


def test_continuous_decrease_carries_Pdot_and_discrete_does_not():
    A, P, Pdot = np.eye(2) * -1.0, np.eye(2), np.eye(2) * 0.25
    np.testing.assert_allclose(
        decrease_matrix(A, P, time="continuous", P_rate=Pdot),
        A.T @ P + P @ A + Pdot,
        atol=1e-15,
    )


# --- "Spectrum is a diagnostic. It does not replace V." ---


def test_a_hurwitz_plant_is_not_certified_without_a_working_P():
    # Eigenvalues are -0.1 twice, so A is Hurwitz, but P = I is not a
    # certificate for it. A spectral lookup would call this stable.
    plant = constant_plant([[-0.1, 10.0], [0.0, -0.1]], name="hurwitz-but-not-by-I")
    assert np.max(np.real(np.linalg.eigvals(plant.A))) < 0.0
    result = verdict(plant, quadratic(np.eye(2), name="P=I"), [1.0, 1.0])
    assert result.status != "certified"


# --- "V is a declared quadratic form", i.e. the decrease form must be ND ---


def test_a_conserved_V_is_not_certified():
    # Skew-symmetric A gives A^T P + P A = 0 exactly with P = I: V is
    # conserved along trajectories, so it does not decrease. The decrease
    # matrix is negative SEMI-definite, never negative definite.
    plant = constant_plant([[0.0, 1.0], [-1.0, 0.0]], name="oscillator")
    cert = quadratic(np.eye(2), name="P=I")
    result = verdict(plant, cert, [1.0, 0.0])
    assert result.sample.max_decrease == 0.0
    assert result.sample.decrease == 0.0
    assert result.status != "certified"
    assert not check_decrease(plant, cert).passed


def test_the_origin_is_still_certified_on_a_marginal_plant():
    plant = constant_plant([[0.0, 1.0], [-1.0, 0.0]], name="oscillator")
    result = verdict(plant, quadratic(np.eye(2), name="P=I"), [0.0, 0.0])
    assert result.status == "certified"
    assert result.sample.value == 0.0


# --- "No backend may expose those identities as kwargs that change the law." ---


def test_negative_atol_cannot_turn_a_refusal_into_a_pass():
    plant, cert = unstable2(), quadratic(np.eye(2), name="P=I")
    assert not check_decrease(plant, cert).passed
    with pytest.raises(ValueError, match="atol"):
        check_decrease(plant, cert, atol=-10.0)
    with pytest.raises(ValueError, match="atol"):
        check_vertices(two_vertex_lpv(), cert, atol=-10.0)


def test_check_vertices_refuses_a_negative_atol_before_evaluating_a_corner(monkeypatch):
    # check_vertices forwards atol to check_decrease, whose own guard would
    # raise anyway, so the test above passes even if check_vertices loses its
    # guard. Patch check_decrease out so only check_vertices' guard can fire.
    import lyapunov.checks as checks_module

    def boom(*_args, **_kwargs):
        raise AssertionError(
            "check_vertices must refuse a negative atol before evaluating any corner"
        )

    monkeypatch.setattr(checks_module, "check_decrease", boom)
    with pytest.raises(ValueError, match="atol"):
        checks_module.check_vertices(
            two_vertex_lpv(), quadratic(np.eye(2), name="P=I"), atol=-1.0
        )


def test_a_positive_atol_only_tightens():
    plant, cert = hurwitz2(), quadratic(np.eye(2), name="P=I")
    assert check_decrease(plant, cert).passed
    assert not check_decrease(plant, cert, atol=1e9).passed


# --- vertex checks: sufficient for a common quadratic, not for affine P ---


def test_vertex_check_marks_whether_it_covers_the_box():
    plant = two_vertex_lpv()
    common = check_vertices(plant, quadratic(np.eye(2), name="P=I"), include_rates=False)
    assert common.extra["sufficient_for_box"] == 1.0
    assert "sufficient common-quadratic test" in common.details

    affine = check_vertices(
        plant, affine_quadratic(np.eye(2), [np.zeros((2, 2))], name="P(theta)")
    )
    assert affine.extra["sufficient_for_box"] == 0.0
    assert "NOT sufficient for the box" in affine.details


# --- "Charts push P by solves, not inverses." ---


def test_push_certificate_never_forms_an_inverse(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("charts must push P by solves, not inverses")

    monkeypatch.setattr(np.linalg, "inv", refuse)
    monkeypatch.setattr(np.linalg, "pinv", refuse)
    cert = quadratic([[2.0, 0.1], [0.1, 3.0]])
    chart = LinearChart(name="shear", T=[[1.0, 2.0], [0.0, 1.0]])
    pushed = push_certificate(cert, chart)
    x = np.array([0.4, -1.2])
    assert float(x @ cert.P @ x) == pytest.approx(
        float((chart.T @ x) @ pushed.P @ (chart.T @ x))
    )


def test_a_chart_cannot_be_mutated_after_it_is_accepted():
    chart = LinearChart(name="frozen", T=[[1.0, 0.0], [0.0, 1.0]])
    with pytest.raises(ValueError):
        chart.T[0, 0] = 0.0


# --- guest: exact i64, no silent bignum where the Rust twin would wrap ---


def test_guest_refuses_a_product_that_leaves_i64():
    with pytest.raises(GuestRefuse, match="overflows i64"):
        guest_quadratic(((2, 0), (0, 3)), (2**62, 0))


def test_every_guest_kernel_range_checks_its_own_result():
    # P = I and x = 2**32: apply2 stays inside i64 (1 * 2**32), so only the
    # final dot product overflows. A check in apply2 alone would miss this.
    assert 2**32 < (1 << 63) - 1
    with pytest.raises(GuestRefuse, match="overflows i64"):
        guest_quadratic(((1, 0), (0, 1)), (2**32, 0))
    # det2: entries in range, product out of range.
    with pytest.raises(GuestRefuse, match="overflows i64"):
        det2(((2**40, 0), (0, 2**40)))
    # mul2: each factor in range, the entry product is not.
    with pytest.raises(GuestRefuse, match="overflows i64"):
        mul2(((2**40, 0), (0, 1)), ((2**40, 0), (0, 1)))
    # jacobi_step: the recurrence itself leaves the range.
    with pytest.raises(GuestRefuse, match="overflows i64"):
        jacobi_step(0, (1 << 62) + 1, 0, 1)


def test_guest_refuses_non_integer_inputs():
    with pytest.raises(GuestRefuse, match="must be an int"):
        run_v_push(P=[[2.0, 0], [0, 3]], T=[[2, 1], [1, 1]], x=[1, 2])


def test_guest_refuses_a_bool_masquerading_as_an_int():
    with pytest.raises(GuestRefuse, match="must be an int"):
        run_discrete_decrease(A=[[0, 1], [0, 0]], P=[[1, 0], [0, 1]], x=[True, 3])


def test_guest_kernels_gate_P_like_the_rust_twin():
    # lib.rs push_p and decrease_form both call require_pd. The Python
    # module-level kernels must too, not only the run_* wrappers.
    not_pd = ((-1, 0), (0, -1))
    with pytest.raises(GuestRefuse, match="positive definite"):
        push_P(not_pd, ((1, 0), (0, 1)))
    with pytest.raises(GuestRefuse, match="positive definite"):
        discrete_decrease_form(((0, 1), (0, 0)), not_pd)


def test_guest_kernels_refuse_a_non_symmetric_P():
    with pytest.raises(GuestRefuse, match="symmetric"):
        push_P(((1, 2), (0, 1)), ((1, 0), (0, 1)))


def test_non_unimodular_chart_is_refused_in_the_guest():
    with pytest.raises(GuestRefuse, match="unimodular"):
        push_P(((1, 0), (0, 1)), ((2, 0), (0, 2)))


# --- host callback: VERIFIED only from a bound host, on the sp1 backend ---


def test_an_unsupported_backend_cannot_mint_verified():
    stmt = run_v_push(P=[[2, 0], [0, 3]], T=[[2, 1], [1, 1]], x=[1, 2])
    receipt = Receipt(
        statement_digest=stmt.digest(),
        claim_scope="computational-integrity-only",
        backend="groth16-ish",  # type: ignore[arg-type]
        verifying_key_digest="vk",
        proof_bytes_hex="ab",
        verified_by_bound_host=True,
    )
    with pytest.raises(GuestRefuse, match="unsupported backend"):
        attach(stmt, receipt)


def test_no_statement_claims_authority():
    stmt = run_v_push(P=[[2, 0], [0, 3]], T=[[2, 1], [1, 1]], x=[1, 2])
    body = stmt.to_dict()
    assert body["may_authorize"] is False
    assert body["traceable"] is False
    assert body["claim_scope"] == "computational-integrity-only"
    assert body["proof_status"] == "NOT_CHECKED"


def test_host_oracle_gap_is_none_because_no_oracle_ran():
    # A hardcoded 0.0 would read as "the float64 oracle agreed exactly".
    stmt = run_v_push(P=[[2, 0], [0, 3]], T=[[2, 1], [1, 1]], x=[1, 2])
    assert stmt.host_oracle_gap is None
    assert stmt.outputs["V_gap"] == 0


# --- "Singular T refused" is a scale-invariant refusal, not a rank claim ---


def test_a_well_conditioned_chart_is_accepted_at_any_scale():
    # det is scale-covariant: det(c*I(n)) = c**n underflows to 0.0 while the
    # condition number stays exactly 1. A determinant gate refuses these; a
    # rank gate does not. n = 24 is MAX_KRONECKER_DIM, and 1e-15 is a
    # femto-scale unit conversion, so this is a reachable chart.
    for dim, scale in ((24, 1e-15), (4, 1e-100), (2, 1e-40)):
        T = scale * np.eye(dim)
        assert float(np.linalg.det(T)) == 0.0 or dim == 2
        assert np.linalg.cond(T) == pytest.approx(1.0)
        chart = LinearChart(name=f"scale-{dim}", T=T)
        assert chart.dim == dim


def test_V_survives_a_chart_whose_determinant_underflowed():
    dim, scale = 24, 1e-15
    assert float(np.linalg.det(scale * np.eye(dim))) == 0.0
    cert = quadratic(np.eye(dim) + 0.01 * (np.eye(dim, k=1) + np.eye(dim, k=-1)))
    chart = LinearChart.scale([scale] * dim, name="femto")
    pushed = push_certificate(cert, chart)
    x = np.ones(dim)
    assert float(x @ cert.P @ x) == pytest.approx(
        float((chart.T @ x) @ pushed.P @ (chart.T @ x))
    )


def test_an_exactly_singular_chart_is_still_refused():
    with pytest.raises(ValueError, match="invertible"):
        LinearChart(name="rank-1", T=[[1.0, 0.0], [2.0, 0.0]])


def test_a_singular_chart_whose_float_determinant_is_nonzero_is_refused():
    # This is the class a determinant gate misses: exactly rank-deficient by
    # construction, yet det != 0.0 in float64 and np.linalg.solve succeeds.
    rng = np.random.default_rng(3)
    refused = examined = 0
    while examined < 8:
        B = rng.normal(size=(5, 4))
        T = np.column_stack([B, B[:, :3] @ rng.normal(size=3)])
        if abs(float(np.linalg.det(T))) == 0.0:
            continue
        examined += 1
        with pytest.raises(ValueError, match="invertible"):
            LinearChart(name="numerically-singular", T=T)
        refused += 1
    assert refused == 8


def test_a_chart_whose_pushforward_overflows_is_refused_not_silently_accepted():
    chart = LinearChart.scale([1e-170, 1e-170], name="beyond-float64")
    with pytest.raises(ValueError):
        push_certificate(quadratic(np.eye(2)), chart)


def test_there_is_still_no_condition_number_constant_anywhere():
    import lyapunov
    from lyapunov import constitution

    names = [n for n in dir(constitution) if not n.startswith("_")]
    assert not [n for n in names if "COND" in n.upper() or "CAP" in n.upper()], names
    assert not [n for n in dir(lyapunov) if "MAX_CONDITION" in n.upper()]


# --- a refusal must mean the maths failed, not that the units are small ---


def test_a_well_conditioned_chart_is_accepted_at_every_unit_scale():
    # T = s * [[1, 0.5], [0.3, 1]] has condition number 2.32 at every s. Only
    # the unit scale changes. An absolute symmetry tolerance on the pushed P'
    # refused s = 1e-3, 1e-6 and 1e-8 while accepting 1e-5 and 1e-7, which is
    # roundoff luck, not a property of the chart.
    P = np.array([[2.0, 0.3], [0.3, 3.0]])
    base = np.array([[1.0, 0.5], [0.3, 1.0]])
    assert np.linalg.cond(base) < 3.0
    x = np.array([0.7, -1.3])
    reference = float(x @ P @ x)
    for scale in (1e-3, 1e-5, 1e-6, 1e-7, 1e-8, 1e3, 1e6):
        chart = LinearChart(name=f"unit-{scale:g}", T=scale * base)
        pushed = push_certificate(quadratic(P, name="P"), chart)
        moved = chart.T @ x
        assert float(moved @ pushed.P @ moved) == pytest.approx(reference, rel=1e-12)


def test_a_pushed_certificate_is_exactly_symmetric():
    # The congruence is symmetric in exact arithmetic, so the stored P' must
    # carry no skew at all: anything else is roundoff this package created.
    base = np.array([[1.0, 0.5], [0.3, 1.0]])
    for scale in (1e-6, 1e-3, 1.0, 1e6):
        pushed = push_certificate(
            quadratic([[2.0, 0.3], [0.3, 3.0]], name="P"),
            LinearChart(name="u", T=scale * base),
        )
        assert np.array_equal(pushed.P, pushed.P.T)


def test_a_correct_certificate_on_a_badly_scaled_plant_is_not_refused():
    # Hurwitz, eigenvalues -1e-5 twice. P is enormous, so the residual is
    # large in absolute terms and tiny relative to the operator. A gate scaled
    # only by ||Q|| called this correct certificate a failure.
    A = np.array([[-1e-5, 1.0], [0.0, -1e-5]])
    cert = solve_lyapunov(A, time="continuous")
    assert float(np.min(np.linalg.eigvalsh(cert.P))) > 0.0
    residual = A.T @ cert.P + cert.P @ A + np.eye(2)
    relative = float(np.max(np.abs(residual))) / float(np.max(np.abs(A.T @ cert.P)))
    assert relative < 1e-9
    assert float(np.max(np.abs(cert.P))) > 1e13


def test_a_scale_float64_cannot_resolve_is_still_refused():
    # Two decades further and the identity is no longer recoverable against Q.
    # That is a refusal, not a certificate with a loose tolerance.
    with pytest.raises(ValueError, match="not resolvable in float64"):
        solve_lyapunov(np.array([[-1e-7, 1.0], [0.0, -1e-7]]), time="continuous")


def test_the_residual_gate_is_unchanged_for_well_scaled_plants():
    # The widened tolerance must not touch ordinary problems: there the
    # backward term is negligible and the gate is still 1e-8 * ||Q||.
    for plant in (hurwitz2(),):
        cert = solve_lyapunov(plant.A, time=plant.time)
        residual = float(
            np.max(np.abs(decrease_matrix(plant.A, cert.P, time=plant.time) + np.eye(2)))
        )
        assert residual < 1e-8
