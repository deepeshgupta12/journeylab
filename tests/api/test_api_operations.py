"""Trip, brief and scenario operations — TST-PLAT-005, TST-CONS-005 · STEP-004.02.

These assert properties of the CONTRACT, before any handler exists. That is the
point of contract-first: a promise that is only checked once code implements it
is a promise nobody has read.

The valuable assertions are the ones that would let a defect through if absent —
an operation that forgets `Idempotency-Key`, an infeasibility response without a
conflict set, a volatile value returned as a bare number.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest
import yaml
from conventions.error_codes import CLIENT_VISIBLE

REPO = pathlib.Path(__file__).resolve().parents[2]
SPEC: dict[str, Any] = yaml.safe_load((REPO / "contracts/openapi.yaml").read_text())
PATHS: dict[str, Any] = SPEC["paths"]

#: Operations that change state. Every one needs an idempotency key.
MUTATING = {"post", "put", "patch", "delete"}


def operations() -> list[tuple[str, str, dict[str, Any]]]:
    return [
        (path, method, op)
        for path, item in PATHS.items()
        for method, op in item.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]


def param_names(op: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for p in op.get("parameters", []):
        ref = p.get("$ref")
        if ref:
            names.add(ref.rsplit("/", 1)[-1])
        elif "name" in p:
            names.add(p["name"])
    return names


class TestEveryOperationIsWellFormed:
    def test_the_planning_operations_are_declared(self) -> None:
        """A SUBSET assertion, not an exhaustive one.

        The first version asserted set equality against exactly the nine
        operations STEP-004.02 added, and STEP-004.03 broke it by adding five
        more — correctly. An exhaustive assertion on a growing surface fails on
        every legitimate addition, which teaches whoever hits it to edit the test
        without reading it.

        What is durable is that these nine exist. The conventions tests below
        cover whatever else arrives.
        """
        ids = {op["operationId"] for _, _, op in operations()}
        assert {
            "createTrip",
            "getTrip",
            "replaceTripBrief",
            "buildEvidencePack",
            "generateScenarios",
            "listScenarios",
            "getScenario",
            "selectScenario",
            "editScenario",
        } <= ids

    def test_operation_ids_are_unique(self) -> None:
        """Two operations sharing an id generate one client method that silently
        calls the wrong endpoint (STEP-004.07 generates from this document)."""
        ids = [op["operationId"] for _, _, op in operations()]
        assert len(ids) == len(set(ids)), f"duplicate operationIds: {sorted(ids)}"

    @pytest.mark.parametrize(("path", "method", "op"), operations(), ids=lambda v: str(v)[:40])
    def test_has_an_operation_id_and_a_summary(
        self, path: str, method: str, op: dict[str, Any]
    ) -> None:
        assert op.get("operationId"), f"{method} {path} has no operationId"
        assert op.get("summary"), f"{method} {path} has no summary"

    def test_every_operation_can_report_a_problem(self) -> None:
        """An operation with only success responses is an operation nobody has
        thought about failing."""
        for path, method, op in operations():
            statuses = set(op["responses"])
            assert statuses - {"200", "201", "202"}, (
                f"{method} {path} declares no failure response at all"
            )


class TestIdempotency:
    """`API_CONTRACTS.md` §1: required on EVERY state-changing command."""

    def test_every_mutating_operation_requires_an_idempotency_key(self) -> None:
        missing = [
            f"{method.upper()} {path}"
            for path, method, op in operations()
            if method in MUTATING and "IdempotencyKey" not in param_names(op)
        ]
        assert not missing, f"state-changing operations without Idempotency-Key: {missing}"

    def test_no_read_operation_demands_one(self) -> None:
        """A GET that requires an idempotency key is a GET somebody copied."""
        wrong = [
            path
            for path, method, op in operations()
            if method == "get" and "IdempotencyKey" in param_names(op)
        ]
        assert not wrong, f"read operations requiring Idempotency-Key: {wrong}"


class TestConcurrency:
    def test_operations_that_replace_state_require_if_match(self) -> None:
        """Replacing a brief or editing a scenario must state which version."""
        for op_id in ("replaceTripBrief", "generateScenarios", "editScenario"):
            op = next(o for _, _, o in operations() if o["operationId"] == op_id)
            assert "IfMatch" in param_names(op), f"{op_id} does not require If-Match"

    def test_readable_resources_return_an_etag(self) -> None:
        """You cannot send `If-Match` for a version you were never given."""
        for op_id in ("createTrip", "getTrip", "replaceTripBrief", "getScenario"):
            op = next(o for _, _, o in operations() if o["operationId"] == op_id)
            ok = next(body for status, body in op["responses"].items() if status.startswith("2"))
            assert "ETag" in ok.get("headers", {}), f"{op_id} returns no ETag"


class TestEnumeration:
    """REQ-SEC-004 — the reason 403 and 404 are one response."""

    def test_every_resource_scoped_operation_uses_the_shared_denial(self) -> None:
        for path, method, op in operations():
            if "{" not in path:
                continue  # collection-level; nothing to enumerate
            responses = op["responses"]
            assert "404" in responses, f"{method} {path} declares no 404"
            assert responses["404"].get("$ref", "").endswith("NotFoundOrForbidden"), (
                f"{method} {path} defines its own 404 instead of reusing the shared "
                f"indistinguishable denial — that is how an existence oracle returns"
            )

    def test_no_operation_declares_a_bare_403(self) -> None:
        """A 403 discloses that something is there to be forbidden."""
        offenders = [
            f"{method.upper()} {path}"
            for path, method, op in operations()
            if "403" in op["responses"]
        ]
        assert not offenders, f"operations declaring 403: {offenders}"


class TestInfeasibilityIsAProductState:
    """TST-CONS-005 — REQ-CONS-005."""

    def test_the_infeasible_response_requires_a_conflict_set(self) -> None:
        schema = SPEC["components"]["responses"]["Infeasible"]["content"][
            "application/problem+json"
        ]["schema"]
        overlay = schema["allOf"][1]
        assert overlay["required"] == ["remediation"], (
            "the infeasible response must require remediation — an infeasibility "
            "with no explanation is the bare error REQ-CONS-005 forbids"
        )

    def test_a_conflict_set_needs_at_least_two_constraints(self) -> None:
        """A single constraint cannot conflict with itself.

        A one-item set means the solver failed to explain, not that it found a
        minimal cause — and shipping that would let 'infeasible: your dates' pass
        as a conflict set.
        """
        assert (
            SPEC["components"]["schemas"]["ConflictSet"]["properties"]["conflicts"]["minItems"] == 2
        )

    def test_the_example_carries_a_real_conflict_set(self) -> None:
        example = SPEC["components"]["responses"]["Infeasible"]["content"][
            "application/problem+json"
        ]["example"]
        assert example["code"] == "solver.infeasible"
        assert len(example["remediation"]["conflicts"]) >= 2
        assert example["remediation"]["relaxations"], (
            "the example should show relaxations — they are what make the screen "
            "actionable rather than merely honest"
        )

    def test_operations_that_can_be_infeasible_use_the_shared_response(self) -> None:
        for op_id in ("replaceTripBrief", "generateScenarios", "editScenario"):
            op = next(o for _, _, o in operations() if o["operationId"] == op_id)
            assert op["responses"]["422"].get("$ref", "").endswith("Infeasible"), (
                f"{op_id} defines its own 422 instead of the shared conflict-set shape"
            )


class TestEvidence:
    """REQ-EVID-001 and REQ-EVID-003."""

    def test_a_volatile_value_cannot_be_returned_bare(self) -> None:
        """Provenance is required by the TYPE, not by convention.

        STEP-004.06 recomposed `Evidenced` from the shared `Provenance` and
        `TemporalValidity` schemas rather than restating source, confidence and
        the time axes inline. The requirement is unchanged and the enforcement is
        stronger: three schemas cannot drift apart when there is one of each.
        """
        ev = SPEC["components"]["schemas"]["Evidenced"]
        assert set(ev["required"]) == {"value", "status", "provenance", "validity"}

        provenance = json.loads(
            (REPO / "contracts" / ev["properties"]["provenance"]["$ref"][2:]).read_text()
        )
        assert {"source", "confidence", "access_label"} <= set(provenance["required"])

        validity = json.loads(
            (REPO / "contracts" / ev["properties"]["validity"]["$ref"][2:]).read_text()
        )
        assert {"observed_at", "effective_from"} <= set(validity["required"])

    def test_status_has_no_default(self) -> None:
        """REQ-EVID-003: an estimate is never rendered as confirmed.

        A default would let a caller omit it and get 'confirmed' for free.
        """
        status = SPEC["components"]["schemas"]["Evidenced"]["properties"]["status"]
        assert status["enum"] == ["confirmed", "estimated"]
        assert "default" not in status

    def test_conflicting_sources_are_retained_not_averaged(self) -> None:
        """REQ-EVID-002. The mean of two departure times is a time no ferry leaves.

        BUG-020: this test used to assert only that the `conflicts` KEY existed.
        It passed while each entry's source was `{type: object}` — an object with
        no declared properties, which generated as `Record<string, never>`. A
        retained conflict that cannot name its source or say when it was observed
        satisfies the letter of REQ-EVID-002 and none of its purpose.

        So the assertion is now about substance. Attribution and the time axes are
        what make a disagreement actionable: without provenance nobody can weigh
        it, and without validity a value that simply CHANGED is indistinguishable
        from two sources that DISAGREE.
        """
        conflicts = SPEC["components"]["schemas"]["Evidenced"]["properties"]["conflicts"]
        entry = conflicts["items"]

        assert set(entry["required"]) == {"value", "provenance", "validity"}
        assert entry["additionalProperties"] is False

        # Composed from the same shared schemas as the primary claim, not restated.
        # A conflicting source described by a different shape is one that drifts.
        assert entry["properties"]["provenance"]["$ref"].endswith("provenance.json")
        assert entry["properties"]["validity"]["$ref"].endswith("temporal-validity.json")

        provenance = json.loads(
            (REPO / "contracts" / entry["properties"]["provenance"]["$ref"][2:]).read_text()
        )
        assert "access_label" in provenance["required"], (
            "a conflicting value may come from an internal_only source; the "
            "interface must be able to plan with it without displaying it"
        )

    def test_the_itinerary_uses_evidenced_for_volatile_fields(self) -> None:
        item = SPEC["components"]["schemas"]["ItineraryItem"]["properties"]
        for field in ("opening_hours", "travel_minutes"):
            assert item[field]["$ref"].endswith("Evidenced"), (
                f"{field} is volatile and must carry its evidence"
            )


class TestMoneyAndTime:
    def test_costs_are_money_never_numbers(self) -> None:
        schemas = SPEC["components"]["schemas"]
        assert schemas["ItineraryItem"]["properties"]["cost"]["$ref"].endswith("Money")
        assert schemas["ScenarioSummary"]["properties"]["total_cost"]["$ref"].endswith("Money")

    def test_itinerary_times_carry_their_zone(self) -> None:
        """A departure without a zone is a departure in the reader's zone."""
        item = SPEC["components"]["schemas"]["ItineraryItem"]["properties"]
        for field in ("starts_at", "ends_at"):
            assert item[field]["$ref"].endswith("ZonedTimestamp")

    def test_trip_dates_are_local_dates_not_instants(self) -> None:
        """DATA-004: a trip starting '12 September' starts on the 12th wherever
        the traveller is."""
        rng = SPEC["components"]["schemas"]["LocalDateRange"]["properties"]
        assert rng["start"]["format"] == "date"
        assert rng["end"]["format"] == "date"


