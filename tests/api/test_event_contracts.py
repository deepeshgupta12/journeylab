"""AsyncAPI event contracts — TST-PLAT-006, TST-DATA-008 · STEP-004.05.

The assertion that matters most is §"no payload carries content". Everything else
here is shape checking; that one is the tenancy boundary.

An event is read by consumers that never authenticated the user who caused it.
A payload carrying trip content hands those consumers data nobody checked they may
see — and the check cannot be added afterwards, because the data is already in the
log. Payloads carry IDs; consumers needing content read it back through an
authorized API, where the tenant boundary is applied.
"""

from __future__ import annotations

import pathlib
import re
from typing import Any

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[2]
SPEC: dict[str, Any] = yaml.safe_load((REPO / "contracts/asyncapi.yaml").read_text())
MESSAGES: dict[str, Any] = SPEC["components"]["messages"]

EVENT_IDS = [f"EVT-{n:03d}" for n in range(1, 9)]


def message_for(event_id: str) -> dict[str, Any]:
    for message in MESSAGES.values():
        if message["x-journeylab-event-id"] == event_id:
            return dict(message)
    raise AssertionError(f"{event_id} is not declared")


def payload_schema(message: dict[str, Any]) -> dict[str, Any]:
    """The event-specific half of the `allOf`."""
    schema: dict[str, Any] = message["payload"]["allOf"][1]["properties"]["payload"]
    return schema


def property_names(node: Any, found: set[str] | None = None) -> set[str]:
    found = set() if found is None else found
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "properties" and isinstance(value, dict):
                found |= set(value)
            property_names(value, found)
    elif isinstance(node, list):
        for item in node:
            property_names(item, found)
    return found


# --- the register is complete ------------------------------------------------


class TestAllEightEventsAreDeclared:
    @pytest.mark.parametrize("event_id", EVENT_IDS)
    def test_event_exists(self, event_id: str) -> None:
        assert message_for(event_id)

    def test_names_follow_the_convention(self) -> None:
        """`journey.<aggregate>.<past-tense-fact>.v<major>`.

        Past tense, because an event is a fact that already happened. A command
        in the stream is an instruction someone can decline, and the two get
        handled very differently by whoever consumes them.
        """
        pattern = re.compile(r"^journey\.[a-z_]+\.[a-z_]+\.v[0-9]+$")
        for message in MESSAGES.values():
            assert pattern.match(message["name"]), f"{message['name']} breaks the convention"

    def test_the_envelope_pattern_matches_the_names(self) -> None:
        """The schema's own regex must accept every name the document declares.

        A pattern that rejects a real event is a validation failure nobody sees
        until the first message is published.
        """
        envelope_pattern = SPEC["components"]["schemas"]["Envelope"]["properties"]["event_type"][
            "pattern"
        ]
        compiled = re.compile(envelope_pattern)
        for message in MESSAGES.values():
            assert compiled.match(message["name"]), (
                f"the Envelope pattern rejects {message['name']}"
            )


# --- REQ-DATA-008: delivery guarantees are explicit --------------------------


class TestDeliveryGuarantees:
    @pytest.mark.parametrize("event_id", EVENT_IDS)
    def test_every_event_declares_one(self, event_id: str) -> None:
        """An undeclared guarantee is assumed, and the assumption is always the
        convenient one."""
        message = message_for(event_id)
        assert message["x-journeylab-delivery"] in {
            "at-least-once",
            "exactly-once-effect",
            "deduplicated-stream",
        }

    @pytest.mark.parametrize("event_id", EVENT_IDS)
    def test_every_event_declares_an_order_key_and_retention(self, event_id: str) -> None:
        message = message_for(event_id)
        assert message["x-journeylab-order-key"]
        assert message["x-journeylab-retention"]

    def test_the_exactly_once_events_are_the_ones_where_a_duplicate_costs(self) -> None:
        """Selection, replan and deletion-completed.

        A duplicated selection starts a second booking handoff; a duplicated
        replan applies a repair twice; a duplicated deletion record corrupts an
        audit trail. Everywhere else a duplicate is merely wasteful.
        """
        exactly_once = {
            m["x-journeylab-event-id"]
            for m in MESSAGES.values()
            if m["x-journeylab-delivery"] == "exactly-once-effect"
        }
        assert exactly_once == {"EVT-004", "EVT-006", "EVT-007"}

    def test_exactly_once_is_described_as_an_effect_not_a_delivery(self) -> None:
        """No transport gives exactly-once delivery.

        Anything claiming to is deduplicating somewhere and calling it a
        guarantee. The contract must require the *effect*, so a consumer knows
        the obligation is theirs.
        """
        assert "exactly-once-effect" in {m["x-journeylab-delivery"] for m in MESSAGES.values()}
        description = message_for("EVT-004")["description"]
        assert "not exactly-once delivery" in description

    def test_deduplicated_streams_declare_their_dedupe_key(self) -> None:
        for message in MESSAGES.values():
            if message["x-journeylab-delivery"] == "deduplicated-stream":
                assert message.get("x-journeylab-dedupe-key"), (
                    f"{message['name']} is deduplicated but does not say on what"
                )


