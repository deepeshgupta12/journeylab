"""Travel-time matrices and profile honesty — TST-A11Y-003 · STEP-005.05.

THE ONE THAT MATTERS MOST IN THIS STEP
    A wheelchair user given walking times receives an itinerary computed for
    somebody who can take stairs. Every duration is plausible; the transfer at Bern
    that needs a footbridge reads as nine minutes. There is no way for the person to
    know, which is what makes it worse than a refusal.

    So these tests do not merely check that a flag exists. They check that walking
    cannot be returned for a wheelchair request, that the refusal carries no
    duration field a caller could coerce, and that the disclosure says step-free
    access was **not checked** rather than implying it was fine.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from matrix import (
    MatrixKey,
    Profile,
    ProfileSupport,
    ProfileUnsupported,
    RoutingError,
    TravelTime,
    is_expired,
    profile_unsupported,
    resolve_profile,
)

NOW = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def support(*profiles: Profile, provider: str = "otp") -> ProfileSupport:
    return ProfileSupport(
        provider_id=provider,
        profiles=frozenset(profiles),
        declared_by="Deepesh Kumar Gupta",
        evidence="provider documentation reviewed 2026-08-17",
    )


# --- REQ-A11Y-003: no silent substitution -------------------------------------


class TestWheelchairIsNeverWalking:
    def test_an_unsupported_wheelchair_profile_is_refused_not_downgraded(self) -> None:
        """The prohibition. Walking times for a wheelchair request are confident
        numbers computed for a different body."""
        outcome = resolve_profile(Profile.WHEELCHAIR, support(Profile.WALKING, Profile.TRANSIT))
        assert isinstance(outcome, ProfileUnsupported)
        assert outcome.profile is Profile.WHEELCHAIR

    def test_the_refusal_carries_no_duration_of_any_kind(self) -> None:
        """A nullable duration is one `or 0` away from becoming a travel time, and a
        travel time is precisely what must not exist here."""
        outcome = profile_unsupported(Profile.WHEELCHAIR, "otp")
        assert not hasattr(outcome, "duration")
        assert not hasattr(outcome, "seconds")
        assert not hasattr(outcome, "minutes")

    def test_the_disclosure_says_not_checked_rather_than_implying_accessible(self) -> None:
        """ "No step-free data" must not read as "step-free". The wording carries the
        requirement, not just the type."""
        text = profile_unsupported(Profile.WHEELCHAIR, "otp").disclosure.lower()
        assert "not been checked" in text
        assert "not shown as accessible" in text
        assert "walking times have not been substituted" in text

    def test_a_supported_profile_is_returned_unchanged(self) -> None:
        """Guards the guard: a resolver that refused everything would pass every
        test above while making the product unable to route anything."""
        outcome = resolve_profile(Profile.WHEELCHAIR, support(Profile.WHEELCHAIR))
        assert outcome is Profile.WHEELCHAIR

    def test_walking_support_does_not_imply_wheelchair_support(self) -> None:
        assert not support(Profile.WALKING).supports(Profile.WHEELCHAIR)

    def test_every_profile_has_its_own_disclosure(self) -> None:
        for profile in Profile:
            assert len(profile_unsupported(profile, "otp").disclosure) > 30

    def test_a_refusal_without_a_disclosure_is_refused(self) -> None:
        with pytest.raises(RoutingError, match="silent substitution"):
            ProfileUnsupported(profile=Profile.WHEELCHAIR, provider_id="otp", disclosure=" ")


class TestProfileSupportIsAttributed:
    def test_support_must_name_who_declared_it_and_why(self) -> None:
        """An unattributed accessibility claim cannot be reviewed, and a reviewer
        must be able to disagree with a named source."""
        with pytest.raises(RoutingError, match="cannot be reviewed"):
            ProfileSupport(
                provider_id="otp",
                profiles=frozenset({Profile.WHEELCHAIR}),
                declared_by="",
                evidence="",
            )

    def test_a_provider_supporting_nothing_is_refused(self) -> None:
        with pytest.raises(RoutingError, match="is not one"):
            ProfileSupport(provider_id="otp", profiles=frozenset(), declared_by="x", evidence="y")


# --- straight-line distance is not a route ------------------------------------


class TestTravelTimeIsAlwaysComputed:
    def test_a_travel_time_requires_recorded_assumptions(self) -> None:
        """A duration nobody can interrogate is not evidence. Walking speed,
        transfer buffer and lift assumptions all change the answer."""
        with pytest.raises(RoutingError, match="assumptions"):
            TravelTime(
                origin_id="a",
                destination_id="b",
                profile=Profile.WALKING,
                duration=timedelta(minutes=9),
                provider_id="otp",
                computed_at=NOW,
                departure_at=NOW,
                assumptions=(),
            )

    def test_a_non_positive_duration_is_refused(self) -> None:
        """A failure must surface rather than become an instant journey — which is
        what a straight-line or zeroed result looks like downstream."""
        for bad in (timedelta(0), timedelta(minutes=-5)):
            with pytest.raises(RoutingError, match="not"):
                TravelTime(
                    origin_id="a",
                    destination_id="b",
                    profile=Profile.WALKING,
                    duration=bad,
                    provider_id="otp",
                    computed_at=NOW,
                    departure_at=NOW,
                    assumptions=("1.4 m/s walking speed",),
                )

    def test_the_module_offers_no_way_to_build_a_time_from_coordinates(self) -> None:
        """The structural half of "straight-line distance is never substituted".

        There is no haversine, no distance helper and no coordinate-taking
        constructor — so the substitution cannot be made by reaching for a
        convenience that happens to exist.
        """
        import matrix

        names = dir(matrix)
        for forbidden in (
            "haversine",
            "distance",
            "as_the_crow_flies",
            "euclidean",
            "great_circle",
        ):
            assert not any(forbidden in n.lower() for n in names), forbidden

    def test_naive_timestamps_are_refused(self) -> None:
        with pytest.raises(RoutingError, match="timezone-aware"):
            TravelTime(
                origin_id="a",
                destination_id="b",
                profile=Profile.WALKING,
                duration=timedelta(minutes=9),
                provider_id="otp",
                computed_at=datetime(2026, 8, 17, 9, 0),  # noqa: DTZ001
                departure_at=NOW,
                assumptions=("default",),
            )

    def test_departure_time_is_part_of_the_result(self) -> None:
        """Time-dependent matrices: the same pair at 08:00 and at 23:00 are
        different answers, so a result that does not record which is unusable."""
        result = TravelTime(
            origin_id="a",
            destination_id="b",
            profile=Profile.TRANSIT,
            duration=timedelta(minutes=41),
            provider_id="otp",
            computed_at=NOW,
            departure_at=NOW + timedelta(hours=14),
            assumptions=("5 min transfer buffer",),
        )
        assert result.departure_at != result.computed_at


# --- the cache key carries the licence ----------------------------------------


def a_key(licence_id: str = "opentransportdata.swiss") -> MatrixKey:
    return MatrixKey(
        profile=Profile.TRANSIT,
        departure_window_start=NOW,
        departure_window_end=NOW + timedelta(hours=1),
        licence_id=licence_id,
        provider_id="otp",
    )


class TestMatrixCacheKey:
    def test_licence_is_part_of_the_identity(self) -> None:
        """Two matrices for the same stops and window from differently-licensed
        sources have different retention rules. Conflating them serves one past its
        terms — a contract breach that looks exactly like a cache hit."""
        assert a_key("opentransportdata.swiss") != a_key("ODbL-1.0")

    def test_a_key_without_a_licence_is_refused(self) -> None:
        with pytest.raises(RoutingError, match="licence_id is required"):
            a_key(licence_id="  ")

    def test_a_reversed_window_is_refused(self) -> None:
        with pytest.raises(RoutingError, match="ends before it starts"):
            MatrixKey(
                profile=Profile.TRANSIT,
                departure_window_start=NOW + timedelta(hours=1),
                departure_window_end=NOW,
                licence_id="x",
                provider_id="otp",
            )

    def test_expiry_follows_the_licence_limit(self) -> None:
        computed = NOW
        assert not is_expired(a_key(), computed, NOW + timedelta(hours=1), 7200)
        assert is_expired(a_key(), computed, NOW + timedelta(hours=3), 7200)

    def test_no_limit_means_the_licence_permits_it_not_that_it_is_unset(self) -> None:
        """`None` is a fact about the source, not a missing value."""
        assert not is_expired(a_key(), NOW, NOW + timedelta(days=365), None)

    def test_naive_times_are_refused(self) -> None:
        with pytest.raises(RoutingError, match="timezone-aware"):
            is_expired(a_key(), NOW, datetime(2026, 8, 17, 10, 0), 60)  # noqa: DTZ001