class TestBriefStructure:
    def test_four_collections_not_a_typed_union(self) -> None:
        """DATA-005. A union invites code that forgets to branch."""
        brief = SPEC["components"]["schemas"]["TripBrief"]
        for name in ("hard", "soft", "inferred", "unresolved"):
            assert name in brief["properties"], f"{name} missing"
            assert name in brief["required"], f"{name} must be required"


class TestPrivacy:
    def test_accessibility_needs_are_declared_never_inferred(self) -> None:
        """REQ-PRIV-003. The field exists only because the traveller filled it in."""
        party = SPEC["components"]["schemas"]["Party"]
        assert "accessibility_needs" in party["properties"]
        description = party["properties"]["accessibility_needs"]["description"]
        assert "never inferred" in description.lower()

    def test_the_party_schema_is_closed(self) -> None:
        """An open object lets an undeclared sensitive attribute in."""
        assert SPEC["components"]["schemas"]["Party"].get("additionalProperties") is False


class TestExamplesAreValid:
    """TST-PLAT-005 — examples must validate against their schemas."""

    def _resolve(self, node: Any) -> Any:
        """Inline every `$ref`, including the external one.

        `ErrorCode` is `$ref: './schemas/error-codes.json'` — deliberately
        external, because inlining the enum in the OpenAPI file would be a second
        source of truth for a list that is generated. The validator has no
        retriever configured, so the reference has to be followed here; without
        this the example tests fail on `Unresolvable` and prove nothing about
        the examples.
        """
        import json

        if isinstance(node, dict):
            ref = node.get("$ref")
            if ref and ref.startswith("#/"):
                target: Any = SPEC
                for part in ref.lstrip("#/").split("/"):
                    target = target[part]
                return self._resolve(target)
            if ref and ref.startswith("./"):
                external = json.loads((REPO / "contracts" / ref[2:]).read_text())
                # Drop the meta-keywords; only the constraint matters here.
                return {k: v for k, v in external.items() if not k.startswith("$")}
            return {k: self._resolve(v) for k, v in node.items()}
        if isinstance(node, list):
            return [self._resolve(v) for v in node]
        return node

    def test_every_declared_example_validates(self) -> None:
        jsonschema = pytest.importorskip("jsonschema")
        checked = 0
        for _path, _method, op in operations():
            bodies = [op.get("requestBody", {}), *op["responses"].values()]
            for body in bodies:
                for media in body.get("content", {}).values():
                    example = media.get("example")
                    if example is None or "schema" not in media:
                        continue
                    jsonschema.validate(example, self._resolve(media["schema"]))
                    checked += 1
        assert checked >= 3, f"only {checked} examples found — the walk is wrong"

    def test_shared_response_examples_validate(self) -> None:
        jsonschema = pytest.importorskip("jsonschema")
        for name in ("NotFoundOrForbidden", "Infeasible"):
            media = SPEC["components"]["responses"][name]["content"]["application/problem+json"]
            jsonschema.validate(media["example"], self._resolve(media["schema"]))

    def test_every_example_error_code_is_registered(self) -> None:
        """An example naming a code the server cannot send is a lie in the contract."""
        import re

        raw = (REPO / "contracts/openapi.yaml").read_text()
        for code in re.findall(r"code: '([a-z][a-z0-9_.]+)'", raw):
            assert code in CLIENT_VISIBLE, f"example uses unregistered code {code!r}"


