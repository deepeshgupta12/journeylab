"""Canonical place entity resolution — TST-DATA-004 · STEP-005.07.

WHAT THESE ARE PROTECTING
    One outcome, above all others: **two different venues must never become one
    place without a human saying so.** A false merge produces an itinerary that is
    internally consistent, has plausible travel times, and sends the traveller to
    the wrong building. Nothing downstream can detect it.

    The opposite error — a duplicate left in a list — is visible, annoying and
    harmless. So the tests are not symmetric, and neither is the matcher.
"""

from __future__ import annotations

import difflib
import json
import pathlib
from datetime import UTC, datetime

import pytest
from entity_resolution import (
    AUTO_MERGE_METRES,
    AUTO_MERGE_SIMILARITY,
    COARSER_THAN_A_VENUE,
    IDENTITY_NAMESPACES,
    REVIEW_METRES,
    CanonicalEntity,
    Coordinate,
    EntityGraph,
    Evaluation,
    LabelledPair,
    Outcome,
    ProviderRecord,
    ResolutionDecision,
    ResolutionError,
    ReviewQueue,
    compare,
    evaluate,
    metres_between,
    name_similarity,
    name_variants,
)
from places.adapter import AdapterError, adapt
from places.licence import OPENSTREETMAP

NOW = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
SAMPLE = pathlib.Path(__file__).parent / "labelled_pairs.json"


def record(
    key: str,
    name: str,
    lat: float,
    lon: float,
    *,
    category: str = "museum",
    provider: str = "osm",
    external_ids: dict[str, str] | None = None,
) -> ProviderRecord:
    return ProviderRecord(
        provider_id=provider,
        provider_place_id=key,
        name=name,
        category=category,
        coordinate=Coordinate(latitude=lat, longitude=lon),
        licence_id="ODbL-1.0",
        observed_at=NOW,
        external_ids=external_ids or {},
    )


def load_sample() -> list[LabelledPair]:
    raw = json.loads(SAMPLE.read_text())
    pairs: list[LabelledPair] = []
    for entry in raw["pairs"]:
        sides = []
        for side in (entry["left"], entry["right"]):
            sides.append(
                ProviderRecord(
                    provider_id=side["provider_id"],
                    provider_place_id=side["provider_place_id"],
                    name=side["name"],
                    category=side["category"],
                    coordinate=Coordinate(latitude=side["latitude"], longitude=side["longitude"]),
                    licence_id="ODbL-1.0",
                    observed_at=NOW,
                    external_ids=side["external_ids"],
                )
            )
        pairs.append(
            LabelledPair(label=entry["label"], left=sides[0], right=sides[1], note=entry["note"])
        )
    return pairs


# --- the measurement, which is the acceptance criterion -------------------------


class TestMeasuredOnALabelledSample:
    """§12: "Precision measured on a labelled sample". Measured, and asserted."""

    def test_no_pair_of_different_venues_is_ever_merged_automatically(self) -> None:
        """Precision 1.0. The only number here that is not negotiable.

        A false merge is the failure this whole sub-step exists to prevent, so the
        assertion is on zero occurrences rather than on a rate.
        """
        result = evaluate(load_sample())
        assert result.false_merges == 0, "a false merge sends a traveller to the wrong building"
        assert result.precision == 1.0

    def test_no_true_duplicate_is_silently_discarded(self) -> None:
        """The test that stops precision being satisfied by merging nothing.

        A matcher that answers DISTINCT to everything scores perfect precision. What
        it loses is the duplicates it will never be asked about again — so those are
        counted separately and must be zero. Anything it cannot decide belongs in
        the queue, where a human still sees it.
        """
        result = evaluate(load_sample())
        assert result.lost == 0, (
            "a true duplicate marked DISTINCT is never reviewed by anyone; "
            "uncertainty belongs in the queue, not in a verdict"
        )

    def test_the_matcher_still_decides_something_on_its_own(self) -> None:
        """Guards the other degenerate answer: queueing everything.

        A matcher that sends every pair to review is safe and useless. This pins the
        measured automatic-decision rate so a change that quietly stops deciding
        fails here rather than showing up as an unmanageable backlog months later.
        """
        result = evaluate(load_sample())
        assert result.auto_merges >= 1
        assert result.distinct >= 3
        assert result.review_rate <= 0.75

    def test_the_recorded_numbers_are_what_the_matcher_actually_produces(self) -> None:
        """The measurement recorded in the sub-step record, pinned.

        Recorded so that the figures in `BR-046` §8 and the completion record cannot
        drift away from the code without the suite failing. These are measurements
        of an adversarial hand-built sample, NOT an estimate of production load —
        see `labelled_pairs.json`.
        """
        result = evaluate(load_sample())
        assert (result.pairs, result.auto_merges, result.reviews, result.distinct) == (
            13,
            3,
            7,
            3,
        )
        assert result.same_in_review == 3
        assert (result.precision, result.recall) == (1.0, 0.5)
        assert round(result.review_rate, 3) == round(7 / 13, 3)


