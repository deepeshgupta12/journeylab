# ADR-015 — Kafka is the event backbone

> Full ADR. Indexed in [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) §1.
> Accepted ADRs are **superseded, never edited** — a reversal creates a new ADR
> that links back to this one.

- **Date:** 2026-08-13 · **Owner:** Deepesh Kumar Gupta · **Status:** Accepted
- **Decision type:** **Owner directive.** Unlike `ADR-013`, this was not an
  implementer recommendation confirmed by the owner — the owner decided it
  outright. Recorded that way rather than dressed up as a researched proposal.

## Context

`DEC-009` — managed queue versus Kafka — has been open since the decision log was
written, blocking `STEP-006` and, less obviously, two things in `STEP-004`:

- `contracts/asyncapi.yaml` declares eight events and **generates no client**
  (`STEP-004.07` §9). The envelope is transport-independent; delivery semantics
  are not, and generating a client would have baked in an assumption.
- The compatibility gate from `STEP-004.08` **does not diff AsyncAPI** for the
  same reason: event compatibility rules turn on redelivery, ordering and
  partitioning, none of which were decided.

The AsyncAPI document was written to survive this. `STEP-004.05` deliberately
declared **no `servers:` block and no `bindings:`**, and put the delivery
guarantee in `x-journeylab-delivery` per message instead — so the contract states
*what consumers must tolerate* without naming a broker. That judgement holds up:
adopting Kafka changes the bindings and changes nothing about the eight payloads.

## Decision

**Apache Kafka is the event backbone.**

## Consequences

### What is now decidable that was not

| Previously deferred | Now |
| --- | --- |
| AsyncAPI client generation (`STEP-004.07` §9) | Can proceed — a `bindings:` block and a `servers:` entry can be written against a known broker |
| AsyncAPI compatibility diffing (`STEP-004.08` §9, `BR-035`) | Can proceed — the rules that were undefinable now have a transport to be defined against |
| `STEP-006` outbox design | Unblocked |

Both were recorded as *deliberately not done, pending `DEC-009`*, in the sub-step
records and blast radii. Neither is silently obsolete: each names this decision as
its trigger, so the follow-up is discoverable rather than remembered.

### What Kafka commits us to

- **Partition key is a contract, not a configuration.** Ordering in Kafka is
  per-partition, and `contracts/asyncapi.yaml` already claims *per-trip ordering
  and nothing more* — `TestOrderingIsHonestAboutItsLimits` asserts that the
  channel description says so. Partitioning by trip is therefore the only choice
  consistent with the published guarantee, and changing the partition key later is
  a **breaking change** by `CONTRACT_CHANGE_POLICY` §2.
- **At-least-once stays at-least-once.** Kafka does not make the eight
  `x-journeylab-delivery: at-least-once` markers stronger. `STEP-004.05` recorded
  that no transport gives exactly-once *delivery*; consumers still need the
  idempotency key the envelope already carries. Kafka's "exactly-once semantics"
  is exactly-once *processing* within a Kafka-to-Kafka transaction, which is not
  what a consumer writing to PostgreSQL gets.
- **Operational cost is now real.** A managed queue was the cheaper MVP option and
  the blueprint permitted it. Kafka means brokers, topic and partition management,
  consumer-group lag monitoring and a schema-compatibility story to run — before
  Phase 1 ships. This is the substantive cost of the decision and it is not
  hidden here.
- **`DEC-007` (cloud provider and region) is now more constrained.** Whether Kafka
  is self-hosted, MSK, Confluent Cloud or Redpanda is a follow-on decision that
  interacts with residency, and it is not settled by this ADR.
- **Tenancy still comes from the envelope.** `Envelope.tenant_id` is required and
  asserted; Kafka adds no tenant boundary of its own, so nothing about
  `REQ-SEC-001` gets easier. A topic-per-tenant layout is explicitly *not* implied.

### What this does not decide

The Kafka **distribution and hosting model**, topic naming, partition count,
retention, and the schema registry question. Each is a `STEP-006` concern and
should not be back-filled into this ADR.

## Alternatives rejected

- **A managed queue (SQS/NATS-style) for MVP, migrating later.** The blueprint
  permitted this and it is cheaper to operate at Phase 1 scale. Rejected by owner
  directive. Worth recording what is given up: the migration was genuinely
  deferrable because the AsyncAPI contract is transport-independent, so this
  buys broker capability earlier at the cost of running it earlier.
- **NATS JetStream** — already in the local stack (`docker-compose.dev.yml`, port
  5702) and lighter to operate. Not chosen; the local stack's NATS is a
  development convenience and its presence is not an architectural commitment.

## Review trigger

Operational load from Kafka proves disproportionate to Phase 1 volume; or
`DEC-007` selects a platform whose managed Kafka offering changes the calculus.

---

## Related
- [DEC-009](../product/02-delivery/DECISION_LOG.md) — the decision this closes
- [STEP-004.05](../product/08-steps/sub-steps/STEP-004/STEP-004.05-asyncapi-events.md) — the contract written to survive this being open
- [BR-035](../product/10-logs/blast-radius/BR-035-compatibility-tests.md) §9 — AsyncAPI diffing, deferred pending this
- [STEP-006](../product/08-steps/STEP-006-canonical-domain-and-events.md) — unblocked by this
- [DECISION_LOG](../product/02-delivery/DECISION_LOG.md) — index of all decisions
