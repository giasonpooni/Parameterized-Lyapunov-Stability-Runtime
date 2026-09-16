"""Host callback refuses to mint VERIFIED without a bound verifier."""

from __future__ import annotations

import unittest

from lyapunov.discrete_guest import CLAIM_SCOPE, GuestRefuse, FIXTURE_V_PUSH, run_v_push
from lyapunov.host_callback import Receipt, attach, attach_fixture_suite, public_values


class HostCallbackTests(unittest.TestCase):
    def test_no_receipt_is_not_checked(self) -> None:
        stmt = run_v_push(**FIXTURE_V_PUSH)
        result = attach(stmt)
        self.assertEqual(result.proof_status, "NOT_CHECKED")
        self.assertFalse(result.to_dict()["may_authorize"])

    def test_public_values_are_id_held_digest(self) -> None:
        stmt = run_v_push(**FIXTURE_V_PUSH)
        pv = public_values(stmt)
        self.assertEqual(set(pv), {"statement_id", "held", "statement_digest"})
        self.assertEqual(pv["statement_digest"], stmt.digest())
        self.assertTrue(pv["held"])

    def test_mismatched_digest_refused(self) -> None:
        stmt = run_v_push(**FIXTURE_V_PUSH)
        rec = Receipt(
            statement_digest="0" * 64,
            claim_scope=CLAIM_SCOPE,
            backend="sp1",
            verifying_key_digest="vk",
            proof_bytes_hex="ab",
        )
        with self.assertRaises(GuestRefuse):
            attach(stmt, rec)

    def test_wrong_scope_refused(self) -> None:
        stmt = run_v_push(**FIXTURE_V_PUSH)
        rec = Receipt(
            statement_digest=stmt.digest(),
            claim_scope="the-building-is-safe",
            backend="sp1",
            verifying_key_digest="vk",
            proof_bytes_hex="ab",
        )
        with self.assertRaises(GuestRefuse):
            attach(stmt, rec)

    def test_opaque_bytes_do_not_become_verified(self) -> None:
        stmt = run_v_push(**FIXTURE_V_PUSH)
        rec = Receipt(
            statement_digest=stmt.digest(),
            claim_scope=CLAIM_SCOPE,
            backend="sp1",
            verifying_key_digest="deadbeef",
            proof_bytes_hex="cafebabe",
        )
        self.assertEqual(attach(stmt, rec).proof_status, "NOT_CHECKED")

    def test_bound_host_verify_is_verified_not_authorize(self) -> None:
        stmt = run_v_push(**FIXTURE_V_PUSH)
        rec = Receipt(
            statement_digest=stmt.digest(),
            claim_scope=CLAIM_SCOPE,
            backend="sp1",
            verifying_key_digest="vk",
            proof_bytes_hex="ab",
            verified_by_bound_host=True,
        )
        result = attach(stmt, rec)
        self.assertEqual(result.proof_status, "VERIFIED")
        self.assertFalse(result.to_dict()["may_authorize"])

    def test_suite_pin_shape(self) -> None:
        body = attach_fixture_suite()
        self.assertFalse(body["confirmed_out_of_development"])
        self.assertEqual(body["proof_status"], "NOT_CHECKED")
        self.assertEqual(body["callbacks"][-1]["public_commit"]["statement_id"], "developable-defect-v1")


if __name__ == "__main__":
    unittest.main()