# --- identity: what an identifier is allowed to mean ----------------------------


class TestIdentifiersThatAreNotIdentity:
    def test_a_shared_website_does_not_merge_two_branches_of_a_chain(self) -> None:
        """A website denotes a chain. Matching on it merges every branch in the
        country into one place, with the confidence of an exact match."""
        left = record(
            "20",
            "Migros Aarbergergasse",
            46.9490,
            7.4395,
            category="supermarket",
            external_ids={"website": "https://www.migros.ch"},
        )
        right = record(
            "21",
            "Migros Marktgasse",
            46.9481,
            7.4413,
            category="supermarket",
            external_ids={"website": "https://www.migros.ch"},
        )
        assert compare(left, right).outcome is Outcome.DISTINCT

    def test_a_shared_address_does_not_merge_two_venues_in_one_building(self) -> None:
        left = record(
            "o1",
            "Tourist Information",
            46.9490,
            7.4398,
            category="information",
            external_ids={"address": "Bahnhofplatz 10a"},
        )
        right = record(
            "o2",
            "Ticketshop",
            46.94901,
            7.43981,
            category="shop",
            external_ids={"address": "Bahnhofplatz 10a"},
        )
        assert compare(left, right).outcome is not Outcome.AUTO_MERGE

    def test_the_ignored_namespace_is_named_in_the_decision(self) -> None:
        """Silently ignoring evidence and having no evidence look identical to a
        reviewer. The decision says which namespaces it declined to trust."""
        left = record(
            "20",
            "Migros A",
            46.9490,
            7.4395,
            category="supermarket",
            external_ids={"website": "https://www.migros.ch"},
        )
        right = record(
            "21",
            "Migros B",
            46.9481,
            7.4413,
            category="supermarket",
            external_ids={"website": "https://www.migros.ch"},
        )
        assert any("website" in r for r in compare(left, right).reasons)

    def test_gtfs_stop_ids_are_not_identity_and_the_reason_is_recorded(self) -> None:
        """STEP-005.04 established that GTFS stop identifiers are scoped to a feed
        publication and are not stable across them. The same string can denote a
        different platform after a republication, so it cannot carry identity."""
        assert "gtfs_stop" in COARSER_THAN_A_VENUE
        assert "gtfs_stop" not in IDENTITY_NAMESPACES

    def test_a_providers_own_key_is_never_cross_provider_identity(self) -> None:
        """Two providers both using the key `12345` are not describing one venue."""
        left = record("12345", "Kunsthaus", 47.3701, 8.5484, provider="alpha")
        right = record(
            "12345", "Bahnhof Thun", 46.7550, 7.6290, category="station", provider="beta"
        )
        assert compare(left, right).outcome is Outcome.DISTINCT


