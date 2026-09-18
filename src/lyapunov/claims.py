"""What a check is allowed to claim, as a code rather than a sentence.

A `CheckResult` that only carries `passed=True` invites the reader to
supply the claim themselves, and the claim they supply is usually larger
than the one the instrument made. A vertex sweep that passes has shown a
common quadratic holds at the declared corners of a declared box. It has
not shown the plant is stable, and there is no code here that says so.

The vocabulary is versioned because consumers pin it. Adding a code is a
new version; changing what a code means is not allowed at all.
"""

from __future__ import annotations

CLAIM_CODES_VERSION = "claim-codes-v1"

#: A common quadratic held at every declared corner. Sufficient for the box
#: because the largest eigenvalue of the decrease family is convex in theta
#: for a constant P; conservative, and never necessary.
SUFFICIENT_COMMON_QUADRATIC = "SUFFICIENT_COMMON_QUADRATIC"

#: The declared sample sites held, and nothing was shown about the rest of
#: the box. This is what an affine P(theta) earns at the corners.
DECLARED_SAMPLES_ONLY = "DECLARED_SAMPLES_ONLY"

#: The decrease form was negative definite at one declared sample.
SAMPLE_DECREASE = "SAMPLE_DECREASE"

#: A supplied P satisfies the Lyapunov equation against a declared Q.
EQUATION_RESIDUAL = "EQUATION_RESIDUAL"

#: V and the scalar decrease survived a linear change of coordinates.
CHART_INVARIANCE = "CHART_INVARIANCE"

#: The chart was accepted but the pushforward left float64. A refusal, not
#: a certificate and not a cap.
CHART_PUSH_REFUSED = "CHART_PUSH_REFUSED"

#: The spectrum is consistent with the certificate. Diagnostic only: a
#: Hurwitz matrix without a P is not a certificate.
SPECTRUM_DIAGNOSTIC = "SPECTRUM_DIAGNOSTIC"

CLAIM_CODES = frozenset(
    {
        SUFFICIENT_COMMON_QUADRATIC,
        DECLARED_SAMPLES_ONLY,
        SAMPLE_DECREASE,
        EQUATION_RESIDUAL,
        CHART_INVARIANCE,
        CHART_PUSH_REFUSED,
        SPECTRUM_DIAGNOSTIC,
    }
)

#: Claims this instrument cannot make, kept here so the prohibition is
#: testable rather than only written down. A vertex sweep is conservative;
#: stability of the plant is not in its power to assert, and neither is
#: safety of anything the plant models.
FORBIDDEN_CLAIMS = frozenset(
    {
        "LPV_STABLE",
        "STABLE",
        "ASYMPTOTICALLY_STABLE",
        "CERTIFIED_STABLE",
        "NECESSARY",
        "VERIFIED",
        "SAFE",
        "AUTHORIZED",
    }
)


def require_claim(code: str) -> str:
    """Admit only a code from the declared vocabulary."""
    if code in FORBIDDEN_CLAIMS:
        raise ValueError(
            f"{code!r} is not a claim this instrument can make "
            f"({CLAIM_CODES_VERSION})"
        )
    if code not in CLAIM_CODES:
        raise ValueError(f"unknown claim {code!r} ({CLAIM_CODES_VERSION})")
    return code
