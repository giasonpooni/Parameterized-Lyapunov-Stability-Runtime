"""Plain-text reports and figures written next to the examples.

Every ``results/`` pin is built by a pure function here, so a test can
rebuild it and compare without running a writer. AGENTS.md: regenerate the
pins from their runner, never hand-edit the numbers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .checks import CheckResult
from .runtime import Verdict


def format_checks(title: str, checks: list[CheckResult]) -> str:
    lines = [f"# {title}", ""]
    for check in checks:
        mark = "PASS" if check.passed else "FAIL"
        lines.append(f"- [{mark}] {check.name}: {check.details}")
    lines.append("")
    return "\n".join(lines)


def format_verdicts(title: str, verdicts: list[Verdict]) -> str:
    lines = [f"# {title}", ""]
    for item in verdicts:
        lines.append(
            f"- {item.status}: {item.details} "
            f"(V={item.sample.value:.3e}, decrease={item.sample.decrease:.3e})"
        )
    lines.append("")
    return "\n".join(lines)


_SUMMARY_KEYS = ("V", "delta_V", "j_final", "defect")


def _summary(statement: dict[str, Any]) -> tuple[str, Any]:
    outputs = statement["outputs"]
    for key in _SUMMARY_KEYS:
        if key in outputs:
            return key, outputs[key]
    raise ValueError(
        f"{statement['statement_id']} reports no known summary key; add one to "
        "_SUMMARY_KEYS rather than printing an empty cell"
    )


def format_guest_suite(suite: dict[str, Any]) -> str:
    """Markdown for ``results/discrete_guest.md``.

    Each statement prints its own numeric contract: the suite spans more
    than one, so a single suite-level contract would be a false claim.
    """
    lines = [
        "# Discrete guest fixtures",
        "",
        "Integer twins only. `proof_status: NOT_CHECKED`.",
        f"claim_scope: `{suite['claim_scope']}`",
        "numeric_contracts: " + ", ".join(f"`{c}`" for c in suite["numeric_contracts"]),
        "",
        "Each statement carries its own contract; the suite spans more than one.",
        "",
        "| statement | contract | held | reported value |",
        "| --- | --- | --- | --- |",
    ]
    for statement in suite["statements"]:
        key, value = _summary(statement)
        lines.append(
            f"| `{statement['statement_id']}` | `{statement['numeric_contract']}` | "
            f"{statement['held']} | {key} = {value} |"
        )
    lines.extend(["", "Not a stamp. Not SI-traceable. Do not import into `gat`.", ""])
    return "\n".join(lines)


def format_host_callbacks(body: dict[str, Any]) -> str:
    """Markdown for ``results/host_callback.md``."""
    lines = [
        "# Host callback",
        "",
        f"proof_status: `{body['proof_status']}`",
        f"cargo_prove_available: `{body['cargo_prove_available']}`",
        f"claim_scope: `{body['claim_scope']}`",
        "",
        "| statement | held | callback |",
        "| --- | --- | --- |",
    ]
    for callback in body["callbacks"]:
        statement = callback["statement"]
        lines.append(
            f"| `{statement['statement_id']}` | {statement['held']} | "
            f"{callback['proof_status']} |"
        )
    lines.extend(["", "Not a stamp. Not verified. Do not import into gat.", ""])
    return "\n".join(lines)


def _bar(x: float, y: float, w: float, h: float, label: str, value: str) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1b1f24" stroke="#c8a24a"/>'
        f'<text x="{x + 8}" y="{y + 22}" fill="#e8e4d9" font-family="ui-monospace,monospace" font-size="13">{label}</text>'
        f'<text x="{x + w - 8}" y="{y + 22}" text-anchor="end" fill="#c8a24a" font-family="ui-monospace,monospace" font-size="13">{value}</text>'
    )


def render_guest_figure() -> str:
    """SVG for ``results/discrete_guest_fixture.svg``, built from the live twins.

    docs/FIGURES.md: a figure may only repeat a pin. Every number below is
    read off a statement this module just ran, never typed in.
    """
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

    rows = [
        ("V-push-v1  V = V'", run_v_push(**FIXTURE_V_PUSH).outputs["V"]),
        ("discrete-decrease-v1  dV", run_discrete_decrease(**FIXTURE_DECREASE).outputs["delta_V"]),
        ("jacobi-step-v1  j after 4 flat steps", run_jacobi_steps(**FIXTURE_JACOBI).outputs["j_final"]),
        ("developable-defect-v1  defect", run_developable_defect(**FIXTURE_DEFECT).outputs["defect"]),
    ]
    top, pitch, height = 68, 44, 264
    bars = "\n  ".join(
        _bar(24, top + index * pitch, 672, 36, label, str(value))
        for index, (label, value) in enumerate(rows)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}">
  <rect width="720" height="{height}" fill="#0f1216"/>
  <text x="24" y="28" fill="#e8e4d9" font-family="ui-sans-serif,sans-serif" font-size="16">i64 discrete-guest fixtures</text>
  <text x="24" y="48" fill="#8b8374" font-family="ui-monospace,monospace" font-size="11">computational-integrity-only · proof_status=NOT_CHECKED · may_authorize=false</text>
  {bars}
</svg>
"""


