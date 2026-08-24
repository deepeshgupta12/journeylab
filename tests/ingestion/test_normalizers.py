"""Provider payload to canonical entity — TST-DATA-007 · STEP-006.05.

WHAT THESE ARE PROTECTING
    Two failures that produce a canonical record no downstream check can question:

      a coerced field  -> provenance says the provider told us, and it did not
      observed_at from
      the clock        -> a replay stamps every historical fact with today, and the
                          entire backfill reports as fresh
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from normalizers import (
    FACT_SCHEMA_VERSION,
    CanonicalFact,
    NormalizationError,
    normalize_fact,
    normalize_place,
    normalize_places,
)
from places.licence import OPENSTREETMAP

OBSERVED = datetime(2026, 8, 21, 9, 0, tzinfo=UTC)
EFFECTIVE = datetime(2026, 6, 1, tzinfo=UTC)


def payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "place_id": "way/12345",
        "name": "Kunstmuseum Bern",
        "category": "museum",
        "coordinate": {"latitude": 46.9500, "longitude": 7.4400},
        "time_zone": "Europe/Zurich",
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


# --- purity ------------------------------------------------------------------------


class TestNormalizersArePure:
    def test_observed_at_is_an_argument_and_not_a_clock(self) -> None:
        """A replay that stamps historical facts with today's date makes the whole
        backfill look current, and the freshness policy has no way to know."""
        signature = inspect.signature(normalize_place)
        assert signature.parameters["observed_at"].default is inspect.Parameter.empty
        source = inspect.getsource(normalize_place)
        assert "now()" not in source and "utcnow" not in source

    def test_the_module_reads_no_clock_at_all(self) -> None:
        """The structural half of "pure": one `datetime.now()` anywhere makes every
        record it touches unreproducible, and nothing downstream can tell.

        Walked as an AST rather than scanned as text. The first version was a
        substring search and it failed against the module's own docstring, which
        explains why `datetime.now()` is forbidden — a text scan cannot tell code
        from prose about code, so it either misses the real call or trips on the
        explanation of it.
        """
        import ast

        import normalizers

        tree = ast.parse(inspect.getsource(normalizers))
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert called.isdisjoint({"now", "utcnow", "today", "time", "getenv"}), called

    def test_the_same_payload_normalizes_identically_twice(self) -> None:
        first = normalize_place(payload(), licence=OPENSTREETMAP, observed_at=OBSERVED)
        second = normalize_place(payload(), licence=OPENSTREETMAP, observed_at=OBSERVED)
        assert first == second

    def test_a_naive_observed_at_is_refused(self) -> None:
        with pytest.raises(NormalizationError, match="timezone-aware"):
            normalize_place(
                payload(),
                licence=OPENSTREETMAP,
                observed_at=datetime(2026, 8, 21, 9, 0),  # noqa: DTZ001
            )


# --- rejection is the feature ----------------------------------------------------------


class TestUnmappableInputIsRejectedNotDefaulted:
    @pytest.mark.parametrize("missing", ["place_id", "category", "coordinate", "time_zone", "name"])
    def test_a_missing_required_field_rejects_the_record(self, missing: str) -> None:
        """`DC-EXT-001`: reject and alert, never coerce. A guessed value produces a
        canonical record that is wrong in a way nothing downstream can detect,
        because provenance says the provider supplied it."""
        with pytest.raises(NormalizationError):
            normalize_place(payload(**{missing: None}), licence=OPENSTREETMAP, observed_at=OBSERVED)

    def test_the_rejection_names_the_record_and_the_reason(self) -> None:
        with pytest.raises(NormalizationError, match="way/12345") as caught:
            normalize_place(payload(category=None), licence=OPENSTREETMAP, observed_at=OBSERVED)
        assert "category" in str(caught.value)

    def test_a_batch_keeps_its_rejections_as_data(self) -> None:
        """A rejection nobody counts is silent data loss: the batch reports a
        smaller number and nothing says why."""
        batch = normalize_places(
            [payload(), payload(place_id="way/2", category=None), payload(place_id="way/3")],
            licence=OPENSTREETMAP,
            observed_at=OBSERVED,
        )
        assert len(batch.places) == 2
        assert len(batch.rejections) == 1
        assert batch.rejections[0].payload_key == "way/2"
        assert round(batch.rejection_rate, 3) == round(1 / 3, 3)

    def test_one_bad_payload_does_not_fail_the_batch(self) -> None:
        """A single provider typo blocking an entire ingestion is its own outage."""
        batch = normalize_places(
            [payload(name=None), payload(place_id="way/9")],
            licence=OPENSTREETMAP,
            observed_at=OBSERVED,
        )
        assert len(batch.places) == 1

    def test_an_empty_batch_has_no_rejection_rate_to_divide_by(self) -> None:
        """Zero over zero. The kind of thing that only fails on the quiet day."""
        assert (
            normalize_places([], licence=OPENSTREETMAP, observed_at=OBSERVED).rejection_rate == 0.0
        )


# --- provenance ------------------------------------------------------------------------


class TestEveryRecordCarriesFullProvenance:
    def test_a_normalized_place_names_its_licence_and_observation_time(self) -> None:
        place = normalize_place(payload(), licence=OPENSTREETMAP, observed_at=OBSERVED)
        assert place.provenance.licence_id == "ODbL-1.0"
        assert place.provenance.observed_at == OBSERVED
        assert place.provenance.access_label == "public"

    def test_a_fact_carries_all_three_time_axes(self) -> None:
        fact = normalize_fact(
            {"field_class": "hours", "value": {"open": "09:00"}},
            licence=OPENSTREETMAP,
            observed_at=OBSERVED,
            effective_from=EFFECTIVE,
            effective_to=EFFECTIVE + timedelta(days=90),
        )
        assert (fact.observed_at, fact.effective_from) == (OBSERVED, EFFECTIVE)
        assert fact.schema_version == FACT_SCHEMA_VERSION

    def test_a_fact_without_a_field_class_is_refused(self) -> None:
        """Without it the fact has no freshness policy, and `STEP-005.08`
        deliberately has no default to fall back on."""
        with pytest.raises(NormalizationError, match="field_class is required"):
            normalize_fact(
                {"value": 1}, licence=OPENSTREETMAP, observed_at=OBSERVED, effective_from=EFFECTIVE
            )

    def test_a_fact_without_a_value_is_not_a_fact(self) -> None:
        with pytest.raises(NormalizationError, match="not a fact"):
            normalize_fact(
                {"field_class": "hours"},
                licence=OPENSTREETMAP,
                observed_at=OBSERVED,
                effective_from=EFFECTIVE,
            )

    def test_a_falsy_value_is_still_a_value(self) -> None:
        """`0`, `False` and `""` are answers. Testing presence with truthiness would
        reject a price of zero and a "closed" flag."""
        for value in (0, False, "", cast("list[object]", [])):
            fact = normalize_fact(
                {"field_class": "price", "value": value},
                licence=OPENSTREETMAP,
                observed_at=OBSERVED,
                effective_from=EFFECTIVE,
            )
            assert fact.value == value

    def test_a_naive_fact_timestamp_is_refused(self) -> None:
        """`CanonicalFact` keeps its own check because **nothing sits behind this
        path** — unlike `normalize_place`, which delegates to an adapter that
        already refuses naive input."""
        with pytest.raises(NormalizationError, match="timezone-aware"):
            normalize_fact(
                {"field_class": "hours", "value": 1},
                licence=OPENSTREETMAP,
                observed_at=datetime(2026, 8, 21, 9, 0),  # noqa: DTZ001
                effective_from=EFFECTIVE,
            )

    def test_a_backwards_effective_window_is_refused(self) -> None:
        with pytest.raises(NormalizationError, match="precedes"):
            CanonicalFact(
                field_class="hours",
                value=1,
                source_id="osm",
                licence_id="ODbL-1.0",
                confidence=0.9,
                access_label="public",
                observed_at=OBSERVED,
                effective_from=EFFECTIVE,
                effective_to=EFFECTIVE - timedelta(days=1),
            )

    def test_confidence_outside_zero_to_one_is_refused(self) -> None:
        with pytest.raises(NormalizationError, match=r"confidence must be 0\.\.1"):
            normalize_fact(
                {"field_class": "hours", "value": 1},
                licence=OPENSTREETMAP,
                observed_at=OBSERVED,
                effective_from=EFFECTIVE,
                confidence=1.5,
            )


def test_the_mapping_is_not_duplicated_from_the_adapter() -> None:
    """Two mappings for one payload shape drift, and the one that drifts is the one
    with fewer tests. The normalizer delegates rather than re-implementing."""
    from normalizers import adapt_with_provenance

    assert "adapt_with_provenance" in inspect.getsource(normalize_place)
    # Both hops, because a mutant that re-implements the mapping one function deeper
    # slipped past the first version of this test.
    for function in (normalize_place, adapt_with_provenance):
        source = inspect.getsource(function)
        for field_name in ("opening_hours", "accessibility", "latitude"):
            assert field_name not in source, f"{function.__name__}: {field_name}"