class TestIdentifierEvidence:
    def test_agreement_on_wikidata_merges(self) -> None:
        left = record(
            "a", "Kunstmuseum Bern", 46.9500, 7.4400, external_ids={"wikidata": "Q194266"}
        )
        right = record(
            "b",
            "Musee des Beaux-Arts de Berne",
            46.95002,
            7.44003,
            provider="partner",
            external_ids={"wikidata": "Q194266"},
        )
        decision = compare(left, right)
        assert decision.outcome is Outcome.AUTO_MERGE
        assert decision.identifier_agreements == ("wikidata:Q194266",)

    def test_conflicting_identifiers_are_not_settled_by_being_close(self) -> None:
        """REQ-EVID-002. Two sources asserting different identities is a conflict to
        surface, not a strong match with a small problem — and five metres of
        proximity is not an argument about which one is wrong."""
        left = record("a", "Zytglogge", 46.9479, 7.4474, external_ids={"wikidata": "Q683385"})
        right = record(
            "b",
            "Zytglogge Bern",
            46.94793,
            7.44744,
            provider="partner",
            external_ids={"wikidata": "Q9999999"},
        )
        decision = compare(left, right)
        assert decision.outcome is Outcome.REVIEW
        assert decision.identifier_conflicts
        assert decision.distance_metres < 10

    def test_a_conflict_blocks_a_merge_that_every_other_signal_demands(self) -> None:
        """The conflict rule in isolation.

        Identical names, identical categories, four metres apart: distance, name and
        category all say merge, and the disagreeing identifiers are the only thing
        that stops it. Without this pair the rule is untested, because the
        same-doorstep rule happens to catch the looser cases anyway.
        """
        left = record(
            "a",
            "Zytglogge",
            46.9479,
            7.4474,
            category="landmark",
            external_ids={"wikidata": "Q683385"},
        )
        right = record(
            "b",
            "Zytglogge",
            46.94793,
            7.44744,
            category="landmark",
            provider="partner",
            external_ids={"wikidata": "Q9999999"},
        )
        decision = compare(left, right)
        assert decision.similarity == 1.0
        assert decision.distance_metres < 5
        assert decision.outcome is Outcome.REVIEW

    def test_agreement_with_distant_coordinates_is_reviewed_not_merged(self) -> None:
        """The identifier says one venue and the coordinates say two places. Both
        facts are kept; a merge that ignored the second would hide a source that is
        wrong about where something is."""
        left = record("a", "Kunsthaus", 47.3701, 8.5484, external_ids={"wikidata": "Q194266"})
        right = record(
            "b",
            "Kunsthaus",
            46.9500,
            7.4400,
            provider="partner",
            external_ids={"wikidata": "Q194266"},
        )
        decision = compare(left, right)
        assert decision.outcome is Outcome.REVIEW
        assert any("disagree" in r for r in decision.reasons)


# --- the gating rule ------------------------------------------------------------


class TestSignalsAreGatedNotSummed:
    def test_a_perfect_name_cannot_pay_for_distance(self) -> None:
        """The false-merge mechanism this design exists to exclude: a weighted score
        lets an identical name buy enough confidence to cover a failing distance."""
        left = record("1", "Coop Bahnhofstrasse", 47.3730, 8.5390, category="supermarket")
        right = record("2", "Coop Bahnhofstrasse", 46.9480, 7.4400, category="supermarket")
        decision = compare(left, right)
        assert decision.similarity == 1.0
        assert decision.outcome is Outcome.DISTINCT

    def test_proximity_alone_does_not_merge(self) -> None:
        left = record("1", "Kunsthaus", 47.3701, 8.5484)
        right = record("2", "Sprüngli", 47.37012, 8.54842, category="cafe")
        assert compare(left, right).outcome is not Outcome.AUTO_MERGE

    @pytest.mark.parametrize("metres", [AUTO_MERGE_METRES + 5, REVIEW_METRES + 5])
    def test_each_gate_holds_at_its_own_boundary(self, metres: float) -> None:
        """Degrees of latitude are about 111 320 m; the offsets below are derived
        rather than eyeballed so the boundary is actually the boundary."""
        left = record("1", "Kunsthaus Zürich", 47.3701, 8.5484)
        right = record(
            "2", "Kunsthaus Zürich", 47.3701 + metres / 111_320.0, 8.5484, provider="partner"
        )
        assert compare(left, right).outcome is not Outcome.AUTO_MERGE


