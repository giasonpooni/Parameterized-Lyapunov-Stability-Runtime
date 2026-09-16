# Development workflow

Maintain the Parameterized Lyapunov Stability Runtime as one project on `main`.

- Work directly on `main` and push completed, validated changes to `origin/main`.
- Do not create development branches, separate project copies, or pull requests unless
  the user explicitly requests them.
- Fetch before pushing, preserve concurrent work, and never force-push `main`.
- Run the default test suite and the quickstart example before pushing library changes.
- Keep the README focused on delivered functionality. Mark research extensions as planned
  until implemented and validated.
- First-release scope is quadratic certificates on declared linear and affine-parameter
  plants. Do not imply SOS, SDP synthesis, CLF control, CUDA, or a Jacobian helper
  until those exist and are tested.
- A is an input. Do not form J_f(x*) here. Do not copy JSPT's condition-number cap.
