//! Exact i64 kernels. No IEEE-754.
//!
//! Every arithmetic result is range-checked. Wrapping is not exactness: a
//! wrapped product would make this twin disagree with the Python guest in
//! `lyapunov.discrete_guest`, and docs/DISCRETE-GUEST-v1.md says a
//! disagreement with the integer twin is a refuse, not a repair. So both
//! sides refuse on overflow instead of returning a value the other cannot
//! reproduce.

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

#[derive(Debug, PartialEq, Eq)]
pub enum GuestError {
    NotUnimodular { det: i64 },
    NotSymmetric,
    NotPd,
    BadK,
    DegenerateStar,
    BadStar,
    Overflow,
    EmptyGraph,
    CenterOutOfRange,
    EdgeOutOfRange,
    DuplicateSpoke,
}

type R<T> = Result<T, GuestError>;

#[inline]
fn mul(a: i64, b: i64) -> R<i64> {
    a.checked_mul(b).ok_or(GuestError::Overflow)
}

#[inline]
fn add(a: i64, b: i64) -> R<i64> {
    a.checked_add(b).ok_or(GuestError::Overflow)
}

#[inline]
fn sub_i(a: i64, b: i64) -> R<i64> {
    a.checked_sub(b).ok_or(GuestError::Overflow)
}

/// `a*b + c*d`, refusing on any overflow.
#[inline]
fn dot2(a: i64, b: i64, c: i64, d: i64) -> R<i64> {
    add(mul(a, b)?, mul(c, d)?)
}

pub fn det(m: Mat2) -> R<i64> {
    sub_i(mul(m.a, m.d)?, mul(m.b, m.c)?)
}

pub fn require_symmetric(p: Mat2) -> R<()> {
    if p.b != p.c {
        return Err(GuestError::NotSymmetric);
    }
    Ok(())
}

pub fn require_pd(p: Mat2) -> R<()> {
    require_symmetric(p)?;
    if p.a <= 0 || det(p)? <= 0 {
        return Err(GuestError::NotPd);
    }
    Ok(())
}

pub fn inv_unimodular(t: Mat2) -> R<Mat2> {
    let d = det(t)?;
    if d != 1 && d != -1 {
        return Err(GuestError::NotUnimodular { det: d });
    }
    Ok(Mat2 {
        a: mul(d, t.d)?,
        b: mul(-d, t.b)?,
        c: mul(-d, t.c)?,
        d: mul(d, t.a)?,
    })
}

pub fn matmul(a: Mat2, b: Mat2) -> R<Mat2> {
    Ok(Mat2 {
        a: dot2(a.a, b.a, a.b, b.c)?,
        b: dot2(a.a, b.b, a.b, b.d)?,
        c: dot2(a.c, b.a, a.d, b.c)?,
        d: dot2(a.c, b.b, a.d, b.d)?,
    })
}

pub fn transpose(m: Mat2) -> Mat2 {
    Mat2 {
        a: m.a,
        b: m.c,
        c: m.b,
        d: m.d,
    }
}

pub fn apply(m: Mat2, v: Vec2) -> R<Vec2> {
    Ok(Vec2 {
        x: dot2(m.a, v.x, m.b, v.y)?,
        y: dot2(m.c, v.x, m.d, v.y)?,
    })
}

pub fn quadratic(p: Mat2, x: Vec2) -> R<i64> {
    let px = apply(p, x)?;
    dot2(x.x, px.x, x.y, px.y)
}

pub fn push_p(p: Mat2, t: Mat2) -> R<Mat2> {
    require_pd(p)?;
    let tinv = inv_unimodular(t)?;
    matmul(transpose(tinv), matmul(p, tinv)?)
}

pub fn v_push(p: Mat2, t: Mat2, x: Vec2) -> R<(Mat2, Vec2, i64, i64)> {
    let p_prime = push_p(p, t)?;
    let x_prime = apply(t, x)?;
    let v = quadratic(p, x)?;
    let v_prime = quadratic(p_prime, x_prime)?;
    Ok((p_prime, x_prime, v, v_prime))
}