# --- the envelope --------------------------------------------------------------


class TestEnvelope:
    def test_tenant_id_is_required_on_every_event(self) -> None:
        """REQ-SEC-001. An unstamped envelope cannot be routed safely, and
        STEP-006's outbox is specified to refuse it."""
        assert "tenant_id" in SPEC["components"]["schemas"]["Envelope"]["required"]

    def test_occurred_at_and_recorded_at_are_both_required(self) -> None:
        """The gap between them is the outbox lag.

        A consumer reasoning about freshness needs both; one timestamp forces it
        to guess which meaning it has.
        """
        required = SPEC["components"]["schemas"]["Envelope"]["required"]
        assert {"occurred_at", "recorded_at"} <= set(required)

    def test_event_id_is_required_because_it_is_the_idempotency_key(self) -> None:
        assert "event_id" in SPEC["components"]["schemas"]["Envelope"]["required"]

    def test_causation_id_is_optional(self) -> None:
        """An event caused by a user action has no causing event — that is the
        root of the chain, not a missing field."""
        envelope = SPEC["components"]["schemas"]["Envelope"]
        assert "causation_id" in envelope["properties"]
        assert "causation_id" not in envelope["required"]

    def test_every_message_uses_the_shared_envelope(self) -> None:
        for message in MESSAGES.values():
            first = message["payload"]["allOf"][0]
            assert first["$ref"].endswith("Envelope"), (
                f"{message['name']} does not compose the shared envelope"
            )


# --- the rule that keeps tenancy enforceable ----------------------------------


class TestNoPayloadCarriesContent:
    """`EVENT_CONTRACTS.md` §1: IDs, versions and classifications only.

    Never trip content, evidence prose, personal data or precise location.
    """

    FORBIDDEN = (
        # personal data
        "email",
        "full_name",
        "name",
        "phone",
        "address",
        "date_of_birth",
        "passport",
        # precise location
        "latitude",
        "longitude",
        "lat",
        "lon",
        "coordinates",
        "geo",
        # trip content and evidence prose
        "constraints",
        "constraint_values",
        "itinerary",
        "items",
        "notes",
        "comment",
        "description",
        "prose",
        "value",
        "values",
        "content",
        "text",
        "body",
        "accessibility_needs",
        "party",
    )

    @pytest.mark.parametrize("event_id", EVENT_IDS)
    def test_payload_carries_no_content_field(self, event_id: str) -> None:
        message = message_for(event_id)
        names = {n.lower() for n in property_names(payload_schema(message))}
        offenders = sorted(names & set(self.FORBIDDEN))
        assert not offenders, (
            f"{message['name']} payload carries {offenders}. Events are read by "
            f"consumers that never authenticated the user who caused them — "
            f"payloads carry IDs, and content is read back through an authorized "
            f"API where the tenant boundary applies."
        )

    def test_the_scan_would_find_one(self) -> None:
        """A search for something absent passes identically when it is broken."""
        seeded: dict[str, Any] = {"properties": {"accessibility_needs": {}}}
        assert "accessibility_needs" in {n.lower() for n in property_names(seeded)}

    @pytest.mark.parametrize("event_id", EVENT_IDS)
    def test_payloads_are_closed(self, event_id: str) -> None:
        """An open payload is where content arrives undeclared."""
        assert payload_schema(message_for(event_id))["additionalProperties"] is False

    def test_the_brief_event_carries_counts_not_constraints(self) -> None:
        """A constraint is the traveller's own words about their accessibility
        needs, their budget and who they travel with."""
        payload = payload_schema(message_for("EVT-001"))
        counts = payload["properties"]["constraint_counts"]
        assert set(counts["required"]) == {"hard", "soft", "inferred", "unresolved"}
        for spec in counts["properties"].values():
            assert spec["type"] == "integer"

    def test_the_deletion_event_subject_is_pseudonymous(self) -> None:
        """This event outlives the data it describes, by design.

        It is the record that deletion happened, retained for a legally required
        minimum. A proof of deletion that carries the person's identity defeats
        the act it proves.
        """
        payload = payload_schema(message_for("EVT-007"))
        description = payload["properties"]["subject_ref"]["description"]
        assert "pseudonymous" in description.lower()
        names = {n.lower() for n in property_names(payload)}
        assert "user_id" not in names
        assert "email" not in names

    def test_failure_reasons_are_codes_not_prose(self) -> None:
        """A reason written as prose eventually contains the row it failed on."""
        payload = payload_schema(message_for("EVT-007"))
        failure = payload["properties"]["failures"]["items"]
        assert "reason_code" in failure["required"]
        assert "reason" not in failure["properties"]


