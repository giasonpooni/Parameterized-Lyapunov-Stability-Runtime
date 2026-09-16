# Discrete guest v1

Satellite of PLSR. Not a second certificate law.

## What this is

A named numeric contract for **exact i64** realizations of three discrete
maps that already exist as axioms or companions:

| statement_id | Map | Owner |
| --- | --- | --- |
| `V-push-v1` | \(V(x)=V'(Tx)\) after \(P'=T^{-T}PT^{-1}\) | PLSR |
| `discrete-decrease-v1` | \(x^\top(A^\top PA-P)x\le 0\) at one sample | PLSR |
| `jacobi-step-v1` | \(j_{n+1}=2j_n-j_{n-1}-h^2 K j_n\) | geodesic companion; hosted here only as an integer twin |

\(T\) must be unimodular (\(\det T=\pm 1\)) so \(P'\) stays in \(\mathbb{Z}\).
A non-unimodular \(T\) is refused. No clip. No nearest-PSD.

## What this is not

- Not an SP1 / RISC-V proof. `proof_status` is `NOT_CHECKED`.
- Not `may_authorize`. Not `traceable`.
- Not a float geodesic, not IEEE-754 in the guest, not a Lyapunov *solve*.
- Not imported into `gat`.
- Not JSPT. \(A\) and \(J\) stay inputs.

## Numeric contract `i64-unimodular-v1`

- All entries are `i64`.
- Dimension 2.
- \(P=P^\top\) and leading minors give a PD check on \(\mathbb{Z}^2\).
- Rounding mode: none. Values must already be integers.
- Host referee: the same integer functions. Float64 PLSR is used only
  to confirm the fixture identities off to the side; disagreement with
  the integer twin is a refuse, not a repair.

## How to attach a zkVM later

1. Compile `guests/discrete-morphisms-v1` as a RISC-V guest.
2. Public values = the `GuestStatement` fields (`statement_id`,
   contract, inputs digest, outputs).
3. Host callback verifies the receipt against `statement_digest`.
4. Scope string remains `computational-integrity-only`.

Until that callback exists, running the Python twin or the Rust CLI
is evaluation, not a proof.

## Run

```bash
PYTHONPATH=src python examples/discrete_guest.py
PYTHONPATH=src python -m unittest tests.test_discrete_guest -q
```