# ============================================================================
# STEP-004.03 — collaboration, booking, live and feedback
# ============================================================================


class TestNoPaymentCredentialAnywhere:
    """TST-BOOK-002 — and this is the assertion I would keep if I could keep one.

    JourneyLab deep-links to providers and never takes a payment. The way that
    stops being an intention and becomes a fact is that **no schema in the
    contract has anywhere to put a card number.** PCI scope you never enter is
    scope you cannot leak.

    Scanned across the whole document rather than reviewed, because review is
    what fails on the eighteenth operation added two years from now.
    """

    #: Field names that would mean a payment credential had entered the contract.
    FORBIDDEN = (
        "card_number",
        "cardnumber",
        "pan",
        "cvv",
        "cvc",
        "card_cvc",
        "security_code",
        "expiry_month",
        "expiry_year",
        "cardholder",
        "card_holder",
        "iban",
        "bic",
        "swift",
        "sort_code",
        "account_number",
        "routing_number",
        "payment_token",
        "payment_method_id",
        "stripe_token",
        "billing_address",
    )

    def _all_property_names(self, node: Any, found: set[str] | None = None) -> set[str]:
        found = set() if found is None else found
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    found |= set(value)
                self._all_property_names(value, found)
        elif isinstance(node, list):
            for item in node:
                self._all_property_names(item, found)
        return found

    def test_no_schema_declares_a_payment_field(self) -> None:
        names = {n.lower() for n in self._all_property_names(SPEC)}
        assert names, "found no properties at all — the walk is broken, not the contract"
        offenders = sorted(names & set(self.FORBIDDEN))
        assert not offenders, (
            f"the contract declares payment-credential fields: {offenders}. "
            f"JourneyLab hands off to the provider and never takes a payment; the "
            f"absence of a field is what keeps that true."
        )

    def test_the_walk_would_actually_find_one(self) -> None:
        """Proves the scan above is not vacuous.

        A test that searches for something absent passes identically when the
        search is broken. This one seeds a payment field into a copy of the
        document and requires the same walk to find it.
        """
        seeded: dict[str, Any] = {
            "components": {"schemas": {"Evil": {"properties": {"card_number": {}}}}}
        }
        assert "card_number" in {n.lower() for n in self._all_property_names(seeded)}

    def test_the_booking_handoff_is_a_closed_object(self) -> None:
        """An open object is somewhere a card number can arrive undeclared."""
        assert SPEC["components"]["schemas"]["BookingHandoff"]["additionalProperties"] is False


