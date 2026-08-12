# GENERATED from contracts/ — DO NOT EDIT.
# Rebuild: pnpm contracts:generate
# STEP-004.07 · REQ-PLAT-007
#
# A hand edit here fails tests/guards/generated-clients.sh, which regenerates
# and diffs. So does a contract change without a regeneration — the guard
# cannot tell the two apart, and does not need to: both mean the committed
# client does not match the contract.

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import AnyUrl, AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class ErrorCodes(StrEnum):
    """
    GENERATED from docs/product/04-contracts/ERROR_MODEL.md — do not edit by hand. Rebuild: uv run python tools/gen_error_codes.py. Only client-visible codes appear here; internal conditions surface as a fallback or a warning and are never returned to a caller.
    """

    validation_invalid_request = 'validation.invalid_request'
    validation_invalid_party = 'validation.invalid_party'
    coverage_unsupported_region = 'coverage.unsupported_region'
    coverage_unsupported_dates = 'coverage.unsupported_dates'
    coverage_provider_degraded = 'coverage.provider_degraded'
    constraint_ambiguous_requires_clarification = (
        'constraint.ambiguous_requires_clarification'
    )
    constraint_unsatisfiable = 'constraint.unsatisfiable'
    solver_infeasible = 'solver.infeasible'
    solver_timeout = 'solver.timeout'
    evidence_pack_stale = 'evidence.pack_stale'
    evidence_insufficient_coverage = 'evidence.insufficient_coverage'
    itinerary_item_protected = 'itinerary.item_protected'
    concurrency_version_mismatch = 'concurrency.version_mismatch'
    collaboration_invitation_expired = 'collaboration.invitation_expired'
    affiliate_unavailable = 'affiliate.unavailable'
    booking_availability_changed = 'booking.availability_changed'
    privacy_deletion_failed = 'privacy.deletion_failed'
    authz_forbidden = 'authz.forbidden'
    tenant_isolation_violation = 'tenant.isolation_violation'


class Remediation(BaseModel):
    """
    A structured, actionable next step where one exists. The design
    principle behind the whole error model: an error must tell the user
    what to do next. "Something went wrong" is not an error model, it is
    an apology.

    **Only `kind` is fixed here; the rest is the specific error's shape.**
    STEP-004.01 declared this with a guessed payload — `conflict_set` and
    `relaxations` as arrays of strings — before any operation needed one.
    STEP-004.02 then needed relaxations that name the constraint they
    relax, because "depart at 15:00 instead" is not actionable unless the
    reader knows which of three constraints it addresses. The guess was
    wrong and the example caught it.

    Composing responses narrow this: see `ConflictSet` and the
    `Infeasible` response.

    """

    model_config = ConfigDict(
        extra='allow',
    )
    kind: str = Field(..., examples=['relax_constraints'])


class Cursor(RootModel[str]):
    root: str = Field(
        ...,
        description='Opaque position marker. **Base64, not encryption** — a client can read and\nrewrite it, so it carries a sort key and an identifier and nothing else.\nNever a tenant or identity: those come from the token (`REQ-SEC-001`), and\nthe server rejects a cursor containing them.\n',
        examples=[
            'eyJjcmVhdGVkX2F0IjoiMjAyNi0wOC0xMVQwMDowMDowMFoiLCJpZCI6InRycF8wMSJ9'
        ],
        max_length=2048,
    )


class Page(BaseModel):
    """
    One page of results. **Offset pagination is not supported** — it re-runs
    the query per page, so a row inserted between page 1 and page 2 shifts
    every later row and the caller silently skips records or sees one twice.

    There is deliberately no `total`: counting costs a second query on every
    request, and for a set that changes while the caller pages through it the
    number is stale before it renders.

    """

    items: list[Any]
    next_cursor: Cursor | None = Field(
        None, description='Absent or null on the last page.'
    )


