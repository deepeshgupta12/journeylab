"""The compatibility classifier — STEP-004.08 (REQ-PLAT-008).

WHAT THESE TESTS ARE REALLY CHECKING
    Not "does the differ notice a difference". Any diff notices differences. What
    matters is whether it reaches the RIGHT VERDICT, and the verdict depends on
    which side of the wire the schema sits on.

    Half of these cases exist as pairs: the same structural edit applied to a
    request schema and to a response schema, asserting **opposite** severities.
    A classifier that ignored direction would pass one of each pair and fail the
    other, and a classifier that reported everything as breaking would pass all the
    breaking cases and fail every additive one. Neither can pass the pairs.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from contract_diff import (  # noqa: E402
    Position,
    Severity,
    _described_properties,
    check_deprecation_metadata,
    diff_contracts,
    major_of,
    schema_positions,
    semantic_review,
)

JsonDict = dict[str, Any]


# --- document builders --------------------------------------------------------
#
# Built rather than loaded from a fixture file: a fixture large enough to exercise
# both directions would be harder to read than the code under test, and a reader
# could not tell which part of it a given assertion depended on.


def doc_with_request(schema: JsonDict, *, version: str = "1.0.0") -> JsonDict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": version},
        "paths": {
            "/things": {
                "post": {
                    "operationId": "createThing",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}
                        },
                    },
                    "responses": {"201": {"description": "created"}},
                }
            }
        },
        "components": {"schemas": {"Thing": schema}},
    }


def doc_with_response(schema: JsonDict, *, version: str = "1.0.0") -> JsonDict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": version},
        "paths": {
            "/things": {
                "get": {
                    "operationId": "listThings",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Thing"}
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {"schemas": {"Thing": schema}},
    }


def severities(old: JsonDict, new: JsonDict, kind: str) -> list[Severity]:
    return [c.severity for c in diff_contracts(old, new).changes if c.kind == kind]


# --- position mapping ---------------------------------------------------------


class TestSchemaPositions:
    """The mapping every other verdict depends on."""

    def test_a_request_schema_is_a_request_schema(self) -> None:
        assert schema_positions(doc_with_request({"type": "object"}))["Thing"] is Position.REQUEST

    def test_a_response_schema_is_a_response_schema(self) -> None:
        assert schema_positions(doc_with_response({"type": "object"}))["Thing"] is Position.RESPONSE

    def test_a_schema_used_both_ways_is_marked_both(self) -> None:
        """`Money` and `Problem` are real instances of this in our contract.

        It matters because BOTH takes the stricter verdict of the two directions,
        and a schema silently classified as only one of them would be wrong about
        the other half of its uses.
        """
        doc = doc_with_request({"type": "object"})
        doc["paths"]["/things"]["post"]["responses"]["201"] = {
            "description": "created",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}},
        }
        assert schema_positions(doc)["Thing"] is Position.BOTH

    def test_nested_refs_inherit_the_position(self) -> None:
        doc = doc_with_response(
            {"type": "object", "properties": {"m": {"$ref": "#/components/schemas/Money"}}}
        )
        doc["components"]["schemas"]["Money"] = {"type": "object"}
        assert schema_positions(doc)["Money"] is Position.RESPONSE

    def test_an_unreferenced_schema_has_no_position(self) -> None:
        """Nothing on the wire depends on it, so no change to it can break a consumer."""
        doc = doc_with_response({"type": "object"})
        doc["components"]["schemas"]["Orphan"] = {"type": "object"}
        assert "Orphan" not in schema_positions(doc)

    def test_a_self_referential_schema_terminates(self) -> None:
        """A nested itinerary is a legitimate cycle; without a guard this recurses forever."""
        doc = doc_with_response(
            {"type": "object", "properties": {"child": {"$ref": "#/components/schemas/Thing"}}}
        )
        assert schema_positions(doc)["Thing"] is Position.RESPONSE


# --- the direction-sensitive pairs --------------------------------------------


class TestRequiredPropertyAdded:
    def test_breaks_a_request(self) -> None:
        old = doc_with_request(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        )
        new = doc_with_request(
            {
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                "required": ["a", "b"],
            }
        )
        assert severities(old, new, "required_request_property_added") == [Severity.BREAKING]

    def test_is_additive_in_a_response(self) -> None:
        """A consumer that has never seen the field simply ignores it."""
        old = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        )
        new = doc_with_response(
            {
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                "required": ["a", "b"],
            }
        )
        assert diff_contracts(old, new).severity is Severity.ADDITIVE


class TestPropertyRemoved:
    def test_breaks_a_response(self) -> None:
        old = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "string"}}}
        )
        new = doc_with_response({"type": "object", "properties": {"a": {"type": "string"}}})
        assert severities(old, new, "response_property_removed") == [Severity.BREAKING]

    def test_is_only_potentially_breaking_in_a_request(self) -> None:
        """The server stops reading it. With a closed schema the caller is rejected;
        with an open one the value is silently ignored, which is worse but not an
        error. Neither is a clean break, and calling it BREAKING would make the
        gate fire on ordinary request-shape tidying."""
        old = doc_with_request(
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "string"}}}
        )
        new = doc_with_request({"type": "object", "properties": {"a": {"type": "string"}}})
        assert severities(old, new, "request_property_removed") == [Severity.POTENTIALLY_BREAKING]


class TestRequiredNessRelaxed:
    def test_breaks_a_response(self) -> None:
        """The subtlest case in the file. Relaxing a guarantee looks generous and
        breaks every consumer that read the field without checking for it."""
        old = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        )
        new = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []}
        )
        assert severities(old, new, "response_property_became_optional") == [Severity.BREAKING]

    def test_is_safe_in_a_request(self) -> None:
        old = doc_with_request(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        )
        new = doc_with_request(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []}
        )
        result = diff_contracts(old, new)
        assert result.severity is Severity.ADDITIVE
        # Reported, not silently dropped — see the companion case above.
        assert [c.kind for c in result.changes] == ["request_property_became_optional"]


class TestRequiredNessTightened:
    def test_breaks_a_request(self) -> None:
        old = doc_with_request(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []}
        )
        new = doc_with_request(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        )
        assert severities(old, new, "request_property_became_required") == [Severity.BREAKING]

    def test_is_safe_in_a_response(self) -> None:
        """Promising more than before cannot break a reader."""
        old = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []}
        )
        new = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        )
        assert diff_contracts(old, new).severity is Severity.ADDITIVE

    def test_but_it_is_still_reported(self) -> None:
        """Safe is not the same as absent, and conflating them produced a real lie.

        Tightening `JobEvent.required` in this sub-step made the gate print "no
        differences from the baseline" while the contract had in fact changed. The
        verdict was right and the report was false. A reader trusts the second one.
        """
        old = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": []}
        )
        new = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        )
        assert severities(old, new, "response_property_became_required") == [Severity.ADDITIVE]


class TestEnumValues:
    def test_removing_a_request_value_breaks(self) -> None:
        old = doc_with_request(
            {"type": "object", "properties": {"s": {"type": "string", "enum": ["a", "b"]}}}
        )
        new = doc_with_request(
            {"type": "object", "properties": {"s": {"type": "string", "enum": ["a"]}}}
        )
        assert severities(old, new, "request_enum_value_removed") == [Severity.BREAKING]

    def test_adding_a_request_value_is_additive(self) -> None:
        old = doc_with_request(
            {"type": "object", "properties": {"s": {"type": "string", "enum": ["a"]}}}
        )
        new = doc_with_request(
            {"type": "object", "properties": {"s": {"type": "string", "enum": ["a", "b"]}}}
        )
        assert diff_contracts(old, new).severity is Severity.ADDITIVE

    def test_adding_a_response_value_is_potentially_breaking(self) -> None:
        """POLICY §2. A consumer with an exhaustive switch meets a value it has no
        branch for. Whether that breaks depends on the consumer, which is why it is
        POTENTIALLY and not BREAKING."""
        old = doc_with_response(
            {"type": "object", "properties": {"s": {"type": "string", "enum": ["a"]}}}
        )
        new = doc_with_response(
            {"type": "object", "properties": {"s": {"type": "string", "enum": ["a", "b"]}}}
        )
        assert severities(old, new, "response_enum_value_added") == [Severity.POTENTIALLY_BREAKING]


class TestTypeChanges:
    def test_a_changed_type_always_breaks(self) -> None:
        old = doc_with_response({"type": "object", "properties": {"n": {"type": "integer"}}})
        new = doc_with_response({"type": "object", "properties": {"n": {"type": "string"}}})
        assert severities(old, new, "property_type_changed") == [Severity.BREAKING]

    def test_a_property_swapped_to_a_ref_is_a_type_change(self) -> None:
        """`amount: {type: integer}` becoming `amount: {$ref: Money}` is exactly the
        refactor STEP-004.06 performed, and it is breaking once a client exists."""
        old = doc_with_response({"type": "object", "properties": {"amount": {"type": "integer"}}})
        new = doc_with_response(
            {"type": "object", "properties": {"amount": {"$ref": "#/components/schemas/Money"}}}
        )
        new["components"]["schemas"]["Money"] = {"type": "object"}
        assert severities(old, new, "property_type_changed") == [Severity.BREAKING]

    def test_a_type_change_does_not_also_report_enum_noise(self) -> None:
        """One edit, one finding. A tool that reports a type change AND three
        consequential enum changes teaches people to skim its output."""
        old = doc_with_request(
            {"type": "object", "properties": {"s": {"type": "string", "enum": ["a", "b"]}}}
        )
        new = doc_with_request({"type": "object", "properties": {"s": {"type": "integer"}}})
        kinds = [c.kind for c in diff_contracts(old, new).changes]
        assert kinds == ["property_type_changed"]


class TestClosingASchema:
    def test_closing_a_request_schema_breaks(self) -> None:
        old = doc_with_request({"type": "object", "properties": {"a": {"type": "string"}}})
        new = doc_with_request(
            {
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "additionalProperties": False,
            }
        )
        assert severities(old, new, "request_schema_closed") == [Severity.BREAKING]

    def test_closing_a_response_schema_is_not_a_client_break(self) -> None:
        old = doc_with_response({"type": "object", "properties": {"a": {"type": "string"}}})
        new = doc_with_response(
            {
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "additionalProperties": False,
            }
        )
        assert diff_contracts(old, new).severity is Severity.ADDITIVE


# --- operation-level ----------------------------------------------------------


class TestOperations:
    def test_removing_an_operation_breaks(self) -> None:
        old = doc_with_response({"type": "object"})
        new = {**old, "paths": {}}
        assert severities(old, new, "operation_removed") == [Severity.BREAKING]

    def test_adding_an_operation_is_additive(self) -> None:
        old = doc_with_response({"type": "object"})
        new = doc_with_response({"type": "object"})
        new["paths"]["/others"] = {
            "get": {"operationId": "listOthers", "responses": {"200": {"description": "ok"}}}
        }
        assert diff_contracts(old, new).severity is Severity.ADDITIVE

    def test_renaming_an_operation_id_breaks(self) -> None:
        """Invisible on the wire and breaks every caller of the generated client,
        which is precisely the kind of change a wire-level diff would wave through."""
        old = doc_with_response({"type": "object"})
        new = doc_with_response({"type": "object"})
        new["paths"]["/things"]["get"]["operationId"] = "getThingList"
        assert severities(old, new, "operation_id_changed") == [Severity.BREAKING]

    def test_removing_a_response_status_breaks(self) -> None:
        old = doc_with_response({"type": "object"})
        old["paths"]["/things"]["get"]["responses"]["404"] = {"description": "gone"}
        new = doc_with_response({"type": "object"})
        assert severities(old, new, "response_removed") == [Severity.BREAKING]

    def test_a_new_required_parameter_breaks(self) -> None:
        old = doc_with_response({"type": "object"})
        new = doc_with_response({"type": "object"})
        new["paths"]["/things"]["get"]["parameters"] = [
            {"name": "region", "in": "query", "required": True, "schema": {"type": "string"}}
        ]
        assert severities(old, new, "required_parameter_added") == [Severity.BREAKING]

    def test_a_new_optional_parameter_is_additive(self) -> None:
        old = doc_with_response({"type": "object"})
        new = doc_with_response({"type": "object"})
        new["paths"]["/things"]["get"]["parameters"] = [
            {"name": "region", "in": "query", "schema": {"type": "string"}}
        ]
        assert diff_contracts(old, new).severity is Severity.ADDITIVE

    def test_making_the_request_body_required_breaks(self) -> None:
        old = doc_with_request({"type": "object"})
        old["paths"]["/things"]["post"]["requestBody"]["required"] = False
        new = doc_with_request({"type": "object"})
        assert severities(old, new, "request_body_became_required") == [Severity.BREAKING]


# --- deprecation metadata -----------------------------------------------------


class TestDeprecationMetadata:
    def test_a_deprecated_operation_needs_both_headers(self) -> None:
        doc = doc_with_response({"type": "object"})
        doc["paths"]["/things"]["get"]["deprecated"] = True
        kinds = {p.detail.split()[-3] for p in check_deprecation_metadata(doc)}
        assert len(check_deprecation_metadata(doc)) == 2, kinds

    def test_sunset_alone_is_not_enough(self) -> None:
        """`Deprecation` says it is going; `Sunset` says when. A sunset with no
        deprecation notice is a date nobody was told to expect."""
        doc = doc_with_response({"type": "object"})
        doc["paths"]["/things"]["get"]["deprecated"] = True
        doc["paths"]["/things"]["get"]["responses"]["200"]["headers"] = {
            "Sunset": {"schema": {"type": "string"}}
        }
        problems = check_deprecation_metadata(doc)
        assert len(problems) == 1
        assert "Deprecation" in problems[0].detail

    def test_both_headers_present_passes(self) -> None:
        doc = doc_with_response({"type": "object"})
        doc["paths"]["/things"]["get"]["deprecated"] = True
        doc["paths"]["/things"]["get"]["responses"]["200"]["headers"] = {
            "Sunset": {"schema": {"type": "string"}},
            "Deprecation": {"schema": {"type": "string"}},
        }
        assert check_deprecation_metadata(doc) == []

    def test_an_active_operation_needs_nothing(self) -> None:
        assert check_deprecation_metadata(doc_with_response({"type": "object"})) == []


# --- version handling ---------------------------------------------------------


class TestMajorVersion:
    @pytest.mark.parametrize(
        ("version", "expected"),
        [("1.0.0", 1), ("2.3.4", 2), ("v3.0.0", 3), ("0.1.0", 0), ("nonsense", 0), ("", 0)],
    )
    def test_major_is_extracted(self, version: str, expected: int) -> None:
        assert major_of(version) == expected

    def test_an_unparseable_version_does_not_look_like_a_bump(self) -> None:
        """Degrading to 0 means an unparseable version can never SATISFY the bump
        requirement. Failing closed is the only safe direction here."""
        assert major_of("garbage") <= major_of("1.0.0")


# --- the whole-document behaviour the gate depends on -------------------------


class TestOverallSeverity:
    def test_no_change_is_additive(self) -> None:
        doc = doc_with_response({"type": "object", "properties": {"a": {"type": "string"}}})
        assert diff_contracts(doc, doc).changes == []
        assert diff_contracts(doc, doc).severity is Severity.ADDITIVE

    def test_the_worst_change_decides(self) -> None:
        """One breaking change among many additive ones must not be averaged away."""
        old = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "string"}}}
        )
        new = doc_with_response(
            {"type": "object", "properties": {"a": {"type": "string"}, "c": {"type": "string"}}}
        )
        result = diff_contracts(old, new)
        assert result.severity is Severity.BREAKING
        assert len(result.breaking) == 1
        assert any(c.severity is Severity.ADDITIVE for c in result.changes)


class TestTheRealContract:
    """Against the actual documents, not builders.

    These would catch a classifier that works on toys and falls over on a document
    with external `$ref`s, `allOf` composition and 22 operations.
    """

    def test_the_current_contract_is_compatible_with_its_own_baseline(self) -> None:
        import yaml

        current = yaml.safe_load((REPO / "contracts" / "openapi.yaml").read_text())
        baseline = yaml.safe_load((REPO / "contracts" / "baseline" / "openapi.yaml").read_text())
        result = diff_contracts(baseline, current)
        assert result.breaking == [], [str(c) for c in result.breaking]

    def test_the_real_contract_has_schemas_in_both_positions(self) -> None:
        """If this ever returns nothing for BOTH, the position walk has stopped
        following `$ref`s and every direction-sensitive verdict above is being
        computed against the wrong ruleset — while still passing, because the
        builders in this file do not exercise the real document's shape.
        """
        import yaml

        current = yaml.safe_load((REPO / "contracts" / "openapi.yaml").read_text())
        positions = schema_positions(current)
        assert Position.BOTH in positions.values()
        assert Position.REQUEST in positions.values()
        assert Position.RESPONSE in positions.values()

    def test_an_unreferenced_schema_is_a_named_export_not_dead_weight(self) -> None:
        """Not every declared schema is referenced by an operation, and that is fine
        for exactly one reason.

        My first version of this test asserted `len(orphans) <= 2` and failed on
        three: `Provenance`, `TemporalValidity` and `ConstraintClass`. The premise
        was wrong, not the count. Those three are bare aliases to
        `contracts/jsonschema/*.json`, declared so a consumer can write
        `Schemas['Provenance']` instead of reaching into `Evidenced['provenance']`.
        They resolve to the same generated type, so there is no duplicate shape —
        they are a naming surface, deliberately.

        Raising the threshold to 3 would have made the test pass and asserted
        nothing. The property actually worth holding is the one that separates a
        deliberate export from a genuine orphan:

            a bare `$ref` alias  -> a named export, legitimate
            an inline definition -> nothing references it and nothing can; dead

        So an unreferenced schema must be a one-key `$ref`. An unreferenced schema
        with a body is either dead weight or evidence that a `$ref` somewhere is
        misspelled — and a misspelled `$ref` is how a schema silently stops being
        validated.
        """
        import yaml

        current = yaml.safe_load((REPO / "contracts" / "openapi.yaml").read_text())
        schemas = current["components"]["schemas"]
        unreferenced = set(schemas) - set(schema_positions(current))

        with_a_body = {
            name
            for name in unreferenced
            if not (isinstance(schemas[name], dict) and set(schemas[name]) == {"$ref"})
        }
        assert with_a_body == set(), (
            f"declared, unreferenced and not a bare alias: {sorted(with_a_body)}. "
            "Either an operation should reference it, or a $ref to it is misspelled, "
            "or it should be deleted."
        )


# --- STEP-004.09 (ENH-001): documented semantic change ------------------------


class TestSemanticReview:
    """The category `CONTRACT_CHANGE_POLICY` §1 calls most dangerous.

    A structural diff cannot see a meaning change. A **documented** one leaves a
    trace, and these assert that the trace is followed without the check firing on
    every reflow — which is the failure mode `ENH-001` costed and the reason it was
    nearly deferred.
    """

    @staticmethod
    def _with_description(text: str) -> JsonDict:
        doc = doc_with_response(
            {
                "type": "object",
                "properties": {"status": {"type": "string", "description": text}},
            }
        )
        return doc

    def test_a_reworded_description_is_reported(self) -> None:
        """Same name, same type, opposite meaning — invisible to everything else."""
        old = self._with_description("`confirmed` means a provider stated it.")
        new = self._with_description("`confirmed` means we derived it.")
        reviews = semantic_review(old, new)
        assert len(reviews) == 1
        assert reviews[0].location == "Thing.status"
        # Both texts, so a reviewer decides in one glance rather than going to look.
        assert "provider stated" in reviews[0].before
        assert "we derived" in reviews[0].after

    def test_reflow_alone_is_not_reported(self) -> None:
        """A YAML block scalar rewrapped at a different width renders identically.

        This is the dominant noise source: descriptions in this contract are
        multi-line block scalars, and any edit nearby can rewrap them.
        """
        old = self._with_description("the traveller must\narrive before 18:00")
        new = self._with_description("the traveller\nmust arrive     before 18:00")
        assert semantic_review(old, new) == []

    def test_emphasis_and_code_marks_alone_are_not_reported(self) -> None:
        old = self._with_description("must arrive before Money is charged")
        new = self._with_description("**must** arrive before `Money` is charged")
        assert semantic_review(old, new) == []

    def test_a_structural_change_is_not_double_reported(self) -> None:
        """It is already reported by the classifier. Echoing it here would make the
        semantic report mostly duplicate, which is how a report becomes noise."""
        old = self._with_description("one meaning")
        new = doc_with_response(
            {
                "type": "object",
                "properties": {"status": {"type": "integer", "description": "quite another"}},
            }
        )
        assert semantic_review(old, new) == []
        # ...and the structural differ does report it.
        assert severities(old, new, "property_type_changed") == [Severity.BREAKING]

    def test_a_new_property_is_not_a_semantic_change(self) -> None:
        old = doc_with_response({"type": "object", "properties": {}})
        new = self._with_description("brand new")
        assert semantic_review(old, new) == []

    def test_a_removed_property_is_not_a_semantic_change(self) -> None:
        old = self._with_description("about to vanish")
        new = doc_with_response({"type": "object", "properties": {}})
        assert semantic_review(old, new) == []

    def test_case_alone_is_not_reported(self) -> None:
        """Sentence-case edits are copy-editing, not meaning."""
        old = self._with_description("Must arrive before 18:00")
        new = self._with_description("must arrive before 18:00")
        assert semantic_review(old, new) == []


class TestSemanticReviewOnTheRealContract:
    def test_the_false_positive_rate_is_measured_not_asserted(self) -> None:
        """`ENH-001`: "If the false-positive rate is not driven near zero first,
        this should not ship."

        So it is counted rather than claimed. The current contract differs from its
        baseline by one additive structural change (BUG-021's `JobEvent.sequence`)
        and no description edits, so the expected count is exactly zero across all
        described properties.

        If this ever fails, the normalisation has stopped removing formatting noise
        — which is the specific way this check degrades into something people
        click through.
        """
        import yaml

        current = yaml.safe_load((REPO / "contracts" / "openapi.yaml").read_text())
        baseline = yaml.safe_load((REPO / "contracts" / "baseline" / "openapi.yaml").read_text())

        described = _described_properties(current)
        assert len(described) > 40, "precondition: the contract should carry many descriptions"

        reviews = semantic_review(baseline, current)
        assert reviews == [], [r.location for r in reviews]

    def test_it_can_still_fire_on_the_real_contract(self) -> None:
        """Guards the guard. A detector that reports nothing on a real corpus
        would satisfy the test above while detecting nothing at all."""
        import copy

        import yaml

        baseline = yaml.safe_load((REPO / "contracts" / "baseline" / "openapi.yaml").read_text())
        seeded = copy.deepcopy(baseline)
        status = seeded["components"]["schemas"]["Evidenced"]["properties"]["status"]
        status["description"] = (
            "`confirmed` means we derived it; `estimated` means a provider said so."
        )

        reviews = semantic_review(baseline, seeded)
        assert [r.location for r in reviews] == ["Evidenced.status"]
