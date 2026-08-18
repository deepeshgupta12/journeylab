"""Canonical place entity resolution — STEP-005.07 (REQ-DATA-004).

THE ASYMMETRY THAT DECIDES EVERY DESIGN CHOICE BELOW

    A missed merge leaves a duplicate in a list. A false merge sends a traveller to
    the wrong building — and does it silently, with a confident itinerary and a
    plausible travel time. The two errors are not comparable, so the matcher is not
    tuned for accuracy. It is tuned so that **the only automatic answer is one that
    cannot be wrong**, and everything else is asked about.

    That makes the review queue the main path rather than an exception, and §8
    reports the measured rate rather than implying otherwise.

WHY THE SIGNALS ARE GATED AND NEVER SUMMED

    The obvious implementation scores distance and name similarity, weights them,
    and merges above a threshold. That is exactly how two branches of the same chain
    get merged: a perfect name match (`Coop Bahnhofstrasse`) buys enough score to
    pay for being 400 m apart. **Compensation between independent signals is the
    false-merge mechanism**, so each signal has its own gate and every gate must be
    cleared. A brilliant name score cannot rescue a failing distance.

    The same rule runs in reverse for evidence against a merge: the category can
    only ever *demote* a decision, never promote one. A cafe inside a museum shares
    the museum's coordinate to the metre, and the category is the only field that
    knows they are two places.

WHY AN IDENTIFIER CONFLICT IS NOT RESOLVED BY PROXIMITY

    Two records five metres apart that carry *different* Wikidata QIDs are not a
    near-certain match with a small data problem. They are two sources asserting
    different identities, and REQ-EVID-002 forbids averaging that away. The conflict
    outranks the geometry: it goes to review, never to a merge, however close it is.

WHAT "CANONICAL" MEANS HERE

    One identity, not one set of values. `CanonicalEntity` holds its members
    verbatim and never flattens them into a single record. That is what makes a
    merge reversible after the fact, and it is the same rule as REQ-EVID-002 —
    conflicting values stay visible instead of being resolved into an average that
    no source ever reported.
"""

from __future__ import annotations

import difflib
import enum
import math
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from places.adapter import CanonicalPlace
from places.adapter import Coordinate as Coordinate  # re-exported: see below

#: `Coordinate` is defined in the places adapter, where a place's location belongs,
#: and re-exported here so a caller of this module does not have to import a second
#: module to construct the type this one takes. Its Null Island refusal is the
#: reason it is a type at all rather than two floats.


class ResolutionError(ValueError):
    """A resolution input or operation was refused, and NOT partially applied."""


# --- identity ------------------------------------------------------------------

#: Namespaces whose identifiers denote **at most one venue**, which is the whole
#: test for whether an identifier can carry identity.
#:
#: An identifier that denotes something *coarser* than a venue — a building, a
#: street address, a phone number, a chain — merges distinct venues by design, and
#: it does so with maximum confidence because the match is exact. That is the
#: failure mode this allowlist exists to prevent, and it is why the list is short.
#:
#: Adding a namespace requires evidence that its issuer mints one identifier per
#: venue. It is not enough that the values happen to agree on the sample in front
#: of you.
IDENTITY_NAMESPACES = frozenset({"wikidata", "osm", "uic"})

#: Namespaces that look like identity and are not, kept by name so a decision can
#: say *why* it ignored one rather than silently dropping it.
#:
#: `gtfs_stop` is here for a second, independent reason established in STEP-005.04:
#: GTFS stop identifiers are scoped to a feed publication and are not stable across
#: publications, so the same string can denote a different platform next week.
COARSER_THAN_A_VENUE = frozenset(
    {"address", "postcode", "phone", "email", "website", "brand", "building", "gtfs_stop"}
)


class Outcome(enum.StrEnum):
    """What the matcher concluded. `REVIEW` is a real answer, not a failure."""

    AUTO_MERGE = "auto_merge"
    REVIEW = "review"
    DISTINCT = "distinct"


# --- thresholds ----------------------------------------------------------------
#
# These are gates, not weights (see the module docstring). The numbers are measured
# against the labelled sample in `tests/ingestion/labelled_pairs.json` and the
# measurement is itself a test, so loosening one of these fails the suite rather
# than quietly changing what the product merges.

