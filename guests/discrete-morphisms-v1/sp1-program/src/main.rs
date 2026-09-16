//! SP1 guest wrapper around the i64 kernels.
//!
//! Built with `cargo prove build` after uncommenting `sp1-zkvm` in
//! Cargo.toml. Native `cargo build` of this package is a source fixture
//! only: the zkVM entrypoint is cfg-gated.
//!
//! Public values committed by the guest, in order:
//!   kind u32   (1=V-push, 2=decrease, 3=jacobi)
//!   held i64   (1 or 0)
//!   payload    V, V' | delta_V | j_final
//!
//! Claim scope is not a field inside the circuit. The host binds
//! `computational-integrity-only` on the receipt. The guest must not
//! commit `may_authorize` or `traceable`.

#![cfg_attr(all(feature = "zkvm", target_os = "zkvm"), no_main)]

#[cfg(all(feature = "zkvm", target_os = "zkvm"))]
sp1_zkvm::entrypoint!(main);

use discrete_logic::{discrete_decrease, jacobi_step, v_push, Mat2, Vec2};

mod discrete_logic {
    include!("../../src/lib.rs");
}

fn pack_v_push() -> (u32, i64, i64, i64) {
    let p = Mat2 { a: 2, b: 0, c: 0, d: 3 };
    let t = Mat2 { a: 2, b: 1, c: 1, d: 1 };
    let x = Vec2 { x: 1, y: 2 };
    let (_pp, _xp, v, vp) = v_push(p, t, x).expect("v-push");
    let held = if v == vp { 1 } else { 0 };
    (1, held, v, vp)
}

fn pack_decrease() -> (u32, i64, i64) {
    let a = Mat2 { a: 0, b: 1, c: 0, d: 0 };
    let p = Mat2 { a: 1, b: 0, c: 0, d: 1 };
    let x = Vec2 { x: 2, y: 3 };
    let delta = discrete_decrease(a, p, x).expect("decrease");
    let held = if delta <= 0 { 1 } else { 0 };
    (2, held, delta)
}

fn pack_jacobi() -> (u32, i64, i64) {
    let mut prev = 0_i64;
    let mut cur = 1_i64;
    for _ in 0..4 {
        let nxt = jacobi_step(prev, cur, 0, 1).expect("jacobi");
        prev = cur;
        cur = nxt;
    }
    (3, 1, cur)
}

pub fn main() {
    let kind: u32 = read_kind();
    match kind {
        1 => {
            let (k, held, v, vp) = pack_v_push();
            commit_i64(k as i64);
            commit_i64(held);
            commit_i64(v);
            commit_i64(vp);
        }
        2 => {
            let (k, held, delta) = pack_decrease();
            commit_i64(k as i64);
            commit_i64(held);
            commit_i64(delta);
        }
        3 => {
            let (k, held, j) = pack_jacobi();
            commit_i64(k as i64);
            commit_i64(held);
            commit_i64(j);
        }
        _ => panic!("unknown statement kind"),
    }
}

fn read_kind() -> u32 {
    #[cfg(all(feature = "zkvm", target_os = "zkvm"))]
    {
        return sp1_zkvm::io::read::<u32>();
    }
    #[cfg(not(all(feature = "zkvm", target_os = "zkvm")))]
    {
        1
    }
}

fn commit_i64(value: i64) {
    #[cfg(all(feature = "zkvm", target_os = "zkvm"))]
    {
        sp1_zkvm::io::commit(&value);
    }
    #[cfg(not(all(feature = "zkvm", target_os = "zkvm")))]
    {
        let _ = value;
    }
}
