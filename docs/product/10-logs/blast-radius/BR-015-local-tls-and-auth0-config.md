# BR-015 — Local TLS and Auth0 configuration

| Field | Value |
| --- | --- |
| Sub-step | Follow-up to STEP-002.05 |
| Requirements | REQ-SEC-003 |
| Author | Deepesh Kumar Gupta |
| Date | 2026-08-06 |

## 1. Intent (step 1)
Make local development able to exercise the session layer at all. `STEP-002.05` set `__Host-` prefixed cookies, which browsers accept **only over HTTPS** — so on plain `http://localhost` every session cookie is silently dropped and none of the sign-in flow can be tested. Also wire the Auth0 values from `ADR-013` without putting a secret anywhere it could be committed.

## 2. Graph state (step 2 — six fields)
| Field | Value |
| --- | --- |
| Repository / branch | journeylab / `main` |
| HEAD commit | `b495d2a` |
| Graph indexed commit | `b495d2a` |
| **Match?** | **Yes** |
| Index timestamp | verified at analysis time |
| Extractor version | not exposed by the tool (recorded, not invented) |
| Coverage | Python and TypeScript indexed |
| Status | **RUNNABLE** |

## 3. Target nodes (step 4)
`apps/web/package.json` (dev script), `apps/web/certificates/` (**gitignored**), `apps/web/src/app/api/health/route.ts` (new), `.env` (**untracked**), `.env.example`, `.gitignore`, `tests/guards/no-tracked-artifacts.sh`.

## 4. Dependencies (step 5)
**Inbound:** none — no code imports any of this. The dev script and the health route are entry points.
**Outbound:** `mkcert` (new local tool dependency, developer machines only — not a runtime or CI dependency); Auth0 tenant `journeylab-dev.eu.auth0.com`.

## 5. Impact by category (step 6 — all twelve)
| # | Category | Affected | Confidence |
| --- | --- | --- | --- |
| 1 | Requirements / scope steps | `REQ-SEC-003`; unblocks local verification of STEP-002.05 | High |
| 2 | Owners / consumers | Sole owner; every future developer must run `mkcert -install` once | High |
| 3 | Frontend routes / components | **One route handler** (`/api/health`). No UI — STEP-003 still owns that | High |
| 4 | Backend services / workflows / jobs | None | High |
| 5 | APIs / schemas / clients / webhooks | **None product-facing.** `/api/health` is scaffold, not `API-NNN` | High |
| 6 | Events / producers / consumers | None | High |
| 7 | Tables / migrations / caches / indexes | None | High |
| 8 | Datasets / models / prompts / retrievers / evals | None | High |
| 9 | Tests / fixtures / contract suites | Guard gains a **key-material rule**; meta-suite 31 → 33 | High |
| 10 | Services / deployments / infrastructure | Local dev only. **`mkcert -install` modifies the system trust store** — deliberately left for the owner to run, since it needs their password and changes machine state | High |
| 11 | Dashboards / alerts / runbooks | None | High |
| 12 | Documentation / deprecation commitments | `.env.example` gains the Auth0 block and cert instructions | High |

## 6. Data-flow inspection (step 7 — MANDATORY, credential paths)
| Question | Evidence |
| --- | --- |
| Can the client secret be committed? | `.env` matched by `.gitignore:29`; `git check-ignore` confirms; `no-tracked-artifacts.sh` already blocked `.env`; file mode `600` |
| Can the TLS private key be committed? | `apps/web/certificates/` and `*.pem`/`*.key`/`*.p12`/`*.pfx` gitignored, **and** a new guard rule fails on tracked key material regardless of `.gitignore` — protecting against `git add -f` and against someone "tidying" `.gitignore` later |
| Does the secret reach the browser bundle? | Not yet consumed by any code. When it is, it must stay in server-only route handlers; `oidc.ts` already documents `clientSecret` as server-side only, and a test asserts it never appears in the authorization URL |
| Is the issuer or client ID sensitive? | **No** — both appear in the browser during a normal sign-in. Recorded so they are not treated as secrets and over-protected into uselessness |

## 7. Classification (step 8)
`direct` · `security/privacy` (key and secret handling) · `operational/tooling` · `unknown`: none.

## 8. Risk (step 9)
| Dimension | 1–5 | Rationale |
| --- | --- | --- |
| Likelihood | 2 | Nothing imports it; the failure mode is a developer machine, not production |
| Severity | **4** | A committed TLS private key or client secret is a credential leak — the key would let anyone impersonate localhost for every developer trusting that CA |
| Reach | 2 | Local development only |
| Detectability | 1 | Guard fails loudly, and it is meta-tested |
| Reversibility | 2 | Config reverts; **a leaked credential does not** — it must be rotated |
| **Confidence** | 4 | HTTPS verified by an actual request; guard verified by a seeded violation |
| Customer criticality | 1 | None |

**Overall: MEDIUM** — low likelihood, but the irreversibility of a credential leak keeps severity high.

## 9. Unknown or low-confidence areas
| Area | Why uncertain | Residual risk |
| --- | --- | --- |
| `mkcert -install` not yet run | Needs the owner's password; modifies the system trust store | **Open.** Until then the browser will warn on `https://localhost:5709`. `curl -k` proved TLS works; **browser acceptance of `__Host-` cookies is not yet proven** |
| No sign-in has been attempted | Client secret not yet pasted; no route handlers wired | **Open.** Auth0 remains unverified end to end, as recorded in BR-014 §9 |
| `mkcert` is a new tool dependency | Only on developer machines; CI never runs the dev server | Low — documented in `.env.example` |
| Cert expires 2028-11-06 | mkcert default | Low, recorded so it is not a mystery later |

## 10. Required actions
HTTPS dev server with an explicit cert path; gitignore all key material; add a guard rule that does not rely on gitignore; `.env` at mode 600 with the secret slot marked; `.env.example` documenting both the Auth0 block and the cert command; a single route so the server can actually be verified.

## 11. Approval
MEDIUM risk — owner approval; single owner, so self-approved (`ADR-010`).

## 12. Post-change verification
| Field | Value |
| --- | --- |
| HTTPS proven | `curl -sk https://localhost:5709/api/health` → `{"status":"ok","secure":true,"cookiePolicy":"__Host- usable"}` |
| Guard proven | Seeded a tracked `.pem` → exit 1 with `TRACKED KEY MATERIAL`; removed → exit 0 |
| Regression | `pnpm verify` green; 292 Python + 41 TypeScript; meta-suite **33/33** |

## 13. Disposition
**Merged.** The key-material rule failed to fire on its first version — the regex was double-escaped through a Python rewrite, so it matched a literal backslash. The meta-test caught it immediately, which is the third time in this project that writing the meta-test *before* trusting the guard has paid for itself.
