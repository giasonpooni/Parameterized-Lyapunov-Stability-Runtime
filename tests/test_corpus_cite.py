from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_corpus_is_integrity_only_and_has_a_needle() -> None:
    document = json.loads((ROOT / "validation" / "invariant-corpus-v1.json").read_text())
    assert document["schema"] == "invariant-corpus-v1"
    assert document["claim_scope"] == "computational-integrity-only"
    ids = {row["id"] for row in document["invariants"] + document["free_coordinates"]}
    assert "cert.V-on-declared-A" in ids
    assert "var.x" in ids
