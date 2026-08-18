"""Deep links, signed callbacks and attribution — TST-BOOK-002 · STEP-005.06.

THE TWO FAILURES THAT MATTER
    **Parse before verify.** A JSON parser run on unauthenticated bytes is the
    whole attack surface the signature was meant to stand in front of, and the
    natural way to write the handler puts the parser first.

    **A payment credential with somewhere to live.** Redaction runs after the value
    is in memory and one forgotten call from a log. The only reliable answer is a
    schema with nowhere to put one.
"""

from __future__ import annotations

import dataclasses
import json
import re
from datetime import UTC, date, datetime, timedelta

import pytest
from affiliate.attribution import (
    AttributionError,
    AttributionRecord,
    BookingOutcome,
    reject_payment_fields,
)
from affiliate.deeplink import (
    ALLOWED_PARAMETERS,
    DeepLinkError,
    PartnerLinkProfile,
    Preservation,
    build_deep_link,
)
from affiliate.webhook import (
    DEFAULT_REPLAY_WINDOW,
    SeenEvents,
    VerifiedCallback,
    WebhookRejectedError,
    expected_signature,
    verify_and_parse,
)

NOW = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
SECRET = "partner-shared-secret"


def signed(payload: dict[str, object], at: datetime = NOW) -> tuple[bytes, str]:
    body = json.dumps(payload).encode()
    return body, expected_signature(body, at, SECRET)


# --- verify before parse ------------------------------------------------------


class TestVerifyBeforeParse:
    def test_a_valid_callback_is_accepted(self) -> None:
        body, signature = signed({"event_id": "evt_1", "booking_ref": "ABC"})
        result = verify_and_parse(body, signature=signature, signed_at=NOW, secret=SECRET, now=NOW)
        assert isinstance(result, VerifiedCallback)
        assert result.event_id == "evt_1"

    def test_malformed_json_with_a_valid_signature_is_still_refused(self) -> None:
        """Proves parsing happens INSIDE the trusted region. A signed-but-invalid
        body must fail as a rejection, not as a parser traceback escaping."""
        body = b"{not json at all"
        signature = expected_signature(body, NOW, SECRET)
        with pytest.raises(WebhookRejectedError):
            verify_and_parse(body, signature=signature, signed_at=NOW, secret=SECRET, now=NOW)

    def test_malformed_json_with_an_invalid_signature_never_reaches_the_parser(self) -> None:
        """The ordering itself. If this raised a JSONDecodeError rather than a
        WebhookRejectedError, the parser would have run on unauthenticated bytes."""
        with pytest.raises(WebhookRejectedError):
            verify_and_parse(
                b"{not json at all",
                signature="0" * 64,
                signed_at=NOW,
                secret=SECRET,
                now=NOW,
            )

    def test_the_entry_points_take_raw_bytes_not_a_parsed_body(self) -> None:
        """Structural. A `verify(signature, parsed_dict)` helper is the function
        everyone would reach for, and reaching for it is the bug — so the two
        functions that exist both take bytes, and there is no third."""
        import inspect

        import affiliate.webhook as module

        # eval_str resolves the annotations that `from __future__ import
        # annotations` turns into strings — otherwise this compares "bytes" to
        # bytes and passes for the wrong reason, or fails for a cosmetic one.
        for name in ("verify_and_parse", "expected_signature"):
            signature = inspect.signature(getattr(module, name), eval_str=True)
            first = next(iter(signature.parameters.values()))
            assert first.annotation is bytes, f"{name} must take raw bytes"

        # Defined HERE, not merely imported here — `dataclass` is in this
        # namespace and is not part of the module's surface.
        public_callables = {
            name
            for name, value in vars(module).items()
            if not name.startswith("_")
            and inspect.isfunction(value)
            and value.__module__ == module.__name__
        }
        assert public_callables == {"expected_signature", "verify_and_parse", "now_utc"}, (
            "a new public function here is a new chance to verify a parsed body"
        )

    def test_a_tampered_body_fails(self) -> None:
        body, signature = signed({"event_id": "evt_1", "amount": "10.00"})
        tampered = body.replace(b"10.00", b"99.99")
        with pytest.raises(WebhookRejectedError):
            verify_and_parse(tampered, signature=signature, signed_at=NOW, secret=SECRET, now=NOW)

    def test_every_rejection_is_indistinguishable(self) -> None:
        """An attacker must not learn whether the signature, the timestamp or the
        body was the problem — the same reasoning as the opaque denial."""
        body, signature = signed({"event_id": "evt_1"})
        reasons = []
        for kwargs in (
            {"signature": "0" * 64, "signed_at": NOW, "now": NOW},
            {"signature": signature, "signed_at": NOW - timedelta(hours=1), "now": NOW},
            {"signature": signature, "signed_at": NOW + timedelta(hours=1), "now": NOW},
        ):
            with pytest.raises(WebhookRejectedError) as caught:
                verify_and_parse(body, secret=SECRET, **kwargs)  # type: ignore[arg-type]
            reasons.append(str(caught.value))
        assert len(set(reasons)) == 1, reasons

    def test_an_empty_secret_is_refused(self) -> None:
        with pytest.raises(WebhookRejectedError, match="empty secret"):
            expected_signature(b"{}", NOW, "")


