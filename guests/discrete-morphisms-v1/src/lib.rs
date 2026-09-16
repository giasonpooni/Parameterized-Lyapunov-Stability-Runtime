//! Exact i64 2x2 kernels. No IEEE-754. No SP1 crate.
//!
//! A later RISC-V guest should call these functions and commit the
//! public values. This crate itself does not prove anything.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Mat2 {
    pub a: i64,
    pub b: i64,
    pub c: i64,
    pub d: i64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Vec2 {
    pub x: i64,
    pub y: i64,
}

#[derive(Debug)]
pub enum GuestError {
    NotUnimodular { det: i64 },
    NotSymmetric,
    NotPd,
    BadK,
}

pub fn det(m: Mat2) -> i64 {
    m.a * m.d - m.b * m.c
}

pub fn require_symmetric(p: Mat2) -> Result<(), GuestError> {
    if p.b != p.c {
        return Err(GuestError::NotSymmetric);
    }
    Ok(())
}

pub fn require_pd(p: Mat2) -> Result<(), GuestError> {
    require_symmetric(p)?;
    if p.a <= 0 || det(p) <= 0 {
        return Err(GuestError::NotPd);
    }
    Ok(())
}

pub fn inv_unimodular(t: Mat2) -> Result<Mat2, GuestError> {
    let d = det(t);
    if d != 1 && d != -1 {
        return Err(GuestError::NotUnimodular { det: d });
    }
    Ok(Mat2 {
        a: d * t.d,
        b: -d * t.b,
        c: -d * t.c,
        d: d * t.a,
    })
}

pub fn mul(a: Mat2, b: Mat2) -> Mat2 {
    Mat2 {
        a: a.a * b.a + a.b * b.c,
        b: a.a * b.b + a.b * b.d,
        c: a.c * b.a + a.d * b.c,
        d: a.c * b.b + a.d * b.d,
    }
}

pub fn transpose(m: Mat2) -> Mat2 {
    Mat2 {
        a: m.a,
        b: m.c,
        c: m.b,
        d: m.d,
    }
}

pub fn apply(m: Mat2, v: Vec2) -> Vec2 {
    Vec2 {
        x: m.a * v.x + m.b * v.y,
        y: m.c * v.x + m.d * v.y,
    }
}

pub fn quadratic(p: Mat2, x: Vec2) -> i64 {
    let px = apply(p, x);
    x.x * px.x + x.y * px.y
}

pub fn push_p(p: Mat2, t: Mat2) -> Result<Mat2, GuestError> {
    require_pd(p)?;
    let tinv = inv_unimodular(t)?;
    Ok(mul(transpose(tinv), mul(p, tinv)))
}

pub fn v_push(p: Mat2, t: Mat2, x: Vec2) -> Result<(Mat2, Vec2, i64, i64), GuestError> {
    let p_prime = push_p(p, t)?;
    let x_prime = apply(t, x);
    let v = quadratic(p, x);
    let v_prime = quadratic(p_prime, x_prime);
    Ok((p_prime, x_prime, v, v_prime))
}

pub fn decrease_form(a: Mat2, p: Mat2) -> Result<Mat2, GuestError> {
    require_pd(p)?;
    let at = transpose(a);
    let atp = mul(at, p);
    Ok(Mat2 {
        a: atp.a * a.a + atp.b * a.c - p.a,
        b: atp.a * a.b + atp.b * a.d - p.b,
        c: atp.c * a.a + atp.d * a.c - p.c,
        d: atp.c * a.b + atp.d * a.d - p.d,
    })
}

pub fn discrete_decrease(a: Mat2, p: Mat2, x: Vec2) -> Result<i64, GuestError> {
    Ok(quadratic(decrease_form(a, p)?, x))
}

pub fn jacobi_step(j_prev: i64, j: i64, k: i64, h2: i64) -> Result<i64, GuestError> {
    if k != 0 && k != 1 && k != -1 {
        return Err(GuestError::BadK);
    }
    Ok(2 * j - j_prev - h2 * k * j)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixture_v_push() {
        let p = Mat2 { a: 2, b: 0, c: 0, d: 3 };
        let t = Mat2 { a: 2, b: 1, c: 1, d: 1 };
        let x = Vec2 { x: 1, y: 2 };
        let (pp, xp, v, vp) = v_push(p, t, x).unwrap();
        assert_eq!(v, 14);
        assert_eq!(vp, 14);
        assert_eq!(xp, Vec2 { x: 4, y: 3 });
        assert_eq!(pp, Mat2 { a: 5, b: -8, c: -8, d: 14 });
    }

    #[test]
    fn fixture_decrease() {
        let a = Mat2 { a: 0, b: 1, c: 0, d: 0 };
        let p = Mat2 { a: 1, b: 0, c: 0, d: 1 };
        let x = Vec2 { x: 2, y: 3 };
        assert_eq!(discrete_decrease(a, p, x).unwrap(), -4);
    }

    #[test]
    fn fixture_jacobi_flat() {
        let mut prev = 0;
        let mut cur = 1;
        for _ in 0..4 {
            let nxt = jacobi_step(prev, cur, 0, 1).unwrap();
            prev = cur;
            cur = nxt;
        }
        assert_eq!(cur, 5);
    }
}
