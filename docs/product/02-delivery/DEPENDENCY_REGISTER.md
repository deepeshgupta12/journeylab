# JourneyLab — Dependency Register

| Field | Value |
| --- | --- |
| Owner | TPM (unassigned — `BLK-001`) |
| Status | `DISCOVERY` |
| Last reviewed | 2026-08-05 |

Navigation: [Roadmap](ROADMAP.md) · [Master tracker](MASTER_TRACKER.md) · [Risks](RISK_REGISTER.md) · [Integration contracts](../04-contracts/INTEGRATION_CONTRACTS.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Internal step dependencies

`A → B` means B cannot start until A's exit gate passes.

| Step | Depends on | Nature | Blocking? |
| --- | --- | --- | --- |
| STEP-002 | STEP-001 | Repo scaffold, CI, ownership | Yes |
| STEP-003 | STEP-002 | Role-aware navigation needs session/policy | Yes |
| STEP-004 | STEP-002 | Contracts embed tenant/auth envelope | Yes |
| STEP-005 | STEP-004, `DEC-002`, `EV-GAP-002` | Adapter contracts + region + licence terms | Yes — **critical path** |
| STEP-006 | STEP-005 | Normalizers need real provider payload shapes | Yes |
| STEP-007 | STEP-003, STEP-006 | Coverage read model + public shell | Yes |
| STEP-008 | STEP-002, STEP-007 | Identity + coverage-qualified entry | Yes |
| STEP-009 | STEP-008, STEP-004 | Profile constraints + brief contract | Yes |
| STEP-010 | STEP-006, STEP-009 | Canonical facts + confirmed brief | Yes |
| STEP-011 | STEP-010 | Candidates filter against the evidence pack | Yes |
| STEP-012 | STEP-011 | Solver consumes the candidate pool + travel matrix | Yes |
| STEP-013 | STEP-012, STEP-003 | Comparison renders scenario versions | Yes |
| STEP-014 | STEP-013 | Edits operate on a compared scenario | Yes (Phase 2) |
| STEP-015 | STEP-013, STEP-002 | Invitations need scoped permissions | Yes (Phase 2) |
| STEP-016 | STEP-013, STEP-005 (affiliate adapter) | Handoff from a selected scenario | Yes |
| STEP-017 | STEP-016 | Activation follows canonical selection | Yes (Phase 3) |
| STEP-018 | STEP-017, STEP-006 | Event matching needs live pack + event backbone | Yes (Phase 3) |
| STEP-019 | STEP-018, STEP-012 | Repair re-invokes the solver on a subgraph | Yes (Phase 3) |
| STEP-020 | STEP-019 | Retrospective follows trip completion | Yes (Phase 3) |
| STEP-021 | STEP-006, STEP-010 | Overrides act on canonical facts | Yes |
| STEP-022 | STEP-006, STEP-013 | Event taxonomy + real usage surfaces | Yes (Phase 2) |
| STEP-023 | STEP-002 | Controls extend tenancy primitives | Yes |
| STEP-024 | STEP-006, STEP-027 | Telemetry backbone + deployable units to observe | Yes |
| STEP-025 | STEP-023, STEP-026 | Deletion must traverse graph + vector stores | Yes |
| STEP-026 | STEP-001 | Graph indexes the repository | Partial — index starts immediately, coverage gates need code |
| STEP-027 | STEP-004, STEP-023 | Release gates enforce contracts + security | Yes |
| STEP-028 | Phase 3 exit | Commercial scale follows a proven product | Yes (Phase 4) |

**Fan-in hotspots** — a slip here delays the most downstream work:

| Step | Downstream steps blocked |
| --- | --- |
| STEP-002 | 12 steps |
| STEP-004 | 9 steps |
| STEP-005 | 8 steps |
| STEP-006 | 8 steps |

---

## 2. External dependencies

These are outside the delivery team's control. Each has a named fallback because "the partner will deliver" is not a plan.

| ID | Dependency | Needed for | Owner | Fallback if unavailable | Status |
| --- | --- | --- | --- | --- | --- |
| EXT-001 | Places/hours/accessibility data provider with cache rights | STEP-005, STEP-010 | Data Architect | None viable — triggers `RISK-001` stop condition | **Unidentified** |
| EXT-002 | Weather forecast + historical normals provider | STEP-005, STEP-012 | Data Architect | Degrade `weather_resilient` objective; disclose limitation | Unidentified |
| EXT-003 | Transit routing + service alerts (GTFS or vendor) | STEP-005, STEP-012 | Data Architect | Walking/driving profiles only; disclose transit gap | Unidentified |
| EXT-004 | Routing engine with wheelchair profile | STEP-005 | Product Architect (`DEC-008`) | Accessibility routing becomes a disclosed limitation, not a claim (`ASM-020`) | Unidentified |
| EXT-005 | Affiliate partner(s) with deep-link parameter support | STEP-016 | Partnerships | Copyable booking details (`REQ-BOOK-004`); `KPI-006` becomes unmeasurable | Unidentified |
| EXT-006 | LLM provider(s) behind the model gateway | STEP-009, STEP-013 | AI/ML Architect | Provider-neutral gateway allows substitution; structured-form entry replaces conversational brief (`REQ-AI-007`) | Not selected |
| EXT-007 | Identity provider (OIDC + passkeys) | STEP-002 | Security Architect (`DEC-004`) | Self-hosted OIDC; increases security ownership burden | Not selected |
| EXT-008 | Cloud provider and region | STEP-027 | Product Architect (`DEC-007`) | None — blocks production deployment | Not selected |
| EXT-009 | Map tile / vector-tile service for MapLibre | STEP-013 | Frontend Lead | List-only comparison already required by `REQ-A11Y-003`, so the product degrades rather than fails | Not selected |
| EXT-010 | Managed queue or Kafka (`DEC-009`) | STEP-006 | Product Architect | Database-backed outbox polling at MVP volume | Not selected |
| EXT-011 | GitNexus knowledge-graph toolchain | STEP-026, all change control | Platform | Static fallback procedure; **does not satisfy the release gate** | **Verified available** — indexed 2026-08-05 |

---

## 3. Cross-cutting dependencies on open decisions

| Open decision | Blocks | Consequence of continued delay |
| --- | --- | --- |
| `DEC-002` region | STEP-005, STEP-010, all evaluation corpora | Phase 1 cannot start; Phase 0 prototype has no target |
| `DEC-004` identity provider | STEP-002 | Every downstream step blocked (12-step fan-in) |
| `DEC-007` cloud/region/residency | STEP-027, data architecture | Deployment design churns; residency may force redesign |
| `DEC-008` routing provider | STEP-005 | Accessibility claim cannot be validated |
| `DEC-009` event backbone | STEP-006 | Outbox implementation shape undecided |
| `DEC-005` KPI thresholds | All release gates | Phase 1 exit cannot be evaluated objectively |
| `BLK-001` owner assignment | Every step's exit gate | Nothing can be signed off; no step leaves `READY` |

---

## 4. Dependency management rules

1. An external dependency without a named fallback is a risk, and must appear in [RISK_REGISTER](RISK_REGISTER.md).
2. A step may not be marked `READY` while a blocking dependency is open.
3. Provider dependencies must be reviewed for concentration (`RISK-008`) before Phase 2 expands coverage.
4. Version dependencies are pinned by lock file (`REQ-PLAT-002`); upgrades follow the change-impact protocol like any other change.
