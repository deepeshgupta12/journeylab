# `tests/`

Test suites per [docs/product/06-quality/TEST_STRATEGY.md](../docs/product/06-quality/TEST_STRATEGY.md).

Planned subdirectories: `unit/`, `integration/`, `e2e/`, `contracts/`,
`security/`, `resilience/`, `evals/`, `fixtures/`.

**Fast tier** (runs at every sub-step) must always include:
- `security/` tenant isolation — regression check **R7**, non-negotiable
- closed-bug regression tests — check **R6**
