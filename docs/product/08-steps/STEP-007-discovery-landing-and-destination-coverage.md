---
step_id: STEP-007
title: Discovery landing and destination coverage
status: IN_REVIEW
release: Phase 1
owners: ["Deepesh Kumar Gupta"]
dependencies: [STEP-003, STEP-006]
requirement_ids: [REQ-TRIP-001, REQ-TRIP-002, REQ-EVID-006]
api_ids: [API-017]
event_ids: []
data_ids: [DATA-006]
ai_ids: []
knowledge_graph_check: REQUIRED
last_updated: 2026-09-16
---

# STEP-007 — Discovery landing and destination coverage

> Status is authoritative in [MASTER_TRACKER](../02-delivery/MASTER_TRACKER.md).

## 1. Outcome
A visitor can tell what is supported, what data is used and what JourneyLab will not do **before signing in**, and an unsupported request is refused rather than partially simulated.

## 2. Why this step exists
The product's trust claim starts before the account. Setting expectations here prevents the worst failure mode: a user planning a trip into a region where evidence is too thin to be reliable, and receiving something that looks authoritative.

## 3. Scope
Public coverage and SEO pages; supported regions, freshness and documented limitations; privacy summary; sample comparisons; date and geography validation; waitlist or read-only inspiration mode when simulation is unsupported.

## 4. Explicit exclusions
Account creation and consent are [STEP-008](STEP-008-account-consent-and-traveler-profile.md). Provider health collection is [STEP-005](STEP-005-source-integrations-and-ingestion.md).

## 5. Actors, permissions and data access
| Actor | Permission | Data accessed | Sensitivity |
| --- | --- | --- | --- |
| Anonymous visitor | Public read | Coverage model only | Public |
| Marketing/content system | Publish content | None | — |

**No provider identities or quota details are ever exposed publicly.**

## 6. Preconditions and dependencies
[STEP-003](STEP-003-design-system-and-application-shell.md) shell and [STEP-006](STEP-006-canonical-data-model-and-event-backbone.md) coverage read model.

## 7. Inputs and source systems
Origin, broad destination interest, dates, device locale; coverage read model; provider health (`EVT-008`).

## 8. Detailed normal workflow
1. Visitor lands; page is server-rendered for speed and SEO.
2. Page shows supported regions, data freshness, limitations, sample comparisons and the privacy summary.
3. Visitor enters a destination and dates.
4. `API-017` validates geography and dates against current coverage and provider health.
5. On success, the visitor proceeds to a qualified start-planning action.

## 9. Alternate, partial and failure workflows
| Condition | Behavior | User-visible result | Requirement |
| --- | --- | --- | --- |
| Region unsupported | Refuse; show supported regions; offer waitlist | Honest scope statement | REQ-TRIP-002 |
| Dates outside window | Refuse with supported bounds | Clear boundary | REQ-TRIP-002 |
| Provider health **insufficient for reliable planning** (published `unavailable`) | **Refuse rather than partially simulate** | Region not accepting new trips | REQ-TRIP-002 |
| Provider published `degraded` — less certain, still usable | **Accept and disclose.** `REQ-EVID-006` asks for degradation to be *surfaced*, not refused; and `RECOVERING` publishes as `degraded`, so refusing here would make every provider recovery a total outage (`BUG-034`) | Region shown degraded, with the disclosure | REQ-EVID-006 |
| Coverage service down | Static fallback listing regions with a staleness notice | Degraded but honest | REQ-EVID-006 |
| Waitlist offered | Inquiry preserved **only with consent** | Consent prompt | REQ-PRIV-002 |

## 10. State machine and lifecycle transitions
`visitor → coverage-checked → qualified → (start planning | waitlisted | declined)`.

## 11. Frontend implementation
`apps/web/src/app/(public)/coverage/page.tsx`, `apps/web/src/app/trips/new/page.tsx` (`PROPOSED`). Server-rendered; no map dependency; full keyboard and screen-reader paths.

## 12. Backend implementation
`services/destination/` coverage query and provider-health read (`PROPOSED`). Cached with a short TTL.

## 13. API, event and integration contracts
`API-017` `GET /v1/coverage` — public, unauthenticated, must not expose provider identities. Consumes `EVT-008`.

## 14. Data model, migration and retention effects
Reads `DATA-006` and the coverage read model. Waitlist inquiries are stored **only with consent** and carry a retention period.

## 15. AI, LLM, RAG, ML and data-science implementation
`NOT_APPLICABLE`. Reason: coverage validation is a deterministic rule over region and date bounds. A model here would introduce uncertainty into precisely the statement that must be reliable.

## 16. Security, privacy, accessibility and responsible-AI controls
Public page carries no tracking beyond typed, privacy-tiered analytics. Privacy summary is presented **before** any data collection. Consent required before storing an inquiry. WCAG 2.2 AA; no map required.

