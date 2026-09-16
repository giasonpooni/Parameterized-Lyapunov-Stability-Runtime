"""Integer guest twins. Proof backend is NOT_CHECKED."""

from __future__ import annotations

import unittest

from lyapunov.discrete_guest import (
    CLAIM_SCOPE,
    GuestRefuse,
    FIXTURE_DECREASE,
    FIXTURE_DEVELOPABLE,
    FIXTURE_DEVELOPABLE_FAIL,
    FIXTURE_JACOBI,
    FIXTURE_V_PUSH,
    det2,
    inv_unimodular,
    push_P,
    run_developable_star,
    run_discrete_decrease,
    run_fixture_suite,
    run_jacobi_steps,
    run_v_push,
)


class DiscreteGuestTests(unittest.TestCase):
    def test_v_push_holds_on_unimodular_fixture(self) -> None:
        stmt = run_v_push(**FIXTURE_V_PUSH)
        self.assertTrue(stmt.held)
        self.assertEqual(stmt.outputs["V"], 14)
        self.assertFalse(stmt.to_dict()["may_authorize"])

    def test_v_push_refuses_non_unimodular_T(self) -> None:
        with self.assertRaises(GuestRefuse):
            run_v_push(P=[[2, 0], [0, 3]], T=[[2, 0], [0, 2]], x=[1, 1])

    def test_discrete_decrease_holds_on_fixture(self) -> None:
        stmt = run_discrete_decrease(**FIXTURE_DECREASE)
        self.assertTrue(stmt.held)
        self.assertEqual(stmt.outputs["delta_V"], -4)

    def test_jacobi_flat_is_linear(self) -> None:
        stmt = run_jacobi_steps(**FIXTURE_JACOBI)
        self.assertEqual(stmt.outputs["trace"], [0, 1, 2, 3, 4, 5])

    def test_developable_star_holds_on_planar_fixture(self) -> None:
        stmt = run_developable_star(**FIXTURE_DEVELOPABLE)
        self.assertTrue(stmt.held)
        self.assertEqual(stmt.outputs["max_abs_triple"], 0)
        self.assertEqual(stmt.statement_id, "developable-star-v1")
        self.assertEqual(stmt.claim_scope, CLAIM_SCOPE)
        self.assertFalse(stmt.to_dict()["may_authorize"])

    def test_developable_star_fails_on_pyramid(self) -> None:
        stmt = run_developable_star(**FIXTURE_DEVELOPABLE_FAIL)
        self.assertFalse(stmt.held)
        self.assertGreater(stmt.outputs["max_abs_triple"], 0)

    def test_developable_star_refuses_degenerate(self) -> None:
        with self.assertRaises(GuestRefuse):
            run_developable_star(vertex=[0, 0, 0], neighbors=[[1, 0, 0], [2, 0, 0], [3, 0, 0]])

    def test_developable_star_refuses_short_star(self) -> None:
        with self.assertRaises(GuestRefuse):
            run_developable_star(vertex=[0, 0, 0], neighbors=[[1, 0, 0], [0, 1, 0]])

    def test_suite_does_not_claim_a_proof(self) -> None:
        suite = run_fixture_suite()
        self.assertEqual(suite["proof_status"], "NOT_CHECKED")
        self.assertFalse(suite["may_authorize"])
        self.assertEqual(len(suite["statements"]), 4)
        self.assertTrue(all(s["held"] for s in suite["statements"]))

    def test_push_P_matches_hand_calculation(self) -> None:
        self.assertEqual(push_P(((2, 0), (0, 3)), ((2, 1), (1, 1))), ((5, -8), (-8, 14)))
        self.assertEqual(det2(((2, 1), (1, 1))), 1)
        self.assertEqual(inv_unimodular(((2, 1), (1, 1))), ((1, -1), (-1, 2)))


if __name__ == "__main__":
    unittest.main()