class TestCategoryOnlyDemotes:
    def test_a_shared_category_at_one_point_does_not_merge_two_venues(self) -> None:
        """A station concourse holds a dozen venues that all declare `restaurant`.
        "Same point and same category, therefore the same place" is the obvious
        optimisation and it merges every one of them."""
        left = record("60", "Restaurant Bahnhofbuffet", 47.3779, 8.5403, category="restaurant")
        right = record("61", "Trattoria Da Vinci", 47.3779, 8.54031, category="restaurant")
        assert compare(left, right).outcome is Outcome.REVIEW

    def test_a_cafe_inside_a_museum_is_not_merged_into_the_museum(self) -> None:
        """Same coordinate to the metre, name derived from the museum's. The
        category is the only field that knows these are two places, and merging them
        gives the traveller the museum's opening hours for the cafe."""
        museum = record("500", "Kunsthaus Zürich", 47.3701, 8.5484, category="museum")
        cafe = record("501", "Kunsthaus Zürich", 47.3701, 8.5484, category="cafe")
        decision = compare(museum, cafe)
        assert decision.similarity == 1.0, "every other signal says merge"
        assert decision.distance_metres < 1.0
        assert decision.outcome is Outcome.REVIEW
        assert any("categories disagree" in r for r in decision.reasons)

    def test_a_matching_category_never_creates_a_merge_on_its_own(self) -> None:
        """Demotion only. Provider taxonomies agree far too easily for a category
        match to be evidence of identity — every restaurant in Bern matches."""
        left = record("1", "Restaurant Bahnhof", 46.7550, 7.6290, category="restaurant")
        right = record("2", "Restaurant Bahnhof", 46.6860, 7.6800, category="restaurant")
        assert compare(left, right).outcome is Outcome.DISTINCT


# --- Switzerland ----------------------------------------------------------------


class TestMultilingualAndSwissSpelling:
    @pytest.mark.parametrize(
        ("left", "right"),
        [
            ("Zürich Hauptbahnhof", "Zuerich Hauptbahnhof"),
            ("Zürich Hauptbahnhof", "Zurich Hauptbahnhof"),
            ("Genève Cornavin", "Geneve Cornavin"),
            ("Grossmünster", "Grossmuenster"),
        ],
    )
    def test_swiss_spelling_variants_are_the_same_name(self, left: str, right: str) -> None:
        """No single normalisation handles all of these: stripping diacritics maps
        `Zürich` to `zurich`, expanding umlauts maps it to `zuerich`, and both
        spellings are in everyday use. Both variants are produced and the best
        pairing wins."""
        assert name_similarity(left, right) >= 0.9

    def test_the_umlaut_expansion_is_what_carries_a_short_name_across_the_gate(
        self,
    ) -> None:
        """Where the second normalisation actually changes the answer, measured.

        For most names it does not: `Zuerich Hauptbahnhof` against
        `Zürich Hauptbahnhof` scores 0.97 on diacritic-stripping alone, comfortably
        over the 0.90 merge gate. The divergence bites on **short** names, where one
        added character is a large fraction of the string — and Swiss inns are
        called `Bär`, `Rössli`, `Löwen`. `Bär` against `Baer` scores 0.857 stripped,
        which fails the gate, and 1.0 with the expansion.

        Recorded with the number because "it helps with umlauts" is not a claim
        anything can check.
        """
        stripped_only = difflib.SequenceMatcher(
            None, name_variants("Bär")[0], name_variants("Baer")[0]
        ).ratio()
        assert stripped_only < AUTO_MERGE_SIMILARITY
        assert name_similarity("Bär", "Baer") == 1.0

    def test_both_normalisations_are_produced(self) -> None:
        stripped, expanded = name_variants("Zürich")
        assert stripped == "zurich"
        assert expanded == "zuerich"

    def test_a_cross_language_duplicate_reaches_a_human(self) -> None:
        """`Kunstmuseum Bern` and `Musee des Beaux-Arts de Berne` share almost no
        characters and are the same building. No string comparison finds this, so
        the same-doorstep rule carries it to review rather than losing it."""
        left = record("a", "Kunstmuseum Bern", 46.9500, 7.4400)
        right = record("b", "Musee des Beaux-Arts de Berne", 46.95001, 7.44001, provider="partner")
        decision = compare(left, right)
        assert decision.similarity < 0.6
        assert decision.outcome is Outcome.REVIEW


