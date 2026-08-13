# BR-014 — Browser session, token refresh and guest sessions

| Field | Value |
| --- | --- |
| Sub-step | STEP-002.05 |
| Requirements | REQ-SEC-003, REQ-PRIV-001 |
| Decisions resolved | **`DEC-004` CLOSED** (`ADR-013`); guest lifetime (`ADR-014`) |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

> **Numbering note:** the sub-step front-matter named `BR-011`, which belongs to STEP-002.02. This record is `BR-014`; the front-matter has been corrected.

## 1. Intent (step 1)
Hold a session in the browser without ever exposing a token to JavaScript, refresh it without interrupting the user or tripping refresh-token rotation, and support a guest who never provides an email.

## 2. Graph state (step 2 — all six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD at analysis | `c58be3b` |
| Graph indexed commit | `c58be3b` — `status` reported stale first; re-indexed before analysis |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor / schema version | **Not exposed** — recorded, not invented |
| Coverage and known gaps | Python indexed. **TypeScript coverage is unproven** — this sub-step adds the repository's first TypeScript, so whether the extractor indexes it is unknown until the post-commit re-index |
| Status | **RUNNABLE** for the Python it touches |

## 3. Target nodes (step 4)
| Node | Type | Location |
| --- | --- | --- |
| `apps/web` | **New package** — minimal Next.js 16.2, auth only | `apps/web/` |
| `auth/session.ts` | Module (new) — the file the sub-step names | `apps/web/src/auth/` |
| `auth/cookies.ts`, `csrf.ts`, `guest.ts`, `refresh.ts`, `oidc.ts` | Modules (new) | " |
| `tests/guards/typecheck.sh` | **Rewritten** | — |
| `pnpm-workspace.yaml`, root `package.json` | Modified — build allowlist, test wiring | — |

## 4. Dependencies (step 5 — graph-derived, three hops)
`impact({target: "RequestContext", direction: "upstream", maxDepth: 3})` → `epistemic: exact`, risk LOW, 5 impacted, 4 direct, all inside `apps/api/src/auth/`.

Nothing in the Python API is modified by this sub-step. The web session layer talks to the identity provider and to its own cookies; it does not import server code.

**Inbound:** none — no page or route handler consumes these modules yet. The Next.js app has **no UI at all**: this is deliberate scaffolding, and `STEP-003` builds the shell on top.

**Outbound:** Auth0 (`ADR-013`) via OIDC discovery; Web Crypto (`crypto.getRandomValues`, `crypto.subtle.digest`).

## 5. Impact by category (step 6 — all twelve, enumerated)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-003`, `REQ-PRIV-001`; STEP-002.05. Unblocks STEP-003 (shell now has an app to live in) and STEP-008 (onboarding) | High |
| 2 | Owners / consumers | Sole owner; no external consumers | High |
| 3 | Frontend routes / components | **First frontend package in the repository.** No routes or components yet — auth modules only. Constrains STEP-003: the sign-in surface must be built inside our own design system, not Auth0's, because `REQ-A11Y-001` requires WCAG 2.2 AA under our control | High |
| 4 | Backend services / workflows / jobs | **None modified.** Session verification on the API side still goes through `auth.claims.TokenVerifier`, whose Auth0 implementation is `STEP-004`'s to wire | High |
| 5 | APIs / schemas / clients / webhooks | **None** — consumes `API-001`, still `PROPOSED` | High |
| 6 | Events / producers / consumers | **None** | High |
| 7 | Tables / columns / migrations / caches / indexes | **No schema change.** Guest sessions need a `tokenHash`/`expiresAt` record; the storage table does not exist and is **carried as a gap** | **Medium — gap** |
| 8 | Datasets / models / prompts / retrievers / tools / evals | **None** | High |
| 9 | Tests / fixtures / contract suites | **+41 TypeScript tests.** `pnpm test` now runs both suites (`uv run pytest && pnpm -r test`). **`typecheck.sh` and `module-boundaries.sh` stopped being vacuous** for the first time since STEP-001 | High |
| 10 | Services / deployments / infrastructure | New workspace package; two build scripts allowlisted (`esbuild`, `sharp`) with reasons. Dev server on port 5709, inside the reserved block | High |
| 11 | Dashboards / alerts / runbooks | None implemented (STEP-024). Failed sign-ins and refresh failures are not counted anywhere | **Medium — carried gap** |
| 12 | Documentation / deprecation commitments | `ADR-013`, `ADR-014`, `DEC-004` closed; FRONTEND_ARCHITECTURE §6 confirmed against implementation | High |

## 6. Data-flow inspection (step 7 — MANDATORY, token storage and transport)
The sub-step names `KG-Q-014` over **token storage and transport**. Traced by construction and asserted by test:

| Hop | Element | Token exposed? | Evidence |
| --- | --- | --- | --- |
| 1 | Authorization request | No token yet; PKCE `code_challenge` only | S256 asserted; verifier never leaves the server |
| 2 | Redirect back | Authorization code + `state` | `state` compared in constant time; provider error checked first |
| 3 | Code exchange | Tokens over TLS, server-side only | `client_secret` never appears in the authorization URL — asserted |
| 4 | Cookie write | **`httpOnly` + `Secure` + `__Host-`** | Every token-bearing cookie asserted `httpOnly`; the one JS-readable cookie (CSRF) asserted to contain no token |
| 5 | Refresh | Single-flight per session | Coalescing asserted by counting provider calls |
| 6 | Sign-out | Every cookie cleared | Iterates `ALL_SESSION_COOKIES`, not the ones in use |
| 7 | Guest token at rest | **Hashed** | Server stores SHA-256, never the token |

