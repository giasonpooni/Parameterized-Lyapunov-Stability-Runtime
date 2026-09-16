"""Plain-text reports written next to the examples."""

from __future__ import annotations

from pathlib import Path

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


def write_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
