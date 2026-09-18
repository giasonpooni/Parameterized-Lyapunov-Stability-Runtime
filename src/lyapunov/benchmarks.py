"""Declared cross-reference cases against sibling published numbers.

These cases copy matrices that already appear in sibling result files or
reference models. They do not import those packages. A refusal is a
benchmark outcome, not a skipped row.

Status of this module: in development. Passing a case does not confirm
the runtime is out of development.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np

from .charts import LinearChart, push_certificate, push_plant
from .equation import certificate_for_plant, decrease_matrix, solve_lyapunov
from .plants import LinearPlant, plant_from_jacobian
from .runtime import evaluate


JSPT_SHA = "b957f701d8e20ddd9c756437c9d9208ab7d36f90"
JSPT_REPO = "giasonpooni/Jacobian-Sensitivity-Propagation-Testbed"


@dataclass(frozen=True)
class CaseResult:
    name: str
    source: str
    outcome: str
    details: str
    numbers: dict[str, float]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _try_solve(name: str, source: str, A: np.ndarray, time: str) -> CaseResult:
    try:
        cert = solve_lyapunov(A, time=time, name=f"V[{name}]")
    except ValueError as exc:
        eigs = np.linalg.eigvals(np.asarray(A, dtype=float))
        return CaseResult(
            name=name,
            source=source,
            outcome="refused",
            details=str(exc),
            numbers={
                "spectral_abscissa": float(np.max(np.real(eigs))),
                "spectral_radius": float(np.max(np.abs(eigs))),
            },
        )
    form = decrease_matrix(A, cert.P, time=time)
    sample = evaluate(
        LinearPlant(name=name, A=A, time=time),
        cert,
        np.ones(A.shape[0]),
    )
    return CaseResult(
        name=name,
        source=source,
        outcome="certified-sample",
        details="Lyapunov solve produced PD P; decrease matrix is ND at the unit sample",
        numbers={
            "min_eig_P": float(np.min(np.linalg.eigvalsh(cert.P))),
            "max_eig_decrease": float(np.max(np.linalg.eigvalsh(form))),
            "V_unit": sample.value,
            "decrease_unit": sample.decrease,
        },
    )


def jspt_affine2() -> CaseResult:
    A = np.array([[2.0, 0.5], [0.0, 1.5]], dtype=float)
    return _try_solve(
        "jspt-affine2",
        f"{JSPT_REPO}@{JSPT_SHA} reference_models.affine2",
        A,
        "continuous",
    )


def jspt_scaled_rotation_discrete() -> CaseResult:
    angle = np.pi / 5.0
    scale = 1.5
    c, s = np.cos(angle), np.sin(angle)
    A = scale * np.array([[c, -s], [s, c]], dtype=float)
    return _try_solve(
        "jspt-scaled-rotation",
        f"{JSPT_REPO}@{JSPT_SHA} reference_models.scaled_rotation",
        A,
        "discrete",
    )


def jspt_storage_as_dynamics() -> CaseResult:
    A = np.diag([2.0, 1.5])
    return _try_solve(
        "jspt-storage-J-as-A",
        f"{JSPT_REPO}@{JSPT_SHA} two_tank_storage Jacobian at any h",
        A,
        "continuous",
    )


def jspt_beam_jacobian_refused_as_A() -> CaseResult:
    load, length, stiffness = 10.0e3, 4.0, 8.0e6
    jac = np.array(
        [
            [
                length**3 / (48.0 * stiffness),
                3.0 * load * length**2 / (48.0 * stiffness),
                -load * length**3 / (48.0 * stiffness**2),
            ]
        ],
        dtype=float,
    )
    try:
        plant_from_jacobian(jac, name="beam-J")
        outcome = "accepted"
        details = "unexpected: non-square J was accepted as A"
    except ValueError as exc:
        outcome = "refused"
        details = str(exc)
    return CaseResult(
        name="jspt-beam-J-as-A",
        source=f"{JSPT_REPO}@{JSPT_SHA} simply_supported_midspan at [10e3, 4, 8e6]",
        outcome=outcome,
        details=details,
        numbers={
            "rows": float(jac.shape[0]),
            "cols": float(jac.shape[1]),
            "J00": float(jac[0, 0]),
            "J01": float(jac[0, 1]),
            "J02": float(jac[0, 2]),
        },
    )


def two_tank_leak_companion() -> CaseResult:
    """Dynamics companion that reuses JSPT tank areas, not FSRT.

    dh_i/dt = -(k_i / a_i) h_i with a = (2.0, 1.5) from two_tank_storage
    and declared leak coefficients k = (0.4, 0.3). This is not the
    JSPT storage Jacobian and not an FSRT filter.
    """
    areas = np.array([2.0, 1.5])
    leak = np.array([0.4, 0.3])
    A = -np.diag(leak / areas)
    return _try_solve(
        "two-tank-leak-companion",
        f"{JSPT_REPO}@{JSPT_SHA} areas from two_tank_storage; leak declared here",
        A,
        "continuous",
    )


def chart_invariance_on_companion() -> CaseResult:
    """Chart invariance of V on the leak companion.

    Note what this case does and does not exercise. The companion's
    ``A = -diag(0.4/2.0, 0.3/1.5)`` is ``-0.2 * I``, a scalar matrix, so
    ``T A T^-1 = A`` for every invertible ``T`` and the plant push is a
    no-op here. The certificate push is what moves. ``push_plant`` on a
    non-scalar ``A`` is covered by ``check_chart_invariance`` on
    ``hurwitz2`` in the quickstart and in tests/test_charts.py.
    """
    areas = np.array([2.0, 1.5])
    leak = np.array([0.4, 0.3])
    A = -np.diag(leak / areas)
    plant = LinearPlant(name="two-tank-leak-companion", A=A, time="continuous")
    cert = certificate_for_plant(plant, name="V-leak")
    chart = LinearChart.scale([1000.0, 1000.0], name="level-mm")
    primed_plant = push_plant(plant, chart)
    primed_cert = push_certificate(cert, chart)
    x = np.array([1.2, 0.8])
    left = evaluate(plant, cert, x)
    right = evaluate(primed_plant, primed_cert, chart.T @ x)
    return CaseResult(
        name="chart-invariance-leak-companion",
        source="PLSR chart push on the two-tank leak companion; levels from JSPT fluid example",
        outcome="certified-sample" if abs(left.value - right.value) < 1e-12 else "failed",
        details="V and decrease compared after x' = T x with T = 1000 I",
        numbers={
            "V": left.value,
            "V_prime": right.value,
            "V_gap": abs(left.value - right.value),
            "decrease": left.decrease,
            "decrease_prime": right.decrease,
            "P_frobenius": float(np.linalg.norm(cert.P, "fro")),
            "P_prime_frobenius": float(np.linalg.norm(primed_cert.P, "fro")),
        },
    )


def run_suite() -> list[CaseResult]:
    return [
        jspt_affine2(),
        jspt_scaled_rotation_discrete(),
        jspt_storage_as_dynamics(),
        jspt_beam_jacobian_refused_as_A(),
        two_tank_leak_companion(),
        chart_invariance_on_companion(),
    ]