class TestBookingStates:
    def test_estimated_and_confirmed_are_states_not_a_boolean(self) -> None:
        """REQ-EVID-003.

        A boolean `is_confirmed` makes an estimate and a confirmation the same
        field with different values, which is how a default of `false` becomes a
        default of `true` in somebody's mapper. Three named states also express
        `cancelled`, which a boolean cannot.
        """
        status = SPEC["components"]["schemas"]["BookingStatus"]
        assert status["type"] == "string"
        assert set(status["enum"]) == {"estimated", "confirmed", "cancelled"}

    def test_no_boolean_confirmation_flag_exists(self) -> None:
        names = {n.lower() for n in TestNoPaymentCredentialAnywhere()._all_property_names(SPEC)}
        for flag in ("is_confirmed", "confirmed", "is_estimated"):
            assert flag not in names, f"{flag!r} reintroduces the boolean this forbids"

    def test_an_unreachable_affiliate_is_not_a_dead_end(self) -> None:
        """REQ-BOOK-004: the traveller can still complete the booking."""
        assert "copyable_details" in SPEC["components"]["schemas"]["BookingHandoff"]["properties"]
        details = SPEC["components"]["schemas"]["CopyableBookingDetails"]
        assert "provider_name" in details["required"]


class TestRepairGenerationIsSeparateFromAcceptance:
    """TST-LIVE-005."""

    def test_they_are_two_operations(self) -> None:
        ids = {op["operationId"] for _, _, op in operations()}
        assert {"generateRepairs", "acceptRepair"} <= ids

    def test_generation_does_not_require_if_match(self) -> None:
        """Because it changes nothing.

        Requiring a version precondition on a read-only projection would imply it
        mutates — and the next person to touch it would make that true.
        """
        gen = next(o for _, _, o in operations() if o["operationId"] == "generateRepairs")
        assert "IfMatch" not in param_names(gen)

    def test_acceptance_does_require_if_match(self) -> None:
        """Because it is the one operation that changes a live plan."""
        accept = next(o for _, _, o in operations() if o["operationId"] == "acceptRepair")
        assert "IfMatch" in param_names(accept)

    def test_a_repair_option_declares_what_it_costs(self) -> None:
        option = SPEC["components"]["schemas"]["RepairOption"]
        assert set(option["required"]) >= {"repair_id", "preserved_plan_percent", "deltas"}
        assert option["properties"]["deltas"]["properties"]["cost"]["$ref"].endswith("Money")

    def test_a_repair_says_when_it_needs_an_unlock(self) -> None:
        """REQ-CONS-011 — surfaced before the choice, not after."""
        assert (
            "touches_protected_items" in SPEC["components"]["schemas"]["RepairOption"]["properties"]
        )


