"""Provider health, coverage and refusal — TST-EVID-006, TST-TRIP-002 · STEP-005.10.

WHAT THESE ARE PROTECTING
    Three failures, each of which looks fine from the inside:

      degradation masked by cache -> the traveller is shown yesterday's answer as
                                     today's (REQ-EVID-006)
      partial simulation          -> a half-planned itinerary that looks like a plan
                                     (REQ-TRIP-002)
      provider identity leaked    -> the supply chain becomes public, and quota
                                     proximity tells an attacker when we degrade
"""

from __future__ import annotations

import inspect
from dataclasses import fields as dataclass_fields
from datetime import UTC, datetime, timedelta

import pytest
from provider_health import (
    PUBLICATION,
    RECOVERY_SUCCESSES,
    CoverageModel,
    HealthChanged,
    HealthError,
    HealthState,
    ProviderHealth,
    PublicCoverage,
    PublicRegion,
    PublishedState,
    RegionFreshness,
    TripAccepted,
    TripRefused,
)

NOW = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)


def provider(pid: str = "otd", *regions: str) -> ProviderHealth:
    return ProviderHealth(provider_id=pid, regions=regions or ("bern",))


def model() -> CoverageModel:
    coverage = CoverageModel()
    coverage.declare_region("bern", depends_on=("otd", "osm"))
    coverage.register(provider("otd", "bern"))
    coverage.register(provider("osm", "bern"))
    return coverage


# --- the state machine ------------------------------------------------------------


class TestRecoveryHasHysteresis:
    def test_one_success_after_an_outage_does_not_restore_health(self) -> None:
        """Promoting on the first success oscillates: healthy, open, healthy, open —
        an event storm, and coverage that accepts and refuses at random, which is
        worse for a traveller than a steady refusal because it is not reproducible."""
        p = provider()
        p.record_failure(reason="timeouts", at=NOW, circuit_open=True)
        p.record_success(at=NOW + timedelta(seconds=30))
        assert p.state is HealthState.RECOVERING
        assert p.published is PublishedState.DEGRADED

    def test_health_returns_after_the_required_run_of_successes(self) -> None:
        p = provider()
        p.record_failure(reason="timeouts", at=NOW, circuit_open=True)
        for i in range(RECOVERY_SUCCESSES):
            p.record_success(at=NOW + timedelta(seconds=30 * (i + 1)))
        assert p.state is HealthState.HEALTHY

    def test_a_failure_during_recovery_resets_the_run(self) -> None:
        """Two successes then a failure is not "nearly recovered"."""
        p = provider()
        p.record_failure(reason="timeouts", at=NOW, circuit_open=True)
        p.record_success(at=NOW)
        p.record_success(at=NOW)
        p.record_failure(reason="timeouts again", at=NOW)
        assert p.successes == 0
        assert p.state is HealthState.DEGRADED

    def test_the_threshold_must_exceed_one_or_it_is_not_hysteresis(self) -> None:
        assert RECOVERY_SUCCESSES > 1


class TestRecoveringIsNotHealthy:
    def test_recovering_publishes_as_degraded(self) -> None:
        """Announcing recovery before it is proven sends full traffic back to a
        half-recovered provider."""
        assert PUBLICATION[HealthState.RECOVERING] is PublishedState.DEGRADED

    def test_every_internal_state_has_a_publication(self) -> None:
        """Four internal states, three published. A state with no mapping would
        raise at the moment of an outage, which is the worst possible moment."""
        for state in HealthState:
            assert state in PUBLICATION


# --- EVT-008 ----------------------------------------------------------------------


