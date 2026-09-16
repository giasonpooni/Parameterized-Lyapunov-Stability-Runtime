//! Exact i64 kernels. No IEEE-754.

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

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Vec3 {
    pub x: i64,
    pub y: i64,
    pub z: i64,
}

#[derive(Debug)]
pub enum GuestError {
    NotUnimodular { det: i64 },
    NotSymmetric,
    NotPd,
    BadK,
    DegenerateStar,
    BadStar,
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

fn sub(a: Vec3, b: Vec3) -> Vec3 {
    Vec3 {
        x: a.x - b.x,
        y: a.y - b.y,
        z: a.z - b.z,
    }
}

fn dot(a: Vec3, b: Vec3) -> i64 {
    a.x * b.x + a.y * b.y + a.z * b.z
}

fn cross(a: Vec3, b: Vec3) -> Vec3 {
    Vec3 {
        x: a.y * b.z - a.z * b.y,
        y: a.z * b.x - a.x * b.z,
        z: a.x * b.y - a.y * b.x,
    }
}

/// Coplanar star: sufficient for discrete K=0. Not a building stamp.
pub fn developable_star(vertex: Vec3, neighbors: &[Vec3]) -> Result<(bool, Vec3, i64), GuestError> {
    if neighbors.len() < 3 || neighbors.len() > 8 {
        return Err(GuestError::BadStar);
    }
    let e0 = sub(neighbors[0], vertex);
    let e1 = sub(neighbors[1], vertex);
    let n = cross(e0, e1);
    if n.x == 0 && n.y == 0 && n.z == 0 {
        return Err(GuestError::DegenerateStar);
    }
    let mut max_abs = 0_i64;
    let mut held = true;
    for p in &neighbors[2..] {
        let t = dot(sub(*p, vertex), n);
        let a = t.abs();
        if a > max_abs {
            max_abs = a;
        }
        if t != 0 {
            held = false;
        }
    }
    Ok((held, n, max_abs))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixture_v_push() {
        let (pp, xp, v, vp) = v_push(
            Mat2 { a: 2, b: 0, c: 0, d: 3 },
            Mat2 { a: 2, b: 1, c: 1, d: 1 },
            Vec2 { x: 1, y: 2 },
        )
        .unwrap();
        assert_eq!(v, 14);
        assert_eq!(vp, 14);
        assert_eq!(xp, Vec2 { x: 4, y: 3 });
        assert_eq!(pp, Mat2 { a: 5, b: -8, c: -8, d: 14 });
    }

    #[test]
    fn fixture_decrease() {
        assert_eq!(
            discrete_decrease(
                Mat2 { a: 0, b: 1, c: 0, d: 0 },
                Mat2 { a: 1, b: 0, c: 0, d: 1 },
                Vec2 { x: 2, y: 3 },
            )
            .unwrap(),
            -4
        );
    }

    #[test]
    fn fixture_developable_plane() {
        let v = Vec3 { x: 0, y: 0, z: 0 };
        let n = [
            Vec3 { x: 1, y: 0, z: 0 },
            Vec3 { x: 0, y: 1, z: 0 },
            Vec3 { x: -1, y: 0, z: 0 },
            Vec3 { x: 0, y: -1, z: 0 },
        ];
        let (held, _, max_abs) = developable_star(v, &n).unwrap();
        assert!(held);
        assert_eq!(max_abs, 0);
    }

    #[test]
    fn fixture_developable_pyramid() {
        let v = Vec3 { x: 0, y: 0, z: 1 };
        let n = [
            Vec3 { x: 1, y: 0, z: 0 },
            Vec3 { x: 0, y: 1, z: 0 },
            Vec3 { x: -1, y: 0, z: 0 },
            Vec3 { x: 0, y: -1, z: 0 },
        ];
        let (held, _, max_abs) = developable_star(v, &n).unwrap();
        assert!(!held);
        assert!(max_abs > 0);
    }
}
