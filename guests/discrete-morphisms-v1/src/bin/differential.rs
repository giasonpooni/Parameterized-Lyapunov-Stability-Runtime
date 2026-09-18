//! Differential harness: the Rust twin, driven one case per line.
//!
//! `tools/differential_twins.py` generates cases, runs them here and against
//! `lyapunov.discrete_guest`, and requires the two to agree on the outcome
//! AND on the refusal kind. docs/DISCRETE-GUEST-v1.md: a disagreement with
//! the integer twin is a refuse, not a repair -- so a disagreement is a bug
//! in one of the twins, and this is how we go looking for one.
//!
//! Deliberately dependency-free, like the rest of the crate: a whitespace
//! protocol rather than serde, so `cargo test --locked` still needs no
//! network and the crate keeps zero dependencies.
//!
//! Protocol, one case per stdin line, one answer per stdout line:
//!   VPUSH  p00 p01 p10 p11 t00 t01 t10 t11 x0 x1
//!   DEC    a00 a01 a10 a11 p00 p01 p10 p11 x0 x1
//!   JAC    j0 j1 k h2 steps
//!   DEFECT nverts x y z... nedges i j... center
//! Answers: `OK <values...>` or `ERR <Kind>`.

use std::io::{self, BufRead, Write};

use discrete_morphisms_v1::{
    developable_defect, discrete_decrease, jacobi_step, v_push, GuestError, Mat2, Vec2, Vec3,
};

fn kind(e: &GuestError) -> &'static str {
    match e {
        GuestError::NotUnimodular { .. } => "NotUnimodular",
        GuestError::NotSymmetric => "NotSymmetric",
        GuestError::NotPd => "NotPd",
        GuestError::BadK => "BadK",
        GuestError::DegenerateStar => "DegenerateStar",
        GuestError::BadStar => "BadStar",
        GuestError::Overflow => "Overflow",
        GuestError::EmptyGraph => "EmptyGraph",
        GuestError::CenterOutOfRange => "CenterOutOfRange",
        GuestError::EdgeOutOfRange => "EdgeOutOfRange",
        GuestError::DuplicateSpoke => "DuplicateSpoke",
    }
}

fn mat(v: &[i64]) -> Mat2 {
    Mat2 { a: v[0], b: v[1], c: v[2], d: v[3] }
}

fn answer(line: &str) -> String {
    let parts: Vec<&str> = line.split_whitespace().collect();
    if parts.is_empty() {
        return "ERR Empty".into();
    }
    let n: Vec<i64> = match parts[1..].iter().map(|t| t.parse::<i64>()).collect() {
        Ok(v) => v,
        Err(_) => return "ERR Parse".into(),
    };
    match parts[0] {
        "VPUSH" if n.len() == 10 => {
            match v_push(mat(&n[0..4]), mat(&n[4..8]), Vec2 { x: n[8], y: n[9] }) {
                Ok((pp, xp, v, vp)) => format!(
                    "OK {} {} {} {} {} {} {} {} {}",
                    i64::from(v == vp), v, vp, xp.x, xp.y, pp.a, pp.b, pp.c, pp.d
                ),
                Err(e) => format!("ERR {}", kind(&e)),
            }
        }
        "DEC" if n.len() == 10 => {
            match discrete_decrease(mat(&n[0..4]), mat(&n[4..8]), Vec2 { x: n[8], y: n[9] }) {
                Ok(delta) => format!("OK {} {}", i64::from(delta <= 0), delta),
                Err(e) => format!("ERR {}", kind(&e)),
            }
        }
        "JAC" if n.len() == 5 => {
            if n[4] < 1 || n[4] > 64 {
                return "ERR BadSteps".into();
            }
            let (mut prev, mut cur) = (n[0], n[1]);
            for _ in 0..n[4] {
                match jacobi_step(prev, cur, n[2], n[3]) {
                    Ok(next) => {
                        prev = cur;
                        cur = next;
                    }
                    Err(e) => return format!("ERR {}", kind(&e)),
                }
            }
            format!("OK 1 {}", cur)
        }
        "DEFECT" if !n.is_empty() => {
            let nv = n[0] as usize;
            let mut at = 1;
            if n.len() < 1 + nv * 3 + 1 {
                return "ERR Parse".into();
            }
            let mut verts = Vec::with_capacity(nv);
            for _ in 0..nv {
                verts.push(Vec3 { x: n[at], y: n[at + 1], z: n[at + 2] });
                at += 3;
            }
            let ne = n[at] as usize;
            at += 1;
            if n.len() != at + ne * 2 + 1 {
                return "ERR Parse".into();
            }
            let mut edges = Vec::with_capacity(ne);
            for _ in 0..ne {
                // A negative index is out of range by construction; map it to
                // a huge usize so the crate's own bound check rejects it,
                // exactly as the Python twin's explicit check does.
                let to_index = |v: i64| if v < 0 { usize::MAX } else { v as usize };
                edges.push((to_index(n[at]), to_index(n[at + 1])));
                at += 2;
            }
            let center = if n[at] < 0 { usize::MAX } else { n[at] as usize };
            match developable_defect(&verts, &edges, center) {
                Ok((held, normal, defect)) => format!(
                    "OK {} {} {} {} {}",
                    i64::from(held), defect, normal.x, normal.y, normal.z
                ),
                Err(e) => format!("ERR {}", kind(&e)),
            }
        }
        _ => "ERR Protocol".into(),
    }
}

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in stdin.lock().lines() {
        let line = match line {
            Ok(text) => text,
            Err(_) => break,
        };
        if line.trim().is_empty() {
            continue;
        }
        writeln!(out, "{}", answer(&line)).expect("write");
    }
    out.flush().expect("flush");
}
