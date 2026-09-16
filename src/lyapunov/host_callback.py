"""Host callback for discrete-guest statements.

The kernel lives in ``discrete_guest``. This module only:

- packages public values
- accepts an optional receipt
- refuses a digest mismatch
- stays ``NOT_CHECKED`` unless a named backend actually verifies

SP1 is optional. Missing ``cargo-prove`` is not a pass.
Claim scope remains ``computational-integrity-only``.
``may_authorize`` is always false.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any, Literal

from .discrete_guest import CLAIM_SCOPE, GuestRefuse, GuestStatement

ProofStatus = Literal["NOT_CHECKED", "INVALID", "VERIFIED"]
Backend = Literal["none", "sp1"]


@dataclass(frozen=True)
class Receipt:
    """What a prover backend must hand back. Bytes are opaque to PLSR."""

    statement_digest: str
    claim_scope: str
    backend: Backend
    verifying_key_digest: str | None
    proof_bytes_hex: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "statement_digest": self.statement_digest,
            "claim_scope": self.claim_scope,
            "backend": self.backend,
            "verifying_key_digest": self.verifying_key_digest,
            "proof_bytes_hex": self.proof_bytes_hex,
        }


@dataclass(frozen=True)
class CallbackResult:
    statement: GuestStatement
    proof_status: ProofStatus
    backend: Backend
    cargo_prove_available: bool
    receipt: Receipt | None
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "statement": self.statement.to_dict(),
            "proof_status": self.proof_status,
            "backend": self.backend,
            "cargo_prove_available": self.cargo_prove_available,
            "receipt": None if self.receipt is None else self.receipt.to_dict(),
            "claim_scope": CLAIM_SCOPE,
            "may_authorize": False,
            "traceable": False,
            "notes": self.notes,
        }


def cargo_prove_available() -> bool:
    return shutil.which("cargo-prove") is not None


def public_values(statement: GuestStatement) -> dict[str, Any]:
    """Values a guest must commit. Not a proof."""
    body = statement.to_dict()
    return {
        "statement_id": body["statement_id"],
        "numeric_contract": body["numeric_contract"],
        "claim_scope": body["claim_scope"],
        "statement_digest": body["statement_digest"],
        "held": body["held"],
        "outputs": body["outputs"],
    }


def attach(
    statement: GuestStatement,
    receipt: Receipt | None = None,
) -> CallbackResult:
    """Attach a host callback to an already-evaluated statement.

    Without a receipt the status is NOT_CHECKED.
    A receipt with the wrong digest or the wrong scope is refused.
    A receipt that names backend ``sp1`` but carries no proof bytes is
    NOT_CHECKED. Opaque bytes without a bound verifier stay NOT_CHECKED.
    """
    available = cargo_prove_available()
    if receipt is None:
        return CallbackResult(
            statement=statement,
            proof_status="NOT_CHECKED",
            backend="none",
            cargo_prove_available=available,
            receipt=None,
            notes="No receipt. Evaluation of the integer twin is not a proof.",
        )
    if receipt.statement_digest != statement.digest():
        raise GuestRefuse("receipt statement_digest does not match the statement")
    if receipt.claim_scope != CLAIM_SCOPE:
        raise GuestRefuse("receipt claim_scope must be computational-integrity-only")
    if receipt.backend != "sp1":
        raise GuestRefuse(f"unsupported backend {receipt.backend!r}")
    if not receipt.proof_bytes_hex or not receipt.verifying_key_digest:
        return CallbackResult(
            statement=statement,
            proof_status="NOT_CHECKED",
            backend="sp1",
            cargo_prove_available=available,
            receipt=receipt,
            notes="SP1 named but proof bytes or vk digest missing. Not verified.",
        )
    return CallbackResult(
        statement=statement,
        proof_status="NOT_CHECKED",
        backend="sp1",
        cargo_prove_available=available,
        receipt=receipt,
        notes=(
            "Proof bytes present but this host has no SP1 verifier bound. "
            "Status stays NOT_CHECKED rather than trusting the label."
        ),
    )


def attach_fixture_suite(receipts: dict[str, Receipt] | None = None) -> dict[str, Any]:
    from .discrete_guest import (
        FIXTURE_DECREASE,
        FIXTURE_JACOBI,
        FIXTURE_V_PUSH,
        run_discrete_decrease,
        run_jacobi_steps,
        run_v_push,
    )

    statements = (
        run_v_push(**FIXTURE_V_PUSH),
        run_discrete_decrease(**FIXTURE_DECREASE),
        run_jacobi_steps(**FIXTURE_JACOBI),
    )
    attached = []
    for stmt in statements:
        rec = None if receipts is None else receipts.get(stmt.statement_id)
        attached.append(attach(stmt, rec).to_dict())
    return {
        "confirmed_out_of_development": False,
        "claim_scope": CLAIM_SCOPE,
        "proof_status": "NOT_CHECKED",
        "may_authorize": False,
        "cargo_prove_available": cargo_prove_available(),
        "guest_manifest": str(
            Path(__file__).resolve().parents[2]
            / "guests"
            / "discrete-morphisms-v1"
            / "sp1-program"
            / "README.md"
        ),
        "callbacks": attached,
        "notes": (
            "Host callback attached. Compile guests/discrete-morphisms-v1/"
            "sp1-program with cargo prove to mint a receipt. Until a bound "
            "verifier accepts that receipt, status is NOT_CHECKED."
        ),
    }