# --- geometry -------------------------------------------------------------------


class TestDistance:
    def test_a_known_distance_is_computed_correctly(self) -> None:
        """Bern to Zurich, about 95 km. A distance function nothing checks against a
        known value is a distance function that can be wrong by a factor."""
        bern = Coordinate(latitude=46.9480, longitude=7.4474)
        zurich = Coordinate(latitude=47.3769, longitude=8.5417)
        assert 93_000 < metres_between(bern, zurich) < 97_000

    def test_null_island_is_refused_at_the_type(self) -> None:
        """`0.0, 0.0` is what providers emit for "unknown", and it is a collision
        point: every unlocated place lands there, zero metres apart, and proximity
        merges the lot."""
        with pytest.raises(AdapterError, match="Null Island"):
            Coordinate(latitude=0.0, longitude=0.0)

    @pytest.mark.parametrize(("lat", "lon"), [(91.0, 0.0), (-91.0, 0.0), (0.0, 181.0)])
    def test_out_of_range_coordinates_are_refused(self, lat: float, lon: float) -> None:
        with pytest.raises(AdapterError, match="out of range"):
            Coordinate(latitude=lat, longitude=lon)


# --- merge, split, undo ---------------------------------------------------------


class TestMergeIsReversible:
    def test_members_are_kept_separately_rather_than_flattened(self) -> None:
        """ "Canonical" means one identity, not one set of values. Flattening makes
        the merge irreversible the moment a field disagrees, and resolves conflicting
        evidence by picking a winner (REQ-EVID-002)."""
        graph = EntityGraph()
        a = record("a", "Kunstmuseum Bern", 46.9500, 7.4400)
        b = record("b", "Musee des Beaux-Arts de Berne", 46.95001, 7.44001, provider="partner")
        merged = graph.merge(
            graph.add(a), graph.add(b), actor="curator", reason="reviewed rev-0001", at=NOW
        )
        entity = graph._entities[merged]
        assert entity.member_keys == ("osm:a", "partner:b")
        assert {m.name for m in entity.members} == {
            "Kunstmuseum Bern",
            "Musee des Beaux-Arts de Berne",
        }

    def test_undo_restores_the_exact_prior_grouping(self) -> None:
        graph = EntityGraph()
        a, b, c = (
            record("a", "Kunsthaus", 47.3701, 8.5484),
            record("b", "Kunsthaus", 47.37011, 8.54841, provider="p2"),
            record("c", "Kunsthaus", 47.37012, 8.54842, provider="p3"),
        )
        first = graph.merge(graph.add(a), graph.add(b), actor="c", reason="same", at=NOW)
        second = graph.merge(first, graph.add(c), actor="c", reason="same again", at=NOW)
        assert graph.entity_for("p3:c").member_keys == ("osm:a", "p2:b", "p3:c")

        graph.undo(graph.history()[-1].operation_id, actor="c", at=NOW)
        assert graph.entity_for("osm:a").member_keys == ("osm:a", "p2:b")
        assert graph.entity_for("p3:c").member_keys == ("p3:c",)
        assert second not in {e.entity_id for e in graph.entities()}

    def test_undoing_out_of_order_is_refused_rather_than_guessed(self) -> None:
        """A reversal that silently discards the decisions made since is not a
        reversal — it is a second, unrecorded decision."""
        graph = EntityGraph()
        a, b, c = (
            record("a", "K", 47.3701, 8.5484),
            record("b", "K", 47.37011, 8.54841, provider="p2"),
            record("c", "K", 47.37012, 8.54842, provider="p3"),
        )
        first = graph.merge(graph.add(a), graph.add(b), actor="c", reason="same", at=NOW)
        graph.merge(first, graph.add(c), actor="c", reason="same again", at=NOW)
        oldest = graph.history()[0].operation_id
        with pytest.raises(ResolutionError, match="touched the same"):
            graph.undo(oldest, actor="c", at=NOW)

    def test_a_split_must_be_an_exact_partition(self) -> None:
        """Dropping a member loses a provider's record and duplicating one
        double-counts it, and neither is visible after the fact."""
        graph = EntityGraph()
        a = record("a", "K", 47.3701, 8.5484)
        b = record("b", "K", 47.37011, 8.54841, provider="p2")
        c = record("c", "K", 47.37012, 8.54842, provider="p3")
        first = graph.merge(graph.add(a), graph.add(b), actor="c", reason="same", at=NOW)
        merged = graph.merge(first, graph.add(c), actor="c", reason="same", at=NOW)

        with pytest.raises(ResolutionError, match="exact partition"):
            graph.split(merged, [["osm:a"], ["p2:b"]], actor="c", reason="drops c", at=NOW)
        with pytest.raises(ResolutionError, match="exact partition"):
            graph.split(
                merged,
                [["osm:a"], ["p2:b", "p2:b", "p3:c"]],
                actor="c",
                reason="duplicates b",
                at=NOW,
            )
        with pytest.raises(ResolutionError, match="at least two"):
            graph.split(merged, [["osm:a", "p2:b", "p3:c"]], actor="c", reason="no-op", at=NOW)

    def test_split_separates_a_wrongly_merged_pair(self) -> None:
        graph = EntityGraph()
        a = record("a", "K", 47.3701, 8.5484)
        b = record("b", "K", 47.37011, 8.54841, provider="p2")
        merged = graph.merge(graph.add(a), graph.add(b), actor="c", reason="same", at=NOW)
        left, right = graph.split(
            merged, [["osm:a"], ["p2:b"]], actor="c", reason="different buildings", at=NOW
        )
        assert graph.entity_for("osm:a").entity_id == left
        assert graph.entity_for("p2:b").entity_id == right


