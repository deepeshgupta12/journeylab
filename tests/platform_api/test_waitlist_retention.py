"""Waitlist retention — BUG-036 · DEC-012.

WHAT THESE ARE PROTECTING
    `DEC-012`: an address is kept until the one message it was given for is sent, and
    never more than 12 calendar months after the grant. Four ways that goes wrong
    quietly:

      the boundary drifts      -> "12 months" computed as 365 days, or in the
                                  database session's time zone, so the same entry is
                                  due on one connection and not another
      the address survives     -> a row marked expired that still holds it — the
                                  withdrawal failure `019` closed, reopened by a
                                  second way for an entry to end
      the grant is destroyed   -> deleting the row, which erases the evidence that
                                  processing was ever lawful
      the sweep is not safe    -> a second run that re-ends rows, or a run that
                                  touches entries the person already withdrew
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import psycopg
import pytest
from dbcheck import DSN, requires_db
from platform_api.waitlist import (
    RETENTION_MONTHS,
    WAITLIST_PURPOSE,
    WaitlistRetentionError,
    expire_waitlist_entries,
    join_waitlist,
    months_before,
    token_hash,
    withdraw_waitlist_consent,
)

#: A distinct era from `test_waitlist.py`, so rows either file leaves behind can never
#: be granted after a sweep instant used here.
T0 = datetime(2030, 9, 10, 9, 24, 11, tzinfo=UTC)


def address() -> str:
    return f"retention-{uuid.uuid4().hex[:12]}@example.com"


# --- the arithmetic -------------------------------------------------------------


class TestCalendarMonths:
    def test_the_period_is_the_one_the_owner_decided(self) -> None:
        """Pinned, so changing it is a decision with a record rather than an edit."""
        assert RETENTION_MONTHS == 12

    def test_twelve_calendar_months_back(self) -> None:
        assert months_before(datetime(2031, 9, 14, 8, tzinfo=UTC), 12) == datetime(
            2030, 9, 14, 8, tzinfo=UTC
        )

    def test_a_leap_day_clamps_to_the_end_of_february(self) -> None:
        """Not an exception, and not 1 March — which would keep the address a day
        longer than the person was told."""
        assert months_before(datetime(2028, 2, 29, 12, tzinfo=UTC), 12) == datetime(
            2027, 2, 28, 12, tzinfo=UTC
        )

    def test_a_month_end_clamps(self) -> None:
        assert months_before(datetime(2026, 3, 31, tzinfo=UTC), 1) == datetime(
            2026, 2, 28, tzinfo=UTC
        )

    def test_it_is_not_365_days(self) -> None:
        """When the year being counted back across contains 29 February, 365 days and
        12 months land on different dates — and the form says months.

        The first version of this test used 1 March 2029, whose preceding year holds
        no leap day, so the two agreed and the test failed for the wrong reason: it
        was asserting a difference that does not exist on that date.
        """
        moment = datetime(2028, 3, 1, tzinfo=UTC)
        assert months_before(moment, 12) == datetime(2027, 3, 1, tzinfo=UTC)
        assert moment - timedelta(days=365) == datetime(2027, 3, 2, tzinfo=UTC)

    def test_a_zoned_instant_is_converted_to_utc_first(self) -> None:
        """00:30 on 29 February 2028 in Zurich is 23:30 on the 28th in UTC.

        In UTC, twelve months back is 28 February 2027 at 23:30. Done in local time it
        is 29 February → clamped to the 28th at 00:30 CET, which is 23:30 on the 27th
        in UTC — **a day earlier**, so the address would be held a day longer than the
        person was told.

        THE FIRST VERSION OF THIS TEST PROVED NOTHING, AND MUTATION TESTING SAID SO.
        It used 00:30 on 1 January. Subtracting twelve months in local time and
        comparing instants lands on exactly the same instant as doing it in UTC, so a
        mutant deleting the conversion survived. Local and UTC arithmetic only diverge
        when the two calendars disagree about a day that gets clamped — which is
        precisely a leap day that exists on one side of midnight UTC and not the other.
        """
        zurich = datetime(2028, 2, 29, 0, 30, tzinfo=ZoneInfo("Europe/Zurich"))
        assert months_before(zurich, 12) == datetime(2027, 2, 28, 23, 30, tzinfo=UTC)

    def test_a_naive_instant_is_refused(self) -> None:
        with pytest.raises(WaitlistRetentionError):
            months_before(datetime(2031, 1, 1), 12)  # noqa: DTZ001 - the point of the test

    def test_a_negative_period_is_refused(self) -> None:
        with pytest.raises(WaitlistRetentionError):
            months_before(T0, -1)


# --- the sweep, against the real schema -----------------------------------------


@pytest.fixture
def db() -> Iterator[psycopg.Connection[Any]]:
    with psycopg.connect(DSN) as conn:
        yield conn


def grant(cur: Any, *, at: datetime) -> tuple[str, str]:
    """A fresh entry granted at `at`. Returns (row id, withdrawal token)."""
    result = join_waitlist(
        cur, email=address(), region_query=None, purpose=WAITLIST_PURPOSE, granted=True, now=at
    )
    cur.execute(
        "SELECT id::text FROM waitlist_entries WHERE withdrawal_token_hash = %s",
        (token_hash(result.withdrawal_token),),
    )
    return cur.fetchall()[0][0], result.withdrawal_token


def row(cur: Any, entry_id: str) -> dict[str, Any]:
    cur.execute(
        "SELECT email, email_normalized, purpose, granted_at, withdrawn_at, expired_at, "
        "to_jsonb(w)::text FROM waitlist_entries w WHERE id = %s",
        (entry_id,),
    )
    email, normalized, purpose, granted_at, withdrawn_at, expired_at, serialised = cur.fetchall()[0]
    return {
        "email": email,
        "email_normalized": normalized,
        "purpose": purpose,
        "granted_at": granted_at,
        "withdrawn_at": withdrawn_at,
        "expired_at": expired_at,
        "serialised": serialised,
    }


@requires_db
class TestTheCap:
    def test_a_fresh_grant_is_kept(self, db: psycopg.Connection[Any]) -> None:
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0)
            db.commit()
            sweep = expire_waitlist_entries(cur, now=T0 + timedelta(days=1))
            db.commit()
            state = row(cur, entry)
        assert entry not in sweep.expired_ids
        assert state["email"] is not None
        assert state["expired_at"] is None

    def test_a_grant_exactly_twelve_months_old_has_ended(self, db: psycopg.Connection[Any]) -> None:
        """The person was told "12 months", not "more than 12"."""
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0)
            db.commit()
            sweep = expire_waitlist_entries(cur, now=datetime(2031, 9, 10, 9, 24, 11, tzinfo=UTC))
            db.commit()
        assert entry in sweep.expired_at_cap
        assert entry not in sweep.expired_after_notification

    def test_one_second_short_of_twelve_months_is_kept(self, db: psycopg.Connection[Any]) -> None:
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0)
            db.commit()
            sweep = expire_waitlist_entries(cur, now=datetime(2031, 9, 10, 9, 24, 10, tzinfo=UTC))
            db.commit()
            state = row(cur, entry)
        assert entry not in sweep.expired_ids
        assert state["email"] is not None


@requires_db
class TestTheSweepCountsCalendarMonths:
    """`months_before` is tested on its own above. This asserts the SWEEP uses it.

    Written before mutation testing rather than after it: every other sweep test spans
    a year with no 29 February, where 365 days and 12 months agree, so a sweep that
    quietly computed its cutoff as `now - 365 days` would have passed all of them.
    """

    def test_a_leap_year_does_not_end_an_entry_a_day_early(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """Granted 1 March 2027; on 29 February 2028 twelve calendar months have not
        passed, so the address is still held. A 365-day cutoff would have ended it."""
        with db.cursor() as cur:
            entry, _ = grant(cur, at=datetime(2027, 3, 1, tzinfo=UTC))
            db.commit()
            sweep = expire_waitlist_entries(cur, now=datetime(2028, 2, 29, tzinfo=UTC))
            db.commit()
            state = row(cur, entry)
        assert entry not in sweep.expired_ids
        assert state["email"] is not None


@requires_db
class TestUntilSent:
    def test_a_notified_entry_ends_however_young_it_is(self, db: psycopg.Connection[Any]) -> None:
        """Sending the one message exhausts the purpose. Waiting out the cap after
        that would keep an address with nothing left to use it for."""
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0)
            cur.execute(
                "UPDATE waitlist_entries SET notified_at = %s WHERE id = %s",
                (T0 + timedelta(hours=2), entry),
            )
            db.commit()
            sweep = expire_waitlist_entries(cur, now=T0 + timedelta(hours=3))
            db.commit()
        assert entry in sweep.expired_after_notification

    def test_a_notification_cannot_predate_the_grant(self, db: psycopg.Connection[Any]) -> None:
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0)
            db.commit()
            with pytest.raises(psycopg.errors.CheckViolation):
                cur.execute(
                    "UPDATE waitlist_entries SET notified_at = %s WHERE id = %s",
                    (T0 - timedelta(seconds=1), entry),
                )
            db.rollback()


@requires_db
class TestWhatExpirySurvivesAndWhatItDoesNot:
    def test_the_address_goes_and_the_grant_stays(self, db: psycopg.Connection[Any]) -> None:
        """Asserted over the whole serialised row, not the columns remembered — the
        lesson of `.04`'s mutant 7, where clearing one address column and not the
        other left a searchable copy behind."""
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0)
            cur.execute("SELECT email FROM waitlist_entries WHERE id = %s", (entry,))
            original = cur.fetchall()[0][0]
            db.commit()
            expire_waitlist_entries(cur, now=datetime(2031, 9, 11, tzinfo=UTC))
            db.commit()
            state = row(cur, entry)

        assert state["email"] is None
        assert state["email_normalized"] is None
        assert original not in state["serialised"]
        assert original.lower() not in state["serialised"]
        assert original.split("@")[0] not in state["serialised"]
        # The evidence survives.
        assert state["purpose"] == WAITLIST_PURPOSE
        assert state["granted_at"] == T0
        assert state["expired_at"] == datetime(2031, 9, 11, tzinfo=UTC)

    def test_the_schema_refuses_an_expired_row_that_kept_its_address(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """The constraint, not the code path — a future sweep that set `expired_at`
        and forgot the address must fail to commit."""
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0)
            db.commit()
            with pytest.raises(psycopg.errors.CheckViolation):
                cur.execute(
                    "UPDATE waitlist_entries SET expired_at = %s WHERE id = %s",
                    (T0 + timedelta(days=400), entry),
                )
            db.rollback()

    def test_an_expired_entry_does_not_block_rejoining(self, db: psycopg.Connection[Any]) -> None:
        """Expiry ends one grant. It does not stop the person giving a new one."""
        with db.cursor() as cur:
            person = address()
            first = join_waitlist(
                cur, email=person, region_query=None, purpose=WAITLIST_PURPOSE, granted=True, now=T0
            )
            db.commit()
            expire_waitlist_entries(cur, now=datetime(2031, 9, 11, tzinfo=UTC))
            db.commit()
            again = join_waitlist(
                cur,
                email=person,
                region_query=None,
                purpose=WAITLIST_PURPOSE,
                granted=True,
                now=datetime(2031, 10, 1, tzinfo=UTC),
            )
            db.commit()
        assert again.withdrawal_token != first.withdrawal_token
        assert again.granted_at == datetime(2031, 10, 1, tzinfo=UTC)


@requires_db
class TestTheSweepIsSafe:
    def test_withdrawn_entries_are_left_alone(self, db: psycopg.Connection[Any]) -> None:
        """They hold no address already. Stamping `expired_at` on them would rewrite
        how the entry ended."""
        with db.cursor() as cur:
            entry, token = grant(cur, at=T0)
            db.commit()
            withdraw_waitlist_consent(cur, token=token, now=T0 + timedelta(days=5))
            db.commit()
            sweep = expire_waitlist_entries(cur, now=datetime(2031, 9, 11, tzinfo=UTC))
            db.commit()
            state = row(cur, entry)
        assert entry not in sweep.expired_ids
        assert state["expired_at"] is None
        assert state["withdrawn_at"] == T0 + timedelta(days=5)

    def test_a_second_sweep_ends_nothing_the_first_ended(self, db: psycopg.Connection[Any]) -> None:
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0)
            db.commit()
            first = expire_waitlist_entries(cur, now=datetime(2031, 9, 11, tzinfo=UTC))
            db.commit()
            second = expire_waitlist_entries(cur, now=datetime(2031, 9, 11, tzinfo=UTC))
            db.commit()
            state = row(cur, entry)
        assert entry in first.expired_ids
        assert entry not in second.expired_ids
        assert state["expired_at"] == datetime(2031, 9, 11, tzinfo=UTC)

    def test_an_entry_granted_after_the_sweep_instant_is_not_touched(
        self, db: psycopg.Connection[Any]
    ) -> None:
        """A sweep whose clock lags a writer's must leave the row for next time rather
        than fail `waitlist_expiry_after_grant` and end nothing."""
        with db.cursor() as cur:
            entry, _ = grant(cur, at=T0 + timedelta(days=10))
            cur.execute(
                "UPDATE waitlist_entries SET notified_at = %s WHERE id = %s",
                (T0 + timedelta(days=10), entry),
            )
            db.commit()
            sweep = expire_waitlist_entries(cur, now=T0)
            db.commit()
        assert entry not in sweep.expired_ids

    def test_a_naive_sweep_instant_is_refused(self, db: psycopg.Connection[Any]) -> None:
        with db.cursor() as cur, pytest.raises(WaitlistRetentionError):
            expire_waitlist_entries(cur, now=datetime(2031, 9, 11))  # noqa: DTZ001