## 17. Observability, analytics and KPIs
`coverage_viewed`, `waitlist_joined`, refusal rate by reason. Refusal-by-degradation rate is a leading indicator for `RISK-001`.

## 18. Files and modules expected to change
All `PROPOSED` — see §11, §12.

## 19. Knowledge-graph pre-change analysis
| Field | Value | 
| --- | --- |
| Graph status | `BLOCKED` — static fallback |
| Queries to run | KG-Q-006 on the coverage read model |
| Expected impact | Public surface; low inbound coupling |

## 20. Blast-radius assessment
Low reach into other services, but **high customer criticality** — this is the first impression and the honesty gate. Detectability is good (public, monitored).

## 21. Implementation task checklist — sub-steps
| Sub-step | Outcome |
| --- | --- |
| STEP-007.01 | Coverage read model and `API-017` | — ✅ **VERIFIED** 2026-09-04 (BR-059, IMPL-059; closes BUG-028/029/030)
| STEP-007.02 | Public coverage/SEO page with limitations and privacy summary | — ✅ **VERIFIED** 2026-09-04 (BR-060, IMPL-060)
| STEP-007.03 | Date and geography validation with honest refusal states | — ✅ **VERIFIED** 2026-09-05 (BR-061, IMPL-061; adds `API-019`, migration `018`, `DEC-011`; closes BUG-034)
| STEP-007.04 | Waitlist / inspiration mode with consent | — ✅ **VERIFIED** 2026-09-11 (BR-063, IMPL-063; adds `API-020`, migration `019`). **The plan's `ConsentRecord` could not be written** — `consent_records` is tenant-scoped and the subject has no account, so consent lives in a platform-level table on `016`'s reasoning. `STEP-008.04` inherits reconciling the two |
| STEP-007.05 | Provider-degradation disclosure wiring | — ✅ **VERIFIED** 2026-09-14 (BR-064, IMPL-064; adds `Coverage.observed_at`, `services/events/src/read_models.py`). **No production code had written `coverage_read_model` until now.** Step close — §25 exit criteria — is a separate unit and is not claimed here |

**Step close, 2026-09-16:** the automatable evidence in §26 is complete and two defects found in the process are fixed (`BUG-036`, `BUG-037`). The step is `IN_REVIEW`: §25's screen-reader criterion is owed and cannot be automated.

## 22. Test and evaluation plan
`TST-TRIP-001`, `TST-TRIP-002`, `TST-EVID-006`, `TST-A11Y-001`. A resilience drill must prove that a degraded provider produces a refusal, not a partial simulation.

## 23. Deployment, feature flag and migration plan
Region availability controlled by flag so a region can be suspended without deployment.

## 24. Rollback, compensation and recovery plan
Static fallback content; region flag off. No data impact.

## 25. Acceptance criteria

- [x] Supported regions, freshness, limitations and privacy summary visible pre-signup (`REQ-TRIP-001`) — **with one caveat stated rather than buried:** no region has ever been declared (`017` seeds none), so a browser has only ever rendered the *empty* state. The populated page is proven at component and API level against rows tests insert. `ENH-007`
- [x] Out-of-coverage requests refused with an explanation and **no scenarios generated** (`REQ-TRIP-002`) — `API-019`, 20 mutants at `.03`, and the drill asserts the refusal carries no `nights`, `itinerary`, `scenario`, `plan` or `options`
- [x] Provider degradation disclosed, not masked by cache (`REQ-EVID-006`) — `observed_at` stamped before caching, invalidation on change, and the drill's four stages
- [ ] **Page completes all tasks by keyboard and screen reader** — **keyboard: yes.** Tab order, focus traps, focus indicators, and every cell of an overflowing table reachable (`BUG-033`). **Screen reader: NOT DONE.** `ACCESSIBILITY_AUTOMATION_LIMITS` §3.2 requires manual journeys across five reader/browser pairs every release, and no headless browser reproduces any of them. **This is the one criterion a machine cannot pass, and it is why this step is `IN_REVIEW` rather than `VERIFIED`**

## 26. Evidence required for completion