class TestEveryOperationIsAudited:
    def test_an_operation_without_a_reason_is_refused(self) -> None:
        graph = EntityGraph()
        a = record("a", "K", 47.3701, 8.5484)
        b = record("b", "K", 47.37011, 8.54841, provider="p2")
        with pytest.raises(ResolutionError, match="records why"):
            graph.merge(graph.add(a), graph.add(b), actor="c", reason="  ", at=NOW)

    def test_an_operation_without_an_actor_is_refused(self) -> None:
        graph = EntityGraph()
        a = record("a", "K", 47.3701, 8.5484)
        b = record("b", "K", 47.37011, 8.54841, provider="p2")
        with pytest.raises(ResolutionError, match="who performed it"):
            graph.merge(graph.add(a), graph.add(b), actor="", reason="same", at=NOW)

    def test_the_history_records_the_state_the_operation_replaced(self) -> None:
        graph = EntityGraph()
        a = record("a", "K", 47.3701, 8.5484)
        b = record("b", "K", 47.37011, 8.54841, provider="p2")
        graph.merge(graph.add(a), graph.add(b), actor="curator", reason="rev-0001", at=NOW)
        operation = graph.history()[0]
        assert operation.kind == "merge"
        assert operation.actor == "curator"
        assert dict(operation.before) == {"ent-0001": ("osm:a",), "ent-0002": ("p2:b",)}

    def test_entity_ids_are_deterministic_rather_than_random(self) -> None:
        """REQ-CONS-006: a scenario is reproducible from its inputs. A random
        identifier makes the same corpus produce a different graph every run."""
        ids = []
        for _ in range(2):
            graph = EntityGraph()
            graph.add(record("a", "K", 47.3701, 8.5484))
            graph.add(record("b", "K", 46.9500, 7.4400, provider="p2"))
            ids.append([e.entity_id for e in graph.entities()])
        assert ids[0] == ids[1] == ["ent-0001", "ent-0002"]


