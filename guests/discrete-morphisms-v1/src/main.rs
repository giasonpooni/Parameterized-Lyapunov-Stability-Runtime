//! Native CLI twin. Not a prover.
//!
//! Prints the fixture public values for the four statements in the suite.
//! proof_status is always NOT_CHECKED. Coordinates printed here are the
//! host-oracle inputs; only (statement_id, held, statement_digest) is public.

use discrete_morphisms_v1::{
    developable_defect, discrete_decrease, jacobi_step, v_push, Mat2, Vec2, Vec3,
};

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

    let vertices = [
        Vec3 { x: 0, y: 0, z: 0 },
        Vec3 { x: 1, y: 0, z: 0 },
        Vec3 { x: 0, y: 1, z: 0 },
        Vec3 { x: -1, y: 0, z: 0 },
        Vec3 { x: 0, y: -1, z: 0 },
    ];
    let edges = [(0, 1), (0, 2), (0, 3), (0, 4)];
    let (dev_held, _n, defect) =
        developable_defect(&vertices, &edges, 0).expect("developable-defect fixture");

    println!("statement_id=V-push-v1 V={v} V_prime={vp} x_prime=[{},{}] P_prime=[[{},{}],[{},{}]] held={}",
        xp.x, xp.y, pp.a, pp.b, pp.c, pp.d, v == vp);
    println!("statement_id=discrete-decrease-v1 delta_V={delta} held={}", delta <= 0);
    println!("statement_id=jacobi-step-v1 j_final={cur} held=true");
    println!("statement_id=developable-defect-v1 defect={defect} held={dev_held}");
    println!("claim_scope=computational-integrity-only");
    println!("proof_status=NOT_CHECKED");
    println!("may_authorize=false");
}
