"""Write the discrete-guest fixture SVG from the live i64 twins."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lyapunov.discrete_guest import (  # noqa: E402
    FIXTURE_DECREASE,
    FIXTURE_DEVELOPABLE,
    FIXTURE_JACOBI,
    FIXTURE_V_PUSH,
    run_developable_star,
    run_discrete_decrease,
    run_jacobi_steps,
    run_v_push,
)


def _bar(x: float, y: float, w: float, h: float, label: str, value: str) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1b1f24" stroke="#c8a24a"/>'
        f'<text x="{x + 8}" y="{y + 22}" fill="#e8e4d9" font-family="ui-monospace,monospace" font-size="13">{label}</text>'
        f'<text x="{x + w - 8}" y="{y + 22}" text-anchor="end" fill="#c8a24a" font-family="ui-monospace,monospace" font-size="13">{value}</text>'
    )


def main() -> None:
    vp = run_v_push(**FIXTURE_V_PUSH)
    dec = run_discrete_decrease(**FIXTURE_DECREASE)
    jac = run_jacobi_steps(**FIXTURE_JACOBI)
    dev = run_developable_star(**FIXTURE_DEVELOPABLE)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="264" viewBox="0 0 720 264">
  <rect width="720" height="264" fill="#0f1216"/>
  <text x="24" y="28" fill="#e8e4d9" font-family="ui-sans-serif,sans-serif" font-size="16">i64 discrete-guest fixtures</text>
  <text x="24" y="48" fill="#8b8374" font-family="ui-monospace,monospace" font-size="11">computational-integrity-only · proof_status=NOT_CHECKED · may_authorize=false</text>
  {_bar(24, 68, 672, 36, "V-push-v1  V = V'", str(vp.outputs["V"]))}
  {_bar(24, 112, 672, 36, "discrete-decrease-v1  dV", str(dec.outputs["delta_V"]))}
  {_bar(24, 156, 672, 36, "jacobi-step-v1  j after 4 flat steps", str(jac.outputs["j_final"]))}
  {_bar(24, 200, 672, 36, "developable-star-v1  max |triple|", str(dev.outputs["max_abs_triple"]))}
</svg>
"""
    out = ROOT / "results" / "discrete_guest_fixture.svg"
    out.write_text(svg, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