# --- the review queue -----------------------------------------------------------


class TestReviewQueue:
    def test_only_a_review_decision_can_be_queued(self) -> None:
        """Queueing an automatic answer hides a decision the matcher already made
        behind a human it did not need."""
        queue = ReviewQueue()
        decided = compare(
            record("1", "Coop Bahnhofstrasse", 47.3730, 8.5390, category="supermarket"),
            record("2", "Coop Bahnhofstrasse", 46.9480, 7.4400, category="supermarket"),
        )
        with pytest.raises(ResolutionError, match="only a REVIEW decision"):
            queue.enqueue(decided, at=NOW)

    def test_a_resolution_names_the_reviewer_and_what_they_saw(self) -> None:
        queue = ReviewQueue()
        item = queue.enqueue(
            compare(
                record("500", "Kunsthaus Zürich", 47.3701, 8.5484),
                record("501", "Kunsthaus Zürich Cafe", 47.3701, 8.5484, category="cafe"),
            ),
            at=NOW,
        )
        with pytest.raises(ResolutionError, match="named"):
            queue.resolve(item, merged=False, actor="", note="separate venues", at=NOW)
        with pytest.raises(ResolutionError, match="what the reviewer saw"):
            queue.resolve(item, merged=False, actor="curator", note="", at=NOW)

    def test_pending_order_is_deterministic(self) -> None:
        queue = ReviewQueue()
        far = compare(
            record("a", "Kunsthaus Zürich", 47.3701, 8.5484),
            record("b", "Kunsthaus Zurich", 47.37090, 8.54855, provider="p2"),
        )
        near = compare(
            record("c", "Kunsthaus Zürich", 47.3701, 8.5484),
            record("d", "Kunsthaus Zürich Cafe", 47.3701, 8.5484, category="cafe"),
        )
        queue.enqueue(far, at=NOW)
        queue.enqueue(near, at=NOW)
        distances = [i.decision.distance_metres for i in queue.pending()]
        assert distances == sorted(distances)

    def test_the_queue_offers_no_way_to_approve_without_a_human(self) -> None:
        """The structural half of "never auto-merged".

        A queue with an expiry, a default or a bulk-approve is a slower version of
        merging without review: the backlog decides instead of the matcher. There is
        no such method to reach for.
        """
        surface = {n for n in dir(ReviewQueue) if not n.startswith("_")}
        assert surface == {"enqueue", "pending", "resolve", "resolutions"}
        for forbidden in ("expire", "auto", "default", "approve_all", "sweep", "timeout"):
            assert not any(forbidden in n for n in surface), forbidden


# --- refusals -------------------------------------------------------------------