class TestReplayWindow:
    def test_a_stale_callback_is_rejected(self) -> None:
        body, signature = signed({"event_id": "evt_1"}, at=NOW - timedelta(minutes=10))
        with pytest.raises(WebhookRejectedError):
            verify_and_parse(
                body,
                signature=signature,
                signed_at=NOW - timedelta(minutes=10),
                secret=SECRET,
                now=NOW,
            )

    def test_a_future_dated_callback_is_rejected(self) -> None:
        """Otherwise an attacker mints a request that stays valid as long as they
        chose — a replay window with no far edge is not a window."""
        future = NOW + timedelta(hours=2)
        body, signature = signed({"event_id": "evt_1"}, at=future)
        with pytest.raises(WebhookRejectedError):
            verify_and_parse(body, signature=signature, signed_at=future, secret=SECRET, now=NOW)

    def test_the_timestamp_is_inside_the_signed_material(self) -> None:
        """A window checked against an attacker-editable timestamp is not a window.
        Changing the timestamp must invalidate the signature."""
        body = json.dumps({"event_id": "evt_1"}).encode()
        assert expected_signature(body, NOW, SECRET) != expected_signature(
            body, NOW + timedelta(seconds=1), SECRET
        )

    def test_a_callback_at_the_window_edge_is_accepted(self) -> None:
        """Guards the guard: a window that rejected everything would pass every
        test above while refusing all legitimate traffic."""
        at = NOW - DEFAULT_REPLAY_WINDOW
        body, signature = signed({"event_id": "evt_1"}, at=at)
        assert (
            verify_and_parse(
                body, signature=signature, signed_at=at, secret=SECRET, now=NOW
            ).event_id
            == "evt_1"
        )


class TestIdempotency:
    def test_a_first_delivery_is_new(self) -> None:
        assert SeenEvents().record("evt_1", NOW) is True

    def test_a_retry_inside_the_window_is_accepted_as_a_duplicate(self) -> None:
        """The tension §5 asks for both halves of: replay protection rejects OLD
        requests, idempotency accepts DUPLICATE ones. A partner retrying after a
        timeout is legitimate and must not be treated as an attack."""
        seen = SeenEvents()
        assert seen.record("evt_1", NOW) is True
        assert seen.record("evt_1", NOW + timedelta(seconds=30)) is False

    def test_the_seen_set_is_bounded_by_the_window(self) -> None:
        """An unbounded seen-set is a memory-exhaustion primitive for anyone able
        to send signed callbacks."""
        seen = SeenEvents(window=timedelta(minutes=5))
        for index in range(50):
            seen.record(f"evt_{index}", NOW)
        seen.record("later", NOW + timedelta(minutes=10))
        assert len(seen._seen) == 1

    def test_distinct_events_are_independent(self) -> None:
        seen = SeenEvents()
        assert seen.record("evt_1", NOW) is True
        assert seen.record("evt_2", NOW) is True