class TestEventEmission:
    def test_a_published_state_change_emits_exactly_one_event(self) -> None:
        p = provider()
        p.record_failure(reason="upstream 503", at=NOW, circuit_open=True)
        assert len(p.events()) == 1
        event = p.events()[0]
        assert (event.previous_state, event.new_state) == (
            PublishedState.HEALTHY,
            PublishedState.UNAVAILABLE,
        )
        assert event.affected_regions == ("bern",)

    def test_an_internal_transition_that_does_not_change_the_published_state_is_recorded_but_not_emitted(
        self,
    ) -> None:
        """`DEGRADED -> RECOVERING` publishes `degraded` on both sides. Emitting it
        would produce a self-transition carrying nothing a consumer can act on, and
        the stream's dedupe key would discard it anyway.

        Recorded rather than dropped: §5 wants every transition visible, and the
        history is where that is satisfied without filling the stream with noise.
        """
        p = provider()
        p.record_failure(reason="upstream 503", at=NOW, circuit_open=True)
        p.record_success(at=NOW + timedelta(seconds=30))
        before = len(p.events())

        # Recovering, then failing again without tripping the breaker. Internally
        # RECOVERING -> DEGRADED; published `degraded` on both sides. This is the
        # flap, and it is the only adjacency where the four-to-three mapping
        # collapses — the others all cross a published boundary.
        p.record_failure(reason="slow again", at=NOW + timedelta(minutes=1))

        collapsed = [
            t
            for t in p.history()
            if t.previous is HealthState.RECOVERING and t.new is HealthState.DEGRADED
        ]
        assert collapsed, "the flap transition happened"
        assert collapsed[0].published is False
        assert len(p.events()) == before, "no event, because nothing a consumer sees changed"

    def test_a_self_transition_event_is_refused_at_the_type(self) -> None:
        with pytest.raises(HealthError, match="carries no"):
            HealthChanged(
                provider_id="otd",
                previous_state=PublishedState.DEGRADED,
                new_state=PublishedState.DEGRADED,
                reason="nothing changed",
                affected_regions=("bern",),
                at=NOW,
            )

    def test_an_event_without_a_reason_is_refused(self) -> None:
        with pytest.raises(HealthError, match="requires a reason"):
            HealthChanged(
                provider_id="otd",
                previous_state=PublishedState.HEALTHY,
                new_state=PublishedState.UNAVAILABLE,
                reason="  ",
                affected_regions=("bern",),
                at=NOW,
            )

    def test_the_dedupe_key_matches_the_contract(self) -> None:
        """`x-journeylab-dedupe-key: provider_id + new_state`."""
        p = provider()
        p.record_failure(reason="down", at=NOW, circuit_open=True)
        assert p.events()[0].dedupe_key == "otd|unavailable"


# --- REQ-TRIP-002 -------------------------------------------------------------------


class TestDegradedRegionsRefuseNewTrips:
    def test_an_unavailable_dependency_refuses_the_trip_with_an_explanation(self) -> None:
        """TST-TRIP-002. Refused, explained, and no partial anything."""
        coverage = model()
        coverage.register(_failed("otd", "bern", circuit_open=True))
        decision = coverage.assess("bern")
        assert isinstance(decision, TripRefused)
        assert "outside current coverage" in decision.reason

    def test_a_degraded_dependency_is_disclosed_rather_than_refused(self) -> None:
        """`REQ-TRIP-002` refuses what is *outside coverage*. Degraded is inside it
        and less certain — and refusing on every degradation would refuse most of the
        time, teaching people the product is broken rather than the data thin."""
        coverage = model()
        coverage.register(_failed("otd", "bern"))
        decision = coverage.assess("bern")
        assert isinstance(decision, TripAccepted)
        assert decision.disclosures, "REQ-EVID-006: degradation is surfaced, not masked"
        assert any("degraded" in d for d in decision.disclosures), (
            "a disclosure that does not say what is wrong discloses nothing"
        )

    def test_a_refusal_without_an_explanation_is_refused_at_the_type(self) -> None:
        """A bare refusal is indistinguishable from a bug, so the traveller retries
        instead of replanning."""
        with pytest.raises(HealthError, match="requires an explanation"):
            TripRefused(region_id="bern", reason="")

    def test_no_type_in_this_module_can_carry_a_partial_itinerary(self) -> None:
        """The structural half of "must not produce a partial simulation".

        A half-planned itinerary is worse than a refusal because it looks like an
        answer. There is no field to put one in.
        """
        import provider_health

        for name in dir(provider_health):
            value = getattr(provider_health, name)
            if not (isinstance(value, type) and hasattr(value, "__dataclass_fields__")):
                continue
            for f in dataclass_fields(value):
                assert not any(
                    token in f.name for token in ("itinerary", "partial", "plan", "scenario")
                ), f"{name}.{f.name}"

    def test_an_undeclared_region_is_refused_rather_than_answered(self) -> None:
        with pytest.raises(HealthError, match="not a declared region"):
            model().assess("zurich")

    def test_a_region_with_no_dependencies_cannot_be_declared(self) -> None:
        """It would report healthy for ever, because nothing can degrade it."""
        with pytest.raises(HealthError, match="no declared dependencies"):
            CoverageModel().declare_region("bern", depends_on=())

    def test_an_untracked_dependency_is_unavailable_rather_than_healthy(self) -> None:
        """ "No news is good news" is how an unmonitored provider stays green through
        an outage."""
        coverage = CoverageModel()
        coverage.declare_region("bern", depends_on=("otd", "never_registered"))
        coverage.register(provider("otd", "bern"))
        assert coverage.region_state("bern") is PublishedState.UNAVAILABLE

    def test_the_worst_dependency_decides_the_region(self) -> None:
        """A region is only as available as its least available input."""
        coverage = model()
        coverage.register(_failed("osm", "bern", circuit_open=True))
        assert coverage.region_state("bern") is PublishedState.UNAVAILABLE


