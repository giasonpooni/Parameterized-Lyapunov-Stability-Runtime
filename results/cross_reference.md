# Cross-reference benchmarks

Status: **in development**. `confirmed_out_of_development: false`.

JSPT pin: `giasonpooni/Jacobian-Sensitivity-Propagation-Testbed@b957f701d8e20ddd9c756437c9d9208ab7d36f90`.

Matrices below are copied from sibling reference models or result
files. This package does not import `sensitivity`. A refusal is a
recorded outcome. These numbers are not a release certificate.

| case | outcome | details |
| --- | --- | --- |
| `jspt-affine2` | refused | solved P must be positive definite; min eigenvalue=-3.571e-01 |
| `jspt-scaled-rotation` | refused | solved P must be positive definite; min eigenvalue=-8.000e-01 |
| `jspt-storage-J-as-A` | refused | solved P must be positive definite; min eigenvalue=-3.333e-01 |
| `jspt-beam-J-as-A` | refused | A must be a nonempty square matrix, got shape (1, 3) |
| `two-tank-leak-companion` | certified-sample | Lyapunov solve produced PD P; decrease matrix is ND at the unit sample |
| `chart-invariance-leak-companion` | certified-sample | V and decrease compared after x' = T x with T = 1000 I |

## Numbers

### jspt-affine2

Source: giasonpooni/Jacobian-Sensitivity-Propagation-Testbed@b957f701d8e20ddd9c756437c9d9208ab7d36f90 reference_models.affine2

- `spectral_abscissa` = 2
- `spectral_radius` = 2

### jspt-scaled-rotation

Source: giasonpooni/Jacobian-Sensitivity-Propagation-Testbed@b957f701d8e20ddd9c756437c9d9208ab7d36f90 reference_models.scaled_rotation

- `spectral_abscissa` = 1.21352549156
- `spectral_radius` = 1.5

### jspt-storage-J-as-A

Source: giasonpooni/Jacobian-Sensitivity-Propagation-Testbed@b957f701d8e20ddd9c756437c9d9208ab7d36f90 two_tank_storage Jacobian at any h

- `spectral_abscissa` = 2
- `spectral_radius` = 2

### jspt-beam-J-as-A

Source: giasonpooni/Jacobian-Sensitivity-Propagation-Testbed@b957f701d8e20ddd9c756437c9d9208ab7d36f90 simply_supported_midspan at [10e3, 4, 8e6]

- `rows` = 1
- `cols` = 3
- `J00` = 1.66666666667e-07
- `J01` = 0.00125
- `J02` = -2.08333333333e-10

### two-tank-leak-companion

Source: giasonpooni/Jacobian-Sensitivity-Propagation-Testbed@b957f701d8e20ddd9c756437c9d9208ab7d36f90 areas from two_tank_storage; leak declared here

- `min_eig_P` = 2.5
- `max_eig_decrease` = -1
- `V_unit` = 5
- `decrease_unit` = -2

### chart-invariance-leak-companion

Source: PLSR chart push on the two-tank leak companion; levels from JSPT fluid example

- `V` = 5.2
- `V_prime` = 5.2
- `V_gap` = 8.881784197e-16
- `decrease` = -2.08
- `decrease_prime` = -2.08
- `P_frobenius` = 3.53553390593
- `P_prime_frobenius` = 3.53553390593e-06