| Evidence | Where it is | State |
| --- | --- | --- |
| Refusal-path test output | `tests/platform_api/test_trip_request.py`, `test_app.py::TestPlanningCheckRefusals` | ✅ |
| **Degradation drill record** | `tests/platform_api/test_degradation_drill.py` — healthy → degraded → unavailable → recovered, driven through fold, read model, cache and both public operations | ✅ **as a repeatable test, not a written-up one-off**: a drill performed once decays, and the next change to the fold or the cache cannot be checked against a paragraph |
| Accessibility audit | `a11y.spec.ts` — axe at WCAG 2.2 AA on four surfaces, keyboard, focus, touch targets, forced-colors, RTL | ⚠️ **automated only**. The manual half is owed — see §25 |
| SEO measurement | `apps/web/src/test/seo.spec.ts` — server-rendered content without JavaScript, page-specific title and description, declared language, not marked unindexable | ✅ **No robots.txt and no sitemap exist.** Neither is required by any document, so none was invented; their absence is recorded here |
| CWV measurement | `a11y.spec.ts` — LCP and CLS now measured on **`/coverage`** as well as `/`, which is what `FRONTEND_ARCHITECTURE` §7's "LCP (coverage/landing)" row actually names | ✅ lab numbers; field measurement is `STEP-024` |

## 27. Open questions, risks and decisions

Both questions this section opened are now closed, and one of them was closed by
finding it unanswered at the step close rather than by anyone remembering it.

| Question | State |
| --- | --- |
| ~~`DEC-002` region unknown, so no coverage content can be written yet~~ | **CLOSED 2026-08-13 — Switzerland** (`ADR-016`). The narrower fact survives it: **no region has ever been declared**, so every surface in this step has only ever been exercised against rows a test inserted (`ENH-007`) |
| ~~Waitlist retention period needs privacy-owner approval~~ | **CLOSED 2026-09-15 — `DEC-012`**: until the one requested message is sent, and never more than 12 calendar months. It was found **unanswered and unimplemented** while gathering this step's exit evidence — `BUG-036` — which is the argument for reading a parent step's §14 and §27 at every sub-step, not only at its close |

Two defects were found at the close itself and fixed before it: `BUG-036` (personal
data with no retention) and `BUG-037` (a region that could never recover, plus an
`EVT-008` dedupe key that would discard a provider's second outage).

## 28. Completion record
| Field | Value |
| --- | --- |
| Completed | Implementation 2026-09-16; **`IN_REVIEW`, not `VERIFIED`** |
| Sub-steps completed | **5 of 5** |
| Regression result | R1–R7 pass on every sub-step and on both close-out fixes. Python 1378 → **1478** across the step |
| Verified by | Deepesh Kumar Gupta. `ADR-010`: one owner, so author and approver are the same person — the four-eyes gap, in force here and stated rather than glossed |
| Blast-radius records | **BR-059 … BR-066** — .01–.05 are BR-059, BR-060, BR-061, BR-063, BR-064. The other three are defects found and fixed inside the step: BR-062 (`BUG-033`), BR-065 (`BUG-036`), BR-066 (`BUG-037`) |
| Implementation records | IMPL-059 … IMPL-066 |
| Mutation testing | 20 (.03) + 13 (.04) + 12 (.05) + 14 (BUG-036) + 11 (BUG-037) = **70 seeded, 70 killed** |
| Migrations added | `016` … `020`, all expand-phase |
| Bugs found and closed at the close itself | **`BUG-036`** — personal data with no retention period; **`BUG-037`** — a region that could never recover, and an `EVT-008` dedupe key that would discard a provider's second outage |

### Why this is `IN_REVIEW` and not `VERIFIED`

`VERIFIED` means "exit criteria met with recorded evidence". Three of §25's four are
met. The fourth requires manual screen-reader journeys over five reader/browser pairs,
which no machine performs and which nobody has performed. Marking the step `VERIFIED`
today would be a claim about evidence that does not exist — the one thing rule 5
forbids outright.

**What unblocks it:** the journeys in `ACCESSIBILITY_AUTOMATION_LIMITS` §3.2, run by a
person against `/` and `/coverage`, recorded here.

### What this step did not deliver, stated plainly

**Nothing real has ever flowed through any of it.** No region is declared, so the
coverage page has only rendered its empty state in a browser; no `EVT-008` consumer
runs, so the projection write and the degradation disclosure are a tested seam rather
than a live pipeline; no scheduler runs, so waitlist retention is enforceable and not
enforced; and no message is ever sent, so a waitlist entry's purpose can never actually
be fulfilled. Every one of those is `ENH-007` in a different costume, and the step is
correct in shape and untested by reality.

### Three findings worth carrying forward

1. **A requirement in a parent step is invisible to a sub-step's pre-change analysis.**
   §14 required a retention period; `.04` planned from its own sub-step file and shipped
   without one. Read §14 and §27 at every sub-step, not only at the close.
2. **A one-sided assertion passes a defect that is its exact mirror.** The only
   mixed-state projection test checked that a healthy sibling cannot mask an outage; a
   fold that could *only* worsen satisfied it perfectly, and a region could never
   recover. `STEP-006`'s close recorded this shape; it recurred in the same module.
3. **Mutation testing cannot find behaviour the code never had.** 70 mutants, 70
   killed, and neither `BUG-036` nor `BUG-037` was found by any of them. Both were found
   by reading requirements against what shipped.