class TestInputsAreRefusedNotRepaired:
    def test_a_decision_must_state_a_reason(self) -> None:
        with pytest.raises(ResolutionError, match="without a reason"):
            ResolutionDecision(
                left_key="a",
                right_key="b",
                outcome=Outcome.DISTINCT,
                reasons=(),
                distance_metres=10.0,
                similarity=0.5,
            )

    def test_a_naive_observation_time_is_refused(self) -> None:
        with pytest.raises(ResolutionError, match="timezone-aware"):
            ProviderRecord(
                provider_id="osm",
                provider_place_id="a",
                name="K",
                category="museum",
                coordinate=Coordinate(latitude=47.3701, longitude=8.5484),
                licence_id="ODbL-1.0",
                observed_at=datetime(2026, 8, 18, 9, 0),  # noqa: DTZ001
            )

    def test_an_entity_with_no_members_is_refused(self) -> None:
        with pytest.raises(ResolutionError, match="not an entity"):
            CanonicalEntity(entity_id="ent-0001", members=())

    def test_comparing_a_record_with_itself_is_refused(self) -> None:
        a = record("a", "K", 47.3701, 8.5484)
        with pytest.raises(ResolutionError, match="itself"):
            compare(a, a)


# --- the pipeline joins up ------------------------------------------------------


class TestAdapterOutputFeedsResolution:
    def test_an_adapted_place_becomes_a_provider_record(self) -> None:
        """BUG-027 was blocking exactly this: before the adapter carried a
        coordinate and a category, the conversion could not be written."""
        place = adapt(
            {
                "place_id": "way/12345",
                "name": "Kunstmuseum Bern",
                "category": "museum",
                "coordinate": {"latitude": 46.9500, "longitude": 7.4400},
                "time_zone": "Europe/Zurich",
            },
            licence=OPENSTREETMAP,
        )
        provider_record = ProviderRecord.from_place(
            place, provider_id="osm", external_ids={"wikidata": "Q194266"}
        )
        assert provider_record.key == "osm:way/12345"
        assert provider_record.licence_id == "ODbL-1.0"
        assert provider_record.coordinate.latitude == 46.9500

    def test_two_providers_of_one_venue_resolve_to_one_entity(self) -> None:
        """TST-DATA-004, the headline acceptance criterion."""
        graph = EntityGraph()
        left = record(
            "way/12345", "Kunstmuseum Bern", 46.9500, 7.4400, external_ids={"wikidata": "Q194266"}
        )
        right = record(
            "be-kmb",
            "Kunstmuseum Bern",
            46.95002,
            7.44003,
            provider="opendata_swiss",
            external_ids={"wikidata": "Q194266"},
        )
        decision = compare(left, right)
        assert decision.outcome is Outcome.AUTO_MERGE
        merged = graph.merge(
            graph.add(left),
            graph.add(right),
            actor="matcher",
            reason=decision.reasons[0],
            at=NOW,
        )
        entity = graph.entity_for(left.key)
        assert entity.entity_id == merged
        assert entity.providers() == ("opendata_swiss", "osm")

    def test_distinct_nearby_venues_are_not_merged(self) -> None:
        """The other half of TST-DATA-004, and the one that matters more."""
        graph = EntityGraph()
        museum = record("500", "Kunsthaus Zürich", 47.3701, 8.5484, category="museum")
        cafe = record("501", "Kunsthaus Zürich Cafe", 47.3701, 8.5484, category="cafe")
        graph.add(museum)
        graph.add(cafe)
        assert compare(museum, cafe).outcome is not Outcome.AUTO_MERGE
        assert len(graph.entities()) == 2


class TestEvaluationCannotBeGamed:
    def test_precision_is_one_when_nothing_is_merged_and_that_is_why_lost_exists(
        self,
    ) -> None:
        """States the degenerate case in code so the reason for the second metric is
        not lost the next time someone tunes a threshold."""
        empty = Evaluation(pairs=10, auto_merges=0, reviews=0, distinct=10, false_merges=0, lost=4)
        assert empty.precision == 1.0
        assert empty.lost == 4

    def test_an_unlabelled_pair_is_refused(self) -> None:
        a = record("a", "K", 47.3701, 8.5484)
        b = record("b", "K", 46.9500, 7.4400, provider="p2")
        with pytest.raises(ResolutionError, match="unlabelled"):
            evaluate([LabelledPair(label="probably", left=a, right=b, note="")])
