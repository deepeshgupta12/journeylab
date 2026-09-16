"""`EVT-008` delivery — BUG-037.

WHAT THIS IS PROTECTING
    The contract declared `x-journeylab-dedupe-key: provider_id + new_state`. That key
    is a *value*, not an occurrence: a provider that goes down, recovers and goes down
    again emits two events with the same `provider_id` and the same `new_state`, so a
    broker honouring the declared key would discard the second outage. The coverage
    projection would then believe the provider healthy while it was down — the
    opposite failure to the one BUG-037 fixed in the fold, and just as silent.

    Nothing in this repository applied the declared key: `IdempotentConsumer`
    dedupes by `event_id`, as `EVENT_CONTRACTS` §3 rule 1 requires. So the defect was in
    the contract a broker would be configured from, not in the code. The key is now
    `event_id`, and these tests hold the contract and the consumer to the same answer.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from consumers import IdempotentConsumer, ProcessedLog
from outbox import Envelope

REPO = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 15, 8, tzinfo=UTC)
ORG = "eeee0000-0000-0000-0000-00000000000e"


def spec() -> dict[str, Any]:
    # Annotated rather than returned straight from `yaml.safe_load`, which is typed
    # `Any` — the same idiom `test_event_contracts.py` uses for this document.
    document: dict[str, Any] = yaml.safe_load((REPO / "contracts/asyncapi.yaml").read_text())
    return document


def health(event_id: str, *, previous: str, new: str, at: datetime) -> Envelope:
    return Envelope(
        event_id=event_id,
        event_type="journey.provider.health_changed.v1",
        occurred_at=at,
        recorded_at=at,
        tenant_id=ORG,
        correlation_id="corr-1",
        actor=None,
        schema_version=1,
        payload_ids={
            "provider_id": "otd",
            "previous_state": previous,
            "new_state": new,
            "affected_regions": "bern",
        },
    )


FIRST_OUTAGE = health("e-1", previous="healthy", new="unavailable", at=NOW)
RECOVERY = health("e-2", previous="unavailable", new="healthy", at=NOW + timedelta(hours=1))
SECOND_OUTAGE = health("e-3", previous="healthy", new="unavailable", at=NOW + timedelta(hours=2))


class TestTheDeclaredKeyIsAnOccurrence:
    def test_evt008_dedupes_by_event_id(self) -> None:
        message = spec()["components"]["messages"]["ProviderHealthChanged"]
        assert message["x-journeylab-delivery"] == "deduplicated-stream"
        assert message["x-journeylab-dedupe-key"] == "event_id"

    def test_the_key_names_a_field_every_envelope_must_carry(self) -> None:
        """A dedupe key naming an optional field dedupes nothing on the events that
        omit it."""
        assert "event_id" in spec()["components"]["schemas"]["Envelope"]["required"]

    def test_the_old_key_would_have_merged_two_outages(self) -> None:
        """The negative control. Without it, "the key is event_id" is a string
        comparison that proves nothing about why the old key was wrong."""

        def value_key(event: Envelope) -> str:
            return f"{event.payload_ids['provider_id']}|{event.payload_ids['new_state']}"

        assert value_key(FIRST_OUTAGE) == value_key(SECOND_OUTAGE)
        assert FIRST_OUTAGE.event_id != SECOND_OUTAGE.event_id

    def test_a_transition_shaped_key_would_merge_them_too(self) -> None:
        """Why the fix is not `provider_id + previous_state + new_state`: a second
        outage repeats the first transition exactly."""

        def transition_key(event: Envelope) -> str:
            ids = event.payload_ids
            return f"{ids['provider_id']}|{ids['previous_state']}|{ids['new_state']}"

        assert transition_key(FIRST_OUTAGE) == transition_key(SECOND_OUTAGE)


class TestTheConsumerKeepsASecondOutage:
    def test_a_second_outage_is_applied_and_a_redelivery_is_not(self) -> None:
        applied: list[str] = []
        consumer = IdempotentConsumer(
            name="coverage",
            handler=lambda event: applied.append(event.event_id),
            log=ProcessedLog(),
        )
        assert consumer.consume([FIRST_OUTAGE, RECOVERY, SECOND_OUTAGE]) == 3
        # Redelivery of the second outage — same event_id — changes nothing.
        assert consumer.consume([SECOND_OUTAGE]) == 0
        assert applied == ["e-1", "e-2", "e-3"]