class TestInvitations:
    def test_expiry_is_required_with_no_default(self) -> None:
        """A link that never expires is a credential someone keeps after leaving."""
        req = SPEC["components"]["schemas"]["CreateInvitationRequest"]
        assert "expires_at" in req["required"]
        assert "default" not in req["properties"]["expires_at"]

    def test_an_invitation_cannot_confer_ownership(self) -> None:
        """Transferring a trip is a deliberate act, not a link you can forward."""
        roles = SPEC["components"]["schemas"]["CreateInvitationRequest"]["properties"]["role"]
        assert "trip_owner" not in roles["enum"]

    def test_the_token_is_returned_once(self) -> None:
        """It appears in the creation response and in no read operation."""
        assert "token" in SPEC["components"]["schemas"]["InvitationCreated"]["required"]
        read_ops = [op for _, method, op in operations() if method == "get"]
        for op in read_ops:
            body = str(op.get("responses", {}))
            assert "InvitationCreated" not in body, (
                f"{op['operationId']} can return an invitation token — a link an "
                f"API will hand back is a link an attacker asks for"
            )

    def test_revocation_exists_and_is_idempotent(self) -> None:
        revoke = next(o for _, _, o in operations() if o["operationId"] == "revokeInvitation")
        assert "204" in revoke["responses"]
        assert "IdempotencyKey" in param_names(revoke)


