"""Integer guest twins. Proof backend is NOT_CHECKED."""

from __future__ import annotations

import unittest

from lyapunov.discrete_guest import (
    CLAIM_SCOPE,
    GuestRefuse,
    FIXTURE_DECREASE,
    FIXTURE_DEFECT,
    FIXTURE_DEFECT_FAIL,
    FIXTURE_DEVELOPABLE,
    FIXTURE_DEVELOPABLE_FAIL,
    FIXTURE_JACOBI,
    FIXTURE_V_PUSH,
    run_developable_defect,
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

    def test_discrete_decrease_holds_on_fixture(self) -> None:
        self.assertEqual(run_discrete_decrease(**FIXTURE_DECREASE).outputs["delta_V"], -4)

    def test_jacobi_flat_is_linear(self) -> None:
        self.assertEqual(run_jacobi_steps(**FIXTURE_JACOBI).outputs["trace"], [0, 1, 2, 3, 4, 5])

    def test_developable_star_holds_on_planar_fixture(self) -> None:
        stmt = run_developable_star(**FIXTURE_DEVELOPABLE)
        self.assertTrue(stmt.held)
        self.assertEqual(stmt.outputs["defect"], 0)

    def test_developable_star_fails_on_pyramid(self) -> None:
        stmt = run_developable_star(**FIXTURE_DEVELOPABLE_FAIL)
        self.assertFalse(stmt.held)

    def test_defect_holds_on_panel_graph(self) -> None:
        stmt = run_developable_defect(**FIXTURE_DEFECT)
        self.assertEqual(stmt.statement_id, "developable-defect-v1")
        self.assertTrue(stmt.held)
        self.assertEqual(stmt.outputs["defect"], 0)
        pub = stmt.public_commit()
        self.assertEqual(set(pub), {"statement_id", "held", "statement_digest"})
        self.assertNotIn("vertices", pub)
        self.assertFalse(stmt.to_dict()["may_authorize"])
        self.assertEqual(stmt.claim_scope, CLAIM_SCOPE)

    def test_defect_fails_on_pyramid_graph(self) -> None:
        stmt = run_developable_defect(**FIXTURE_DEFECT_FAIL)
        self.assertFalse(stmt.held)
        self.assertGreater(stmt.outputs["defect"], 0)

    def test_defect_refuses_bad_center(self) -> None:
        with self.assertRaises(GuestRefuse):
            run_developable_defect(vertices=[[0, 0, 0]], edges=[], center=3)

    def test_suite_fourth_is_defect(self) -> None:
        suite = run_fixture_suite()
        self.assertEqual(len(suite["statements"]), 4)
        self.assertEqual(suite["statements"][-1]["statement_id"], "developable-defect-v1")
        self.assertEqual(suite["proof_status"], "NOT_CHECKED")
        self.assertTrue(all(s["held"] for s in suite["statements"]))


if __name__ == "__main__":
    unittest.main()
