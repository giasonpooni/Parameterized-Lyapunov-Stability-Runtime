# SP1 program

Requires `cargo-prove` 6.8+ and the `succinct` rustup toolchain.

```bash
cd guests/discrete-morphisms-v1/sp1-program
cargo prove build
# ELF:
# target/elf-compilation/riscv64im-succinct-zkvm-elf/release/discrete-morphisms-sp1-program

cd ../sp1-host
# execute is the default; there is no --execute flag
SP1_PROVER=cpu cargo run --release -- --kind 1 --out receipt.json
SP1_PROVER=cpu cargo run --release -- --prove --kind 1 --out receipt.json
```

Execute is not a proof. Only `--prove` after `client.verify` may set
`verified_by_bound_host=true`. `may_authorize` stays false.
CI does not build this package.

This program commits `(kind, held, a, b)`. That is **not** the public
commit the guest law requires, which is `statement_id`, `held`,
`statement_digest`. Because `statement_digest` is not committed, a
receipt from this program is not bound to any particular statement, so
nothing here may set `verified_by_bound_host`. Closing that gap means
changing the committed public values and re-deriving the verifying key,
which needs `cargo prove`; see the "Known gap" section of `HANDOFF.md`.
Do not wire a new statement kind before then.