#: Above this, nothing merges automatically whatever the name says.
AUTO_MERGE_METRES = 50.0

#: Beyond this, two records are different venues and are not even asked about.
#: Swiss chains put identically-named branches a few hundred metres apart.
REVIEW_METRES = 150.0

#: At this range the records are on the same doorstep. Something is there — either
#: one venue described twice or a venue inside another — and a human should say
#: which. This is the rule that catches the cross-language duplicate that no string
#: comparison can see: `Kunstmuseum Bern` and `Musee des Beaux-Arts de Berne` have
#: almost no characters in common and are the same building.
SAME_POINT_METRES = 25.0

#: Name agreement required before anything merges without being asked about.
AUTO_MERGE_SIMILARITY = 0.90

#: Below this the names are unrelated, and only `SAME_POINT_METRES` can still
#: produce a review.
REVIEW_SIMILARITY = 0.60


def metres_between(a: Coordinate, b: Coordinate) -> float:
    """Great-circle distance in metres, **for identity only**.

    This answers "are these the same place". It never answers "how long does it take
    to get from one to the other" — STEP-005.05 prohibits straight-line distance as
    a travel time, and the prohibition is not weakened by a distance function
    existing one service away for a different question. `tests/integrations/
    test_routing_matrix.py` asserts the routing module cannot reach this.
    """
    radius_m = 6_371_008.8
    phi1, phi2 = math.radians(a.latitude), math.radians(b.latitude)
    d_phi = phi2 - phi1
    d_lambda = math.radians(b.longitude - a.longitude)
    h = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius_m * math.asin(math.sqrt(h))


_GERMAN_EXPANSIONS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _tidy(text: str) -> str:
    kept = [c if c.isalnum() or c.isspace() else " " for c in text]
    return " ".join("".join(kept).split())


def name_variants(name: str) -> tuple[str, str]:
    """The two normalisations of a Swiss name, because neither one is enough.

    `Zürich`, `Zuerich` and `Zurich` are one city written three ways, and **no
    single normalisation makes all three equal**:

      * stripping diacritics gives `zurich`, `zuerich`, `zurich` — 1 and 3 agree
      * expanding umlauts gives `zuerich`, `zuerich`, `zurich` — 1 and 2 agree

    So both are produced and `name_similarity` takes the best pairing. Picking one
    normalisation would systematically miss one of the two spelling conventions
    actually used in this country.
    """
    lowered = name.casefold()
    return _tidy(_strip_diacritics(lowered)), _tidy(lowered.translate(_GERMAN_EXPANSIONS))


def name_similarity(left: str, right: str) -> float:
    """Best similarity across the normalisation variants, 0.0 to 1.0."""
    return max(
        difflib.SequenceMatcher(None, a, b).ratio()
        for a in name_variants(left)
        for b in name_variants(right)
    )


@dataclass(frozen=True, slots=True)
class ProviderRecord:
    """One provider's view of one venue. The input to resolution.

    `provider_place_id` is the provider's own key and is **never** identity across
    providers — two providers reusing the string `12345` are not describing the same
    museum. Cross-provider identity travels in `external_ids`, and only for the
    namespaces in `IDENTITY_NAMESPACES`.
    """

    provider_id: str
    provider_place_id: str
    name: str
    category: str
    coordinate: Coordinate
    licence_id: str
    observed_at: datetime
    external_ids: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label, value in (
            ("provider_id", self.provider_id),
            ("provider_place_id", self.provider_place_id),
            ("name", self.name),
            ("licence_id", self.licence_id),
        ):
            if not value.strip():
                raise ResolutionError(f"{label} is required on a provider record")
        if self.observed_at.tzinfo is None:
            raise ResolutionError("observed_at must be timezone-aware")

    @property
    def key(self) -> str:
        """Stable within a provider, unique across them, and reproducible."""
        return f"{self.provider_id}:{self.provider_place_id}"

    @classmethod
    def from_place(
        cls,
        place: CanonicalPlace,
        *,
        provider_id: str,
        external_ids: Mapping[str, str] | None = None,
    ) -> ProviderRecord:
        """Adapter output to resolution input.

        This exists so the pipeline is one path rather than two shapes that drift.
        It is also what BUG-027 was blocking: before the adapter carried a
        coordinate and a category, this conversion could not be written at all.
        """
        return cls(
            provider_id=provider_id,
            provider_place_id=place.place_id,
            name=place.name,
            category=place.category,
            coordinate=place.coordinate,
            licence_id=place.provenance.licence_id,
            observed_at=place.provenance.observed_at,
            external_ids=dict(external_ids or {}),
        )


