"""The waitlist and its consent — TST-PRIV-004 · STEP-007.04.

WHAT THESE ARE PROTECTING
    The first operation in this product that writes a stranger's personal data on an
    unauthenticated request, and the four ways that goes wrong quietly:

      consent assumed            -> an entry written because a field defaulted to
                                    true, rather than because somebody agreed
      the address echoed back    -> BUG-035, on an endpoint where the value that
                                    failed validation is somebody's email address
      withdrawal that cascades   -> REQ-PRIV-004: withdrawing one purpose must not
                                    touch a purpose granted separately
      withdrawal that pretends   -> a row marked withdrawn that still holds the
                                    address it was supposed to erase

    The last is the one worth naming. "Withdrawn" is a state somebody is told about
    and cannot inspect, so a withdrawal that sets a flag and leaves the data is a
    defect nobody outside this repository could ever detect.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
import pytest
from dbcheck import DSN, requires_db
from fastapi.testclient import TestClient
from platform_api.waitlist import (
    EMAIL_MAX_LENGTH,
    WAITLIST_PURPOSE,
    WaitlistError,
    join_waitlist,
    mint_withdrawal_token,
    normalise_email,
    require_consent,
    token_hash,
    validate_email,
    validate_region_query,
    withdraw_waitlist_consent,
)

NOW = datetime(2026, 9, 10, 9, 24, 11, tzinfo=UTC)


@dataclass
class FakeCursor:
    """Enough cursor for the pure paths. Refuses to pretend it ran SQL."""

    rows: list[tuple[Any, ...]] = field(default_factory=list)
    executed: list[tuple[str, tuple[object, ...]]] = field(default_factory=list)

    def execute(self, query: str, params: tuple[object, ...] = (), /) -> object:
        self.executed.append((query, params))
        return None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows


def unique_address() -> str:
    """A fresh address per test.

    The active-entry index is unique per address, so a fixed literal would make
    these tests order-dependent and green only on a clean database — which is the
    kind of thing that passes locally and fails once in CI.
    """
    return f"traveller-{uuid.uuid4().hex[:12]}@example.com"


# --- consent is an action, not a default -------------------------------------


class TestConsentIsExplicit:
    """REQ-PRIV-002. The sub-step's rule: no entry without a consent record."""

    def test_a_waitlist_entry_without_consent_is_refused(self) -> None:
        with pytest.raises(WaitlistError) as caught:
            require_consent(purpose=WAITLIST_PURPOSE, granted=False)
        assert caught.value.fields == ("consent.granted",)

    def test_refusing_consent_writes_nothing(self) -> None:
        """Not "returns an error" — writes NOTHING.

        A refusal that had already inserted a row would satisfy any test asserting
        the status code and none asserting the point of the rule.
        """
        cursor = FakeCursor()
        with pytest.raises(WaitlistError):
            join_waitlist(
                cursor,
                email="someone@example.com",
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=False,
                now=NOW,
            )
        assert cursor.executed == [], "a refused request reached the database"

    def test_an_invalid_address_writes_nothing_either(self) -> None:
        cursor = FakeCursor()
        with pytest.raises(WaitlistError):
            join_waitlist(
                cursor,
                email="not-an-address",
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
        assert cursor.executed == []

    def test_a_purpose_this_endpoint_does_not_serve_is_refused(self) -> None:
        """The enum has one member, and this is why it is not a free string.

        A `purpose` column accepting anything is a column that eventually holds
        'marketing', because one caller passed it and nothing said no.
        """
        with pytest.raises(WaitlistError) as caught:
            require_consent(purpose="marketing", granted=True)
        assert caught.value.fields == ("consent.purpose",)


# --- the address is never echoed ---------------------------------------------


class TestTheAddressIsNeverEchoed:
    """BUG-035's lesson, applied where the offending value identifies a person."""

    @pytest.mark.parametrize(
        "address",
        [
            "no-at-sign",
            "two@@example.com",
            "@example.com",
            "local@",
            "local@nodot",
            "has space@example.com",
            "a@b.com\nInjected: header",
        ],
    )
    def test_a_rejected_address_never_appears_in_the_message(self, address: str) -> None:
        """The message names the FIELD. It must not quote the value.

        On an unauthenticated endpoint the message reaches a problem document, so
        quoting the input both discloses personal data and reflects arbitrary
        attacker-supplied text back to whoever reads the response.
        """
        with pytest.raises(WaitlistError) as caught:
            validate_email(address)
        message = str(caught.value)
        assert address not in message
        # The distinctive part, so a partial echo is caught too.
        assert address.split("@")[0] not in message or len(address.split("@")[0]) < 3
        assert caught.value.fields == ("email",)

    def test_an_oversized_address_is_rejected_by_length_not_by_content(self) -> None:
        too_long = "a" * EMAIL_MAX_LENGTH + "@example.com"
        with pytest.raises(WaitlistError) as caught:
            validate_email(too_long)
        assert "a" * 20 not in str(caught.value)


class TestAddressHandling:
    def test_a_valid_address_is_returned_as_typed(self) -> None:
        """Trimmed, but not lowercased.

        The local part is case-sensitive under RFC 5321. Effectively no operator
        treats it that way, which is a reason to compare case-insensitively and not
        a reason to rewrite somebody's name.
        """
        assert validate_email("  Traveller@Example.com  ") == "Traveller@Example.com"

    def test_normalisation_is_only_for_comparison(self) -> None:
        assert normalise_email("  Traveller@Example.COM ") == "traveller@example.com"

    def test_an_empty_destination_is_absent_rather_than_blank(self) -> None:
        assert validate_region_query("   ") is None
        assert validate_region_query(None) is None

    def test_an_oversized_destination_is_refused(self) -> None:
        with pytest.raises(WaitlistError) as caught:
            validate_region_query("x" * 65)
        assert caught.value.fields == ("region_query",)


class TestTheWithdrawalToken:
    def test_the_stored_form_is_a_hash_and_not_the_token(self) -> None:
        """A database reader must be able to verify a token and not to mint one."""
        token = mint_withdrawal_token()
        stored = token_hash(token)
        assert stored != token
        assert token not in stored
        assert len(stored) == 64  # sha256 hex

    def test_two_tokens_are_never_the_same(self) -> None:
        tokens = {mint_withdrawal_token() for _ in range(256)}
        assert len(tokens) == 256

    def test_a_token_is_long_enough_to_be_a_secret(self) -> None:
        """This is the entire authorisation for withdrawal. A guessed token
        withdraws somebody else's consent."""
        assert len(mint_withdrawal_token()) >= 40


# --- the database behaviour, against a real schema ---------------------------


@pytest.fixture
def db() -> Iterator[psycopg.Connection[Any]]:
    with psycopg.connect(DSN) as conn:
        yield conn


@requires_db
class TestAgainstTheRealSchema:
    """`RISK-017`: the graph holds one node per `.sql` file, so a migration's blast
    radius comes from running it. These exercise `019` rather than describe it."""

    def test_a_grant_is_recorded_and_the_token_round_trips(
        self, db: psycopg.Connection[Any]
    ) -> None:
        address = unique_address()
        with db.cursor() as cur:
            grant = join_waitlist(
                cur,
                email=address,
                region_query="Faroe Islands",
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            db.commit()

            assert grant.purpose == WAITLIST_PURPOSE
            assert grant.basis == "consent"

            cur.execute(
                "SELECT email, email_normalized, region_query, withdrawal_token_hash, "
                "withdrawn_at FROM waitlist_entries WHERE email_normalized = %s",
                (normalise_email(address),),
            )
            rows = cur.fetchall()
        assert len(rows) == 1
        stored_email, normalized, region, stored_hash, withdrawn = rows[0]
        assert stored_email == address
        assert normalized == address.lower()
        assert region == "Faroe Islands"
        assert withdrawn is None
        # The plaintext token is nowhere in the row.
        assert stored_hash == token_hash(grant.withdrawal_token)
        assert grant.withdrawal_token not in str(rows[0])

    def test_a_repeat_join_rotates_the_token_without_a_second_row(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """One active entry per address, and the response shape is identical.

        That is what stops this operation being a test for whether an address is
        already on the list.
        """
        address = unique_address()
        with db.cursor() as cur:
            first = join_waitlist(
                cur,
                email=address,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            second = join_waitlist(
                cur,
                email=address,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW + timedelta(days=3),
            )
            db.commit()

            cur.execute(
                "SELECT count(*) FROM waitlist_entries WHERE email_normalized = %s",
                (normalise_email(address),),
            )
            count = cur.fetchall()[0][0]

        assert count == 1, "a repeated join created a second active entry"
        assert first.withdrawal_token != second.withdrawal_token
        # RE-SUBMITTING A FORM IS NOT A NEW DECISION. Moving `granted_at` forward
        # would quietly extend anything measured from it.
        assert second.granted_at == first.granted_at

    def test_withdrawal_deletes_the_address_and_keeps_the_grant(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """REQ-PRIV-006 and the evidence rule, which are not in conflict.

        The grant is evidence that processing was lawful and survives. The address
        is personal data and does not.
        """
        address = unique_address()
        with db.cursor() as cur:
            grant = join_waitlist(
                cur,
                email=address,
                region_query="Svalbard",
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            db.commit()

            result = withdraw_waitlist_consent(
                cur, token=grant.withdrawal_token, now=NOW + timedelta(days=1)
            )
            db.commit()

            assert result is not None
            assert result.changed is True

            cur.execute(
                "SELECT email, email_normalized, purpose, granted_at, withdrawn_at "
                "FROM waitlist_entries WHERE withdrawal_token_hash = %s",
                (token_hash(grant.withdrawal_token),),
            )
            rows = cur.fetchall()

        assert len(rows) == 1, "the row was deleted; the grant is the evidence"
        email, normalized, purpose, granted_at, withdrawn_at = rows[0]
        assert email is None, "the address survived a withdrawal"
        assert normalized is None, "the normalised address survived a withdrawal"
        assert purpose == WAITLIST_PURPOSE
        assert granted_at == NOW
        assert withdrawn_at is not None

    def test_the_address_is_gone_from_every_column_that_held_it(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """The traversal assertion. Not "the column we remembered" — the row.

        A withdrawal that cleared `email` and left `email_normalized` would pass a
        narrower test and leave a searchable copy of the address behind.
        """
        address = unique_address()
        with db.cursor() as cur:
            grant = join_waitlist(
                cur,
                email=address,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            db.commit()
            withdraw_waitlist_consent(cur, token=grant.withdrawal_token, now=NOW)
            db.commit()

            cur.execute(
                "SELECT to_jsonb(w)::text FROM waitlist_entries w WHERE withdrawal_token_hash = %s",
                (token_hash(grant.withdrawal_token),),
            )
            serialised = cur.fetchall()[0][0]

        assert address not in serialised
        assert address.lower() not in serialised
        assert address.split("@")[0] not in serialised

    def test_the_schema_refuses_a_withdrawn_row_that_kept_its_address(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """The constraint, not the code path.

        `waitlist_active_has_address` is what makes "withdrawal erases the address"
        structural. A future code path that forgot the second half must fail to
        commit rather than leave personal data behind a withdrawal, so the
        constraint is exercised directly.
        """
        address = unique_address()
        with db.cursor() as cur:
            grant = join_waitlist(
                cur,
                email=address,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            db.commit()

            with pytest.raises(psycopg.errors.CheckViolation):
                cur.execute(
                    "UPDATE waitlist_entries SET withdrawn_at = %s "
                    "WHERE withdrawal_token_hash = %s",
                    (NOW, token_hash(grant.withdrawal_token)),
                )
            db.rollback()

    def test_withdrawing_twice_succeeds_and_changes_nothing(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """The state the caller asked for is the state that holds."""
        address = unique_address()
        with db.cursor() as cur:
            grant = join_waitlist(
                cur,
                email=address,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            db.commit()

            first = withdraw_waitlist_consent(
                cur, token=grant.withdrawal_token, now=NOW + timedelta(days=1)
            )
            db.commit()
            second = withdraw_waitlist_consent(
                cur, token=grant.withdrawal_token, now=NOW + timedelta(days=2)
            )
            db.commit()

        assert first is not None and second is not None
        assert first.changed is True
        assert second.changed is False, "the second call re-dated the withdrawal"
        assert first.withdrawn_at == second.withdrawn_at

    def test_an_unknown_token_is_indistinguishable_from_a_wrong_one(
        self, db: psycopg.Connection[Any]
    ) -> None:
        with db.cursor() as cur:
            never_issued = withdraw_waitlist_consent(cur, token=mint_withdrawal_token(), now=NOW)
        assert never_issued is None

    def test_withdrawing_lets_the_same_address_rejoin(self, db: psycopg.Connection[Any]) -> None:
        """A plain UNIQUE would make withdrawal permanent.

        Having withdrawn, the person could never come back — the tombstone would
        still own their address. The index is partial for this reason.
        """
        address = unique_address()
        with db.cursor() as cur:
            first = join_waitlist(
                cur,
                email=address,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            db.commit()
            withdraw_waitlist_consent(cur, token=first.withdrawal_token, now=NOW)
            db.commit()

            rejoined = join_waitlist(
                cur,
                email=address,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW + timedelta(days=30),
            )
            db.commit()

        assert rejoined.withdrawal_token != first.withdrawal_token
        assert rejoined.granted_at == NOW + timedelta(days=30), (
            "a rejoin is a new decision and must carry its own date"
        )

    def test_the_schema_refuses_a_second_purpose(self, db: psycopg.Connection[Any]) -> None:
        """REQ-PRIV-002 enforced by the database, not only by the enum."""
        with db.cursor() as cur:
            with pytest.raises(psycopg.errors.CheckViolation):
                cur.execute(
                    "INSERT INTO waitlist_entries (email, email_normalized, purpose, basis, "
                    "granted_at, withdrawal_token_hash) VALUES (%s, %s, %s, %s, %s, %s)",
                    ("x@example.com", "x@example.com", "marketing", "consent", NOW, "deadbeef"),
                )
            db.rollback()


# --- REQ-PRIV-004: withdrawal does not cascade -------------------------------


@requires_db
class TestWithdrawalTouchesNothingElse:
    """TST-PRIV-004 — withdrawing one purpose leaves every other intact."""

    def test_waitlist_withdrawal_does_not_touch_consent_records(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """The two consent stores are separate tables, and this proves the
        separation rather than asserting it.

        `consent_records` (DATA-016) belongs to account holders and STEP-008.04.
        A waitlist withdrawal must not reach into it — not because it is unlikely
        to, but because "withdrawal is independent" is the requirement.
        """
        address = unique_address()
        with db.cursor() as cur:
            cur.execute("SELECT count(*), coalesce(max(schema_version), 0) FROM consent_records")
            before = cur.fetchall()[0]

            grant = join_waitlist(
                cur,
                email=address,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            db.commit()
            withdraw_waitlist_consent(cur, token=grant.withdrawal_token, now=NOW)
            db.commit()

            cur.execute("SELECT count(*), coalesce(max(schema_version), 0) FROM consent_records")
            after = cur.fetchall()[0]

        assert before == after

    def test_withdrawal_affects_exactly_one_row(self, db: psycopg.Connection[Any]) -> None:
        """Two people on the list; one withdraws. The other is untouched."""
        staying, leaving = unique_address(), unique_address()
        with db.cursor() as cur:
            kept = join_waitlist(
                cur,
                email=staying,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            going = join_waitlist(
                cur,
                email=leaving,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=NOW,
            )
            db.commit()

            withdraw_waitlist_consent(cur, token=going.withdrawal_token, now=NOW)
            db.commit()

            cur.execute(
                "SELECT email, withdrawn_at FROM waitlist_entries WHERE withdrawal_token_hash = %s",
                (token_hash(kept.withdrawal_token),),
            )
            survivor = cur.fetchall()[0]

        assert survivor[0] == staying, "an unrelated entry lost its address"
        assert survivor[1] is None, "an unrelated consent was withdrawn"


# --- the HTTP surface --------------------------------------------------------


@pytest.fixture
def client() -> Iterator[TestClient]:
    os.environ["JOURNEYLAB_DATABASE_URL"] = DSN
    import app as application

    with TestClient(application.app) as running:
        yield running


def idempotent() -> dict[str, str]:
    return {"Idempotency-Key": f"waitlist-{uuid.uuid4().hex}"}


@requires_db
class TestTheHttpSurface:
    def test_joining_returns_the_token_exactly_once(self, client: TestClient) -> None:
        response = client.post(
            "/waitlist",
            json={
                "email": unique_address(),
                "region_query": "Faroe Islands",
                "consent": {"purpose": WAITLIST_PURPOSE, "granted": True},
            },
            headers=idempotent(),
        )
        assert response.status_code == 201
        body = response.json()
        assert set(body) == {"purpose", "basis", "granted_at", "withdrawal_token"}
        assert body["purpose"] == WAITLIST_PURPOSE
        assert body["basis"] == "consent"
        assert len(body["withdrawal_token"]) >= 40

    def test_the_response_does_not_echo_the_address(self, client: TestClient) -> None:
        """It is what the caller just sent, so returning it adds nothing — and a
        response containing an email address ends up in a client-side log."""
        address = unique_address()
        response = client.post(
            "/waitlist",
            json={"email": address, "consent": {"purpose": WAITLIST_PURPOSE, "granted": True}},
            headers=idempotent(),
        )
        assert address not in response.text

    def test_consent_false_is_refused_and_names_the_field(self, client: TestClient) -> None:
        address = unique_address()
        response = client.post(
            "/waitlist",
            json={"email": address, "consent": {"purpose": WAITLIST_PURPOSE, "granted": False}},
            headers=idempotent(),
        )
        assert response.status_code == 400
        assert response.headers["content-type"].startswith("application/problem+json")
        body = response.json()
        assert body["code"] == "validation.invalid_request"
        assert body["remediation"]["fields"] == ["consent.granted"]
        # The refusal must not carry the address it refused.
        assert address not in response.text

    def test_a_missing_consent_block_is_refused(self, client: TestClient) -> None:
        """No default anywhere: the field is required by the model too."""
        response = client.post(
            "/waitlist",
            json={"email": unique_address()},
            headers=idempotent(),
        )
        assert response.status_code == 400
        assert response.json()["code"] == "validation.invalid_request"

    def test_a_truthy_string_is_not_consent(self, client: TestClient) -> None:
        """`StrictBool`. "true" arriving where a consent decision belongs is an
        accident, and coercing it would record a grant nobody gave."""
        response = client.post(
            "/waitlist",
            json={
                "email": unique_address(),
                "consent": {"purpose": WAITLIST_PURPOSE, "granted": "true"},
            },
            headers=idempotent(),
        )
        assert response.status_code == 400

    def test_an_invalid_address_is_refused_without_being_echoed(self, client: TestClient) -> None:
        response = client.post(
            "/waitlist",
            json={
                "email": "definitely not an address",
                "consent": {"purpose": WAITLIST_PURPOSE, "granted": True},
            },
            headers=idempotent(),
        )
        assert response.status_code == 400
        assert "definitely not an address" not in response.text

    def test_the_idempotency_key_is_required(self, client: TestClient) -> None:
        """The contract declares the parameter; this is what enforces it."""
        response = client.post(
            "/waitlist",
            json={
                "email": unique_address(),
                "consent": {"purpose": WAITLIST_PURPOSE, "granted": True},
            },
        )
        assert response.status_code == 400
        assert response.json()["remediation"]["fields"] == ["Idempotency-Key"]

    def test_a_round_trip_join_then_withdraw(self, client: TestClient) -> None:
        address = unique_address()
        joined = client.post(
            "/waitlist",
            json={"email": address, "consent": {"purpose": WAITLIST_PURPOSE, "granted": True}},
            headers=idempotent(),
        )
        token = joined.json()["withdrawal_token"]

        withdrawn = client.post(
            "/waitlist:withdraw",
            json={"withdrawal_token": token},
            headers=idempotent(),
        )
        assert withdrawn.status_code == 200
        body = withdrawn.json()
        assert set(body) == {"purpose", "withdrawn_at"}
        assert address not in withdrawn.text

        with psycopg.connect(DSN) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT email FROM waitlist_entries WHERE withdrawal_token_hash = %s",
                (token_hash(token),),
            )
            assert cur.fetchall()[0][0] is None

    def test_an_unknown_token_is_404_not_403(self, client: TestClient) -> None:
        """A 403 discloses that there is something there to be forbidden.

        The contract forbids a bare 403 everywhere and this operation reuses the
        shared `NotFoundOrForbidden`, so a token that never existed and a token
        belonging to somebody else are indistinguishable.
        """
        response = client.post(
            "/waitlist:withdraw",
            json={"withdrawal_token": mint_withdrawal_token()},
            headers=idempotent(),
        )
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "authz.forbidden"
        assert body["status"] == 404
        assert body["retryable"] is False

    def test_withdrawing_twice_over_http_is_a_success(self, client: TestClient) -> None:
        joined = client.post(
            "/waitlist",
            json={
                "email": unique_address(),
                "consent": {"purpose": WAITLIST_PURPOSE, "granted": True},
            },
            headers=idempotent(),
        )
        token = joined.json()["withdrawal_token"]
        for _ in range(2):
            again = client.post(
                "/waitlist:withdraw",
                json={"withdrawal_token": token},
                headers=idempotent(),
            )
            assert again.status_code == 200

    def test_the_response_shape_is_identical_for_a_repeat_join(self, client: TestClient) -> None:
        """So the operation cannot be used to discover whether an address is listed."""
        address = unique_address()
        payload = {
            "email": address,
            "consent": {"purpose": WAITLIST_PURPOSE, "granted": True},
        }
        first = client.post("/waitlist", json=payload, headers=idempotent())
        second = client.post("/waitlist", json=payload, headers=idempotent())

        assert first.status_code == second.status_code == 201
        assert set(first.json()) == set(second.json())
        assert first.json()["granted_at"] == second.json()["granted_at"]

    def test_an_unknown_field_is_rejected_rather_than_dropped(self, client: TestClient) -> None:
        """`additionalProperties: false`, mirrored by `extra="forbid"`.

        A client sending traveller details to an unauthenticated endpoint is
        refused rather than silently having them dropped — the drop would look
        like acceptance.
        """
        response = client.post(
            "/waitlist",
            json={
                "email": unique_address(),
                "consent": {"purpose": WAITLIST_PURPOSE, "granted": True},
                "date_of_birth": "1990-01-01",
            },
            headers=idempotent(),
        )
        assert response.status_code == 400


# --- the source itself -------------------------------------------------------


class TestNothingLogsTheAddress:
    """§8: the address is never logged, never a trace attribute, never in an event.

    Asserted on the source, because a passing request proves nothing about a
    logging call that did not happen to fire.
    """

    def test_the_rule_module_imports_no_logger(self) -> None:
        import inspect

        from platform_api import waitlist

        source = inspect.getsource(waitlist)
        for forbidden in ("import logging", "logger", "print(", "warnings.warn"):
            assert forbidden not in source, f"{forbidden} in the waitlist rule"

    def test_the_handlers_do_not_log_either(self) -> None:
        import inspect

        import app as application

        for handler in (application.join_the_waitlist, application.withdraw_from_the_waitlist):
            source = inspect.getsource(handler)
            for forbidden in ("logging", "logger", "print("):
                assert forbidden not in source, f"{forbidden} in {handler.__name__}"
