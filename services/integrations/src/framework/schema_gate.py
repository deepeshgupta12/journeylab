"""Schema validation that rejects and never coerces — STEP-005.01 (REQ-DATA-002).

WHY "NEVER COERCES" IS THE ENTIRE POINT
    Every ingestion library will happily turn `"42"` into `42`, `"true"` into
    `True`, and a missing field into `None`. Each of those is a silent decision
    about a provider's data, made by us, and recorded downstream as if the provider
    had said it.

    This product's whole claim is that a rendered fact is traceable to a source
    (`REQ-EVID-001`) and that an estimate is never shown as confirmed
    (`REQ-EVID-003`). A coercion breaks both quietly: the value is ours, the
    provenance says theirs, and nothing in the pipeline knows.

    A provider changing `departure` from a string to an object is a schema drift
    event that should page someone. Coerced, it becomes a plausible wrong departure
    time in an itinerary.

WHY DRIFT IS ITS OWN SIGNAL
    `SchemaDriftError` is separate from a validation failure on one record. One bad
    record is a provider bug; a shape change is a contract change, and
    `REQ-DATA-002` asks for an alert rather than a skipped row. The caller decides
    what to do; this module makes the distinction available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jsonschema


class SchemaRejectedError(Exception):
    """A payload did not match its schema and was NOT adapted to fit."""


class SchemaDriftError(SchemaRejectedError):
    """The provider's shape changed, as opposed to one record being bad.

    A subclass so a caller that only cares about "this failed" needs no change,
    while one that wants to page on drift can catch the narrower type.
    """


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    """What happened, in a form that can be recorded rather than just raised."""

    provider: str
    accepted: int
    rejected: int
    drift_detected: bool


def validate(payload: Any, schema: dict[str, Any], *, provider: str) -> Any:
    """Return the payload unchanged, or raise. There is no third outcome.

    Returning the input **identically** is deliberate: a function that validates
    and returns is one refactor away from validating and returning something
    adjusted, and the type signature would not change. The test asserts identity,
    not equality.
    """
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if not errors:
        return payload

    first = errors[0]
    location = "/".join(str(p) for p in first.absolute_path) or "(root)"

    # A type mismatch at the top of a document is a shape change; a constraint
    # violation deep inside one record is a bad record. Imperfect, and better than
    # treating a provider redesign as a skippable row.
    is_drift = first.validator == "type" and len(first.absolute_path) <= 1

    message = (
        f"{provider}: payload rejected at {location} — {first.message}. "
        f"NOT coerced: adapting a provider's value silently makes it ours while the "
        f"provenance still says theirs (REQ-EVID-001)."
    )
    raise (SchemaDriftError if is_drift else SchemaRejectedError)(message)