# --- specific guarantees the requirements name ---------------------------------


class TestReproducibilityIsAuditableFromTheStream:
    """REQ-CONS-006."""

    def test_the_generation_event_carries_seed_and_versions(self) -> None:
        """So "why did this run produce that answer?" is answerable six months
        later from the log alone — without the database, and without trusting
        that nobody changed a default in between."""
        payload = payload_schema(message_for("EVT-003"))
        # BUG-021: `model_versions` was checked for existence only, and was
        # OPTIONAL while the other three were required. REQ-CONS-006 names all four
        # — inputs, config, model versions and seed — and three out of four does not
        # reproduce a run.
        assert {
            "random_seed",
            "solver_version",
            "evidence_pack_id",
            "model_versions",
        } <= set(payload["required"])

        # A map of name -> version. An untyped object would satisfy "present and
        # required" while recording nothing identifiable.
        model_versions = payload["properties"]["model_versions"]
        assert model_versions["type"] == "object"
        assert model_versions["additionalProperties"]["type"] == "string", (
            "model_versions must map a model name to a version string; an untyped "
            "object records nothing a rerun could pin"
        )


class TestOrderingIsHonestAboutItsLimits:
    def test_per_trip_ordering_is_the_only_guarantee_claimed(self) -> None:
        channel = SPEC["channels"]["journeyEvents"]["description"]
        assert "only guarantee" in channel.lower()
        assert "cross-trip" in channel.lower()

    def test_events_that_are_not_about_a_trip_say_so(self) -> None:
        """Keying a deletion request or provider health by `trip_id` would be
        wrong: a deletion spans every trip a subject has, and provider health is
        not a property of a trip at all."""
        assert message_for("EVT-007")["x-journeylab-order-key"] == "request_id"
        assert message_for("EVT-008")["x-journeylab-order-key"] == "provider_id"


class TestProviderIdentityStaysInternal:
    def test_the_health_event_carries_a_provider_id(self) -> None:
        """It is an internal stream, and this is the one place the id belongs."""
        payload = payload_schema(message_for("EVT-008"))
        assert "provider_id" in payload["required"]

    def test_no_client_facing_event_names_a_provider(self) -> None:
        """The public coverage endpoint publishes one aggregate value precisely
        because this event's contents must not reach a client."""
        for event_id in ("EVT-001", "EVT-002", "EVT-003", "EVT-004", "EVT-005", "EVT-006"):
            names = {n.lower() for n in property_names(payload_schema(message_for(event_id)))}
            assert "provider_id" not in names, f"{event_id} names a provider"
            assert "provider_name" not in names


class TestTheTransportDecisionIsNotBakedIn:
    """DEC-009 — queue versus Kafka — must change the transport, not the contract.

    The sub-step asked for this to be confirmed rather than assumed.
    """

    def test_no_broker_or_client_library_is_named(self) -> None:
        raw = (REPO / "contracts/asyncapi.yaml").read_text().lower()
        # Comments explaining DEC-009 legitimately mention Kafka; the SERVERS and
        # BINDINGS sections are what would bake a transport in.
        document = yaml.safe_load(raw)
        assert "servers" not in document, (
            "declaring a server binds the contract to a transport before DEC-009 is answered"
        )
        for channel in document["channels"].values():
            assert "bindings" not in channel, "a channel binding names a transport"