class Money(BaseModel):
    """
    Integer minor units. NEVER floating point. `0.1 + 0.2` is not `0.3` in IEEE 754 and currency arithmetic is mostly addition, so a total summed from float line items stops matching the sum of what is displayed. The exponent is not always 2: JPY and KRW have none, BHD/KWD/TND have three — so only formatting divides.
    """

    model_config = ConfigDict(
        extra='forbid',
    )
    amount_minor: int = Field(
        ..., description='€12.34 is 1234. ¥100 is 100.', examples=[1234]
    )
    currency: str = Field(
        ..., description='ISO 4217.', examples=['EUR'], pattern='^[A-Z]{3}$'
    )


class TemporalValidity(BaseModel):
    """
    THREE TIME AXES, and conflating any two is a class of bug this product cannot afford (`DATA-007`).

      observed_at    when the source stated it
      effective_*    when the fact is true in the world
      recorded_at    when we wrote it down

    A ferry timetable observed in March, effective until October, recorded in our database in April is not stale in June — but a system with one timestamp cannot express that, and will either discard good data or serve expired data. Which of the two depends on which meaning the single field happened to get.
    """

    model_config = ConfigDict(
        extra='forbid',
    )
    observed_at: AwareDatetime = Field(
        ..., description='When the source stated it. Not when we fetched it.'
    )
    effective_from: AwareDatetime = Field(
        ..., description='When the fact starts being true in the world.'
    )
    effective_to: AwareDatetime | None = Field(
        None,
        description='Absent means open-ended. Absent is not the same as expired, and a consumer must not treat it as such.',
    )
    recorded_at: AwareDatetime | None = Field(
        None,
        description="When we persisted it. The gap from `observed_at` is our ingestion lag, which is ours to fix and not the source's fault.",
    )