@dataclass(frozen=True, slots=True)
class ResolutionDecision:
    """Why the matcher concluded what it did, in enough detail to argue with.

    A decision that records only its outcome cannot be reviewed, cannot be audited
    after a bad merge, and cannot be re-derived when a threshold moves. All three
    are needed here, so the evidence travels with the verdict.
    """

    left_key: str
    right_key: str
    outcome: Outcome
    reasons: tuple[str, ...]
    distance_metres: float
    similarity: float
    identifier_agreements: tuple[str, ...] = ()
    identifier_conflicts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ResolutionError(
                "a decision without a reason cannot be reviewed or audited; "
                "every outcome states why"
            )


def _identifier_evidence(
    left: ProviderRecord, right: ProviderRecord
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Agreements, conflicts, and the namespaces deliberately not consulted."""
    agreements: list[str] = []
    conflicts: list[str] = []
    ignored: list[str] = []
    shared = sorted(set(left.external_ids) & set(right.external_ids))
    for namespace in shared:
        if namespace not in IDENTITY_NAMESPACES:
            ignored.append(namespace)
            continue
        if left.external_ids[namespace] == right.external_ids[namespace]:
            agreements.append(f"{namespace}:{left.external_ids[namespace]}")
        else:
            conflicts.append(
                f"{namespace}:{left.external_ids[namespace]} vs {right.external_ids[namespace]}"
            )
    return tuple(agreements), tuple(conflicts), tuple(ignored)


def compare(left: ProviderRecord, right: ProviderRecord) -> ResolutionDecision:
    """Decide whether two provider records describe one venue.

    Identifier evidence is consulted first and outranks geometry in both directions:
    agreement can carry a merge across a coordinate disagreement, and conflict blocks
    one however close the two records sit.
    """
    if left.key == right.key:
        raise ResolutionError(f"{left.key} compared against itself")

    distance = metres_between(left.coordinate, right.coordinate)
    similarity = name_similarity(left.name, right.name)
    agreements, conflicts, ignored = _identifier_evidence(left, right)
    reasons: list[str] = []
    if ignored:
        reasons.append(
            f"shared identifiers not treated as identity (coarser than a venue, "
            f"or feed-scoped): {', '.join(ignored)}"
        )

    def decision(outcome: Outcome, *why: str) -> ResolutionDecision:
        return ResolutionDecision(
            left_key=left.key,
            right_key=right.key,
            outcome=outcome,
            reasons=tuple(reasons + list(why)),
            distance_metres=distance,
            similarity=similarity,
            identifier_agreements=agreements,
            identifier_conflicts=conflicts,
        )

    # 1. A conflict is unresolved evidence, not a weak signal (REQ-EVID-002).
    if conflicts:
        if distance <= REVIEW_METRES:
            return decision(
                Outcome.REVIEW,
                f"identifiers disagree ({'; '.join(conflicts)}) at {distance:.0f} m — "
                f"two sources assert different identities and proximity does not "
                f"settle which is right",
            )
        return decision(
            Outcome.DISTINCT,
            f"identifiers disagree ({'; '.join(conflicts)}) and the records are "
            f"{distance:.0f} m apart",
        )

    # 2. Agreement on an identity-bearing namespace is the strongest evidence there
    #    is — but a large coordinate disagreement is a second fact, not noise, and
    #    it stays visible rather than being overridden.
    if agreements:
        if distance > REVIEW_METRES:
            return decision(
                Outcome.REVIEW,
                f"identifiers agree ({', '.join(agreements)}) but the coordinates "
                f"disagree by {distance:.0f} m — one of the two sources is wrong "
                f"about where this is",
            )
        return _demote_on_category(
            decision(Outcome.AUTO_MERGE, f"identifiers agree: {', '.join(agreements)}"),
            left,
            right,
        )

    # 3. No identity evidence. Gates only, never a weighted sum.
    if distance > REVIEW_METRES:
        return decision(
            Outcome.DISTINCT,
            f"{distance:.0f} m apart, beyond the {REVIEW_METRES:.0f} m review range",
        )

    if distance <= AUTO_MERGE_METRES and similarity >= AUTO_MERGE_SIMILARITY:
        return _demote_on_category(
            decision(
                Outcome.AUTO_MERGE,
                f"{distance:.0f} m apart with name similarity {similarity:.2f}",
            ),
            left,
            right,
        )

    if distance <= SAME_POINT_METRES:
        return decision(
            Outcome.REVIEW,
            f"{distance:.0f} m apart — the same doorstep. The names agree only "
            f"{similarity:.2f}, which in a multilingual country is not evidence of "
            f"anything either way",
        )

    if similarity >= REVIEW_SIMILARITY:
        return decision(
            Outcome.REVIEW,
            f"similar names ({similarity:.2f}) {distance:.0f} m apart — close enough "
            f"to ask about, not close enough to merge unasked",
        )

    return decision(
        Outcome.DISTINCT,
        f"{distance:.0f} m apart with unrelated names ({similarity:.2f})",
    )


def _demote_on_category(
    proposed: ResolutionDecision, left: ProviderRecord, right: ProviderRecord
) -> ResolutionDecision:
    """Category can demote a merge to a review. It can never promote anything.

    A cafe inside a museum sits at the museum's coordinate and often carries the
    museum's name. Nothing geometric or textual separates them; the declared
    category does.

    DEMOTION ONLY, AND THE ASYMMETRY IS THE POINT
        "Same point, same category, therefore the same place" is the obvious next
        step and it is wrong: a station concourse holds a dozen venues that all
        declare `restaurant`. A category *match* is the weakest possible evidence of
        identity, because provider taxonomies are coarse — so it never promotes
        anything, and every decision that is not already an automatic merge passes
        through unchanged.
    """
    if proposed.outcome is not Outcome.AUTO_MERGE:
        return proposed
    left_category, right_category = (
        left.category.strip().casefold(),
        right.category.strip().casefold(),
    )
    if not left_category or not right_category or left_category == right_category:
        return proposed
    return ResolutionDecision(
        left_key=proposed.left_key,
        right_key=proposed.right_key,
        outcome=Outcome.REVIEW,
        reasons=(
            *proposed.reasons,
            f"categories disagree ({left.category!r} vs {right.category!r}) — a venue "
            f"inside another venue looks exactly like this, so it is asked about "
            f"rather than merged",
        ),
        distance_metres=proposed.distance_metres,
        similarity=proposed.similarity,
        identifier_agreements=proposed.identifier_agreements,
        identifier_conflicts=proposed.identifier_conflicts,
    )


# --- the canonical entity and its audited, reversible history -------------------


@dataclass(frozen=True, slots=True)
class CanonicalEntity:
    """One venue, and every provider record that describes it — kept separately.

    The members are not merged into a single set of values, and that is deliberate.
    Flattening would make the merge irreversible the moment a field disagreed, and
    it would resolve conflicting evidence by picking a winner, which REQ-EVID-002
    forbids. A caller that needs one value chooses it explicitly and can show what
    it chose between.
    """

    entity_id: str
    members: tuple[ProviderRecord, ...]

    def __post_init__(self) -> None:
        if not self.members:
            raise ResolutionError(f"{self.entity_id}: an entity with no members is not an entity")

    @property
    def member_keys(self) -> tuple[str, ...]:
        return tuple(sorted(m.key for m in self.members))

    def providers(self) -> tuple[str, ...]:
        return tuple(sorted({m.provider_id for m in self.members}))


@dataclass(frozen=True, slots=True)
class Operation:
    """One audited change, carrying enough state to be undone exactly.

    `before` is the full member grouping of every entity the operation touched. A
    log that recorded only "merged A and B" cannot undo the second merge into a
    three-member entity without guessing which member came from where; this one
    restores the exact prior grouping.
    """

    operation_id: str
    kind: str
    at: datetime
    actor: str
    reason: str
    entity_ids: tuple[str, ...]
    before: tuple[tuple[str, tuple[str, ...]], ...]
    after: tuple[tuple[str, tuple[str, ...]], ...]

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ResolutionError("every operation records who performed it")
        if not self.reason.strip():
            raise ResolutionError(
                "every operation records why. An unexplained merge cannot be "
                "reviewed later, and a merge is exactly the thing reviewed later"
            )


@dataclass
class EntityGraph:
    """Provider records grouped into canonical entities, with a reversible history.

    Entity identifiers are allocated from a counter rather than a random UUID, so
    the same input sequence produces the same graph on any machine and on any run
    (REQ-CONS-006). A random identifier would make a scenario irreproducible by the
    definition the product uses for its own scenarios.
    """

    _entities: dict[str, CanonicalEntity] = field(default_factory=dict)
    _owner: dict[str, str] = field(default_factory=dict)
    #: Every record ever admitted, by key. Merges and splits regroup records and
    #: never destroy them, so this is what an undo restores from — reconstructing
    #: members by walking the history would depend on the history being complete,
    #: which is exactly the property an undo cannot assume.
    _records: dict[str, ProviderRecord] = field(default_factory=dict)
    _history: list[Operation] = field(default_factory=list)
    _next_entity: int = 1
    _next_operation: int = 1

    def _allocate_entity_id(self) -> str:
        allocated = f"ent-{self._next_entity:04d}"
        self._next_entity += 1
        return allocated

    def _allocate_operation_id(self) -> str:
        allocated = f"op-{self._next_operation:04d}"
        self._next_operation += 1
        return allocated

    def _snapshot(self, entity_ids: Iterable[str]) -> tuple[tuple[str, tuple[str, ...]], ...]:
        return tuple(
            (entity_id, self._entities[entity_id].member_keys)
            for entity_id in sorted(entity_ids)
            if entity_id in self._entities
        )

    def add(self, record: ProviderRecord) -> str:
        """Admit a provider record as its own entity. Idempotent by record key."""
        existing = self._owner.get(record.key)
        if existing is not None:
            return existing
        entity_id = self._allocate_entity_id()
        self._entities[entity_id] = CanonicalEntity(entity_id=entity_id, members=(record,))
        self._owner[record.key] = entity_id
        self._records[record.key] = record
        return entity_id

    def entity_for(self, record_key: str) -> CanonicalEntity:
        entity_id = self._owner.get(record_key)
        if entity_id is None:
            raise ResolutionError(f"{record_key} is not in the graph")
        return self._entities[entity_id]

    def entities(self) -> tuple[CanonicalEntity, ...]:
        return tuple(self._entities[k] for k in sorted(self._entities))

    def history(self) -> tuple[Operation, ...]:
        return tuple(self._history)

    def merge(self, left_id: str, right_id: str, *, actor: str, reason: str, at: datetime) -> str:
        """Merge two entities into one, recording how to undo it."""
        if left_id == right_id:
            raise ResolutionError(f"{left_id} merged with itself")
        for entity_id in (left_id, right_id):
            if entity_id not in self._entities:
                raise ResolutionError(f"unknown entity {entity_id}")

        before = self._snapshot((left_id, right_id))
        merged_members = tuple(
            sorted(
                self._entities[left_id].members + self._entities[right_id].members,
                key=lambda m: m.key,
            )
        )
        target = self._allocate_entity_id()
        del self._entities[left_id]
        del self._entities[right_id]
        self._entities[target] = CanonicalEntity(entity_id=target, members=merged_members)
        for member in merged_members:
            self._owner[member.key] = target

        self._record("merge", (left_id, right_id, target), before, actor, reason, at)
        return target

    def split(
        self,
        entity_id: str,
        groups: Sequence[Sequence[str]],
        *,
        actor: str,
        reason: str,
        at: datetime,
    ) -> tuple[str, ...]:
        """Split one entity into an explicit partition of its members.

        The partition must be exact — every member in exactly one group. A split
        that silently dropped or duplicated a member would lose a provider's record
        or double-count it, and neither is visible afterwards.
        """
        if entity_id not in self._entities:
            raise ResolutionError(f"unknown entity {entity_id}")
        entity = self._entities[entity_id]
        by_key = {member.key: member for member in entity.members}
        flattened = [key for group in groups for key in group]
        if len(groups) < 2:
            raise ResolutionError("a split produces at least two entities")
        if sorted(flattened) != sorted(by_key):
            raise ResolutionError(
                f"{entity_id}: the split must be an exact partition of "
                f"{sorted(by_key)}, got {sorted(flattened)}"
            )

        before = self._snapshot((entity_id,))
        del self._entities[entity_id]
        produced: list[str] = []
        for group in groups:
            new_id = self._allocate_entity_id()
            members = tuple(sorted((by_key[key] for key in group), key=lambda m: m.key))
            self._entities[new_id] = CanonicalEntity(entity_id=new_id, members=members)
            for member in members:
                self._owner[member.key] = new_id
            produced.append(new_id)

        self._record("split", (entity_id, *produced), before, actor, reason, at)
        return tuple(produced)

    def undo(self, operation_id: str, *, actor: str, at: datetime) -> None:
        """Restore the exact grouping an operation replaced.

        Refused unless it is the most recent operation touching those entities.
        Undoing out of order would silently discard the decisions made since, and a
        reversal that destroys a later human judgement is not a reversal.
        """
        target = next((op for op in self._history if op.operation_id == operation_id), None)
        if target is None:
            raise ResolutionError(f"unknown operation {operation_id}")

        touched = set(target.entity_ids)
        later = [
            op
            for op in self._history
            if op.at >= target.at
            and op.operation_id != operation_id
            and touched & set(op.entity_ids)
            and self._history.index(op) > self._history.index(target)
        ]
        if later:
            raise ResolutionError(
                f"{operation_id} cannot be undone: "
                f"{', '.join(op.operation_id for op in later)} touched the same "
                f"entities afterwards, and reversing this now would discard them"
            )

        before = self._snapshot(
            entity_id for entity_id in target.entity_ids if entity_id in self._entities
        )
        for entity_id in target.entity_ids:
            self._entities.pop(entity_id, None)
        for entity_id, keys in target.before:
            members = tuple(sorted((self._records[key] for key in keys), key=lambda m: m.key))
            self._entities[entity_id] = CanonicalEntity(entity_id=entity_id, members=members)
            for member in members:
                self._owner[member.key] = entity_id

        self._record(
            "undo",
            tuple(sorted({*target.entity_ids, *(e for e, _ in target.before)})),
            before,
            actor,
            f"undo of {operation_id}: {target.reason}",
            at,
        )

    def _record(
        self,
        kind: str,
        entity_ids: tuple[str, ...],
        before: tuple[tuple[str, tuple[str, ...]], ...],
        actor: str,
        reason: str,
        at: datetime,
    ) -> None:
        self._history.append(
            Operation(
                operation_id=self._allocate_operation_id(),
                kind=kind,
                at=at,
                actor=actor,
                reason=reason,
                entity_ids=entity_ids,
                before=before,
                after=self._snapshot(entity_ids),
            )
        )


# --- the review queue -----------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReviewItem:
    item_id: str
    decision: ResolutionDecision
    raised_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewResolution:
    item_id: str
    merged: bool
    actor: str
    note: str
    resolved_at: datetime

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ResolutionError("a review is resolved by a person, and the person is named")
        if not self.note.strip():
            raise ResolutionError(
                "a review resolution records what the reviewer saw. Without it the "
                "next reviewer of the same pair starts from nothing"
            )


@dataclass
class ReviewQueue:
    """Pairs a human must decide.

    There is deliberately **no expiry, no default and no auto-approve**. A queue
    that merges what nobody got round to reviewing is a slower version of merging
    without review, and the backlog — not the matcher — becomes what decides.
    Growth is the intended failure mode: it is visible, and it degrades nothing.
    """

    _items: dict[str, ReviewItem] = field(default_factory=dict)
    _resolutions: list[ReviewResolution] = field(default_factory=list)
    _next_item: int = 1

    def enqueue(self, decision: ResolutionDecision, *, at: datetime) -> str:
        if decision.outcome is not Outcome.REVIEW:
            raise ResolutionError(
                f"only a REVIEW decision is queued; {decision.outcome} was decided "
                f"and queueing it would hide an automatic answer behind a human one"
            )
        item_id = f"rev-{self._next_item:04d}"
        self._next_item += 1
        self._items[item_id] = ReviewItem(item_id=item_id, decision=decision, raised_at=at)
        return item_id

    def pending(self) -> tuple[ReviewItem, ...]:
        """Closest pairs first — the ones most likely to be real duplicates.

        Ordered deterministically so two runs over the same corpus present the same
        queue (REQ-CONS-006).
        """
        return tuple(
            sorted(
                self._items.values(),
                key=lambda i: (i.decision.distance_metres, i.item_id),
            )
        )

    def resolve(
        self, item_id: str, *, merged: bool, actor: str, note: str, at: datetime
    ) -> ReviewResolution:
        if item_id not in self._items:
            raise ResolutionError(f"unknown review item {item_id}")
        resolution = ReviewResolution(
            item_id=item_id, merged=merged, actor=actor, note=note, resolved_at=at
        )
        del self._items[item_id]
        self._resolutions.append(resolution)
        return resolution

    def resolutions(self) -> tuple[ReviewResolution, ...]:
        return tuple(self._resolutions)


# --- measurement ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LabelledPair:
    label: str
    left: ProviderRecord
    right: ProviderRecord
    note: str


@dataclass(frozen=True, slots=True)
class Evaluation:
    """What the matcher actually does on a labelled sample.

    `precision` alone is a useless target: a matcher that merges nothing scores a
    perfect 1.0. `lost` is the metric that excludes that degenerate answer — it
    counts true duplicates the matcher declared DISTINCT, which are the ones no
    human will ever be asked about.
    """

    pairs: int
    auto_merges: int
    reviews: int
    distinct: int
    false_merges: int
    lost: int
    #: True duplicates the matcher sent to review rather than merging. Not a
    #: failure — it is the intended answer for the hard cases — but recall cannot
    #: be computed without it.
    same_in_review: int = 0

    @property
    def precision(self) -> float:
        if self.auto_merges == 0:
            return 1.0
        return (self.auto_merges - self.false_merges) / self.auto_merges

    @property
    def recall(self) -> float:
        same = self.auto_merges - self.false_merges + self.lost + self.same_in_review
        if same == 0:
            return 1.0
        return (self.auto_merges - self.false_merges) / same

    @property
    def review_rate(self) -> float:
        return self.reviews / self.pairs if self.pairs else 0.0


def evaluate(pairs: Sequence[LabelledPair]) -> Evaluation:
    """Run the matcher over a labelled sample and count what it got right.

    Shipped rather than kept in the tests, because the numbers it produces are
    reported to the owner and a measurement that only exists inside a test cannot be
    re-run against a real corpus when one arrives.
    """
    auto = reviews = distinct = false_merges = lost = same_in_review = 0
    for pair in pairs:
        if pair.label not in {"same", "different"}:
            raise ResolutionError(f"unlabelled pair: {pair.label!r}")
        outcome = compare(pair.left, pair.right).outcome
        if outcome is Outcome.AUTO_MERGE:
            auto += 1
            if pair.label == "different":
                false_merges += 1
        elif outcome is Outcome.REVIEW:
            reviews += 1
            if pair.label == "same":
                same_in_review += 1
        else:
            distinct += 1
            if pair.label == "same":
                lost += 1
    return Evaluation(
        pairs=len(pairs),
        auto_merges=auto,
        reviews=reviews,
        distinct=distinct,
        false_merges=false_merges,
        lost=lost,
        same_in_review=same_in_review,
    )