# --- TST-BOOK-002: no payment credential anywhere -----------------------------


class TestNoPaymentDataCanBeStored:
    def test_the_attribution_record_has_no_payment_field(self) -> None:
        """Not redacted — absent. `slots=True` means one cannot even be attached
        at runtime."""
        record = AttributionRecord(
            partner_id="p",
            click_reference="c",
            partner_booking_reference="B1",
            outcome=BookingOutcome.BOOKED,
            occurred_at=NOW,
            tenant_id="t",
        )
        for forbidden in ("card", "pan", "cvv", "iban", "payment", "billing"):
            assert not any(forbidden in field.lower() for field in record.__slots__)
        # frozen=True plus slots=True: assignment is refused, and an attribute that
        # is not in __slots__ has nowhere to live even if it were not frozen.
        with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
            record.card_number = "4111111111111111"  # type: ignore[attr-defined]

    @pytest.mark.parametrize(
        "field",
        [
            "card_number",
            "cardNumber",
            "ccnum",
            "pan",
            "cvv",
            "cvc",
            "security_code",
            "iban",
            "sort_code",
            "account_number",
            "expiry_date",
            "cardholder",
        ],
    )
    def test_a_payment_shaped_field_is_refused(self, field: str) -> None:
        with pytest.raises(AttributionError, match="payment-shaped"):
            reject_payment_fields({field: "x"})

    def test_it_is_refused_at_any_depth(self) -> None:
        with pytest.raises(AttributionError, match=re.escape("booking.traveller.cvv")):
            reject_payment_fields({"booking": {"traveller": {"cvv": "123"}}})

    def test_it_is_refused_inside_a_list(self) -> None:
        with pytest.raises(AttributionError):
            reject_payment_fields({"items": [{"ok": 1}, {"card_number": "4111"}]})

    def test_it_refuses_rather_than_strips(self) -> None:
        """A partner sending card data is a contract change to escalate, not a
        stream to filter — and filtering still passes the value through our memory
        and possibly our logs on the way to being dropped."""
        payload = {"card_number": "4111"}
        with pytest.raises(AttributionError):
            reject_payment_fields(payload)
        assert payload == {"card_number": "4111"}, "the payload must not be mutated"

    def test_an_ordinary_payload_passes(self) -> None:
        """Guards the guard: a matcher that refused everything would pass every
        test above while making the adapter unable to accept any callback."""
        reject_payment_fields({"event_id": "e", "booking_ref": "B", "traveller": {"party_size": 2}})

    def test_a_booked_outcome_needs_a_partner_reference(self) -> None:
        with pytest.raises(AttributionError, match="reconciled"):
            AttributionRecord(
                partner_id="p",
                click_reference="c",
                partner_booking_reference=None,
                outcome=BookingOutcome.BOOKED,
                occurred_at=NOW,
                tenant_id="t",
            )

    def test_a_tenant_is_required(self) -> None:
        with pytest.raises(AttributionError, match="REQ-SEC-001"):
            AttributionRecord(
                partner_id="p",
                click_reference="c",
                partner_booking_reference=None,
                outcome=BookingOutcome.CLICKED,
                occurred_at=NOW,
                tenant_id="  ",
            )


# --- deep links and ASM-012 ---------------------------------------------------


def a_profile(**preservation: Preservation) -> PartnerLinkProfile:
    return PartnerLinkProfile(partner_id="partner", parameters=dict(preservation), checked_at=NOW)


