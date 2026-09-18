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
    r"\b(one|two|three|four|five|six|seven|eight|\d+)\s+"
    # qualifiers may be hyphenated: "four discrete-guest statements"
    r"(?:[A-Za-z0-9`-]+\s+){0,3}?"
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
    assert len(EXPECTED_IDS) in NUMBER_WORDS, (
        "extend NUMBER_WORDS before adding a ninth statement"
    )
    expected_word = NUMBER_WORDS[len(EXPECTED_IDS)]
    expected = {expected_word, str(len(EXPECTED_IDS))}
    wrong: list[str] = []
    for relative in ENUMERATING_DOCS:
        for line_no, line in enumerate(
            (ROOT / relative).read_text(encoding="utf-8").splitlines(), start=1
        ):
            for match in COUNT_PHRASE.finditer(line):
                if match.group(1).lower() not in expected:
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
    # Structural, not a substring scan: the commit carries a sha256 hex
    # digest, so a future single-letter input key such as "a" would match it
    # by accident and fail for no reason.
    for statement in _suite()["statements"]:
        commit = statement["public_commit"]
        assert set(commit) == {"statement_id", "held", "statement_digest"}
        assert set(commit) & set(statement["inputs"]) == set()
        assert set(commit) & set(statement["outputs"]) == set()
        # Compare types too: in Python 1 == True, so an integer input of 1
        # would otherwise "match" the boolean held and fail for no reason.
        published = (commit["statement_id"], commit["statement_digest"])
        for key, value in statement["inputs"].items():
            assert not any(
                type(value) is type(shown) and value == shown for shown in published
            ), f"{statement['statement_id']} publishes the input {key}"
        assert isinstance(commit["held"], bool)


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


def test_quickstart_pin_matches_its_generator():
    from lyapunov.reports import format_quickstart

    assert _committed("quickstart.md") == format_quickstart(), (
        "results/quickstart.md is stale; rerun examples/quickstart.py"
    )
    assert "[FAIL]" not in _committed("quickstart.md")


def test_cross_reference_md_pin_matches_its_generator():
    from lyapunov.benchmarks import JSPT_REPO, JSPT_SHA
    from lyapunov.reports import format_cross_reference

    assert _committed("cross_reference.md") == format_cross_reference(
        run_suite(), JSPT_REPO, JSPT_SHA
    ), "results/cross_reference.md is stale; rerun examples/cross_reference.py"


@pytest.mark.skipif(
    cargo_prove_available(),
    reason="the committed pin was written on a host without cargo-prove",
)
def test_host_callback_json_pin_matches_its_runner():
    # Field-by-field, not a spot check: a hand-edited pin with a flipped
    # held, a fabricated digest or proof_status VERIFIED must not ship green.
    expected = json.dumps(attach_fixture_suite(), indent=2) + "\n"
    assert _committed("host_callback.json") == expected, (
        "results/host_callback.json is stale or hand-edited; "
        "rerun examples/host_callback.py"
    )


def test_no_committed_pin_carries_an_absolute_path():
    for pin in RESULTS.iterdir():
        text = pin.read_text(encoding="utf-8")
        assert "/home/" not in text and "C:\\" not in text, (
            f"{pin.name} pins one machine's layout into the record"
        )


#: An assertion of authority, as opposed to prose forbidding one. Matching
#: the word anywhere would flag GATE.md's own "Do not report VERIFIED
#: without a bound verifier", which is the line that makes the rule.
ASSERTED_AUTHORITY = (
    '"proof_status": "VERIFIED"',
    '"may_authorize": true',
    '"traceable": true',
    '"verified_by_bound_host": true',
)


def test_no_pin_asserts_authority_it_does_not_have():
    offenders: list[str] = []
    for pin in sorted(p for p in RESULTS.iterdir() if p.is_file()):
        for number, line in enumerate(pin.read_text(encoding="utf-8").splitlines(), 1):
            for claim in ASSERTED_AUTHORITY:
                if claim in line:
                    offenders.append(f"{pin.name}:{number}: {line.strip()[:90]}")
    assert not offenders, offenders


def test_no_registry_table_row_claims_verification():
    # A table row is an assertion about a statement. Prose is not.
    offenders: list[str] = []
    for relative in REGISTRY_TABLES:
        for number, line in enumerate(
            (ROOT / relative).read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.lstrip().startswith("|"):
                continue
            lowered = line.lower()
            if "verified" in lowered or "may_authorize" in lowered or "traceable" in lowered:
                offenders.append(f"{relative}:{number}: {line.strip()[:90]}")
    assert not offenders, offenders


def test_every_runner_output_is_tracked_by_git():
    import subprocess

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
    try:
        listed = subprocess.run(
            ["git", "ls-files", "results"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        pytest.skip(f"git unavailable: {exc}")
    tracked = {name.split("/")[-1] for name in listed}
    missing = [name for name in written if name not in tracked]
    assert not missing, (
        f"written by a runner but not tracked by git, so a fresh clone lacks "
        f"them: {missing}"
    )


def test_development_status_is_still_recorded_everywhere_it_is_claimed():
    assert _suite()["confirmed_out_of_development"] is False
    assert attach_fixture_suite()["confirmed_out_of_development"] is False
    assert json.loads(_committed("cross_reference.json"))["confirmed_out_of_development"] is False


def test_the_public_surface_is_sorted_and_matches_what_is_imported():
    import lyapunov

    assert lyapunov.__all__ == sorted(lyapunov.__all__), "__all__ is not sorted"
    assert len(lyapunov.__all__) == len(set(lyapunov.__all__)), "__all__ has duplicates"
    missing = [name for name in lyapunov.__all__ if not hasattr(lyapunov, name)]
    assert not missing, f"__all__ names nothing imports: {missing}"
    public = {
        name
        for name in dir(lyapunov)
        if not name.startswith("_") and name not in {"annotations"}
    }
    submodules = {
        "benchmarks", "certificates", "charts", "checks", "constitution",
        "discrete_guest", "equation", "host_callback", "linalg", "plants",
        "reference_plants", "reports", "runtime",
    }
    undeclared = public - set(lyapunov.__all__) - submodules
    assert not undeclared, f"public but not in __all__: {sorted(undeclared)}"
