# Blast Radius Assessments

One `BR-NNN-<slug>.md` file per change, created from [BLAST_RADIUS_TEMPLATE](../../05-knowledge-graph/BLAST_RADIUS_TEMPLATE.md) **before** implementation begins.

| Field | Value |
| --- | --- |
| Owner | Change author; approved by the code owner |
| Status | `READY` — no assessments yet; no code changes have occurred |
| Requirement | `REQ-KG-008` — no change may merge without a completed record |
| Last reviewed | 2026-08-05 |

Navigation: [Template](../../05-knowledge-graph/BLAST_RADIUS_TEMPLATE.md) · [Change impact protocol](../../05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md) · [Logs index](../README.md)

---

## Index

| ID | Title | Sub-step | Risk | Graph status | Disposition | Date |
| --- | --- | --- | --- | --- | --- | --- |
| — | *No assessments* | | | | | |

---

## Rules

1. **Created before implementation**, not written retrospectively to satisfy a reviewer.
2. The **pre-change** section is completed before any code is written; the **post-change** section before the commit.
3. The "unknown or low-confidence areas" section may not be empty unless the graph is current, coverage meets target, and every impact category was explicitly enumerated.
4. **Risk may never be scored lower than the confidence score implies.** A `BLOCKED` graph means confidence 5 and a risk level that cannot be LOW.
5. HIGH and CRITICAL assessments require owner approval before implementation.
6. Linked from the sub-step file, the pull request and [REGRESSION_LOG](../REGRESSION_LOG.md).
7. Assessments are never deleted — a superseded one is marked and referenced.

---

## Current constraint

The code knowledge graph indexes **documentation only** (`RISK-014`). Until application source exists and is indexed, every assessment must record:

> Graph status: `BLOCKED — static fallback applied`. Dependency coverage unverified. Confidence: 5. This does not satisfy the `REQ-KG-008` release gate.