class TestFeedbackConsent:
    def test_consent_scope_is_required(self) -> None:
        """Feedback is training signal. Using it without a stated scope uses
        someone's trip to improve a model they did not agree to improve."""
        req = SPEC["components"]["schemas"]["FeedbackRequest"]
        assert "consent_scope" in req["required"]
        scope = req["properties"]["consent_scope"]
        assert scope["enum"][0] == "this_trip_only", "the narrowest scope should be first"

    def test_absence_of_feedback_cannot_be_recorded(self) -> None:
        """The moment a field exists for 'did not respond', something treats
        silence as dissatisfaction."""
        names = {
            n.lower()
            for n in TestNoPaymentCredentialAnywhere()._all_property_names(
                SPEC["components"]["schemas"]["FeedbackRequest"]
            )
        }
        for forbidden in ("no_response", "did_not_respond", "declined", "ignored", "dismissed"):
            assert forbidden not in names

    def test_sentiment_is_explicit_not_inferred(self) -> None:
        sentiment = SPEC["components"]["schemas"]["FeedbackRequest"]["properties"]["sentiment"]
        assert set(sentiment["enum"]) == {"positive", "negative", "mixed"}
        assert "inferred" not in str(sentiment).lower()


class TestPhase3OperationsStillObeyTheConventions:
    """The later operations are the ones most likely to drift from the rules.

    They are written furthest from the sub-step that set them, by whoever picks
    up Phase 3 — so the conventions are asserted across ALL operations, not
    re-checked per batch.
    """

    def test_every_operation_including_phase_3_uses_the_shared_denial(self) -> None:
        for path, method, op in operations():
            if "{" not in path:
                continue
            assert op["responses"]["404"].get("$ref", "").endswith("NotFoundOrForbidden"), (
                f"{method} {path} defines its own 404"
            )

    def test_no_operation_anywhere_declares_a_403(self) -> None:
        offenders = [f"{m.upper()} {p}" for p, m, op in operations() if "403" in op["responses"]]
        assert not offenders, offenders

    def test_every_mutating_operation_still_requires_idempotency(self) -> None:
        missing = [
            f"{m.upper()} {p}"
            for p, m, op in operations()
            if m in MUTATING and "IdempotencyKey" not in param_names(op)
        ]
        assert not missing, missing


# ============================================================================
# STEP-004.04 — privacy, admin, coverage and jobs
# ============================================================================


class TestPublicCoverageLeaksNothing:
    """TST-EVID-006 — the only unauthenticated operation in the contract."""

    def test_exactly_one_operation_is_public(self) -> None:
        """An unauthenticated endpoint is a decision, not an oversight.

        Global `security` requires a bearer token; an operation opts out by
        declaring `security: []`. Counting them is how a second one added by
        accident becomes visible.
        """
        public = [op["operationId"] for _, _, op in operations() if op.get("security") == []]
        assert public == ["getCoverage"], (
            f"unauthenticated operations: {public}. Exactly one is intended — a "
            f"traveller must be able to learn their destination is unsupported "
            f"without registering to be told no."
        )

    def test_coverage_is_a_closed_schema(self) -> None:
        """An open public response is where a provider name eventually appears."""
        assert SPEC["components"]["schemas"]["Coverage"]["additionalProperties"] is False
        assert SPEC["components"]["schemas"]["CoverageRegion"]["additionalProperties"] is False

    def test_provider_health_is_an_aggregate_not_a_breakdown(self) -> None:
        """REQ-EVID-006.

        A per-provider list names the supply chain; a count tells an attacker how
        many suppliers are degraded, which is when the product is weakest.
        """
        health = SPEC["components"]["schemas"]["Coverage"]["properties"]["provider_health"]
        assert health["type"] == "string"
        assert set(health["enum"]) == {"healthy", "degraded", "unavailable"}

    def test_no_provider_or_quota_field_reaches_the_public_response(self) -> None:
        names = {
            n.lower()
            for n in TestNoPaymentCredentialAnywhere()._all_property_names(
                {
                    "a": SPEC["components"]["schemas"]["Coverage"],
                    "b": SPEC["components"]["schemas"]["CoverageRegion"],
                }
            )
        }
        for leak in (
            "provider_id",
            "provider_name",
            "providers",
            "quota",
            "quota_remaining",
            "rate_limit",
            "supplier",
            "vendor",
        ):
            assert leak not in names, f"public coverage exposes {leak!r}"


