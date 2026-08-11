"""Trip, brief and scenario operations — TST-PLAT-005, TST-CONS-005 · STEP-004.02.

These assert properties of the CONTRACT, before any handler exists. That is the
point of contract-first: a promise that is only checked once code implements it
is a promise nobody has read.

The valuable assertions are the ones that would let a defect through if absent —
an operation that forgets `Idempotency-Key`, an infeasibility response without a
conflict set, a volatile value returned as a bare number.
"""

from __future__ import annotations

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
    def test_all_nine_operations_are_declared(self) -> None:
        ids = {op["operationId"] for _, _, op in operations()}
        assert ids == {
            "createTrip",
            "getTrip",
            "replaceTripBrief",
            "buildEvidencePack",
            "generateScenarios",
            "listScenarios",
            "getScenario",
            "selectScenario",
            "editScenario",
        }

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
        """Provenance is required by the TYPE, not by convention."""
        ev = SPEC["components"]["schemas"]["Evidenced"]
        assert set(ev["required"]) == {"value", "status", "source", "observed_at", "confidence"}

    def test_status_has_no_default(self) -> None:
        """REQ-EVID-003: an estimate is never rendered as confirmed.

        A default would let a caller omit it and get 'confirmed' for free.
        """
        status = SPEC["components"]["schemas"]["Evidenced"]["properties"]["status"]
        assert status["enum"] == ["confirmed", "estimated"]
        assert "default" not in status

    def test_conflicting_sources_are_retained_not_averaged(self) -> None:
        """REQ-EVID-002. The mean of two departure times is a time no ferry leaves."""
        assert "conflicts" in SPEC["components"]["schemas"]["Evidenced"]["properties"]

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
