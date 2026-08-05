# JourneyLab — AI, LLM, RAG, ML and Data Science Architecture

| Field | Value |
| --- | --- |
| Owner | AI/ML Architect (unassigned — `BLK-001`) |
| Status | `DISCOVERY` — target design; nothing implemented |
| Upstream source | Blueprint §13 (AI/ML), §14 (responsible AI), §16 (evaluation) |
| Governing rule | `ADR-002` — deterministic engines own feasibility; the model owns language |
| Last reviewed | 2026-08-05 |

Navigation: [Technical architecture](TECHNICAL_ARCHITECTURE.md) · [AI evaluation](../06-quality/AI_ML_EVALUATION.md) · [Security & responsible AI](SECURITY_PRIVACY_RESPONSIBLE_AI.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Where AI is and is not used

The blueprint's central design claim is that travel planning is a **constrained optimisation problem**, not a text-generation problem. AI is therefore confined to the parts that are genuinely linguistic or statistical.

| Task | Mechanism | Why not an LLM |
| --- | --- | --- |
| Schedule feasibility | **CP-SAT solver** | Must be provably correct and reproducible; an LLM cannot guarantee `REQ-CONS-004` |
| Budget and cost arithmetic | **Deterministic calculation** | Money must be exact |
| Travel time | **Routing engine + matrices** | Straight-line approximation produces plans that fail in reality |
| Opening-hours eligibility | **Deterministic temporal filter** | A boolean over effective time |
| Permissions and state transitions | **Domain services** | Security boundary |
| Uncertainty ranges | **Monte Carlo simulation** | Requires calibrated distributions, not narrative |
| Natural-language brief → typed constraints | **LLM** (`AI-001`) | Genuinely linguistic |
| Trade-off explanation | **LLM** (`AI-003`) | Genuinely linguistic |
| Semantic evidence retrieval | **Hybrid retrieval** (`AI-002`) | Intent matching |
| Preference ranking | **Contextual ranking model** (`AI-009`) | Statistical learning from explicit signals |

---

## 2. AI capability register

### AI-001 — TripBrief extraction
| Field | Value |
| --- | --- |
| Scope step / outcome | STEP-009 — user's free text becomes an auditable typed constraint document |
| Non-AI baseline | Structured forms only. **This is the fallback**, and it must remain fully usable |
| Input / output | Text + locale → JSON Schema-validated `TripBrief` draft with per-field class (hard/soft/inferred/unresolved) and confidence |
| Deterministic validators | Date/currency/unit parsing, coverage check, constraint-satisfiability precheck. **A field the validator rejects is never accepted from the model** |
| Human approval | **Required** — user confirms the interpretation before solving (`REQ-CONS-002`) |
| Failure / abstention | Ambiguity ⇒ blocking clarification; schema violation ⇒ fail closed to the form |
| Budget | Per-request cost and latency budget; degrade to form entry rather than exceed |
| Evaluation | Field-level precision/recall, unit/date accuracy, blocking-ambiguity detection across locales |

### AI-002 — Temporal, permission-aware hybrid retrieval
| Field | Value |
| --- | --- |
| Scope step / outcome | STEP-010 — assemble the evidence pack |
| Non-AI baseline | Structured provider queries by place ID and date |
| Mechanism | Lexical (names, codes) + dense (intent) retrieval → geospatial, temporal, tenant and access filters **applied before ranking** → fusion → reranking → optional graph expansion |
| Deterministic validators | Freshness policy, licence/access label, coverage scoring |
| Failure | Low coverage or low source agreement ⇒ hand to `AI-004` |
| Evaluation | Place/entity recall, temporal-filter correctness, citation-span accuracy, contradiction detection |

### AI-003 — Trade-off explanation
| Field | Value |
| --- | --- |
| Scope step / outcome | STEP-013 — user understands why scenarios differ |
| Non-AI baseline | Templated deltas from computed score components (fully functional without a model) |
| Constraint | **Explanation may never alter a score, a price or a feasibility verdict.** It describes solver output |
| Deterministic validators | Every volatile claim must resolve to an evidence span (`REQ-EVID-004`); a claim without a citation is removed before display |
| Prohibited | Visa, health, legal or safety assertions (`REQ-AI-010`) |
| Evaluation | Groundedness, trade-off completeness, calibrated uncertainty, absence of unsupported claims |

### AI-004 — Corrective retrieval and abstention
| Field | Value |
| --- | --- |
| Scope step / outcome | STEP-010 — avoid confident answers on thin evidence |
| Mechanism | Detect low coverage/agreement → decompose query → second retrieval pass → if still insufficient, **return uncertainty or a blocking question** |
| Hard rule | **Never fill gaps from model memory** (`REQ-AI-004`). Abstention is a success behavior |
| Evaluation | Abstention precision/recall on a deliberately sparse evidence set |

### AI-005 — Candidate ranking
| Field | Value |
| --- | --- |
| Scope step | STEP-011 |
| Mechanism | Feature-based ranking over the preference vector, **after** deterministic hard filters |
| Hard rule | Ranking can never reintroduce an option a hard filter excluded (`REQ-CONS-003`) |
| Non-AI baseline | Popularity + distance heuristic |

### AI-006 — Constraint optimisation (deterministic, not ML)
| Field | Value |
| --- | --- |
| Scope step | STEP-012, STEP-019 |
| Mechanism | CP-SAT: hard constraints + weighted soft objectives; minimal conflict extraction on infeasibility |
| Testing | Property-based tests generating adversarial constraint combinations |
| Reproducibility | Deterministic seed; stored solver configuration and version |

### AI-007 — Monte Carlo simulation
| Field | Value |
| --- | --- |
| Scope step | STEP-012 |
| Mechanism | Calibrated distributions for price, duration, delay and weather; sensitivity analysis; confidence intervals and fragility |
| Hard rule | Never present a point estimate as certain (`REQ-CONS-008`) |
| Calibration | Distributions validated against historical outcomes; an uncalibrated band is a defect |

### AI-008 — Scenario diversity ranking
| Field | Value |
| --- | --- |
| Scope step | STEP-012 |
| Mechanism | Maximal marginal relevance / constrained diversification so scenarios differ **materially**, not cosmetically |
| Risk addressed | `RISK-002`, `ASM-023` |

### AI-009 — Preference learning *(Phase 3)*
| Field | Value |
| --- | --- |
| Scope step | STEP-020 |
| Mechanism | Contextual ranking from **explicit** accept/reject/edit signals; conservative exploration |
| Hard rules | Consent required; no inference of sensitive attributes (`REQ-PRIV-003`); user-visible changes with reset (`REQ-TRIP-008`) |
| Evaluation | Ranking acceptance lift, calibration, subgroup performance, reset correctness |

---

## 3. RAG design

| Aspect | Design |
| --- | --- |
| Source ownership | Every source has documented licence terms and permitted cache duration before ingestion (`REQ-DATA-001`) |
| Parsing/chunking | Per document type: structured provider records stay atomic (one fact = one unit); prose is chunked with heading context preserved |
| Metadata | Every chunk carries source, observed time, effective window, access label, tenant scope and confidence |
| Retrieval | Hybrid lexical + dense; **filters applied before ranking**, never after |
| Query decomposition | Multi-constraint questions split into sub-queries (place, hours, transit, weather) |
| Reranking | Cross-encoder or equivalent over the fused candidate set |
| Graph retrieval | Used where multi-hop evidence is needed ("what depends on this venue closing") — permission-aware |
| Citations | Claim-to-source spans; citation correctness evaluated **independently of prose quality** |
| Conflicts | Conflicting evidence is surfaced with a source hierarchy, never averaged (`REQ-EVID-002`) |
| Injection defence | Retrieved text and MCP tool descriptions are untrusted data; instruction/data isolation + detectors (`REQ-AI-009`) |
| Index updates | Incremental on evidence change; deletion propagates to vector chunks (`REQ-PRIV-006`) |
| Rollback | Index versions are restorable; a bad index rolls back without an application deploy |

---

## 4. Model gateway and tool boundary

| Control | Rule |
| --- | --- |
| Provider neutrality | All model calls route through one gateway; providers are substitutable (`EXT-006`) |
| Structured output | JSON Schema enforced; schema violation fails closed (`REQ-AI-002`) |
| Tool allowlist | **Read-only tools only.** Booking write actions are outside the MVP (`REQ-AI-005`) |
| MCP | If used, stateless per-request authorization; server/tool descriptions treated as untrusted metadata |
| Budgets | Per-capability cost and latency budgets; degrade rather than exceed (`REQ-AI-008`) |
| Tracing | One trace per request containing prompt version, model version, retrieval config, source pack, tool results, cost, latency — sensitive fields redacted (`REQ-AI-006`) |
| State mutation | **Impossible.** Model output passes through command validation and user authorization before any state change (`REQ-AI-001`) |

---

## 5. ML and data science practice

| Concern | Practice |
| --- | --- |
| Problem formulation | Every model states the decision it supports; a model without a decision is not built |
| Labels | Explicit user signals only; **no inferred sensitive attributes** |
| Features | Point-in-time correct — features computed from data available at decision time |
| Leakage prevention | Time-based splits; no post-outcome features; leakage checks in CI |
| Baselines | Every model competes against a deterministic baseline; it ships only if it beats it on the agreed metric |
| Backtesting | Destination/date backtests with calibration reports |
| Uncertainty | Confidence intervals required; calibration monitored |
| Subgroup analysis | Performance checked across party composition and accessibility-constraint groups |
| Causal claims | Only from randomized or quasi-experimental designs with stated identification assumptions. **Engagement improvement is never reported as outcome improvement** |
| Registry | Inputs, outputs, owner, metrics, fairness, latency and rollback contract per model |
| Promotion | Shadow → champion/challenger → gated rollout |
| Drift | Feature and outcome drift monitored; retraining triggers documented |
| Reproducibility | Seeds, data snapshots and config versioned |

---

## 6. Failure and fallback matrix

| Failure | Detection | Fallback | User-visible behavior |
| --- | --- | --- | --- |
| LLM provider down | Gateway health | Alternate provider → structured form | Brief entry switches to form; planning continues |
| Schema violation | Output validation | Reject, retry once, then form | No malformed brief ever reaches the solver |
| Low evidence coverage | Coverage scoring | `AI-004` abstention | Uncertainty stated or option blocked; never invented |
| Injection detected | Guardrail | Drop the content, alert | Evidence excluded with a stated reason |
| Retrieval timeout | Latency budget | Cached pack marked stale | Stale banner at point of use |
| Explanation ungrounded | Citation validator | Remove the claim | Prose shortens; scores unchanged |
| Solver timeout | Worker budget | Best-known feasible or last valid version | Progress + cancel; never an unvalidated plan |
| Ranker unavailable | Health | Deterministic objective ordering | Diversity may reduce; feasibility unaffected |

**The product remains functional with every AI capability disabled.** Scenario generation, comparison and booking handoff are deterministic paths.
</content>