class TestPrivacyRequestLifecycle:
    """TST-PRIV-005."""

    def test_all_four_request_kinds_are_specified(self) -> None:
        kinds = SPEC["components"]["schemas"]["PrivacyRequest"]["properties"]["kind"]["enum"]
        assert set(kinds) == {"export", "correction", "consent_withdrawal", "deletion"}

    def test_the_request_is_trackable_to_completion(self) -> None:
        """A deletion the subject cannot verify is a deletion they must trust."""
        ids = {op["operationId"] for _, _, op in operations()}
        assert {"createPrivacyRequest", "getPrivacyRequest"} <= ids

    def test_every_store_req_priv_006_names_is_tracked_individually(self) -> None:
        """A single boolean goes true when the easy stores finish.

        REQ-PRIV-006 requires deletion to traverse primary, object, vector,
        graph, cache, export and token stores. The record names each, so a
        subject can see which are outstanding.
        """
        stores = SPEC["components"]["schemas"]["PrivacyStoreStatus"]["properties"]["store"]
        assert set(stores["enum"]) == {
            "primary",
            "object",
            "vector",
            "graph",
            "cache",
            "export",
            "token",
        }

    def test_partial_failure_is_a_distinct_state(self) -> None:
        """REQ-PRIV-007. Six of seven stores is not 'complete'."""
        states = SPEC["components"]["schemas"]["PrivacyRequestRecord"]["properties"]["state"]
        assert "partially_failed" in states["enum"]
        assert "complete" in states["enum"]

    def test_acceptance_is_202_not_200(self) -> None:
        """The work continues after the response; saying otherwise is a lie the
        subject acts on."""
        op = next(o for _, _, o in operations() if o["operationId"] == "createPrivacyRequest")
        assert "202" in op["responses"]
        assert "200" not in op["responses"]


class TestFourEyesIsInTheContract:
    def test_the_server_sets_the_status_not_the_caller(self) -> None:
        """A caller that could request `active` could skip four-eyes."""
        request = SPEC["components"]["schemas"]["EvidenceOverrideRequest"]
        assert "status" not in request["properties"]
        assert request["additionalProperties"] is False

        response = SPEC["components"]["schemas"]["EvidenceOverride"]
        assert "pending_approval" in response["properties"]["status"]["enum"]

    def test_an_override_requires_a_reason_and_evidence(self) -> None:
        """A fact override with neither is an opinion overwriting a source."""
        request = SPEC["components"]["schemas"]["EvidenceOverrideRequest"]
        assert {"reason", "evidence"} <= set(request["required"])
        assert request["properties"]["reason"]["minLength"] >= 10, '"fix" is not a reason'
        assert request["properties"]["evidence"]["minItems"] >= 1

    def test_the_impact_is_previewable_before_it_applies(self) -> None:
        override = SPEC["components"]["schemas"]["EvidenceOverride"]
        assert "impact_preview" in override["required"]


class TestJobStreaming:
    def test_heartbeat_is_a_declared_event_type(self) -> None:
        """Without it, a client cannot tell a slow job from a dead connection."""
        events = SPEC["components"]["schemas"]["JobEvent"]["properties"]["event"]["enum"]
        assert "heartbeat" in events

    def test_warnings_are_carried_not_only_progress_and_result(self) -> None:
        """A generation that succeeded while three providers were degraded is not
        the same as one that succeeded cleanly (REQ-EVID-006)."""
        events = SPEC["components"]["schemas"]["JobEvent"]["properties"]["event"]["enum"]
        assert {"progress", "warning", "result", "error"} <= set(events)

    def test_the_stream_is_event_stream_not_json(self) -> None:
        op = next(o for _, _, o in operations() if o["operationId"] == "streamJobEvents")
        assert "text/event-stream" in op["responses"]["200"]["content"]

    def test_cancellation_exists_and_is_202(self) -> None:
        """A job mid-flight stops at a safe point; 204 would claim it already had."""
        op = next(o for _, _, o in operations() if o["operationId"] == "cancelJob")
        assert "202" in op["responses"]
        assert "204" not in op["responses"]

    def test_events_are_sequenced(self) -> None:
        """So a client that reconnects can tell whether it missed anything."""
        assert "sequence" in SPEC["components"]["schemas"]["JobEvent"]["properties"]
