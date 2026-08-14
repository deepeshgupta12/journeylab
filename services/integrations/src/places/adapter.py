"""Provider payload to canonical place — STEP-005.02 (REQ-DATA-001, REQ-PRIV-003).

WHAT MAKES THIS AN ADAPTER RATHER THAN A PARSER
    It refuses more than it accepts. Three things it will not do, each because the
    alternative produces a confident wrong answer downstream:

      1. It will not ingest without a `LicenceRecord` (REQ-DATA-001). The signature
         makes that structural rather than a check somebody remembers.
      2. It will not guess hours. An unparseable `opening_hours` becomes UNKNOWN,
         which the solver must already handle — never a guess, because wrong hours
         are a hard-constraint violation and `BUG_REGISTER` defines that as S1.
      3. It will not infer accessibility. REQ-PRIV-003 permits declaration only,
         and "step-free because the building is new" is inference wearing a fact's
         clothes.

PROVENANCE IS ASSEMBLED HERE, NOT LATER
    Every field arrives with its source, observation time and licence. Attaching
    provenance downstream means guessing where a value came from, and a guessed
    provenance is worse than none — it looks authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .hours import HoursError, OpeningHours, parse, unknown_hours
from .licence import LicenceRecord


class AdapterError(ValueError):
    """The payload could not be adapted, and was NOT partially accepted."""


@dataclass(frozen=True, slots=True)
class Provenance:
    """Matches `contracts/jsonschema/provenance.json`.

    `licence_id` is the field STEP-004.06 added and nothing used until now. It is
    load-bearing from this sub-step onward: `ADR-016` established that OSM facts
    arrive under ODbL while `opendata.swiss` facts do not, and the two will sit
    side by side in one evidence pack from the first ingestion.
    """

    source_id: str
    source_name: str
    observed_at: datetime
    confidence: float
    access_label: str
    licence_id: str

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise AdapterError("observed_at must be timezone-aware")
        if not 0.0 <= self.confidence <= 1.0:
            raise AdapterError(f"confidence must be 0..1, got {self.confidence}")
        if self.access_label not in {"public", "display_permitted", "internal_only"}:
            raise AdapterError(f"unknown access_label {self.access_label!r}")


@dataclass(frozen=True, slots=True)
class CanonicalPlace:
    """What ingestion produces. Wider than the API's `Place`, deliberately.

    The contract's `Place` is the public surface; this is what the evidence pack
    holds. Keeping them separate means an internal field does not become a public
    promise by accident.
    """

    place_id: str
    name: str
    time_zone: str
    hours: OpeningHours
    #: Declared accessibility features. Empty means NOT DECLARED — never "no
    #: features". The distinction is REQ-PRIV-003 and it is the difference between
    #: "the source is silent" and "this place is inaccessible".
    accessibility: tuple[str, ...]
    provenance: Provenance
    warnings: tuple[str, ...] = field(default=())


#: Accessibility keys we accept as DECLARED. Anything else is dropped rather than
#: mapped to the nearest neighbour: a wrong accessibility fact is worse for the
#: person relying on it than a missing one.
DECLARED_ACCESSIBILITY = frozenset(
    {"wheelchair", "step_free", "accessible_toilet", "hearing_loop", "tactile_guidance"}
)


def adapt(
    payload: dict[str, Any],
    *,
    licence: LicenceRecord,
    observed_at: datetime | None = None,
    confidence: float = 0.8,
) -> CanonicalPlace:
    """Map one provider payload to a canonical place.

    `licence` is a required keyword argument and that is the whole enforcement of
    REQ-DATA-001: there is no way to call this without having recorded the terms.
    """
    moment = observed_at or datetime.now(UTC)
    warnings: list[str] = []

    name = str(payload.get("name") or "").strip()
    if not name:
        raise AdapterError("a place without a name cannot be rendered or cited")

    time_zone = str(payload.get("time_zone") or "").strip()
    if not time_zone:
        # Required by the contract's `Place`, and required for hours to mean
        # anything at all. Defaulting it would silently place a Swiss museum in UTC.
        raise AdapterError(
            f"{name!r}: time_zone is required. Hours without a zone are a plan that "
            f"is wrong by an hour twice a year (contract: Place.time_zone)."
        )

    raw_hours = payload.get("opening_hours")
    if not raw_hours:
        hours = unknown_hours(time_zone)
        warnings.append("no opening_hours in the payload; recorded as UNKNOWN")
    else:
        try:
            hours = parse(str(raw_hours), time_zone=time_zone)
        except HoursError as exc:
            # NOT a failure of the whole place. The name and location are still
            # usable facts; only the hours are unknown, and saying so is more
            # useful than discarding the record or inventing a schedule.
            hours = unknown_hours(time_zone)
            warnings.append(f"unparseable opening_hours, recorded as UNKNOWN: {exc}")

    declared = payload.get("accessibility")
    accessibility: tuple[str, ...] = ()
    if isinstance(declared, list):
        kept = sorted({str(a) for a in declared} & DECLARED_ACCESSIBILITY)
        dropped = sorted({str(a) for a in declared} - DECLARED_ACCESSIBILITY)
        accessibility = tuple(kept)
        if dropped:
            warnings.append(f"accessibility keys not in the declared vocabulary: {dropped}")

    return CanonicalPlace(
        place_id=str(payload.get("place_id") or "").strip() or f"{licence.licence_id}:{name}",
        name=name,
        time_zone=time_zone,
        hours=hours,
        accessibility=accessibility,
        provenance=Provenance(
            source_id=licence.licence_id,
            source_name=licence.source_name,
            observed_at=moment,
            confidence=confidence,
            access_label="public",
            licence_id=licence.licence_id,
        ),
        warnings=tuple(warnings),
    )