pub fn decrease_form(a: Mat2, p: Mat2) -> R<Mat2> {
    require_pd(p)?;
    let at = transpose(a);
    let atp = matmul(at, p)?;
    Ok(Mat2 {
        a: sub_i(dot2(atp.a, a.a, atp.b, a.c)?, p.a)?,
        b: sub_i(dot2(atp.a, a.b, atp.b, a.d)?, p.b)?,
        c: sub_i(dot2(atp.c, a.a, atp.d, a.c)?, p.c)?,
        d: sub_i(dot2(atp.c, a.b, atp.d, a.d)?, p.d)?,
    })
}

pub fn discrete_decrease(a: Mat2, p: Mat2, x: Vec2) -> R<i64> {
    quadratic(decrease_form(a, p)?, x)
}

pub fn jacobi_step(j_prev: i64, j: i64, k: i64, h2: i64) -> R<i64> {
    if k != 0 && k != 1 && k != -1 {
        return Err(GuestError::BadK);
    }
    let two_j = mul(2, j)?;
    let curvature = mul(mul(h2, k)?, j)?;
    sub_i(sub_i(two_j, j_prev)?, curvature)
}

fn vsub(a: Vec3, b: Vec3) -> R<Vec3> {
    Ok(Vec3 {
        x: sub_i(a.x, b.x)?,
        y: sub_i(a.y, b.y)?,
        z: sub_i(a.z, b.z)?,
    })
}

fn vdot(a: Vec3, b: Vec3) -> R<i64> {
    add(dot2(a.x, b.x, a.y, b.y)?, mul(a.z, b.z)?)
}

fn vcross(a: Vec3, b: Vec3) -> R<Vec3> {
    Ok(Vec3 {
        x: sub_i(mul(a.y, b.z)?, mul(a.z, b.y)?)?,
        y: sub_i(mul(a.z, b.x)?, mul(a.x, b.z)?)?,
        z: sub_i(mul(a.x, b.y)?, mul(a.y, b.x)?)?,
    })
}

/// Coplanar star: sufficient for discrete K=0. Not a building stamp.
///
/// Returns `(held, normal, defect)` where `defect` is `max |(p - v) . n|`
/// over the spokes past the first pair. `held` iff the defect is zero. This
/// is a sampled defect, never a `sum(theta) = 2*pi` angle sum.
pub fn developable_star(vertex: Vec3, neighbors: &[Vec3]) -> R<(bool, Vec3, i64)> {
    if neighbors.len() < 3 || neighbors.len() > 8 {
        return Err(GuestError::BadStar);
    }
    let e0 = vsub(neighbors[0], vertex)?;
    let e1 = vsub(neighbors[1], vertex)?;
    let n = vcross(e0, e1)?;
    if n.x == 0 && n.y == 0 && n.z == 0 {
        return Err(GuestError::DegenerateStar);
    }
    let mut max_abs = 0_i64;
    let mut held = true;
    for p in &neighbors[2..] {
        let t = vdot(vsub(*p, vertex)?, n)?;
        let a = t.checked_abs().ok_or(GuestError::Overflow)?;
        if a > max_abs {
            max_abs = a;
        }
        if t != 0 {
            held = false;
        }
    }
    Ok((held, n, max_abs))
}

/// Spokes of `center` in a declared panel graph, in edge order.
///
/// Twin of `lyapunov.discrete_guest.star_from_panel_graph`. Coordinates stay
/// here; only `(statement_id, held, statement_digest)` is ever public.
pub fn star_from_panel_graph(
    vertices: &[Vec3],
    edges: &[(usize, usize)],
    center: usize,
) -> R<(Vec3, Vec<Vec3>)> {
    if vertices.is_empty() {
        return Err(GuestError::EmptyGraph);
    }
    if center >= vertices.len() {
        return Err(GuestError::CenterOutOfRange);
    }
    let mut spokes: Vec<usize> = Vec::new();
    for &(i, j) in edges {
        if i >= vertices.len() || j >= vertices.len() {
            return Err(GuestError::EdgeOutOfRange);
        }
        if i == center && j != center {
            spokes.push(j);
        } else if j == center && i != center {
            spokes.push(i);
        }
    }
    let mut seen = spokes.clone();
    seen.sort_unstable();
    seen.dedup();
    if seen.len() != spokes.len() {
        return Err(GuestError::DuplicateSpoke);
    }
    Ok((vertices[center], spokes.iter().map(|&i| vertices[i]).collect()))
}

/// `developable-defect-v1` on a declared panel graph. Held iff defect == 0.
pub fn developable_defect(
    vertices: &[Vec3],
    edges: &[(usize, usize)],
    center: usize,
) -> R<(bool, Vec3, i64)> {
    let (v, spokes) = star_from_panel_graph(vertices, edges, center)?;
    developable_star(v, &spokes)
}

