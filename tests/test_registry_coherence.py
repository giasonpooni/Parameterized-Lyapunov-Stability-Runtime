"""The guest registry, the docs that describe it, and the results/ pins must agree.

docs/GATE.md went stale at "three discrete identities" because nothing read
it. These tests read it. A fifth statement, a renamed id, or a hand-edited
pin turns them red.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from lyapunov.benchmarks import run_suite
from lyapunov.discrete_guest import run_fixture_suite
from lyapunov.host_callback import attach_fixture_suite, cargo_prove_available
from lyapunov.reports import (
    format_guest_suite,
    format_host_callbacks,
    render_guest_figure,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

#: The declared suite, in order. developable-defect-v1 is last.
EXPECTED_IDS = (
    "V-push-v1",
    "discrete-decrease-v1",
    "jacobi-step-v1",
    "developable-defect-v1",
)

#: Docs that enumerate or count the guest statements.
ENUMERATING_DOCS = (
    "docs/GATE.md",
    "docs/DISCRETE-GUEST-v1.md",
    "HANDOFF.md",
    "guests/discrete-morphisms-v1/README.md",
)

NUMBER_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
}

#: Any phrase that states how many guest statements there are.
COUNT_PHRASE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight)\s+"
    r"(?:exact\s+|integer\s+|discrete\s+|i64\s+)*"
    r"(discrete identities|discrete maps|i64 twins|integer twins|"
    r"integer statements|guest statements|statements|identities|maps|twins)\b",
    re.IGNORECASE,
)


def _suite():
    return run_fixture_suite()


def test_registry_is_exactly_the_declared_four_in_order():
    ids = tuple(s["statement_id"] for s in _suite()["statements"])
    assert ids == EXPECTED_IDS


def test_every_statement_id_appears_in_every_enumerating_doc():
    missing: list[str] = []
    for relative in ENUMERATING_DOCS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for statement_id in EXPECTED_IDS:
            if statement_id not in text:
                missing.append(f"{relative} does not mention {statement_id}")
    assert not missing, "\n".join(missing)


#: Docs whose markdown table IS the statement registry, and the column the
#: statement_id sits in.
REGISTRY_TABLES = ("docs/GATE.md", "docs/DISCRETE-GUEST-v1.md")

TABLE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`(i64-[^`]+)`\s*\|", re.MULTILINE)


def test_each_registry_table_lists_exactly_the_suite_in_order():
    suite = {s["statement_id"]: s["numeric_contract"] for s in _suite()["statements"]}
    for relative in REGISTRY_TABLES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        rows = TABLE_ROW.findall(text)
        assert rows, f"{relative} has no statement table"
        assert [r[0] for r in rows] == list(EXPECTED_IDS), (
            f"{relative} statement table is {[r[0] for r in rows]}, "
            f"expected {list(EXPECTED_IDS)}"
        )
        for statement_id, contract in rows:
            assert contract == suite[statement_id], (
                f"{relative} gives {statement_id} the contract {contract}, "
                f"the code gives it {suite[statement_id]}"
            )


def test_no_doc_states_a_stale_statement_count():
    expected_word = NUMBER_WORDS[len(EXPECTED_IDS)]
    wrong: list[str] = []
    for relative in ENUMERATING_DOCS:
        for line_no, line in enumerate(
            (ROOT / relative).read_text(encoding="utf-8").splitlines(), start=1
        ):
            for match in COUNT_PHRASE.finditer(line):
                if match.group(1).lower() != expected_word:
                    wrong.append(f"{relative}:{line_no}: {match.group(0)!r} in {line.strip()!r}")
    assert not wrong, (
        f"the suite has {len(EXPECTED_IDS)} statements ({expected_word}); "
        "these lines say otherwise:\n" + "\n".join(wrong)
    )


def test_each_statement_carries_its_own_contract_and_the_suite_claims_no_single_one():
    suite = _suite()
    assert "numeric_contract" not in suite, (
        "a suite-level numeric_contract would be false: the statements span "
        f"{sorted({s['numeric_contract'] for s in suite['statements']})}"
    )
    contracts = {s["numeric_contract"] for s in suite["statements"]}
    assert suite["numeric_contracts"] == sorted(contracts)
    assert len(contracts) > 1


def test_public_commit_is_only_id_held_digest_for_every_statement():
    for statement in _suite()["statements"]:
        assert set(statement["public_commit"]) == {
            "statement_id",
            "held",
            "statement_digest",
        }, statement["statement_id"]
        assert statement["may_authorize"] is False
        assert statement["traceable"] is False
        assert statement["proof_status"] == "NOT_CHECKED"


def test_no_statement_leaks_coordinates_into_its_public_commit():
    for statement in _suite()["statements"]:
        blob = json.dumps(statement["public_commit"])
        for key in statement["inputs"]:
            assert key not in blob, f"{statement['statement_id']} leaks {key}"


def test_digest_is_stable_across_runs():
    first = {s["statement_id"]: s["statement_digest"] for s in _suite()["statements"]}
    second = {s["statement_id"]: s["statement_digest"] for s in _suite()["statements"]}
    assert first == second


# --- results/ pins are regenerated, never hand-edited (AGENTS.md) ---


def _committed(name: str) -> str:
    return (RESULTS / name).read_text(encoding="utf-8")


def test_discrete_guest_json_pin_matches_its_runner():
    expected = json.dumps(_suite(), indent=2) + "\n"
    assert _committed("discrete_guest.json") == expected, (
        "results/discrete_guest.json is stale; rerun examples/discrete_guest.py"
    )


def test_discrete_guest_md_pin_matches_its_runner():
    assert _committed("discrete_guest.md") == format_guest_suite(_suite()), (
        "results/discrete_guest.md is stale; rerun examples/discrete_guest.py"
    )


def test_figure_pin_matches_its_generator():
    assert _committed("discrete_guest_fixture.svg") == render_guest_figure(), (
        "results/discrete_guest_fixture.svg is stale; rerun examples/write_figures.py"
    )


def test_figure_only_repeats_numbers_the_guest_produced():
    # docs/FIGURES.md: a figure may only repeat a pin.
    figure = render_guest_figure()
    suite = _suite()
    for statement in suite["statements"]:
        assert statement["statement_id"] in figure
    values = {
        "V-push-v1": suite["statements"][0]["outputs"]["V"],
        "discrete-decrease-v1": suite["statements"][1]["outputs"]["delta_V"],
        "jacobi-step-v1": suite["statements"][2]["outputs"]["j_final"],
        "developable-defect-v1": suite["statements"][3]["outputs"]["defect"],
    }
    for value in values.values():
        assert f">{value}</text>" in figure
    assert "stable" not in figure.lower()
    assert "VERIFIED" not in figure


@pytest.mark.skipif(
    cargo_prove_available(),
    reason="the committed pin was written on a host without cargo-prove",
)
def test_host_callback_pins_match_their_runner():
    body = attach_fixture_suite()
    assert _committed("host_callback.md") == format_host_callbacks(body), (
        "results/host_callback.md is stale; rerun examples/host_callback.py"
    )
    committed = json.loads(_committed("host_callback.json"))
    assert committed["cargo_prove_available"] is False
    assert committed["proof_status"] == "NOT_CHECKED"
    assert committed["may_authorize"] is False
    assert [c["public_commit"]["statement_id"] for c in committed["callbacks"]] == list(
        EXPECTED_IDS
    )


def test_cross_reference_pin_matches_its_runner_apart_from_the_timestamp():
    committed = json.loads(_committed("cross_reference.json"))
    assert committed["confirmed_out_of_development"] is False
    assert [case.as_dict() for case in run_suite()] == committed["cases"], (
        "results/cross_reference.json is stale; rerun examples/cross_reference.py"
    )


def test_quickstart_pin_records_no_failure():
    text = _committed("quickstart.md")
    assert "[FAIL]" not in text
    assert "[PASS]" in text


def test_every_runner_output_is_tracked_or_ignored():
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    written = (
        "quickstart.md",
        "cross_reference.json",
        "cross_reference.md",
        "discrete_guest.json",
        "discrete_guest.md",
        "discrete_guest_fixture.svg",
        "host_callback.json",
        "host_callback.md",
    )
    for name in written:
        assert (RESULTS / name).exists(), (
            f"results/{name} is written by a runner but not committed, and "
            f"nothing in .gitignore explains it:\n{ignored}"
        )


def test_development_status_is_still_recorded_everywhere_it_is_claimed():
    assert _suite()["confirmed_out_of_development"] is False
    assert attach_fixture_suite()["confirmed_out_of_development"] is False
    assert json.loads(_committed("cross_reference.json"))["confirmed_out_of_development"] is False