def quickstart_scenario() -> tuple[list[CheckResult], list[Verdict]]:
    """The checks and samples the quickstart pins.

    Built here rather than in the example so a test can rebuild the pin
    without running a writer, the same way the guest pins work.
    """
    import numpy as np

    from .certificates import quadratic
    from .charts import LinearChart
    from .checks import (
        check_chart_invariance,
        check_decrease,
        check_equation_residual,
        check_spectrum_agrees_with_certificate,
        check_vertices,
    )
    from .equation import certificate_for_plant
    from .plants import plant_from_jacobian
    from .reference_plants import discrete_contract, hurwitz2, two_vertex_lpv
    from .runtime import verdict

    continuous = hurwitz2()
    discrete = discrete_contract()
    lpv = two_vertex_lpv()
    supplied = plant_from_jacobian(continuous.A, name="A=J(x*)")

    Q = np.eye(2)
    v_cont = certificate_for_plant(continuous, Q, name="V-hurwitz")
    v_disc = certificate_for_plant(discrete, Q, name="V-discrete")
    v_supplied = certificate_for_plant(supplied, Q, name="V-from-J")
    v_lpv = quadratic(np.eye(2), name="V-lpv")

    checks = [
        check_equation_residual(continuous, v_cont, Q),
        check_equation_residual(discrete, v_disc, Q),
        check_spectrum_agrees_with_certificate(continuous, v_cont),
        check_spectrum_agrees_with_certificate(discrete, v_disc),
        check_decrease(supplied, v_supplied),
        check_chart_invariance(
            continuous,
            v_cont,
            LinearChart.scale([1000.0, 0.01], name="milli"),
            [0.5, -0.2],
        ),
        check_vertices(lpv, v_lpv, include_rates=False),
    ]
    samples = [
        verdict(continuous, v_cont, [0.0, 0.0]),
        verdict(continuous, v_cont, [0.8, -0.3]),
        verdict(lpv, v_lpv, [0.4, -0.2], theta=[0.0]),
        verdict(lpv, v_lpv, [0.4, -0.2], theta=[1.0]),
    ]
    return checks, samples


def format_quickstart() -> str:
    """Markdown for ``results/quickstart.md``."""
    checks, samples = quickstart_scenario()
    return format_checks("Quickstart checks", checks) + format_verdicts(
        "Runtime samples", samples
    )


def format_cross_reference(cases: list[Any], repo: str, sha: str) -> str:
    """Markdown for ``results/cross_reference.md``.

    AGENTS.md: commit the markdown the run wrote, and do not hand-edit those
    numbers. Building it here lets a test rebuild and compare it.
    """
    lines = [
        "# Cross-reference benchmarks",
        "",
        "Status: **in development**. `confirmed_out_of_development: false`.",
        "",
        f"JSPT pin: `{repo}@{sha}`.",
        "",
        "Matrices below are copied from sibling reference models or result",
        "files. This package does not import `sensitivity`. A refusal is a",
        "recorded outcome. These numbers are not a release certificate.",
        "",
        "| case | outcome | details |",
        "| --- | --- | --- |",
    ]
    for case in cases:
        details = case.details.replace("|", "\\|")
        lines.append(f"| `{case.name}` | {case.outcome} | {details} |")
    lines.extend(["", "## Numbers", ""])
    for case in cases:
        lines.append(f"### {case.name}")
        lines.append("")
        lines.append(f"Source: {case.source}")
        lines.append("")
        for key, value in case.numbers.items():
            lines.append(f"- `{key}` = {value:.12g}")
        lines.append("")
    return "\n".join(lines)


def write_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
