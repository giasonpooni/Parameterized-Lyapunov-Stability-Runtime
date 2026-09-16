//! Native CLI twin. Not a prover.
//!
//! Prints the fixture public values. proof_status is always NOT_CHECKED.

use discrete_morphisms_v1::{discrete_decrease, jacobi_step, v_push, Mat2, Vec2};

fn main() {
    let p = Mat2 { a: 2, b: 0, c: 0, d: 3 };
    let t = Mat2 { a: 2, b: 1, c: 1, d: 1 };
    let x = Vec2 { x: 1, y: 2 };
    let (pp, xp, v, vp) = v_push(p, t, x).expect("v-push fixture");
    let a = Mat2 { a: 0, b: 1, c: 0, d: 0 };
    let p_dec = Mat2 { a: 1, b: 0, c: 0, d: 1 };
    let xd = Vec2 { x: 2, y: 3 };
    let delta = discrete_decrease(a, p_dec, xd).expect("decrease fixture");
    let mut prev = 0_i64;
    let mut cur = 1_i64;
    for _ in 0..4 {
        let nxt = jacobi_step(prev, cur, 0, 1).expect("jacobi");
        prev = cur;
        cur = nxt;
    }
    println!("statement_id=V-push-v1 V={v} V_prime={vp} x_prime=[{},{}] P_prime=[[{},{}],[{},{}]] held={}",
        xp.x, xp.y, pp.a, pp.b, pp.c, pp.d, v == vp);
    println!("statement_id=discrete-decrease-v1 delta_V={delta} held={}", delta <= 0);
    println!("statement_id=jacobi-step-v1 j_final={cur}");
    println!("claim_scope=computational-integrity-only");
    println!("proof_status=NOT_CHECKED");
    println!("may_authorize=false");
}
