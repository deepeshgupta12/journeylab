"""Documented provider limits — STEP-005 reconnaissance, 2026-08-17.

WHY THESE ARE TESTED AT ALL
    They are facts about somebody else's system, and `BUG-026` was exactly that
    kind of fact carried as a justified guess. A constant describing an external
    service needs a citation or a test; these have both.

WHY THEY ARE A COST CONTROL
    `opentransportdata.swiss` is free below its rate limit and explicitly charges
    above it — "These limits can be exceeded, but then costs will be incurred",
    with paid tiers from CHF 500/month. So `ADR-016`'s zero-spend constraint is not
    satisfied by choosing the provider; it is satisfied by staying under these
    numbers. The framework's `TokenBucket` must be configured from them.
"""

from __future__ import annotations

import pytest
from framework.resilience import RateLimitedError, TokenBucket
from places.licence import (
    SWISS_TRANSPORT,
    SWISS_TRANSPORT_GTFS_RT_PER_MINUTE,
    SWISS_TRANSPORT_GTFS_SA_PER_MINUTE,
    SWISS_TRANSPORT_GTFS_SA_PER_MINUTE_CONSERVATIVE,
    SWISS_TRANSPORT_GTFS_SA_PER_MINUTE_OPTIMISTIC,
    SWISS_TRANSPORT_OJP_PER_DAY,
    SWISS_TRANSPORT_OJP_PER_MINUTE,
)


class TestDocumentedLimits:
    def test_the_gtfs_rt_limit_is_five_per_minute(self) -> None:
        """Pinned so a future edit cannot raise it to a comfortable-looking number
        and quietly move the product onto a paid tier."""
        assert SWISS_TRANSPORT_GTFS_RT_PER_MINUTE == 5

    def test_the_ojp_limits_are_recorded(self) -> None:
        assert SWISS_TRANSPORT_OJP_PER_MINUTE == 50
        assert SWISS_TRANSPORT_OJP_PER_DAY == 20_000

    def test_the_realtime_limit_is_far_tighter_than_the_journey_planner(self) -> None:
        """The asymmetry is the thing to remember: ten times tighter, and it is the
        feed a monitoring loop would poll most often."""
        assert SWISS_TRANSPORT_GTFS_RT_PER_MINUTE * 10 == SWISS_TRANSPORT_OJP_PER_MINUTE


class TestABucketBuiltFromTheDocumentedLimitStaysFree:
    def test_five_calls_a_minute_are_permitted_and_the_sixth_is_not(self) -> None:
        """The bucket is what keeps us on the free tier. Refusal here is the
        intended outcome — the alternative is an invoice."""
        bucket = TokenBucket(
            capacity=SWISS_TRANSPORT_GTFS_RT_PER_MINUTE,
            refill_per_second=SWISS_TRANSPORT_GTFS_RT_PER_MINUTE / 60,
        )
        for _ in range(SWISS_TRANSPORT_GTFS_RT_PER_MINUTE):
            bucket.take(0.0)
        with pytest.raises(RateLimitedError):
            bucket.take(0.0)

    def test_the_freshness_slo_is_achievable_inside_the_limit(self) -> None:
        """`.04` promises minute-level alert freshness (5 min). Five polls a minute
        allows one every twelve seconds, so the SLO and the free tier are
        compatible — worth asserting, because a promise the licence cannot fund
        would be a commitment to overspend.
        """
        seconds_between_polls = 60 / SWISS_TRANSPORT_GTFS_RT_PER_MINUTE
        assert seconds_between_polls == 12
        assert seconds_between_polls < 5 * 60

    def test_the_licence_still_permits_commercial_use(self) -> None:
        """Free-below-a-limit is not the same as non-commercial. Open-Meteo was
        rejected for the latter (ADR-016 §2); this is the former."""
        assert SWISS_TRANSPORT.commercial_use_permitted


class TestTheDisputedServiceAlertsLimit:
    """The provider's own two pages disagree, so both are kept.

    `REQ-EVID-002`: conflicting evidence is retained, never averaged. That rule was
    written for provider facts inside an evidence pack, and it applies no less to a
    number that decides whether this project receives an invoice.
    """

    def test_both_readings_are_recorded(self) -> None:
        assert SWISS_TRANSPORT_GTFS_SA_PER_MINUTE_CONSERVATIVE == 2
        assert SWISS_TRANSPORT_GTFS_SA_PER_MINUTE_OPTIMISTIC == 5

    def test_they_are_not_averaged(self) -> None:
        """The specific wrong move. An average of two documented claims is a third
        figure nobody published."""
        average = (
            SWISS_TRANSPORT_GTFS_SA_PER_MINUTE_CONSERVATIVE
            + SWISS_TRANSPORT_GTFS_SA_PER_MINUTE_OPTIMISTIC
        ) / 2
        assert SWISS_TRANSPORT_GTFS_SA_PER_MINUTE != average

    def test_code_uses_the_safer_reading(self) -> None:
        """Not a compromise — an asymmetry. Under-polling costs freshness we can
        measure; over-polling costs money and the provider's goodwill."""
        assert SWISS_TRANSPORT_GTFS_SA_PER_MINUTE == SWISS_TRANSPORT_GTFS_SA_PER_MINUTE_CONSERVATIVE

    def test_the_freshness_slo_survives_the_pessimistic_reading(self) -> None:
        """The reason the dispute does not block anything: even at two polls a
        minute, one poll every thirty seconds is well inside `.04`'s five-minute
        alert SLO. Had it not been, the SLO would have needed revisiting."""
        seconds_between_polls = 60 / SWISS_TRANSPORT_GTFS_SA_PER_MINUTE
        assert seconds_between_polls == 30
        assert seconds_between_polls < 5 * 60
