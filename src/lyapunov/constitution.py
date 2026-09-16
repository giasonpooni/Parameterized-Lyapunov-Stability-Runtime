"""Frozen numeric law for certificates.

These are not user parameters. The caller supplies A, P, the parameter
schedule, and a state. They do not set a condition-number cap. Chart
conditioning belongs to JSPT; this package refuses a singular T by
failing a solve.
"""

SYMMETRY_ATOL = 1e-12
MIN_DECREASE_MARGIN = 0.0
MAX_KRONECKER_DIM = 24
