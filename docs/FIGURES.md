# Figures

README diagrams are seating charts. They do not authorize.

| Asset | Source | May claim |
| --- | --- | --- |
| Mermaid in README | hand-written, matches GATE.md | ownership split |
| `results/discrete_guest_fixture.svg` | `examples/write_figures.py` | V=V'=14, ΔV=-4, j=5, defect=0 on the i64 fixtures |

Every number in the figure is read off a statement the generator just ran;
`lyapunov.reports.render_guest_figure` is the single source, and
`tests/test_registry_coherence.py` compares the committed SVG against it.

Do not add phase portraits, spectrum plots, or a green "stable" badge.
`proof_status` stays `NOT_CHECKED` until a bound host verifies.