class Source(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str
    name: str = Field(
        ...,
        description="Display name, safe to show. NOT the provider's internal identity, which is commercially confidential and never leaves the platform (`ERROR_MODEL.md` §5).",
    )


class AccessLabel(StrEnum):
    """
    `internal_only` means we may plan with it and may not show it. Licensed data frequently arrives this way, and the distinction is contractual rather than technical.
    """

    public = 'public'
    display_permitted = 'display_permitted'
    internal_only = 'internal_only'


class Provenance(BaseModel):
    """
    Where a value came from and how much to trust it.

    `access_label` governs whether the value may be shown at all: a licence may permit us to plan with a fact but not to display it, and the two are different permissions. A provenance record without it forces every renderer to guess, and renderers guess permissively.
    """

    model_config = ConfigDict(
        extra='forbid',
    )
    source: Source
    confidence: float = Field(..., ge=0.0, le=1.0)
    access_label: AccessLabel = Field(
        ...,
        description='`internal_only` means we may plan with it and may not show it. Licensed data frequently arrives this way, and the distinction is contractual rather than technical.',
    )
    licence_id: str | None = Field(
        None,
        description='Which licence governs retention and attribution for this value (`SC-LIC-01`).',
    )


class ConstraintClass(StrEnum):
    """
    THE FOUR CLASSES ARE KEPT DISTINCT, and collapsing any pair breaks something specific:

      hard        violating it makes the plan wrong. Zero violations is REQ-CONS-004, an S1 if breached
      soft        a preference the solver trades off
      inferred    WE derived it, the traveller did not say it. Requires provenance, and must be reviewable
      unresolved  a blocking ambiguity. The plan cannot be solved until it is answered (REQ-CONS-002)

    Merging `hard` and `soft` produces a solver that quietly relaxes a wheelchair requirement to save nine minutes. Merging `inferred` into either hides that a machine put words in the traveller's mouth. Merging `unresolved` into `soft` produces a confident plan built on a guess — the exact failure this product exists to remove.
    """

    hard = 'hard'
    soft = 'soft'
    inferred = 'inferred'
    unresolved = 'unresolved'


class Status(StrEnum):
    """
    `confirmed` means a provider stated it. `estimated` means we derived
    it. The interface must never present the second as the first.

    """

    confirmed = 'confirmed'
    estimated = 'estimated'


class Conflict(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    value: Any
    provenance: Provenance
    validity: TemporalValidity


class Evidenced(BaseModel):
    """
    A volatile value together with the evidence for it.

    **`REQ-EVID-001`: every volatile fact shows source, observed time,
    effective time and confidence.** This schema is how that stops being a
    promise — a bare number cannot be returned for a volatile field, because
    the field's type is this object and every provenance member is required.

    **`REQ-EVID-003`: an estimate is never rendered as confirmed.** `status`
    is required and has no default. A caller that ignores it renders an
    estimate as fact, which is the specific failure this product exists to
    remove, so it is not optional and not inferable.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    value: Any
    status: Status = Field(
        ...,
        description='`confirmed` means a provider stated it. `estimated` means we derived\nit. The interface must never present the second as the first.\n',
    )
    provenance: Provenance
    validity: TemporalValidity
    conflicts: list[Conflict] | None = Field(
        None,
        description='Other sources that disagree. **Retained, never averaged**\n(`REQ-EVID-002`) — the mean of two conflicting departure times is a\ntime no ferry leaves.\n',
    )


class Conflict1(BaseModel):
    constraint_id: str
    statement: str = Field(
        ..., description="The constraint in the traveller's own words."
    )


class Relaxation(BaseModel):
    constraint_id: str
    suggestion: str


class ConflictSet(BaseModel):
    """
    Why no feasible plan exists, and what would restore one.

    **`REQ-CONS-005`: infeasibility returns a minimal conflict set, never a
    plausible invalid plan.** Minimal matters: "these seventeen constraints
    conflict" is not actionable, and a traveller cannot tell which one to
    relax. The set is the smallest subset that is still contradictory.

    """

    kind: str | None = Field(
        None,
        description='Set by the composing response. Declared here so the composition is\nlegible from this schema alone.\n',
    )
    conflicts: list[Conflict1] = Field(
        ...,
        description='At least two. A single constraint cannot conflict with itself — a\none-item set means the solver failed to explain, not that it found a\nminimal cause.\n',
        min_length=2,
    )
    relaxations: list[Relaxation] | None = Field(
        None,
        description='Concrete alternatives, each of which alone restores feasibility.\nOptional because the solver cannot always find one, and inventing a\nsuggestion it has not verified would be worse than offering none.\n',
    )


class Place(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str = Field(..., max_length=200)
    time_zone: str = Field(
        ..., description='IANA identifier. Required — see `ZonedTimestamp`.'
    )
    place_id: str | None = None


class LocalDateRange(BaseModel):
    """
    **Local dates, not timestamps** (`DATA-004`). A trip starting "12
    September" starts on the 12th wherever the traveller is; converting it to
    an instant at creation would shift it for anyone in another zone.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    start: date
    end: date


class Child(RootModel[int]):
    root: int = Field(..., ge=0, le=17)


class Party(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    adults: int = Field(..., ge=1, le=20)
    children: list[Child] | None = Field(
        None,
        description='Ages at the time of travel, which is what affects eligibility.',
        max_length=20,
    )
    accessibility_needs: list[str] | None = Field(
        None,
        description='**Declared, never inferred** (`REQ-PRIV-003`). Nothing in this product\nderives an accessibility need from behaviour; it appears here only\nbecause the traveller stated it.\n',
    )


class CreateTripRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    origin: Place | None = None
    destination_region: str
    date_range: LocalDateRange
    party: Party
    currency: str = Field(..., pattern='^[A-Z]{3}$')
    locale: str


class Trip(BaseModel):
    trip_id: str
    origin: Place | None = None
    destination_region: str
    date_range: LocalDateRange
    party: Party
    currency: str = Field(..., pattern='^[A-Z]{3}$')
    locale: str
    version: int = Field(..., ge=1)
    canonical_scenario_id: str | None = Field(
        None,
        description='Exactly zero or one (`DATA-004`). A trip with two canonical plans is\na trip nobody has decided.\n',
    )
    permissions: list[str] | None = Field(
        None,
        description='What the CALLER may do. Presentation only — the server enforces\nregardless, and a client that hides a button has hidden a button, not\nprevented an action.\n',
    )


class Constraint(BaseModel):
    constraint_id: str
    statement: str
    unit: str | None = Field(
        None,
        description='Required by `DATA-005` for every entry. "Under two hours" and "under\n120" are the same constraint only if the unit is stated.\n',
    )
    priority: int = Field(..., ge=1)
    provenance: str | None = Field(
        None, description='Required on every `inferred` entry (`DATA-005`).'
    )


class TripBrief(BaseModel):
    """
    **Four separate collections, never a single typed-union list**
    (`DATA-005`). A union invites code that forgets to branch; four arrays
    make "did you handle unresolved constraints?" a question the type system
    asks.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    version: int = Field(..., ge=1)
    hard: list[Constraint]
    soft: list[Constraint]
    inferred: list[Constraint] = Field(
        ..., description='Every entry carries a provenance reference.'
    )
    unresolved: list[Constraint] = Field(
        ...,
        description='Ambiguities that block solving. A brief with a blocking unresolved\nentry is not solvable, and saying so is better than guessing\n(`REQ-CONS-002`).\n',
    )
    confirmed_at: AwareDatetime | None = None


class Status1(StrEnum):
    queued = 'queued'
    running = 'running'
    succeeded = 'succeeded'
    failed = 'failed'


class JobHandle(BaseModel):
    """
    Returned within 500 ms by any operation that cannot complete in a request.
    `events_url` is a `text/event-stream` endpoint, so progress is pushed
    rather than polled.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    job_id: str
    status: Status1
    events_url: str


class GenerateScenariosRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    objectives: list[str] = Field(..., min_length=1)
    scenario_count: int = Field(..., ge=1, le=10)
    evidence_pack_id: str = Field(
        ...,
        description='The immutable pack this run is solved against (`DATA-008`,\n`ADR-004`). Naming it is what makes the run reproducible.\n',
    )
    random_seed: int | None = Field(
        None,
        description='Supplied by the caller so a run can be repeated exactly\n(`REQ-CONS-006`). Omitted means the server chooses and returns it.\n',
    )


class ScenarioEdit(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    edit_type: str
    target_item_id: str | None = None
    payload: dict[str, Any] | None = None
    impact_preview_token: str = Field(
        ...,
        description='Proof that the caller was shown the consequences of this edit before\napplying it. Semantics are designed with STEP-014; declared required\nand opaque now so the shape cannot change without a version bump.\n',
    )


class Role(StrEnum):
    """
    **Not `trip_owner`.** Ownership is not something an owner can hand out
    through an invitation link; transferring it is a separate, deliberate
    act. An invitation that could confer ownership is an invitation that
    can lose you your trip.

    """

    trip_editor = 'trip_editor'
    trip_viewer = 'trip_viewer'


class CreateInvitationRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    role: Role = Field(
        ...,
        description='**Not `trip_owner`.** Ownership is not something an owner can hand out\nthrough an invitation link; transferring it is a separate, deliberate\nact. An invitation that could confer ownership is an invitation that\ncan lose you your trip.\n',
    )
    expires_at: AwareDatetime = Field(
        ...,
        description='**Required, no default.** A link that never expires is a credential\nthe recipient can forward, lose, or keep after leaving the trip.\n',
    )
    email: str | None = Field(
        None,
        description="Optional. When present the invitation is delivered rather than\nreturned as a bare link. Not required, because a traveller sharing a\nplan with a friend should not have to surrender the friend's address.\n",
    )


class InvitationCreated(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    invitation_id: str
    role: str
    expires_at: AwareDatetime
    token: str = Field(
        ...,
        description='**Returned once, here, and never readable again.** A collaboration\nlink retrievable from an API is a collaboration link an attacker\nretrieves too. Losing it means revoking and reissuing, which is cheap.\n',
    )


class BookingStatus(StrEnum):
    """
    **Distinct states, not a boolean.** `REQ-EVID-003` forbids rendering an
    estimate as confirmed, and a boolean `is_confirmed` makes the two the same
    field with different values — which is how a default of `false` becomes a
    default of `true` in someone's mapper. Three named states also leave room
    for `cancelled`, which a boolean cannot express at all.

    """

    estimated = 'estimated'
    confirmed = 'confirmed'
    cancelled = 'cancelled'


class CreateBookingHandoffRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    item_id: str
    preferred_provider_id: str | None = None


class CopyableBookingDetails(BaseModel):
    """
    What the traveller needs to complete the booking **themselves** when the
    affiliate is unreachable (`REQ-BOOK-004`). A dead deep link must never be
    a dead end.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    provider_name: str = Field(
        ...,
        description="Display name only. The provider's internal identity is commercially\nconfidential and is never returned (`ERROR_MODEL.md` §5).\n",
    )
    reference_hint: str | None = None
    booking_url: str | None = None


class OfflineManifestEntry(BaseModel):
    kind: str
    uri: str
    bytes: int | None = Field(None, ge=0)


class Readiness(BaseModel):
    """
    What is and is not ready, itemised. A blank refusal to activate tells
    a traveller at an airport nothing they can act on.

    """

    ready: bool
    blocking: list[str] | None = None


class Manifest(BaseModel):
    entries: list[OfflineManifestEntry]


class ActivationResult(BaseModel):
    """
    The offline manifest is **extensible on purpose**. Its exact shape depends
    on device constraints STEP-017 has not established, and freezing a guess
    now would make the correction a breaking change. Typed entries plus room
    to grow.

    """

    activated: bool
    readiness: Readiness = Field(
        ...,
        description='What is and is not ready, itemised. A blank refusal to activate tells\na traveller at an airport nothing they can act on.\n',
    )
    manifest: Manifest


class Effort(StrEnum):
    low = 'low'
    medium = 'medium'
    high = 'high'


class Subject(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    kind: str
    id: str


class Sentiment(StrEnum):
    """
    Explicit only. Every value here was chosen by a person; nothing infers
    one from behaviour (`REQ-PRIV-003`).

    """

    positive = 'positive'
    negative = 'negative'
    mixed = 'mixed'


class ConsentScope(StrEnum):
    """
    **Required.** Feedback is training signal, and using it without a
    stated scope is using someone's trip to improve a model they did not
    agree to improve. The narrowest option is the first one.

    """

    this_trip_only = 'this_trip_only'
    improve_my_trips = 'improve_my_trips'
    improve_the_product = 'improve_the_product'


class FeedbackRequest(BaseModel):
    """
    **No field records the absence of feedback.** The moment one exists,
    something treats silence as dissatisfaction — and a traveller who simply
    got on with their holiday is not an unhappy one.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    subject: Subject
    sentiment: Sentiment = Field(
        ...,
        description='Explicit only. Every value here was chosen by a person; nothing infers\none from behaviour (`REQ-PRIV-003`).\n',
    )
    comment: str | None = Field(None, max_length=2000)
    consent_scope: ConsentScope = Field(
        ...,
        description="**Required.** Feedback is training signal, and using it without a\nstated scope is using someone's trip to improve a model they did not\nagree to improve. The narrowest option is the first one.\n",
    )


class FeedbackRecord(BaseModel):
    feedback_id: str
    recorded_at: AwareDatetime
    consent_scope: str


class Kind(StrEnum):
    export = 'export'
    correction = 'correction'
    consent_withdrawal = 'consent_withdrawal'
    deletion = 'deletion'


class PrivacyRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    kind: Kind
    subject_confirmation: str | None = Field(
        None,
        description='Required by the handler when `kind` is `deletion`. Declared optional\nhere because the contract cannot express that conditional without\na conditional that generated clients render badly; the handler\nenforces it and `TST-PRIV-005` will assert it. Stated rather than left\nas an apparent hole.\n',
    )
    correction: dict[str, Any] | None = Field(
        None, description='Field-level corrections. Used when `kind` is `correction`.\n'
    )


class Store(StrEnum):
    primary = 'primary'
    object = 'object'
    vector = 'vector'
    graph = 'graph'
    cache = 'cache'
    export = 'export'
    token = 'token'


class State(StrEnum):
    pending = 'pending'
    complete = 'complete'
    retrying = 'retrying'
    failed = 'failed'


class PrivacyStoreStatus(BaseModel):
    """
    Per-store progress. `REQ-PRIV-006` requires deletion to traverse primary,
    object, vector, graph, cache, export and token stores — so the record
    names them individually. **A subject who asked for deletion must be able
    to see which stores are still outstanding**, not a single boolean that is
    true when the easy ones finished.

    """

    store: Store
    state: State


class State1(StrEnum):
    """
    `partially_failed` exists deliberately. A deletion that finished six
    of seven stores is not complete, and calling it complete is the exact
    failure `REQ-PRIV-007` guards against.

    """

    accepted = 'accepted'
    in_progress = 'in_progress'
    complete = 'complete'
    partially_failed = 'partially_failed'


class PrivacyRequestRecord(BaseModel):
    request_id: str
    kind: str
    state: State1 = Field(
        ...,
        description='`partially_failed` exists deliberately. A deletion that finished six\nof seven stores is not complete, and calling it complete is the exact\nfailure `REQ-PRIV-007` guards against.\n',
    )
    stores: list[PrivacyStoreStatus]
    created_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    export_url: str | None = Field(
        None,
        description="Present for a completed export. Expiring, single-use; a permanent link\nto someone's entire trip history is a credential.\n",
    )


class EvidenceItem(BaseModel):
    description: str
    url: str | None = None


class EvidenceOverrideRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    fact_id: str
    value: Any
    reason: str = Field(
        ...,
        description='**Required, with a minimum length.** An override with no stated reason\nis indistinguishable from a mistake six months later, and "fix" is not\na reason.\n',
        min_length=10,
    )
    effective_from: AwareDatetime
    effective_to: AwareDatetime | None = None
    evidence: list[EvidenceItem] = Field(
        ...,
        description='What the curator is relying on. A fact override with no supporting\nevidence is an opinion overwriting a source.\n',
        min_length=1,
    )


class Status2(StrEnum):
    """
    **Set by the server, not requested.** A high-impact override is
    created `pending_approval` and takes effect only when a second curator
    approves it — a caller that could choose `active` would be a caller
    that could skip four-eyes.

    """

    active = 'active'
    pending_approval = 'pending_approval'
    rejected = 'rejected'


class ImpactPreview(BaseModel):
    """
    Which scenarios this would change, before it takes effect. An override
    whose consequences are invisible until applied is one nobody can
    review.

    """

    affected_scenario_count: int = Field(..., ge=0)
    affected_trip_count: int | None = Field(None, ge=0)


class EvidenceOverride(BaseModel):
    override_id: str
    status: Status2 = Field(
        ...,
        description='**Set by the server, not requested.** A high-impact override is\ncreated `pending_approval` and takes effect only when a second curator\napproves it — a caller that could choose `active` would be a caller\nthat could skip four-eyes.\n',
    )
    impact_preview: ImpactPreview = Field(
        ...,
        description='Which scenarios this would change, before it takes effect. An override\nwhose consequences are invisible until applied is one nobody can\nreview.\n',
    )
    approver_required: bool | None = Field(
        None, description='True when four-eyes applies.'
    )


class Freshness(StrEnum):
    current = 'current'
    degraded = 'degraded'
    stale = 'stale'


class CoverageRegion(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    region_id: str
    display_name: str
    date_bounds: LocalDateRange
    freshness: Freshness
    limitations: list[str] | None = Field(
        None,
        description='Documented honestly. `REQ-TRIP-002` wants an honest scope statement,\nand "ferry timetables are seasonal and change monthly" is worth more\nto a traveller than a green tick.\n',
    )


class ProviderHealth(StrEnum):
    """
    An aggregate. Never a list, never named, never a count — each of those
    leaks the shape of the supply chain.

    """

    healthy = 'healthy'
    degraded = 'degraded'
    unavailable = 'unavailable'


class Coverage(BaseModel):
    """
    **Public. Contains no provider identity and no quota detail**
    (`REQ-EVID-006`).

    Which supplier backs a region is commercially confidential, and how close
    a provider is to its quota tells an attacker precisely when the product
    degrades. This answers *what is supported*, never *how it is supplied* —
    which is why `provider_health` is one aggregate label rather than a
    per-provider breakdown, and why the schema is **closed**.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    regions: list[CoverageRegion]
    provider_health: ProviderHealth = Field(
        ...,
        description='An aggregate. Never a list, never named, never a count — each of those\nleaks the shape of the supply chain.\n',
    )


class Event(StrEnum):
    heartbeat = 'heartbeat'
    progress = 'progress'
    warning = 'warning'
    result = 'result'
    error = 'error'


class ZonedTimestamp(BaseModel):
    """
    An instant plus the IANA zone it should be read in. Both, because a trip
    in Tokyo is read in Tokyo time by a traveller sitting in London, and
    because a calendar day is not always 24 hours long — DST correctness is a
    feasibility concern, not a formatting one.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    instant: AwareDatetime = Field(
        ..., description='RFC 3339, UTC.', examples=['2026-03-29T01:30:00Z']
    )
    time_zone: str = Field(
        ..., description='IANA identifier.', examples=['Europe/London']
    )


class ErrorCode(RootModel[ErrorCodes]):
    root: ErrorCodes


class Problem(BaseModel):
    """
    RFC 9457 problem details. Every failure the API reports has this shape and
    is served as `application/problem+json`.

    **What is never here:** another tenant's data, a stack trace, a provider
    identity, or any request content. `ERROR_MODEL.md` §5 states these
    prohibitions and `conventions/problem.py` enforces them — a detail string
    containing a traceback, connection string, credential or email address
    raises rather than being redacted, because a silently-truncated message
    still ships.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    type: AnyUrl = Field(
        ...,
        description='Stable URI, derived from `code`. **Never changes meaning once\npublished** — changing it would require changing the code, which is\nalready a breaking change under CONTRACT_CHANGE_POLICY.\n',
        examples=['https://journeylab.app/problems/solver.infeasible'],
    )
    title: str = Field(
        ...,
        description='Short, human-readable summary. Stable per code.',
        examples=['No feasible schedule exists'],
    )
    status: int = Field(..., examples=[422], ge=100, le=599)
    code: ErrorCode
    detail: str | None = Field(
        None,
        description='Safe to display. Optional: an error with nothing specific to add omits\nit rather than repeating the title.\n',
    )
    instance: str | None = Field(
        None,
        description='The request path that produced this problem.',
        examples=['/v1/trips/trp_01/scenarios:generate'],
    )
    correlation_id: str = Field(
        ...,
        description='Always present. `ERROR_MODEL.md` calls it "the single thing support\nneeds"; an optional correlation ID is absent from exactly the\nresponses anyone wants to investigate.\n',
        examples=['corr_9f3c2a1b4d5e6f70'],
    )
    retryable: bool = Field(
        ...,
        description='**Explicit, never inferred from the status.** A 503 from a degraded\nprovider is retryable; a 503 because the region is unsupported is not,\nand only the register knows which.\n',
    )
    remediation: Remediation | None = Field(
        None,
        description='A structured, actionable next step where one exists. The design\nprinciple behind the whole error model: an error must tell the user\nwhat to do next. "Something went wrong" is not an error model, it is\nan apology.\n\n**Only `kind` is fixed here; the rest is the specific error\'s shape.**\nSTEP-004.01 declared this with a guessed payload — `conflict_set` and\n`relaxations` as arrays of strings — before any operation needed one.\nSTEP-004.02 then needed relaxations that name the constraint they\nrelax, because "depart at 15:00 instead" is not actionable unless the\nreader knows which of three constraints it addresses. The guess was\nwrong and the example caught it.\n\nComposing responses narrow this: see `ConflictSet` and the\n`Infeasible` response.\n',
    )


class ScenarioSummary(BaseModel):
    scenario_id: str
    label: str
    feasible: bool = Field(
        ...,
        description='Always true for a returned scenario. Present so the field exists in\nthe contract before STEP-019 introduces a scenario that becomes\ninfeasible after a condition change.\n',
    )
    metrics: dict[str, Any] = Field(
        ..., description='Comparison metrics. Money is always `Money`, never a number.'
    )
    total_cost: Money | None = None


class ItineraryItem(BaseModel):
    item_id: str
    kind: str
    title: str | None = None
    starts_at: ZonedTimestamp
    ends_at: ZonedTimestamp
    cost: Money | None = None
    opening_hours: Evidenced | None = None
    travel_minutes: Evidenced | None = None
    protected: bool | None = Field(
        None,
        description='Booked or pinned. An edit touching a protected item is refused until\nthe user explicitly unlocks it (`REQ-CONS-011`).\n',
    )


class Scenario(BaseModel):
    scenario_id: str
    trip_id: str
    version: int = Field(..., ge=1)
    brief_version: int = Field(
        ...,
        description='The exact brief this was solved against. Reproducibility needs it\n(`REQ-CONS-006`), and a scenario whose brief has moved on is stale\nrather than wrong.\n',
    )
    evidence_pack_id: str
    random_seed: int | None = None
    items: list[ItineraryItem]
    score_components: dict[str, Any] | None = None


class BookingHandoff(BaseModel):
    """
    **There is no payment field here, and there is none anywhere in this
    contract.** JourneyLab deep-links to the provider; it never takes a
    payment. PCI scope you never enter is scope you cannot leak, and the
    absence of a field is what makes that structural rather than intended.

    """

    model_config = ConfigDict(
        extra='forbid',
    )
    handoff_id: str
    item_id: str
    booking_status: BookingStatus
    deep_link: str | None = None
    price: Money | None = None
    copyable_details: CopyableBookingDetails | None = None
    booking_reference: str | None = Field(
        None,
        description="The provider's own reference, once they confirm. An opaque string we\nstore and display — never a credential, and never anything that could\nbe used to act on the traveller's behalf.\n",
    )


class Deltas(BaseModel):
    cost: Money
    minutes: int
    effort: Effort | None = None


class RepairOption(BaseModel):
    """
    One alternative, with what it costs. **Generating this changes nothing** —
    acceptance is a separate call.

    """

    repair_id: str
    summary: str | None = None
    preserved_plan_percent: float = Field(
        ...,
        description='How much of the existing plan survives. The number a traveller\nactually cares about mid-trip: "you keep 80% of your afternoon" is a\ndecision they can make in thirty seconds.\n',
        ge=0.0,
        le=100.0,
    )
    deltas: Deltas
    touches_protected_items: bool | None = Field(
        None,
        description='True when applying this needs an explicit unlock first\n(`REQ-CONS-011`). Surfaced on the option so the traveller learns it\nbefore choosing, not after.\n',
    )


class JobEvent(BaseModel):
    """
    One server-sent event. `heartbeat` is not filler: without it a client
    cannot tell a job that is thinking from a connection that died.

    """

    event: Event
    job_id: str
    sequence: int = Field(
        ...,
        description='Monotonic, so a client that reconnects can tell whether it missed\nanything rather than assuming it did not.\n',
    )
    progress_percent: float | None = Field(None, ge=0.0, le=100.0)
    message: str | None = None
    problem: Problem | None = None
