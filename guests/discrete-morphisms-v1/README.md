# discrete-morphisms-v1

Exact `i64` twins of the four discrete-guest statements: `V-push-v1`,
`discrete-decrease-v1`, `jacobi-step-v1` and `developable-defect-v1`,
plus the `developable-star-v1` helper the defect statement is built on.

Every arithmetic result is range-checked with `checked_*`. Wrapping is not
exactness: a wrapped product would disagree with the Python twin in
`lyapunov.discrete_guest`, and a twin disagreement is a refuse, not a
repair. Both sides return an overflow refusal instead.

This crate does **not** depend on SP1. Compiling it to RISC-V and
proving it is a later host callback. Until then `proof_status` is
`NOT_CHECKED`.

```bash
cargo test
cargo run
```

`cargo run` prints one line per statement plus `claim_scope`,
`proof_status` and `may_authorize`. The printed coordinates are
host-oracle inputs; only `statement_id`, `held` and `statement_digest`
are ever public.

Do not add `sp1-zkvm` here until a numeric contract pin exists and the
Python oracle still matches.
