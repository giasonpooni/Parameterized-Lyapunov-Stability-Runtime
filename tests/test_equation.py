from __future__ import annotations

import numpy as np
import pytest

from lyapunov.checks import check_equation_residual, check_spectrum_agrees_with_certificate
from lyapunov.equation import certificate_for_plant, decrease_matrix, solve_lyapunov
from lyapunov.reference_plants import discrete_contract, hurwitz2


def test_continuous_equation_residual():
    plant = hurwitz2()
    Q = np.eye(2)
    cert = certificate_for_plant(plant, Q)
    check_equation_residual(plant, cert, Q).raise_for_failure()
    form = decrease_matrix(plant.A, cert.P, time="continuous")
    assert float(np.max(np.linalg.eigvalsh(form))) < 0.0


def test_discrete_equation_residual():
    plant = discrete_contract()
    Q = np.eye(2)
    cert = certificate_for_plant(plant, Q)
    check_equation_residual(plant, cert, Q).raise_for_failure()
    form = decrease_matrix(plant.A, cert.P, time="discrete")
    assert float(np.max(np.linalg.eigvalsh(form))) < 0.0


def test_spectrum_is_diagnostic_not_certificate():
    plant = hurwitz2()
    cert = certificate_for_plant(plant)
    check_spectrum_agrees_with_certificate(plant, cert).raise_for_failure()


def test_known_scalar_continuous():
    cert = solve_lyapunov([[-4.0]], Q=[[1.0]], time="continuous")
    np.testing.assert_allclose(cert.P, [[1.0 / 8.0]], atol=1e-12)


def test_known_scalar_discrete():
    cert = solve_lyapunov([[0.5]], Q=[[1.0]], time="discrete")
    np.testing.assert_allclose(cert.P, [[1.0 / 0.75]], atol=1e-12)


def test_oversize_solve_is_refused():
    with pytest.raises(ValueError, match="dim"):
        solve_lyapunov(np.eye(25) * -1.0)
