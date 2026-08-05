# JourneyLab — Risk Register and Stop Conditions

| Field | Value |
| --- | --- |
| Owner | TPM + Product Lead (unassigned — `BLK-001`) |
| Status | `DISCOVERY` |
| Upstream source | Blueprint §22 (Risks, mitigations and stop conditions) |
| Rule | A stop condition is contractual. If it triggers, work halts pending an explicit decision — it is not a discussion prompt |
| Last reviewed | 2026-08-05 |

Navigation: [Assumptions](ASSUMPTION_REGISTER.md) · [Decisions](DECISION_LOG.md) · [Roadmap](ROADMAP.md) · [Master tracker](MASTER_TRACKER.md) · [00-START-HERE](../00-START-HERE.md)

---

## Scoring

**Likelihood** (L) and **Impact** (I) on 1–5. **Exposure** = L × I. Exposure ≥ 15 requires an active mitigation owner and a tracker blocker; ≥ 20 requires a phase-gate review before proceeding.

Scores below are **initial estimates by the documentation author**, not owner-accepted. They must be re-scored by the named owner at Phase 0 review.

---

## 1. Product and market risks

### RISK-002 — Generated scenarios feel similar or obvious
| Field | Value |
| --- | --- |
| L × I | 3 × 5 = **15** |
| Description | Users perceive the 3–5 scenarios as cosmetic variants, so comparison adds no value over a single itinerary |
| Leading indicators | Low comparison completion (`KPI-003`); diversity metric near threshold; users select the first scenario without inspecting others |
| Mitigation | Objective-specific optimisation, MMR/constrained diversification (`AI-008`), user comparison research in Phase 0 |
| **Stop condition** | **Users do not prefer comparison to existing manual or single-itinerary tools.** Halt Phase 1 build; revisit product definition |
| Related | `ASM-010`, `ASM-023`, `KPI-001` |
| Owner | Product Lead |

### RISK-007 — The handoff seam breaks the user journey
| Field | Value |
| --- | --- |
| L × I | 3 × 3 = **9** |
| Description | Users abandon at the transition from planning to third-party booking because context is lost or trust drops |
| Mitigation | Preserve parameters in deep links, copyable fallback details, clear estimated-vs-confirmed states |
| Stop condition | Folded into `RISK-005` |
| Related | `ASM-017`, `KPI-006` |

## 2. Data, legal and provider risks

### RISK-001 — Destination data is incomplete, stale or legally unavailable
| Field | Value |
| --- | --- |
| L × I | 4 × 5 = **20 — highest exposure in the register** |
| Description | The evidence pack cannot be assembled with adequate coverage, freshness or permitted use. Without it there is no solver input and no product |
| Leading indicators | Coverage report gaps; licence negotiations without cache rights (`ASM-019`); field-level freshness breaches |
| Mitigation | Narrow coverage to one region, field-level freshness policy, licensed providers, curator overrides, blocking thresholds rather than silent degradation |
| **Stop condition** | **Critical facts cannot meet accuracy/freshness or permitted-use requirements.** Halt before Phase 1 architecture work |
| Related | `ASM-011`, `ASM-019`, `ASM-020`, `ASM-021`, `EV-GAP-002`, `DEC-002` |
| Owner | Data Architect + Legal |

### RISK-005 — Affiliate handoff damages user experience or attribution
| Field | Value |
| --- | --- |
| L × I | 3 × 4 = **12** |
| Mitigation | Preserve parameters, reconcile confirmations, copyable fallback details, partner technical review before integration |
| **Stop condition** | **Partners cannot provide a reliable handoff or attribution path.** Business model returns to `DEC-003` |
| Related | `ASM-012`, `EV-GAP-003`, `KPI-006` |

### RISK-008 — Provider dependency concentration
| Field | Value |
| --- | --- |
| L × I | 3 × 4 = **12** |
| Description | A single provider supplies places, hours or transit for the only supported region; its outage, price change or term change halts the product |
| Mitigation | Connector framework with provider-independent interfaces; circuit breakers; documented degraded behavior; second-source evaluation before Phase 2 |
| Stop condition | None separately — escalates into `RISK-001` |

## 3. Safety, trust and compliance risks

### RISK-004 — A harmful or infeasible recommendation causes loss
| Field | Value |
| --- | --- |
| L × I | 2 × 5 = **10** (low likelihood, severe impact) |
| Description | A traveler acts on a plan containing a closed venue, an impossible transfer, or an unsupported safety/visa implication and suffers cost or harm |
| Leading indicators | Any non-zero hard-constraint violation; citation correctness below 95%; user-reported incorrect facts trending up |
| Mitigation | Hard validation before display (`REQ-CONS-004`), citations with observed time (`REQ-EVID-001`), confidence bands, explicit user approval, prohibition on safety/visa claims (`REQ-AI-010`), incident response |
| **Stop condition** | **Hard-constraint violations persist above the defined release threshold** (threshold is zero for the release corpus) |
| Related | `KPI-002`, `TST-CONS-004`, `TST-AI-010` |
| Owner | Engineering + Product |

