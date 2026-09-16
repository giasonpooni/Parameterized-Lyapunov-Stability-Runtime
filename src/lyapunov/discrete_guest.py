"""Scaled-integer discrete morphisms for a later zkVM guest.

Satellite. NumPy PLSR remains the float64 oracle.
Claim scope is always computational-integrity-only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Literal

CLAIM_SCOPE = "computational-integrity-only"
STATEMENT_V_PUSH = "V-push-v1"
STATEMENT_DECREASE = "discrete-decrease-v1"
STATEMENT_JACOBI = "jacobi-step-v1"
STATEMENT_DEVELOPABLE = "developable-star-v1"
STATEMENT_DEFECT = "developable-defect-v1"
NUMERIC_CONTRACT = "i64-unimodular-v1"
NUMERIC_CONTRACT_STAR = "i64-coplanar-star-v1"
NUMERIC_CONTRACT_DEFECT = "i64-sampled-defect-v1"


class GuestRefuse(ValueError):
    """The discrete map is not an admitted integer realization."""


def _as_i64(value: int | float, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise GuestRefuse(f"{name} must be an int, got {type(value).__name__}")
    if value < -(1 << 63) or value > (1 << 63) - 1:
        raise GuestRefuse(f"{name} overflows i64")
    return int(value)


def _mat2(values: list[list[int]], name: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if len(values) != 2 or any(len(row) != 2 for row in values):
        raise GuestRefuse(f"{name} must be 2x2")
    return (
        (_as_i64(values[0][0], f"{name}[0,0]"), _as_i64(values[0][1], f"{name}[0,1]")),
        (_as_i64(values[1][0], f"{name}[1,0]"), _as_i64(values[1][1], f"{name}[1,1]")),
    )


def _vec2(values: list[int], name: str) -> tuple[int, int]:
    if len(values) != 2:
        raise GuestRefuse(f"{name} must have length 2")
    return _as_i64(values[0], f"{name}[0]"), _as_i64(values[1], f"{name}[1]")


def _vec3(values: list[int], name: str) -> tuple[int, int, int]:
    if len(values) != 3:
        raise GuestRefuse(f"{name} must have length 3")
    return (
        _as_i64(values[0], f"{name}[0]"),
        _as_i64(values[1], f"{name}[1]"),
        _as_i64(values[2], f"{name}[2]"),
    )


def _sub(a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _require_symmetric(P: tuple[tuple[int, int], tuple[int, int]], name: str = "P") -> None:
    if P[0][1] != P[1][0]:
        raise GuestRefuse(f"{name} must be symmetric")


def det2(M: tuple[tuple[int, int], tuple[int, int]]) -> int:
    return M[0][0] * M[1][1] - M[0][1] * M[1][0]


def mul2(
    A: tuple[tuple[int, int], tuple[int, int]],
    B: tuple[tuple[int, int], tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int]]:
    return (
        (A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]),
        (A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]),
    )


def transpose(M: tuple[tuple[int, int], tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    return ((M[0][0], M[1][0]), (M[0][1], M[1][1]))


def apply2(M: tuple[tuple[int, int], tuple[int, int]], x: tuple[int, int]) -> tuple[int, int]:
    return (M[0][0] * x[0] + M[0][1] * x[1], M[1][0] * x[0] + M[1][1] * x[1])


def quadratic(P: tuple[tuple[int, int], tuple[int, int]], x: tuple[int, int]) -> int:
    Px = apply2(P, x)
    return x[0] * Px[0] + x[1] * Px[1]


def inv_unimodular(T: tuple[tuple[int, int], tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    d = det2(T)
    if d not in (1, -1):
        raise GuestRefuse(f"T must be unimodular (det ±1), got det={d}")
    return ((d * T[1][1], -d * T[0][1]), (-d * T[1][0], d * T[0][0]))


def push_P(
    P: tuple[tuple[int, int], tuple[int, int]],
    T: tuple[tuple[int, int], tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int]]:
    Tinv = inv_unimodular(T)
    return mul2(transpose(Tinv), mul2(P, Tinv))


def discrete_decrease_form(
    A: tuple[tuple[int, int], tuple[int, int]],
    P: tuple[tuple[int, int], tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int]]:
    AtP = mul2(transpose(A), P)
    return (
        (
            AtP[0][0] * A[0][0] + AtP[0][1] * A[1][0] - P[0][0],
            AtP[0][0] * A[0][1] + AtP[0][1] * A[1][1] - P[0][1],
        ),
        (
            AtP[1][0] * A[0][0] + AtP[1][1] * A[1][0] - P[1][0],
            AtP[1][0] * A[0][1] + AtP[1][1] * A[1][1] - P[1][1],
        ),
    )


def jacobi_step(j_prev: int, j: int, k: int, h2: int) -> int:
    if k not in (0, 1, -1):
        raise GuestRefuse("K must be 0, 1, or -1")
    h2 = _as_i64(h2, "h2")
    return 2 * j - j_prev - h2 * k * j


def jacobi_trace(j0: int, j1: int, k: int, h2: int, steps: int) -> list[int]:
    if steps < 1 or steps > 64:
        raise GuestRefuse("steps must be in 1..64")
    prev, cur = _as_i64(j0, "j0"), _as_i64(j1, "j1")
    out = [prev, cur]
    for _ in range(steps):
        nxt = jacobi_step(prev, cur, k, h2)
        out.append(nxt)
        prev, cur = cur, nxt
    return out


def coplanar_star(
    vertex: tuple[int, int, int],
    neighbors: tuple[tuple[int, int, int], ...],
) -> tuple[bool, tuple[int, int, int], list[int]]:
    if len(neighbors) < 3 or len(neighbors) > 8:
        raise GuestRefuse("star must have 3..8 neighbors")
    e0 = _sub(neighbors[0], vertex)
    e1 = _sub(neighbors[1], vertex)
    normal = _cross(e0, e1)
    if normal == (0, 0, 0):
        raise GuestRefuse("first two edges are collinear; star is degenerate")
    triples = [_dot(_sub(p, vertex), normal) for p in neighbors[2:]]
    held = all(t == 0 for t in triples)
    return held, normal, triples


def star_from_panel_graph(
    vertices: list[list[int]],
    edges: list[list[int]],
    center: int,
) -> tuple[tuple[int, int, int], tuple[tuple[int, int, int], ...]]:
    if not vertices:
        raise GuestRefuse("panel graph has no vertices")
    center = _as_i64(center, "center")
    if center < 0 or center >= len(vertices):
        raise GuestRefuse("center index out of range")
    nbr_idx: list[int] = []
    for k, edge in enumerate(edges):
        if len(edge) != 2:
            raise GuestRefuse(f"edges[{k}] must be a pair")
        i, j = _as_i64(edge[0], f"edges[{k}][0]"), _as_i64(edge[1], f"edges[{k}][1]")
        if i < 0 or j < 0 or i >= len(vertices) or j >= len(vertices):
            raise GuestRefuse(f"edges[{k}] index out of range")
        if i == center and j != center:
            nbr_idx.append(j)
        elif j == center and i != center:
            nbr_idx.append(i)
    if len(set(nbr_idx)) != len(nbr_idx):
        raise GuestRefuse("duplicate spoke in panel graph")
    v = _vec3(vertices[center], "vertices[center]")
    neighbors = tuple(_vec3(vertices[i], f"vertices[{i}]") for i in nbr_idx)
    return v, neighbors


@dataclass(frozen=True)
class GuestStatement:
    statement_id: str
    numeric_contract: str
    claim_scope: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    held: bool
    proof_status: Literal["NOT_CHECKED"]
    host_oracle_gap: float
    notes: str

    def digest(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()

    def public_commit(self) -> dict[str, Any]:
        """What a guest may commit. Coordinates stay off this tuple."""
        return {
            "statement_id": self.statement_id,
            "held": self.held,
            "statement_digest": self.digest(),
        }

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["statement_digest"] = self.digest()
        body["public_commit"] = self.public_commit()
        body["may_authorize"] = False
        body["traceable"] = False
        return body


def run_v_push(P: list[list[int]], T: list[list[int]], x: list[int]) -> GuestStatement:
    P_i = _mat2(P, "P")
    T_i = _mat2(T, "T")
    x_i = _vec2(x, "x")
    _require_symmetric(P_i)
    if det2(P_i) <= 0 or P_i[0][0] <= 0:
        raise GuestRefuse("P must be positive definite on Z^2 (leading minor and det)")
    P_prime = push_P(P_i, T_i)
    x_prime = apply2(T_i, x_i)
    V = quadratic(P_i, x_i)
    V_prime = quadratic(P_prime, x_prime)
    held = V == V_prime
    return GuestStatement(
        statement_id=STATEMENT_V_PUSH,
        numeric_contract=NUMERIC_CONTRACT,
        claim_scope=CLAIM_SCOPE,
        inputs={"P": P, "T": T, "x": x, "det_T": det2(T_i)},
        outputs={"P_prime": [list(P_prime[0]), list(P_prime[1])], "x_prime": list(x_prime), "V": V, "V_prime": V_prime},
        held=held,
        proof_status="NOT_CHECKED",
        host_oracle_gap=0.0 if held else float(abs(V - V_prime)),
        notes="Unimodular chart push of P. SP1 prover not attached.",
    )


def run_discrete_decrease(A: list[list[int]], P: list[list[int]], x: list[int]) -> GuestStatement:
    A_i = _mat2(A, "A")
    P_i = _mat2(P, "P")
    x_i = _vec2(x, "x")
    _require_symmetric(P_i)
    if det2(P_i) <= 0 or P_i[0][0] <= 0:
        raise GuestRefuse("P must be positive definite on Z^2")
    form = discrete_decrease_form(A_i, P_i)
    delta = quadratic(form, x_i)
    held = delta <= 0
    return GuestStatement(
        statement_id=STATEMENT_DECREASE,
        numeric_contract=NUMERIC_CONTRACT,
        claim_scope=CLAIM_SCOPE,
        inputs={"A": A, "P": P, "x": x},
        outputs={"decrease_form": [list(form[0]), list(form[1])], "delta_V": delta},
        held=held,
        proof_status="NOT_CHECKED",
        host_oracle_gap=0.0,
        notes="Discrete decrease at one sample. P is an input. No Lyapunov solve in the guest.",
    )


def run_jacobi_steps(j0: int, j1: int, k: int, h2: int, steps: int) -> GuestStatement:
    trace = jacobi_trace(j0, j1, k, h2, steps)
    return GuestStatement(
        statement_id=STATEMENT_JACOBI,
        numeric_contract=NUMERIC_CONTRACT,
        claim_scope=CLAIM_SCOPE,
        inputs={"j0": j0, "j1": j1, "K": k, "h2": h2, "steps": steps},
        outputs={"trace": trace, "j_final": trace[-1]},
        held=True,
        proof_status="NOT_CHECKED",
        host_oracle_gap=0.0,
        notes="Discrete Jacobi recurrence. Owner is the geodesic companion; PLSR only hosts the integer twin.",
    )


def run_developable_star(vertex: list[int], neighbors: list[list[int]]) -> GuestStatement:
    v = _vec3(vertex, "vertex")
    pts = tuple(_vec3(p, f"neighbors[{i}]") for i, p in enumerate(neighbors))
    held, normal, triples = coplanar_star(v, pts)
    defect = 0 if not triples else max(abs(t) for t in triples)
    return GuestStatement(
        statement_id=STATEMENT_DEVELOPABLE,
        numeric_contract=NUMERIC_CONTRACT_STAR,
        claim_scope=CLAIM_SCOPE,
        inputs={"vertex": vertex, "neighbors": neighbors},
        outputs={"normal": list(normal), "triples": triples, "defect": defect, "max_abs_triple": defect},
        held=held,
        proof_status="NOT_CHECKED",
        host_oracle_gap=0.0,
        notes="Coplanar star helper. Prefer developable-defect-v1 on a panel graph.",
    )


def run_developable_defect(
    vertices: list[list[int]],
    edges: list[list[int]],
    center: int,
) -> GuestStatement:
    """Sampled defect on a declared panel graph. held iff defect == 0.

    defect is max |triple product| of the center star against the first
    face normal. Exact i64. Not Sigma theta, not a facade stamp.
    Coordinates belong in inputs for the host oracle; public_commit
    is only statement_id, held, digest.
    """
    v, neighbors = star_from_panel_graph(vertices, edges, center)
    held, normal, triples = coplanar_star(v, neighbors)
    defect = 0 if not triples else max(abs(t) for t in triples)
    if held != (defect == 0):
        raise GuestRefuse("held and defect==0 must agree")
    return GuestStatement(
        statement_id=STATEMENT_DEFECT,
        numeric_contract=NUMERIC_CONTRACT_DEFECT,
        claim_scope=CLAIM_SCOPE,
        inputs={"vertices": vertices, "edges": edges, "center": center},
        outputs={"defect": defect, "normal": list(normal), "triples": triples},
        held=held,
        proof_status="NOT_CHECKED",
        host_oracle_gap=0.0,
        notes=(
            "Sampled K proxy on a panel graph. held iff defect=0. "
            "Public commit is id/held/digest. Coordinates stay private to the guest. "
            "Not an IFC entity. Do not import into gat."
        ),
    )


FIXTURE_V_PUSH = {"P": [[2, 0], [0, 3]], "T": [[2, 1], [1, 1]], "x": [1, 2]}
FIXTURE_DECREASE = {"A": [[0, 1], [0, 0]], "P": [[1, 0], [0, 1]], "x": [2, 3]}
FIXTURE_JACOBI = {"j0": 0, "j1": 1, "k": 0, "h2": 1, "steps": 4}
FIXTURE_DEVELOPABLE = {
    "vertex": [0, 0, 0],
    "neighbors": [[1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, -1, 0]],
}
FIXTURE_DEVELOPABLE_FAIL = {
    "vertex": [0, 0, 1],
    "neighbors": [[1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, -1, 0]],
}
FIXTURE_DEFECT = {
    "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, -1, 0]],
    "edges": [[0, 1], [0, 2], [0, 3], [0, 4]],
    "center": 0,
}
FIXTURE_DEFECT_FAIL = {
    "vertices": [[0, 0, 1], [1, 0, 0], [0, 1, 0], [-1, 0, 0], [0, -1, 0]],
    "edges": [[0, 1], [0, 2], [0, 3], [0, 4]],
    "center": 0,
}


def run_fixture_suite() -> dict[str, Any]:
    statements = [
        run_v_push(**FIXTURE_V_PUSH),
        run_discrete_decrease(**FIXTURE_DECREASE),
        run_jacobi_steps(**FIXTURE_JACOBI),
        run_developable_defect(**FIXTURE_DEFECT),
    ]
    return {
        "confirmed_out_of_development": False,
        "claim_scope": CLAIM_SCOPE,
        "proof_backend": "none",
        "proof_status": "NOT_CHECKED",
        "may_authorize": False,
        "numeric_contract": NUMERIC_CONTRACT,
        "statements": [s.to_dict() for s in statements],
        "notes": (
            "Integer twins. developable-defect-v1 public_commit is id/held/digest. "
            "Do not import this module into gat."
        ),
    }
