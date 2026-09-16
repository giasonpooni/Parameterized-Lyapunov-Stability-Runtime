# SP1 program

Requires `cargo-prove` 6.8+ and the `succinct` rustup toolchain.

```bash
cd guests/discrete-morphisms-v1/sp1-program
cargo prove build
# ELF:
# target/elf-compilation/riscv64im-succinct-zkvm-elf/release/discrete-morphisms-sp1-program

cd ../sp1-host
SP1_PROVER=cpu cargo run --release -- --execute --kind 1 --out receipt.json
SP1_PROVER=cpu cargo run --release -- --prove --kind 1 --out receipt.json
```

Execute is not a proof. Only `--prove` after `client.verify` may set
`verified_by_bound_host=true`. `may_authorize` stays false.
CI does not build this package.
