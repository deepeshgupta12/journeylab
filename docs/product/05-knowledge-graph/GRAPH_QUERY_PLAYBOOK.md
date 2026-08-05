# JourneyLab — Graph Query Playbook

| Field | Value |
| --- | --- |
| Owner | Platform (unassigned — `BLK-001`) |
| Status | `READY` for code-graph queries · `DISCOVERY` for domain-graph queries (not built) |
| Last reviewed | 2026-08-05 |

Navigation: [Change impact protocol](CHANGE_IMPACT_PROTOCOL.md) · [Schema](KNOWLEDGE_GRAPH_SCHEMA.md) · [Domain graph](DOMAIN_KNOWLEDGE_GRAPH.md) · [Quality](GRAPH_QUALITY_AND_GOVERNANCE.md) · [00-START-HERE](../00-START-HERE.md)

---

## 1. Before any query

```bash
npx gitnexus status          # confirm index commit == HEAD
npx gitnexus analyze         # refresh if stale
```

**A query against a stale graph produces confident wrong answers.** Always record the indexed commit alongside the result.

---

## 2. Code-graph queries (GitNexus)

### KG-Q-006 — What depends on this symbol?
*Required before every edit (`REQ-KG-008`).*
```
mcp__gitnexus__impact({ target: "generate_scenarios", direction: "upstream" })
mcp__gitnexus__impact({ target: "generate_scenarios", direction: "downstream" })
mcp__gitnexus__context({ name: "generate_scenarios" })
```
Report: direct callers, affected execution flows, risk level. Escalate on HIGH/CRITICAL.

### KG-Q-007 — Which production services and customer workflows does this change affect?
```
mcp__gitnexus__impact({ target: "<symbol>", direction: "upstream" })
mcp__gitnexus__route_map()
```
Traverse `CALLS*` → `EXPOSES` → `DEPLOYED_AS` → `Service`, then `IMPLEMENTS_REQUIREMENT` → `ScopeStep`.

### KG-Q-008 — What lacks an owner, test, runbook or current documentation?
*Governance sweep — run before every release.*
```cypher
MATCH (n) WHERE n:APIEndpoint OR n:Event OR n:Model OR n:Service
WITH n WHERE NOT (n)-[:OWNED_BY]->(:Owner)
RETURN labels(n), n.id, n.source_location;

MATCH (r:Requirement) WHERE NOT (r)<-[:IMPLEMENTS_REQUIREMENT]-()-[:TESTED_BY]->(:TestCase)
RETURN r.id;

MATCH (a:Alert) WHERE NOT (a)-[:RECOVERED_BY]->(:Runbook) RETURN a.id;
```
Run via `mcp__gitnexus__cypher`. **Counts must not increase between sub-steps** (regression check R4/R5).

### KG-Q-009 — Complete evidence path from output to source
```cypher
MATCH path = (ui:Module)-[:CALLS*1..6]->(f:Function)-[:READS|RETRIEVES_FROM*1..3]->(src)
WHERE ui.path CONTAINS 'features/compare'
RETURN path;
```
Serves lineage auditing and `REQ-EVID-004`.

### KG-Q-013 — API surface impact
```
mcp__gitnexus__api_impact({ ... })
```
Which endpoints, generated clients and consumer tests change. Feeds [CONTRACT_CHANGE_POLICY](../04-contracts/CONTRACT_CHANGE_POLICY.md) §3.2.

### KG-Q-014 — Security/privacy data-flow check
*Mandatory when touching auth, tenancy, redaction, retrieval inputs, prompts, export or deletion.*
```
mcp__gitnexus__trace({ ... })      # source → sink
mcp__gitnexus__pdg_query({ ... })  # what guards this statement
```

### KG-Q-015 — Pre-commit scope verification
```
mcp__gitnexus__detect_changes()
```
Confirms only expected symbols and flows changed. **Required before every commit.**

### KG-Q-016 — Structural health
```
mcp__gitnexus__check({ cycles: true })
```
Import cycles indicate the modular-monolith boundaries (`ADR-003`) are eroding.

---

## 3. Domain-graph queries *(specified; not yet implemented)*

All are tenant-filtered **during** traversal.

