//! SP1 guest. Compiles with `cargo prove build`.
//!
//! Public values, in order:
//!   kind i64    1=V-push, 2=decrease, 3=jacobi
//!   held i64    1 or 0
//!   a, b        V,V' | delta_V,0 | j_final,0
//!
//! Does not commit may_authorize or traceable.

#![no_main]
sp1_zkvm::entrypoint!(main);

use discrete_morphisms_v1::{discrete_decrease, jacobi_step, v_push, Mat2, Vec2};

fn pack_v_push() -> (i64, i64, i64, i64) {
    let p = Mat2 { a: 2, b: 0, c: 0, d: 3 };
    let t = Mat2 { a: 2, b: 1, c: 1, d: 1 };
    let x = Vec2 { x: 1, y: 2 };
    let (_pp, _xp, v, vp) = v_push(p, t, x).expect("v-push");
    (1, i64::from(v == vp), v, vp)
}

fn pack_decrease() -> (i64, i64, i64, i64) {
    let a = Mat2 { a: 0, b: 1, c: 0, d: 0 };
    let p = Mat2 { a: 1, b: 0, c: 0, d: 1 };
    let x = Vec2 { x: 2, y: 3 };
    let delta = discrete_decrease(a, p, x).expect("decrease");
    (2, i64::from(delta <= 0), delta, 0)
}

fn pack_jacobi() -> (i64, i64, i64, i64) {
    let mut prev = 0_i64;
    let mut cur = 1_i64;
    for _ in 0..4 {
        let nxt = jacobi_step(prev, cur, 0, 1).expect("jacobi");
        prev = cur;
        cur = nxt;
    }
    (3, 1, cur, 0)
}

pub fn main() {
    let kind = sp1_zkvm::io::read::<u32>();
    let (k, held, a, b) = match kind {
        1 => pack_v_push(),
        2 => pack_decrease(),
        3 => pack_jacobi(),
        _ => panic!("unknown statement kind"),
    };
    sp1_zkvm::io::commit(&k);
    sp1_zkvm::io::commit(&held);
    sp1_zkvm::io::commit(&a);
    sp1_zkvm::io::commit(&b);
}