### RISK-006 — Precise location or trip sharing creates privacy or stalking risk
| Field | Value |
| --- | --- |
| L × I | 3 × 5 = **15** |
| Description | Shared itinerary links or live location expose a traveler's real-time whereabouts to someone who should not have them |
| Mitigation | Location sharing default off, opt-in ephemeral processing, expiring invitations, view logs, download controls, abuse monitoring (`REQ-SEC-008`, `REQ-PRIV-008`) |
| **Stop condition** | **Required safeguards cannot be implemented for the live-companion scope.** Phase 3 does not ship |
| Owner | Security Architect + Privacy Owner |

### RISK-009 — Prompt injection via retrieved destination content
| Field | Value |
| --- | --- |
| L × I | 3 × 4 = **12** |
| Description | Provider content, reviews or documents contain instructions that alter model behavior, causing fabricated facts or unauthorized tool use |
| Mitigation | Treat all retrieved text and MCP tool descriptions as untrusted data (`REQ-SEC-006`), instruction/data isolation, injection detectors (`REQ-AI-009`), allowlisted read-only tools (`REQ-AI-005`), adversarial evaluation set |
| Stop condition | None — mitigations are mandatory rather than optional; failure blocks release via `TST-AI-009` |

### RISK-010 — Cross-tenant or cross-trip data exposure
| Field | Value |
| --- | --- |
| L × I | 2 × 5 = **10** |
| Description | A cache key, job, export, graph traversal or collaborator link leaks one user's trip data to another |
| Mitigation | Tenant ID on every row/event/cache key, row-level security, continuous isolation tests, permission-aware graph traversal (`REQ-KG-006`) |
| Stop condition | Any confirmed cross-tenant exposure halts release immediately and triggers incident response |

## 4. Economic and delivery risks

### RISK-003 — Planning cost per trip is too high
| Field | Value |
| --- | --- |
| L × I | 3 × 4 = **12** |
| Mitigation | Cache evidence and travel matrices, prefer deterministic solvers over model calls, route models by task, measure cost per saved trip (`KPI-007`) |
| **Stop condition** | **Quality-preserving unit economics cannot reach target contribution margin.** Note: the target margin is undefined (`DEC-003`), so this stop condition is **currently unmeasurable** — that is itself a gap |
| Related | `ASM-016`, `EV-GAP-006` |

### RISK-011 — No named owners exist for any step
| Field | Value |
| --- | --- |
| L × I | 5 × 4 = **20** |
| Description | Every step file carries `owners: []`. Exit gates require sign-off that nobody is authorized to give |
| Leading indicators | Already realised — this is a present condition, not a future risk |
| Mitigation | Assign owners before any step leaves `READY`; tracked as blocker `BLK-001` |
| Stop condition | Implementation must not begin on an unowned step |
| Owner | Whoever commissions the build |

### RISK-012 — Solver latency exceeds the interactive budget
| Field | Value |
| --- | --- |
| L × I | 3 × 3 = **9** |
| Description | CP-SAT plus Monte Carlo exceeds p95 ≤ 45 s for a 7-day trip, making generation feel broken |
| Mitigation | Solver spike before committing (`ASM-022`), time-boxed solving with best-known solution, progressive streaming, cancellation, cached travel matrices |
| Stop condition | None — degrades to fewer scenarios or a longer documented budget, both of which require a product decision |

### RISK-013 — Documentation and code diverge
| Field | Value |
| --- | --- |
| L × I | 4 × 3 = **12** |
| Description | This documentation set becomes stale once implementation starts, and the traceability matrix silently lies |
| Mitigation | Documentation freshness table in [MASTER_TRACKER](MASTER_TRACKER.md); `REQ-KG-008` pre-change record required per change; graph query `KG-Q-008` reports untested requirements; documentation currency is a GA gate |
| Stop condition | None — but a stale document blocks its step's `VERIFIED` transition |

### RISK-014 — The code knowledge graph is not load-bearing yet
| Field | Value |
| --- | --- |
| L × I | 4 × 3 = **12** |
| Description | GitNexus currently indexes **documentation only** (119 nodes, verified 2026-08-05). Impact analysis on application symbols is impossible until code exists, so the first code changes risk merging without a meaningful pre-change check |
| Mitigation | Static fallback procedure ([CHANGE_IMPACT_PROTOCOL](../05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md) §7); re-index immediately after the first code merge; `REQ-KG-001` coverage gate enforced from the first source file |
| Stop condition | None — but pre-change checks stay `BLOCKED` (fallback only) until code is indexed, and the fallback explicitly does not satisfy the release gate |
| Related | `ASM-025` |

---

## 5. Exposure summary

| Exposure | Risks | Required action |
| --- | --- | --- |
| **20** | `RISK-001` (data availability), `RISK-011` (no owners) | Phase-gate review before proceeding |
| **15** | `RISK-002` (scenario sameness), `RISK-006` (location privacy) | Active mitigation owner + tracker blocker |
| **12** | `RISK-003`, `RISK-005`, `RISK-008`, `RISK-009`, `RISK-013`, `RISK-014` | Named mitigation, reviewed each phase |
| **≤10** | `RISK-004`, `RISK-007`, `RISK-010`, `RISK-012` | Monitored; mitigations are mandatory controls |

**Two risks are already realised, not prospective:** `RISK-011` (no owners assigned) and `RISK-014` (graph covers documentation only). Both are reflected as blockers in [MASTER_TRACKER](MASTER_TRACKER.md).
</content>
