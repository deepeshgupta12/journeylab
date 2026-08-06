# ADR-011 — psycopg 3 is the PostgreSQL driver; no ORM is adopted yet

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-06 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- **Context:** `STEP-002.02` must bind tenant context to a database transaction so the row-level security policies from `STEP-002.01` apply. That requires a driver. `TECHNICAL_ARCHITECTURE` confirms Python 3.14 + FastAPI, but **records no database driver or ORM decision** — so this could not be taken silently as an implementation detail.
- **Decision:** **psycopg 3** (`psycopg[binary,pool]`) is the PostgreSQL driver. **No ORM is adopted** at this time.
- **Consequences:**
  - Native async support, matching FastAPI's request model and the `ASYNC` ruff rules already enabled.
  - Server-side binding of parameters, which is what makes the tenant binding injection-safe. This mattered concretely: `SET LOCAL app.current_org = $1` is a **syntax error** in PostgreSQL — SET takes no bind parameters — so the alternative is formatting a value into SQL on the tenancy boundary. `SELECT set_config('app.current_org', %s, true)` keeps it a parameter. Verified against PostgreSQL 18.4.
  - `psycopg_pool` is available for `STEP-004` without adding a dependency, and `SET LOCAL`'s transaction scope is what makes pooling safe (proven in `STEP-002.01` and again in `tests/api/`).
  - Deferring the ORM keeps `db.py` dependent on a **structural** cursor protocol rather than a concrete library, so the modules written here do not have to change when an ORM arrives.
  - **Cost, stated plainly:** without an ORM, every query is hand-written SQL and migrations stay hand-authored. That is acceptable while the schema is one migration; it becomes a real burden if deferred much past `STEP-006`.
- **Alternatives rejected:**
  - **asyncpg** — faster, but its own parameter syntax and type handling diverge from DB-API, and it has no sync path for scripts and migrations tooling.
  - **SQLAlchemy (Core or ORM) now** — a larger commitment than this sub-step needs, and adopting it to bind one session setting would decide the data-access strategy for the whole product as a side effect of a security task.
  - **psycopg 2** — no native async; maintenance mode relative to psycopg 3.
- **Review trigger:** Before `STEP-006` (outbox and workers), when the volume of hand-written SQL becomes measurable, or if a second service needs the same data access.

---

## Review trigger
See the entry above where stated; otherwise revisit when a dependent step is
implemented or a stated assumption is invalidated.

## Related
- [ADR-002](ADR-002-deterministic-engines-own-feasibility.md) — deterministic components own correctness
- [BR-011](../product/10-logs/blast-radius/BR-011-tenant-context-at-the-api-boundary.md) — the change that forced this decision
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
- [00-START-HERE](../product/00-START-HERE.md)
