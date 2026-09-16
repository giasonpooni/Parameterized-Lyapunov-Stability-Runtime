//! Host: execute or prove the discrete-morphisms guest.
//!
//!   SP1_PROVER=cpu cargo run --release -- --execute --kind 1
//!   SP1_PROVER=cpu cargo run --release -- --prove --kind 1

use clap::Parser;
use sp1_sdk::{include_elf, HashableKey, ProverClient, SP1Stdin};

pub const ELF: &[u8] = include_elf!("discrete-morphisms-sp1-program");

#[derive(Parser, Debug)]
struct Args {
    #[arg(long, default_value_t = 1)]
    kind: u32,
    #[arg(long, default_value_t = false)]
    prove: bool,
    #[arg(long, default_value = "receipt.json")]
    out: String,
}

fn main() {
    let args = Args::parse();
    let client = ProverClient::from_env();
    let mut stdin = SP1Stdin::new();
    stdin.write(&args.kind);
    let (pk, vk) = client.setup(ELF);
    let vk_digest = vk.bytes32();

    if !args.prove {
        let (public_values, report) = client.execute(ELF, &stdin).run().expect("execute");
        let words = read_i64s(&public_values.to_vec());
        let body = serde_json::json!({
            "mode": "execute",
            "kind": args.kind,
            "public_values": words,
            "cycles": report.total_instruction_count(),
            "verifying_key_digest": vk_digest,
            "proof_bytes_hex": serde_json::Value::Null,
            "claim_scope": "computational-integrity-only",
            "backend": "sp1",
            "proof_status": "NOT_CHECKED",
            "verified_by_bound_host": false,
            "may_authorize": false,
        });
        std::fs::write(&args.out, serde_json::to_string_pretty(&body).unwrap()).unwrap();
        println!("{body}");
        return;
    }

    let proof = client.prove(&pk, &stdin).run().expect("prove");
    client.verify(&proof, &vk).expect("verify");
    let proof_bytes = bincode::serialize(&proof).unwrap_or_default();
    let words = read_i64s(proof.public_values.as_slice());
    let body = serde_json::json!({
        "mode": "prove",
        "kind": args.kind,
        "public_values": words,
        "verifying_key_digest": vk_digest,
        "proof_bytes_hex": hex::encode(proof_bytes),
        "claim_scope": "computational-integrity-only",
        "backend": "sp1",
        "proof_status": "VERIFIED",
        "verified_by_bound_host": true,
        "may_authorize": false,
    });
    std::fs::write(&args.out, serde_json::to_string_pretty(&body).unwrap()).unwrap();
    println!("verified kind={} vk={}", args.kind, vk_digest);
}

fn read_i64s(bytes: &[u8]) -> Vec<i64> {
    bytes
        .chunks_exact(8)
        .map(|c| i64::from_le_bytes(c.try_into().unwrap()))
        .collect()
}
