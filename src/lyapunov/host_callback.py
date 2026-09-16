"""Host callback for discrete-guest statements.

VERIFIED only when a bound host set verified_by_bound_host after client.verify.
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
    statement_digest: str
    claim_scope: str
    backend: Backend
    verifying_key_digest: str | None
    proof_bytes_hex: str | None
    verified_by_bound_host: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "statement_digest": self.statement_digest,
            "claim_scope": self.claim_scope,
            "backend": self.backend,
            "verifying_key_digest": self.verifying_key_digest,
            "proof_bytes_hex": self.proof_bytes_hex,
            "verified_by_bound_host": self.verified_by_bound_host,
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
            "public_commit": self.statement.public_commit(),
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
    """Guest-facing public tuple: id, held, digest."""
    return statement.public_commit()


def attach(statement: GuestStatement, receipt: Receipt | None = None) -> CallbackResult:
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
    if receipt.verified_by_bound_host:
        return CallbackResult(
            statement=statement,
            proof_status="VERIFIED",
            backend="sp1",
            cargo_prove_available=available,
            receipt=receipt,
            notes="Bound host reported client.verify success. Still not an authorization.",
        )
    return CallbackResult(
        statement=statement,
        proof_status="NOT_CHECKED",
        backend="sp1",
        cargo_prove_available=available,
        receipt=receipt,
        notes="Proof bytes present but verified_by_bound_host is false.",
    )


def attach_fixture_suite(receipts: dict[str, Receipt] | None = None) -> dict[str, Any]:
    from .discrete_guest import (
        FIXTURE_DECREASE,
        FIXTURE_DEFECT,
        FIXTURE_JACOBI,
        FIXTURE_V_PUSH,
        run_developable_defect,
        run_discrete_decrease,
        run_jacobi_steps,
        run_v_push,
    )

    statements = (
        run_v_push(**FIXTURE_V_PUSH),
        run_discrete_decrease(**FIXTURE_DECREASE),
        run_jacobi_steps(**FIXTURE_JACOBI),
        run_developable_defect(**FIXTURE_DEFECT),
    )
    attached = [
        attach(stmt, None if receipts is None else receipts.get(stmt.statement_id)).to_dict()
        for stmt in statements
    ]
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
        "notes": "Four integer statements. Public commit is id/held/digest. may_authorize stays false.",
    }