# --- REQ-EVID-006 ---------------------------------------------------------------------


class TestThePublicViewCannotNameAProvider:
    def test_the_public_types_have_nowhere_to_put_a_provider(self) -> None:
        """`Coverage`: "an aggregate. Never a list, never named, never a count — each
        of those leaks the shape of the supply chain."

        Satisfied by the shape of the type rather than by remembering to strip a
        field, which is the same construction as the attribution record in `.06`.
        """
        # `provider_health` is the one permitted use of the word, and it is the
        # contract's own field name for the single aggregate. Everything else that
        # mentions a provider is a leak.
        allowed = {"provider_health"}
        for public_type in (PublicRegion, PublicCoverage):
            names = {f.name for f in dataclass_fields(public_type)} - allowed
            for forbidden in ("provider", "count", "quota", "supplier", "vendor"):
                assert not any(forbidden in n for n in names), f"{public_type.__name__}.{forbidden}"

    def test_a_degraded_provider_is_visible_without_being_named(self) -> None:
        """Both requirements at once: the traveller learns **that** the answer is
        degraded and never **who** degraded it."""
        coverage = model()
        coverage.register(_failed("otd", "bern"))
        view = coverage.public_view()
        assert view.provider_health is PublishedState.DEGRADED
        assert view.regions[0].freshness is RegionFreshness.DEGRADED
        assert "otd" not in repr(view)

    def test_an_unavailable_region_is_marked_not_accepting_trips(self) -> None:
        coverage = model()
        coverage.register(_failed("otd", "bern", circuit_open=True))
        region = coverage.public_view().regions[0]
        assert region.accepting_trips is False
        assert region.freshness is RegionFreshness.STALE
        assert region.limitations, "a refusal must arrive with its explanation"

    def test_the_aggregate_takes_the_worst_region(self) -> None:
        coverage = model()
        coverage.declare_region("geneva", depends_on=("osm",))
        coverage.register(_failed("otd", "bern", circuit_open=True))
        view = coverage.public_view()
        assert view.provider_health is PublishedState.UNAVAILABLE
        assert {r.region_id for r in view.regions} == {"bern", "geneva"}

    def test_the_public_projection_drops_identity_irrecoverably(self) -> None:
        """There is no method that maps a public region back to its providers."""
        assert {n for n in dir(PublicCoverage) if not n.startswith("_")} == {
            "regions",
            "provider_health",
        }
        assert {n for n in dir(PublicRegion) if not n.startswith("_")} == {
            "region_id",
            "freshness",
            "accepting_trips",
            "limitations",
        }
        # And no method anywhere maps a public value back to the providers behind it.
        for name, value in vars(CoverageModel).items():
            if name.startswith("_") or not callable(value):
                continue
            signature = inspect.signature(value)
            assert "PublicRegion" not in str(signature), name


# --- refusals -----------------------------------------------------------------------


class TestConfigurationIsRefusedNotGuessed:
    def test_a_provider_with_no_regions_is_refused(self) -> None:
        """Its degradation could not be attributed to any coverage, so the refusal
        path would silently never fire."""
        with pytest.raises(HealthError, match="no declared regions"):
            ProviderHealth(provider_id="otd", regions=())

    def test_a_provider_without_an_identifier_is_refused(self) -> None:
        with pytest.raises(HealthError, match="needs an identifier"):
            ProviderHealth(provider_id="  ", regions=("bern",))


def _failed(pid: str, region: str, *, circuit_open: bool = False) -> ProviderHealth:
    p = ProviderHealth(provider_id=pid, regions=(region,))
    p.record_failure(reason="upstream failure", at=NOW, circuit_open=circuit_open)
    return p
