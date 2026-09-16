# SP1 program (optional)

Wraps the i64 kernels in `../src/lib.rs`.

This directory is **not** part of the library crate. CI does not build it.

```bash
# After sp1up / cargo-prove is on PATH:
# 1. Uncomment sp1-zkvm in Cargo.toml
# 2. cargo prove build
# 3. Host: prove kind=1|2|3, bind receipt.statement_digest to the
#    Python GuestStatement.digest(), claim_scope=computational-integrity-only
```

Until that host verifier is bound in `lyapunov.host_callback.attach`,
status is `NOT_CHECKED`. Opaque proof bytes are not accepted as
`VERIFIED`. `may_authorize` stays false.
