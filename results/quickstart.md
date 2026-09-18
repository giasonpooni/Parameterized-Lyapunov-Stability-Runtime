# Quickstart checks

- [PASS] EQUATION_RESIDUAL equation:hurwitz2:V-hurwitz: max |A-form + Q|=1.110e-16
- [PASS] EQUATION_RESIDUAL equation:discrete-contract:V-discrete: max |A-form + Q|=2.746e-17
- [PASS] SPECTRUM_DIAGNOSTIC spectrum:hurwitz2: abscissa=-1.000e+00, max eig(M)=-1.000e+00
- [PASS] SPECTRUM_DIAGNOSTIC spectrum:discrete-contract: radius=6.000e-01, max eig(M)=-1.000e+00
- [PASS] SAMPLE_DECREASE decrease:A=J(x*):V-from-J: min eig(P)=1.531e-01, max eig(M)=-1.000e+00
- [PASS] CHART_INVARIANCE chart:hurwitz2:milli: V gap=0.000e+00, decrease gap=0.000e+00; unscaled ||P||_F=6.972e-01 vs ||P'||_F=3.333e+03
- [PASS] SUFFICIENT_COMMON_QUADRATIC vertices:two-vertex-lpv:V-lpv: 2 corners, 0 failed; worst theta=[1.0] rate=None max eig(M)=-1.586e+00; the declared theta_dot box does not enter: a constant P has Pdot = 0
# Runtime samples

- certified: V=0.000e+00, decrease=0.000e+00, max eig(M)=-1.000e+00 (V=0.000e+00, decrease=0.000e+00)
- certified: V=2.300e-01, decrease=-7.300e-01, max eig(M)=-1.000e+00 (V=2.300e-01, decrease=-7.300e-01)
- certified: V=2.000e-01, decrease=-4.800e-01, max eig(M)=-2.000e+00 (V=2.000e-01, decrease=-4.800e-01)
- certified: V=2.000e-01, decrease=-6.400e-01, max eig(M)=-1.586e+00 (V=2.000e-01, decrease=-6.400e-01)
