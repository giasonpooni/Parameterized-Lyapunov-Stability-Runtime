# Discrete guest v1

Satellite of PLSR. Not a second certificate law.

## What this is

A named numeric contract for **exact i64** realizations of four discrete
maps that already exist as axioms or companions:

| statement_id | numeric contract | Map | Owner |
| --- | --- | --- | --- |
| `V-push-v1` | `i64-unimodular-v1` | \(V(x)=V'(Tx)\) after \(P'=T^{-T}PT^{-1}\) | PLSR |
| `discrete-decrease-v1` | `i64-unimodular-v1` | \(x^\top(A^\top PA-P)x\le 0\) at one sample | PLSR |
| `jacobi-step-v1` | `i64-unimodular-v1` | \(j_{n+1}=2j_n-j_{n-1}-h^2 K j_n\) | geodesic companion; hosted here only as an integer twin |
| `developable-defect-v1` | `i64-sampled-defect-v1` | sampled defect \(=0\) on a declared panel graph | PLSR |

There is **no suite-level contract**. Each statement carries its own, and
`run_fixture_suite()` reports `numeric_contracts` as a list.

`developable-star-v1` under `i64-coplanar-star-v1` is a helper that takes a
vertex and its spokes directly. Prefer `developable-defect-v1`, which reads
the same star out of a declared panel graph. It is not a suite member.

\(T\) must be unimodular (\(\det T=\pm 1\)) so \(P'\) stays in \(\mathbb{Z}\).
A non-unimodular \(T\) is refused. No clip. No nearest-PSD.

## What this is not

- Not an SP1 / RISC-V proof. `proof_status` is `NOT_CHECKED`.
- Not `may_authorize`. Not `traceable`.
- Not a float geodesic, not IEEE-754 in the guest, not a Lyapunov *solve*.
- Not imported into `gat`.
- Not JSPT. \(A\) and \(J\) stay inputs.

The defect is \(\max |(p-v)\cdot n|\) over the spokes of the star. It is a
sampled proxy, never an angle sum \(\sum\theta=2\pi\), and never a facade
stamp: `held` is a statement about arithmetic, not about a building.

## Numeric contracts

`i64-unimodular-v1`

- All entries are `i64`. Dimension 2.
- \(P=P^\top\) and leading minors give a PD check on \(\mathbb{Z}^2\).
- \(\det T=\pm 1\).

`i64-coplanar-star-v1` and `i64-sampled-defect-v1`

- All coordinates are `i64`. Points are 3-vectors; 3 to 8 spokes.
- The normal is \(e_0\times e_1\) from the first two spokes. Collinear first
  two spokes are a refusal, not a repair.
- `i64-sampled-defect-v1` additionally reads the star out of a declared
  panel graph: a duplicate spoke or an out-of-range index is a refusal.

Common to all of them

- Rounding mode: none. Values must already be integers.
- **Exactness is the contract.** Python integers are unbounded and Rust
  `i64` wraps, so any computed value outside `i64` is refused on both
  sides. Returning a bignum on one side and a wrapped value on the other
  would be a silent disagreement between the twins.
- Host referee: the same integer functions. Float64 PLSR is used only to
  confirm the fixture identities off to the side; disagreement with the
  integer twin is a refuse, not a repair. `host_oracle_gap` is `None`
  whenever no float64 oracle was consulted, which is every statement here
  — a hardcoded `0.0` would read as "the oracle agreed exactly".

## Public values

A guest may commit exactly three fields:

```text
statement_id, held, statement_digest
```

Coordinates, matrices, traces and defects stay in `inputs` / `outputs` for
the host oracle and never reach the public tuple. `public_commit()` is the
only sanctioned shape, and `tests/test_registry_coherence.py` holds every
statement to it.

## How to attach a zkVM later

1. Compile `guests/discrete-morphisms-v1` as a RISC-V guest.
2. Commit `statement_id`, `held` and `statement_digest` as the public
   values — the same three fields as `public_commit()`, and nothing else.
   Do not commit inputs, an inputs digest, or outputs.
3. Host callback verifies the receipt against `statement_digest`. Because
   the digest is committed by the guest, the receipt is then bound to the
   statement it came from.
4. Scope string remains `computational-integrity-only`.

The SP1 program in `sp1-program/` does not do step 2 yet: it commits
`(kind, held, a, b)`. That gap is recorded in `HANDOFF.md` and is why
`proof_status` stays `NOT_CHECKED` regardless of what that program emits.
Until that callback exists, running the Python twin or the Rust CLI is
evaluation, not a proof.

## Run

```bash
uv run --python 3.13 python examples/discrete_guest.py
uv run --python 3.13 python examples/host_callback.py
uv run --python 3.13 --dev pytest -q tests/test_discrete_guest.py
```

Without `uv`, from the repository root:

```bash
PYTHONPATH=src python examples/discrete_guest.py
PYTHONPATH=src python -m unittest tests.test_discrete_guest -v
```

The Rust twin needs no `cargo-prove`:

```bash
cd guests/discrete-morphisms-v1 && cargo test && cargo run
```