### KG-Q-001 — Infeasibility from a closure or delay
```cypher
MATCH (ie:ImpactEvent {id: $eventId})-[:AFFECTS]->(item:ItineraryItem)
MATCH (item)-[:PRECEDES*0..3]->(downstream:ItineraryItem)
MATCH (sv:ScenarioVersion)-[:CONTAINS_ITEM]->(downstream)
WHERE sv.tenant_id = $tenantId AND sv.is_canonical
RETURN downstream.id, downstream.start_local, downstream.protected,
       sv.trip_id, ie.severity, ie.confidence
ORDER BY downstream.start_local;
```
Serves STEP-018/019 and admin override preview.

### KG-Q-002 — Why this activity over the alternatives
```cypher
MATCH (s:Scenario {id: $scenarioId})-[:SELECTED_OVER]->(alt:Scenario)
MATCH (s)-[:VERSION_OF*0..1]->()-[:CONTAINS_ITEM]->(i:ItineraryItem)-[:SUPPORTED_BY]->(e:EvidenceFact)
MATCH (t:Traveler)-[:HAS_CONSTRAINT]->(c:Constraint)
WHERE s.tenant_id = $tenantId
RETURN i.id, collect(DISTINCT {fact: e.value, source: e.source_id,
       observed: e.observed_at, confidence: e.confidence}) AS evidence,
       collect(DISTINCT c.class) AS constraint_classes, alt.objective_label;
```
Serves `REQ-EVID-004`. **Returns constraint classes, not sensitive values** (`REQ-COLL-002`).

### KG-Q-003 — Facts expiring before the trip
```cypher
MATCH (sv:ScenarioVersion {id: $versionId})-[:CONTAINS_ITEM]->(:ItineraryItem)
      -[:SUPPORTED_BY]->(e:EvidenceFact)-[:VALID_DURING]->(w)
MATCH (e)-[:OBSERVED_BY]->(p:Provider)
WHERE w.effective_to < $tripStartDate AND sv.tenant_id = $tenantId
RETURN e.id, e.field, w.effective_to, p.id ORDER BY w.effective_to;
```
Drives proactive refresh before departure (`REQ-EVID-005`).

### KG-Q-005 — Override blast radius
```cypher
MATCH (e:EvidenceFact {id: $factId})<-[:SUPPORTED_BY]-(i:ItineraryItem)
MATCH (sv:ScenarioVersion)-[:CONTAINS_ITEM]->(i)
RETURN count(DISTINCT sv.trip_id) AS trips_affected,
       count(DISTINCT sv.id) AS scenario_versions_affected,
       collect(DISTINCT i.id)[..50] AS sample_items;
```
Shown to the curator **before** applying an override (`REQ-ADMIN-003`).

### KG-Q-011 — Contradicting evidence in a scenario
```cypher
MATCH (sv:ScenarioVersion {id: $versionId})-[:CONTAINS_ITEM]->(:ItineraryItem)
      -[:SUPPORTED_BY]->(a:EvidenceFact)-[:CONTRADICTS]-(b:EvidenceFact)
RETURN a.field, a.value, a.confidence, a.observed_at,
       b.value, b.confidence, b.observed_at;
```
Powers the evidence drawer's conflict display (`REQ-EVID-002`).

---

## 4. Permission rules for every query

1. Tenant/repository filters are applied **during traversal**, never as a post-filter.
2. A result must never reveal the existence of a node the caller cannot inspect at source (`REQ-KG-006`).
3. Path counts, aggregate counts and timing must not leak existence.
4. Sensitive constraint **values** are never returned across collaborators — only classes.
5. Every graph answer is logged with its traversed evidence and the indexed commit.

---

## 5. Recording query evidence

Every pre-change and post-change record must carry:

```markdown
**Graph evidence**
- Indexed commit: `<sha>` (HEAD: `<sha>`) — match: yes/no
- Extractor version: `<v>`
- Queries run: KG-Q-006, KG-Q-007
- Direct dependents: N · Indirect (3 hops): M
- Unknown/low-confidence areas: <explicit list>
- Result: <summary>
```

If the graph could not be queried, state `BLOCKED`, name the reason, and apply the static fallback — never present fallback results as graph results.
</content>
