"""Integer guest twins. Proof backend is NOT_CHECKED."""

from __future__ import annotations

import unittest

from lyapunov.discrete_guest import (
    CLAIM_SCOPE,
    GuestRefuse,
    FIXTURE_DECREASE,
    FIXTURE_JACOBI,
    FIXTURE_V_PUSH,
    det2,
    inv_unimodular,
    push_P,
    run_discrete_decrease,
    run_fixture_suite,
    run_jacobi_steps,
    run_v_push,
)


class DiscreteGuestTests(unittest.TestCase):
    def test_v_push_holds_on_unimodular_fixture(self) -> None:
        stmt = run_v_push(**FIXTURE_V_PUSH)
        self.assertTrue(stmt.held)
        self.assertEqual(stmt.outputs["V"], stmt.outputs["V_prime"])
        self.assertEqual(stmt.outputs["V"], 14)
        self.assertEqual(stmt.proof_status, "NOT_CHECKED")
        self.assertEqual(stmt.claim_scope, CLAIM_SCOPE)
        body = stmt.to_dict()
        self.assertFalse(body["may_authorize"])
        self.assertFalse(body["traceable"])

    def test_v_push_refuses_non_unimodular_T(self) -> None:
        with self.assertRaises(GuestRefuse):
            run_v_push(P=[[2, 0], [0, 3]], T=[[2, 0], [0, 2]], x=[1, 1])

    def test_v_push_refuses_nonsymmetric_P(self) -> None:
        with self.assertRaises(GuestRefuse):
            run_v_push(P=[[2, 1], [0, 3]], T=[[1, 0], [0, 1]], x=[1, 0])

    def test_v_push_refuses_non_pd_P(self) -> None:
        with self.assertRaises(GuestRefuse):
            run_v_push(P=[[1, 0], [0, -1]], T=[[1, 0], [0, 1]], x=[1, 1])

    def test_inverse_roundtrip(self) -> None:
        T = ((2, 1), (1, 1))
        Tinv = inv_unimodular(T)
        self.assertEqual(det2(T), 1)
        self.assertEqual(Tinv, ((1, -1), (-1, 2)))

    def test_push_P_matches_hand_calculation(self) -> None:
        P = ((2, 0), (0, 3))
        T = ((2, 1), (1, 1))
        self.assertEqual(push_P(P, T), ((5, -8), (-8, 14)))

    def test_discrete_decrease_holds_on_fixture(self) -> None:
        stmt = run_discrete_decrease(**FIXTURE_DECREASE)
        self.assertTrue(stmt.held)
        self.assertEqual(stmt.outputs["delta_V"], -4)

    def test_discrete_decrease_refuses_when_sample_increases(self) -> None:
        stmt = run_discrete_decrease(A=[[2, 0], [0, 2]], P=[[1, 0], [0, 1]], x=[1, 0])
        self.assertFalse(stmt.held)
        self.assertGreater(stmt.outputs["delta_V"], 0)

    def test_jacobi_flat_is_linear(self) -> None:
        stmt = run_jacobi_steps(**FIXTURE_JACOBI)
        self.assertEqual(stmt.outputs["trace"], [0, 1, 2, 3, 4, 5])

    def test_jacobi_refuses_bad_K(self) -> None:
        with self.assertRaises(GuestRefuse):
            run_jacobi_steps(j0=0, j1=1, k=2, h2=1, steps=1)

    def test_suite_does_not_claim_a_proof(self) -> None:
        suite = run_fixture_suite()
        self.assertFalse(suite["confirmed_out_of_development"])
        self.assertEqual(suite["proof_status"], "NOT_CHECKED")
        self.assertFalse(suite["may_authorize"])
        self.assertEqual(len(suite["statements"]), 3)
        self.assertTrue(all(s["held"] for s in suite["statements"]))


if __name__ == "__main__":
    unittest.main()