#[cfg(test)]
mod tests {
    use super::*;

    const PLANE: [Vec3; 5] = [
        Vec3 { x: 0, y: 0, z: 0 },
        Vec3 { x: 1, y: 0, z: 0 },
        Vec3 { x: 0, y: 1, z: 0 },
        Vec3 { x: -1, y: 0, z: 0 },
        Vec3 { x: 0, y: -1, z: 0 },
    ];
    const STAR_EDGES: [(usize, usize); 4] = [(0, 1), (0, 2), (0, 3), (0, 4)];

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
    fn fixture_jacobi_flat_is_linear() {
        let mut prev = 0_i64;
        let mut cur = 1_i64;
        for _ in 0..4 {
            let nxt = jacobi_step(prev, cur, 0, 1).unwrap();
            prev = cur;
            cur = nxt;
        }
        assert_eq!(cur, 5);
    }

    #[test]
    fn fixture_developable_plane() {
        let (held, _, max_abs) = developable_star(PLANE[0], &PLANE[1..]).unwrap();
        assert!(held);
        assert_eq!(max_abs, 0);
    }

    #[test]
    fn fixture_developable_pyramid() {
        let v = Vec3 { x: 0, y: 0, z: 1 };
        let (held, _, max_abs) = developable_star(v, &PLANE[1..]).unwrap();
        assert!(!held);
        assert!(max_abs > 0);
    }

    #[test]
    fn fixture_defect_holds_on_panel_graph() {
        let (held, _, defect) = developable_defect(&PLANE, &STAR_EDGES, 0).unwrap();
        assert!(held);
        assert_eq!(defect, 0);
    }

    #[test]
    fn fixture_defect_fails_on_pyramid_graph() {
        let mut verts = PLANE;
        verts[0] = Vec3 { x: 0, y: 0, z: 1 };
        let (held, _, defect) = developable_defect(&verts, &STAR_EDGES, 0).unwrap();
        assert!(!held);
        assert!(defect > 0);
    }

    #[test]
    fn defect_refuses_center_out_of_range() {
        assert_eq!(
            developable_defect(&PLANE, &STAR_EDGES, 9).unwrap_err(),
            GuestError::CenterOutOfRange
        );
    }

    #[test]
    fn defect_refuses_duplicate_spoke() {
        let edges = [(0, 1), (1, 0), (0, 2), (0, 3)];
        assert_eq!(
            developable_defect(&PLANE, &edges, 0).unwrap_err(),
            GuestError::DuplicateSpoke
        );
    }

    #[test]
    fn overflow_is_refused_not_wrapped() {
        // P = diag(2, 3) is PD; x near i64::MAX makes x^T P x overflow.
        let p = Mat2 { a: 2, b: 0, c: 0, d: 3 };
        let big = Vec2 { x: i64::MAX / 2, y: 0 };
        assert_eq!(quadratic(p, big).unwrap_err(), GuestError::Overflow);
        // Wrapping would have produced a finite, wrong value instead.
        assert!(i64::MAX / 2 > 0);
    }

    #[test]
    fn non_pd_p_is_refused_by_the_kernels_not_only_the_wrappers() {
        let not_pd = Mat2 { a: -1, b: 0, c: 0, d: -1 };
        let t = Mat2 { a: 1, b: 0, c: 0, d: 1 };
        assert_eq!(push_p(not_pd, t).unwrap_err(), GuestError::NotPd);
        assert_eq!(
            decrease_form(Mat2 { a: 0, b: 1, c: 0, d: 0 }, not_pd).unwrap_err(),
            GuestError::NotPd
        );
    }

    #[test]
    fn non_symmetric_p_is_refused() {
        let skew = Mat2 { a: 1, b: 2, c: 0, d: 1 };
        assert_eq!(require_pd(skew).unwrap_err(), GuestError::NotSymmetric);
    }

    #[test]
    fn non_unimodular_chart_is_refused() {
        let p = Mat2 { a: 1, b: 0, c: 0, d: 1 };
        let t = Mat2 { a: 2, b: 0, c: 0, d: 2 };
        assert_eq!(
            push_p(p, t).unwrap_err(),
            GuestError::NotUnimodular { det: 4 }
        );
    }
}
