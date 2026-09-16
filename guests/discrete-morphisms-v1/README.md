# discrete-morphisms-v1

Exact `i64` twins of `V-push-v1`, `discrete-decrease-v1`, and
`jacobi-step-v1`.

This crate does **not** depend on SP1. Compiling it to RISC-V and
proving it is a later host callback. Until then `proof_status` is
`NOT_CHECKED`.

```bash
cargo test
cargo run
```

Do not add `sp1-zkvm` here until a numeric contract pin exists and the
Python oracle still matches.