There is deliberately **no function anywhere in this package** that writes a token to `localStorage`, `sessionStorage` or a JS-readable cookie. The guarantee is the absence of the capability, not a rule asking people not to.

## 7. Classification (step 8)
`direct` (new credential handling in the browser) · `security/privacy` · `architecture` (first frontend package) · **`unknown`:** whether the knowledge graph indexes TypeScript.

## 8. Risk scoring (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood of unintended effect | 2 | No consumer yet; nothing existing is modified |
| Severity if it occurs | **5** | A JS-readable token turns any XSS into full account takeover. Credential handling in the browser is the highest-severity surface in the product |
| Reach | **5** | Every authenticated interaction passes through this session layer |
| Detectability | 2 | 41 tests, 7/7 mutants killed |
| Reversibility | 2 | Client code reverts cleanly; **server-side revocation remains authoritative regardless of client version** (sub-step §11) |
| **Confidence in this analysis** | 3 | Graph `epistemic: exact` for Python, but **the Auth0 integration is unverified against a live tenant** — the single largest gap in this record |
| Customer criticality | 1 | No customers yet |

**Overall: HIGH.**

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| ~~Auth0 never exercised for real~~ | **CLOSED 2026-08-06.** Tenant `journeylab-dev.eu.auth0.com` created; a real browser sign-in completed: `/api/auth/login` 302 → Auth0 → `/api/auth/callback` 302 → `/?auth=ok`. `?auth=ok` is reachable only when state verification passes **and** `exchangeCode` returns real tokens, so the code exchange with the live client secret is proven. Credentials independently confirmed by a preflight probe (`invalid_grant`, not `invalid_client`) | **Narrowed further 2026-08-06.** A real browser sign-in produced `__Host-jl_session` and `__Host-jl_refresh`, both present and httpOnly, over a trusted TLS connection — read server-side, which is the only way to observe an httpOnly cookie. **Session establishment is proven.** Still unproven: **passkey enrolment** — Auth0 did not offer one, so the connection is password-only and the `REQ-SEC-003` passkey clause is unmet; also tenant rate limits and rotation under genuine concurrency |
| Guest session storage does not exist | No table for `tokenHash`/`expiresAt` | **Open.** `validateGuestSession` takes the record as an argument and denies when it is `undefined`, so the logic is complete and fails closed — but nothing persists it yet |
| No route handlers or middleware | Scaffolding is auth modules only | **Open.** The functions return cookie specs; nothing sets them on a real response until STEP-003/STEP-004 |
| Accessibility of auth flows unverified | §8 requires keyboard and screen-reader completeness with announced errors | **Open — no UI exists to test.** Binds at STEP-003. This acceptance criterion is **not met** |
| **Passkeys not enabled in the tenant** | Sign-in completed with a password; Auth0 offered no passkey enrolment | **Open, and ACCEPTED as non-blocking by the owner (2026-08-06).** `REQ-SEC-003` says "OIDC with passkey support". The provider supports it (`ADR-013`); the tenant connection has it switched off (Auth0 → Authentication → Database → the connection → Passkey). The clause is **unmet, not untested**, and the owner has decided it does not block progress — it must be closed before the requirement can be marked satisfied at release |
| Live-token revocation — **discharged at STEP-002.08** | `.04` deferred it here; this sub-step provides sign-out and fail-closed refresh | **Partially closed.** Sign-out clears cookies and refresh failure ends the session, but an access token already issued stays valid until it expires. True immediate revocation needs a server-side denylist — carried to STEP-002.07 |
| TypeScript in the knowledge graph | First TypeScript in the repository | **Open** — resolved at the post-commit re-index |

## 10. Required actions (step 10)
httpOnly `__Host-` cookies with no JS-readable alternative; single-flight refresh; server-side guest expiry with hashed storage; fail closed on provider outage; double-submit CSRF; PKCE S256; keep Auth0 confined to one adapter; record `ADR-013`/`ADR-014`.

## 11. Approval (step 11)
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Security Architect | Deepesh Kumar Gupta | **Approved** | 2026-08-06 |

HIGH risk, single owner — author and approver coincide (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| Re-indexed at commit | post-commit re-index |
| `detect_changes()` | New `apps/web` package, rewritten typecheck guard, workspace config. No existing symbol modified |
| Regression R1–R7 | **PASS** — 292 Python + 41 TypeScript; R7 12/12; meta-suite 25/25 |
| Mutation testing | **7/7 killed** |

## 13. Disposition
**Merged with two acceptance criteria unmet:** accessibility of the auth flows (no UI exists) and verification against a live Auth0 tenant. `DEC-004` is closed after three deferrals. Two guards stopped being vacuous, and the rewritten `typecheck.sh` immediately caught a real configuration defect.