class TestDeepLinks:
    def test_a_link_carries_the_permitted_parameters(self) -> None:
        link = build_deep_link(
            base_url="https://partner.example/book",
            partner=a_profile(check_in=Preservation.PRESERVED),
            click_reference="c1",
            check_in=date(2026, 9, 1),
        )
        assert "check_in=2026-09-01" in link.url
        assert "click_ref=c1" in link.url

    def test_unreliable_parameters_are_reported(self) -> None:
        """A dropped parameter is worse than a rejected one: the traveller lands on
        a page for a different date and nothing says the context was lost."""
        link = build_deep_link(
            base_url="https://partner.example/book",
            partner=a_profile(check_in=Preservation.PRESERVED, party_size=Preservation.SUBSTITUTED),
            click_reference="c1",
            check_in=date(2026, 9, 1),
            party_size=2,
        )
        assert link.unreliable_parameters == ("party_size",)

    def test_an_unverified_parameter_counts_as_unreliable(self) -> None:
        """Unverified is not the same as preserved, and defaulting it to preserved
        would be the optimistic assumption ASM-012 exists to test."""
        link = build_deep_link(
            base_url="https://partner.example/book",
            partner=a_profile(),
            click_reference="c1",
            check_in=date(2026, 9, 1),
        )
        assert "check_in" in link.unreliable_parameters

    def test_plain_http_is_refused(self) -> None:
        with pytest.raises(DeepLinkError, match="https"):
            build_deep_link(
                base_url="http://partner.example/book",
                partner=a_profile(),
                click_reference="c1",
            )

    def test_the_parameter_allowlist_carries_nothing_identifying(self) -> None:
        """A deep link reaches browser history, referrer headers and the partner's
        logs. The click reference is opaque and ours."""
        for forbidden in ("email", "name", "phone", "user", "traveller_id"):
            assert forbidden not in ALLOWED_PARAMETERS

    def test_a_preservation_claim_needs_a_check_date(self) -> None:
        """Undated, it is an assumption wearing an observation's clothes."""
        with pytest.raises(DeepLinkError, match="check date"):
            PartnerLinkProfile(
                partner_id="p",
                parameters={"check_in": Preservation.PRESERVED},
                checked_at=None,
            )

    def test_an_all_unverified_profile_needs_no_date(self) -> None:
        """Because it claims nothing."""
        PartnerLinkProfile(
            partner_id="p", parameters={"check_in": Preservation.UNVERIFIED}, checked_at=None
        )

    def test_an_existing_query_string_is_preserved(self) -> None:
        link = build_deep_link(
            base_url="https://partner.example/book?utm_source=x",
            partner=a_profile(),
            click_reference="c1",
        )
        assert "utm_source=x" in link.url
        assert "&click_ref=c1" in link.url


class TestConstantTimeComparisonIsStructural:
    """A timing property cannot be asserted behaviourally, so it is asserted in
    the source.

    Mutation testing replaced `hmac.compare_digest` with `!=` and the whole suite
    still passed — correctly, because a unit test cannot observe a timing side
    channel. That leaves the property real and unguarded, which is the worst of
    both: everyone believes it holds and nothing checks it.

    So the check moves to where the property lives. Same technique as
    `test_the_module_offers_no_way_to_build_a_time_from_coordinates` in the
    routing adapter: when behaviour cannot see it, absence and presence in the
    source can.
    """

    def test_the_signature_comparison_uses_compare_digest(self) -> None:
        import inspect

        import affiliate.webhook as module

        source = inspect.getsource(module.verify_and_parse)
        assert "hmac.compare_digest" in source, (
            "signature comparison must be constant-time: `==` on a hex digest leaks "
            "the correct prefix, and a signature is then guessable one byte at a time"
        )

    def test_no_plain_equality_is_used_on_the_signature(self) -> None:
        import inspect

        import affiliate.webhook as module

        source = inspect.getsource(module.verify_and_parse)
        assert "== signature" not in source
        assert "expected != signature" not in source
        assert "signature ==" not in source
