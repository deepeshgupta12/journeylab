"""Provider payload to canonical entity — STEP-006.05 (REQ-DATA-007).

WHY THESE ARE PURE FUNCTIONS

    A normalizer that reads a clock, a database or a config file cannot be replayed,
    and replay is the point: `REQ-CONS-006` makes a scenario reproducible from its
    inputs, and the canonical records are those inputs. Every value a normalizer
    produces comes from its arguments, so re-running one over the same fixture a
    year later gives the same row.

    `observed_at` is therefore an argument, not `datetime.now()`. That looks like
    ceremony until a replay stamps every historical fact with today's date and the
    freshness policy declares the entire backfill current.

REJECTION IS THE FEATURE

    `DC-EXT-001`: *"Schema drift ⇒ reject and alert, never coerce."* A normalizer's
    job is not to get a row out of every payload. A field that does not map is a
    provider change we have not understood yet, and guessing produces a canonical
    record that is wrong in a way no downstream check can detect — provenance says
    it came from the provider, and it did not.

    So `normalize_place` raises with the field named, and the batch helper keeps
    rejections **as data** rather than logging them: a rejection nobody counts is a
    silent data loss.

SCHEMA VERSION IS STAMPED ON EVERY RECORD

    Not for tidiness. When a normalizer changes, the records it wrote before the
    change are still in the database, and the only way to tell which mapping
    produced a given row is to have recorded it at write time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from places.adapter import AdapterError, CanonicalPlace, Coordinate
from places.licence import LicenceRecord

#: Bumped whenever a mapping changes meaning. Recorded on every record, because
#: after the change there is no other way to tell which mapping wrote a given row.
PLACE_SCHEMA_VERSION = 1
FACT_SCHEMA_VERSION = 1


class NormalizationError(ValueError):
    """The payload was refused. No partial record was produced."""


@dataclass(frozen=True, slots=True)
class Rejection:
    """A payload that did not map, kept rather than logged.

    A rejection nobody counts is silent data loss: the batch reports a smaller
    number and nothing says why. `reason` names the field so the provider change
    can be found without re-running anything.
    """

    provider_id: str
    payload_key: str
    reason: str


@dataclass(frozen=True, slots=True)
class NormalizedBatch:
    """What a batch produced, including what it refused."""

    places: tuple[CanonicalPlace, ...]
    rejections: tuple[Rejection, ...]

    @property
    def rejection_rate(self) -> float:
        total = len(self.places) + len(self.rejections)
        return len(self.rejections) / total if total else 0.0


@dataclass(frozen=True, slots=True)
class CanonicalFact:
    """One atomic claim, with its three time axes and full provenance."""

    field_class: str
    value: Any
    source_id: str
    licence_id: str
    confidence: float
    access_label: str
    observed_at: datetime
    effective_from: datetime
    effective_to: datetime | None
    schema_version: int = FACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for label, moment in (
            ("observed_at", self.observed_at),
            ("effective_from", self.effective_from),
            ("effective_to", self.effective_to),
        ):
            if moment is not None and moment.tzinfo is None:
                raise NormalizationError(f"{label} must be timezone-aware")
        if not 0.0 <= self.confidence <= 1.0:
            raise NormalizationError(f"confidence must be 0..1, got {self.confidence}")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise NormalizationError("effective_to precedes effective_from")


def normalize_place(
    payload: dict[str, Any],
    *,
    licence: LicenceRecord,
    observed_at: datetime,
    confidence: float = 0.8,
) -> CanonicalPlace:
    """One provider payload to one canonical place. Pure.

    `observed_at` is required rather than defaulted to now, because a replay that
    stamps historical facts with today's date makes the whole backfill look fresh
    and the freshness policy has no way to know otherwise.

    Delegates the field mapping to the STEP-005.02 adapter rather than duplicating
    it: two mappings for one payload shape drift, and the one that drifts is the one
    with fewer tests.
    """
    # No naive-timestamp check here. The adapter refuses one and has its own test,
    # so a duplicate guard is a line no assertion can distinguish from its
    # neighbour — mutation testing showed exactly that, by killing nothing when it
    # was removed. `CanonicalFact` keeps its own check because nothing sits behind
    # that path.
    try:
        return adapt_with_provenance(
            payload, licence=licence, observed_at=observed_at, confidence=confidence
        )
    except AdapterError as exc:
        raise NormalizationError(
            f"{payload.get('place_id') or payload.get('name') or '<unkeyed>'}: {exc}"
        ) from exc


def adapt_with_provenance(
    payload: dict[str, Any],
    *,
    licence: LicenceRecord,
    observed_at: datetime,
    confidence: float,
) -> CanonicalPlace:
    """The adapter call, isolated so the delegation is visible in one place."""
    from places.adapter import adapt

    return adapt(payload, licence=licence, observed_at=observed_at, confidence=confidence)


def normalize_places(
    payloads: list[dict[str, Any]],
    *,
    licence: LicenceRecord,
    observed_at: datetime,
) -> NormalizedBatch:
    """Normalize a batch, keeping refusals as data.

    One bad payload does not fail the batch — that would make a single provider typo
    block an entire ingestion — but the rejections are returned rather than dropped,
    so the count is visible and `.08` can quarantine on it.
    """
    places: list[CanonicalPlace] = []
    rejections: list[Rejection] = []
    for payload in payloads:
        try:
            places.append(normalize_place(payload, licence=licence, observed_at=observed_at))
        except NormalizationError as exc:
            rejections.append(
                Rejection(
                    provider_id=licence.licence_id,
                    payload_key=str(payload.get("place_id") or payload.get("name") or "<unkeyed>"),
                    reason=str(exc),
                )
            )
    return NormalizedBatch(places=tuple(places), rejections=tuple(rejections))


def normalize_fact(
    payload: dict[str, Any],
    *,
    licence: LicenceRecord,
    observed_at: datetime,
    effective_from: datetime,
    effective_to: datetime | None = None,
    confidence: float = 0.8,
) -> CanonicalFact:
    """One atomic claim, with provenance that names its licence.

    `field_class` and `value` are required and are not defaulted: a fact with no
    field class cannot be given a freshness threshold (`STEP-005.08` has no default
    policy either), and a fact with no value is not a fact.
    """
    field_class = str(payload.get("field_class") or "").strip()
    if not field_class:
        raise NormalizationError(
            "field_class is required — without it the fact has no freshness policy, "
            "and STEP-005.08 deliberately has no default to fall back on"
        )
    if "value" not in payload:
        raise NormalizationError(f"{field_class}: a fact without a value is not a fact")
    return CanonicalFact(
        field_class=field_class,
        value=payload["value"],
        source_id=licence.licence_id,
        licence_id=licence.licence_id,
        confidence=confidence,
        access_label="public",
        observed_at=observed_at,
        effective_from=effective_from,
        effective_to=effective_to,
    )


__all__ = [
    "FACT_SCHEMA_VERSION",
    "PLACE_SCHEMA_VERSION",
    "CanonicalFact",
    "Coordinate",
    "NormalizationError",
    "NormalizedBatch",
    "Rejection",
    "normalize_fact",
    "normalize_place",
    "normalize_places",
]
