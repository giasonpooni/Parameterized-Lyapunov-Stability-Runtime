"""Parameterized Lyapunov Stability Runtime.

This package owns certificate structure ``V``. Linearization
``A = J_f(x*)`` is an input, formed in JSPT or supplied by the caller.
"""

from .benchmarks import CaseResult, run_suite
from .certificates import (
    AffineCertificate,
    QuadraticCertificate,
    affine_quadratic,
    quadratic,
)
from .charts import LinearChart, push_certificate, push_plant
from .checks import (
    CheckResult,
    check_chart_invariance,
    check_decrease,
    check_equation_residual,
    check_spectrum_agrees_with_certificate,
    check_vertices,
    spectral_abscissa,
    spectral_radius,
)
from .constitution import MAX_KRONECKER_DIM, MIN_DECREASE_MARGIN, SYMMETRY_ATOL
from .equation import certificate_for_plant, decrease_matrix, solve_lyapunov
from .plants import (
    AffinePlant,
    LinearPlant,
    affine_box_plant,
    constant_plant,
    plant_from_jacobian,
)
from .reference_plants import reference_catalogue
from .discrete_guest import (
    CLAIM_SCOPE as GUEST_CLAIM_SCOPE,
    GuestRefuse,
    GuestStatement,
    run_developable_defect,
    run_developable_star,
    run_discrete_decrease,
    run_fixture_suite,
    run_jacobi_steps,
    run_v_push,
)
from .host_callback import CallbackResult, Receipt, attach, attach_fixture_suite, public_values
from .runtime import CertificateSample, Verdict, evaluate, verdict

__all__ = [
    "AffineCertificate",
    "AffinePlant",
    "CallbackResult",
    "CaseResult",
    "CertificateSample",
    "CheckResult",
    "GUEST_CLAIM_SCOPE",
    "GuestRefuse",
    "GuestStatement",
    "LinearChart",
    "LinearPlant",
    "MAX_KRONECKER_DIM",
    "MIN_DECREASE_MARGIN",
    "QuadraticCertificate",
    "Receipt",
    "SYMMETRY_ATOL",
    "Verdict",
    "affine_box_plant",
    "affine_quadratic",
    "attach",
    "attach_fixture_suite",
    "certificate_for_plant",
    "check_chart_invariance",
    "check_decrease",
    "check_equation_residual",
    "check_spectrum_agrees_with_certificate",
    "check_vertices",
    "constant_plant",
    "decrease_matrix",
    "evaluate",
    "plant_from_jacobian",
    "public_values",
    "push_certificate",
    "push_plant",
    "quadratic",
    "reference_catalogue",
    "run_developable_defect",
    "run_developable_star",
    "run_discrete_decrease",
    "run_fixture_suite",
    "run_jacobi_steps",
    "run_suite",
    "run_v_push",
    "solve_lyapunov",
    "spectral_abscissa",
    "spectral_radius",
    "verdict",
]

__version__ = "0.1.0"
