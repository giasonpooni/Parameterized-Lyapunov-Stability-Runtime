# Parameterized Lyapunov Stability Runtime

Not opened. This is not a second Jacobian package and not a GPU stack.

When implementation starts:

- take A = J_f(x*) from Jacobian-Sensitivity-Propagation-Testbed
  (or the later Rust gate)
- own the certificate structure V, not finite differences
- see docs/GATE.md
