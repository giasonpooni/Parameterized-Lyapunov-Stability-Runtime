"""Frozen numeric law for certificates.

These are not user parameters. The caller supplies A, P, the parameter
schedule, and a state. They do not set a condition-number cap. Chart
conditioning belongs to JSPT; this package refuses a singular T by
failing a solve.
"""

SYMMETRY_ATOL = 1e-12
MIN_DECREASE_MARGIN = 0.0
MAX_KRONECKER_DIM = 24

# The Lyapunov solve's residual gate. These decide whether a certificate is
# issued, so they belong here and in docs/KERNEL.md, not inline in the solve.
# The tolerance is the backward-error estimate
# ``RESIDUAL_BACKWARD_FACTOR * eps * ||operator|| * ||P||`` clamped between
# ``RESIDUAL_FLOOR_RELATIVE * ||Q||`` and ``RESIDUAL_CAP_RELATIVE * ||Q||``.
# The floor keeps well-scaled problems exactly as strict as they were. The
# cap keeps the forward error meaningful: the equation is A^T P + P A = -Q,
# so once the residual approaches ||Q|| the identity is not recovered at all.
RESIDUAL_FLOOR_RELATIVE = 1e-8
RESIDUAL_CAP_RELATIVE = 1e-6
RESIDUAL_BACKWARD_FACTOR = 64.0
