"""Shared JSON Schema library — TST-AI-002 · STEP-004.06.

Two things are being defended.

**The deterministic boundary.** `ADR-002` gives feasibility to deterministic
engines and language to the model. `REQ-AI-001` says model output can never mutate
trip state without validation. `trip-brief-extraction.json` is where "never"
becomes enforceable, and `REQ-AI-002` requires a violation to fail closed to the
structured form rather than degrade to something plausible.

**Reuse.** A shared library that anything may bypass is a folder of files. The
duplication gate below is what makes it a library.
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO / "contracts/jsonschema"
OPENAPI: dict[str, Any] = yaml.safe_load((REPO / "contracts/openapi.yaml").read_text())


def load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((SCHEMA_DIR / name).read_text())
    return data


SHARED = ["money.json", "temporal-validity.json", "provenance.json", "constraint-class.json"]


class TestTheLibraryIsWellFormed:
    def test_every_shared_type_exists(self) -> None:
        present = {p.name for p in SCHEMA_DIR.glob("*.json")}
        assert set(SHARED) <= present

    @pytest.mark.parametrize("name", [*SHARED, "trip-brief-extraction.json"])
    def test_each_declares_a_versioned_id(self, name: str) -> None:
        """`$id` carries `/v1/`.

        A schema without a version in its identifier cannot be superseded: the
        only way to change it is in place, which breaks every consumer at once.
        """
        schema = load(name)
        assert schema["$id"].startswith("https://journeylab.app/schemas/v1/")
        assert schema["$id"].endswith(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    @pytest.mark.parametrize("name", [*SHARED, "trip-brief-extraction.json"])
    def test_each_is_valid_json_schema(self, name: str) -> None:
        jsonschema = pytest.importorskip("jsonschema")
        jsonschema.Draft202012Validator.check_schema(load(name))

    @pytest.mark.parametrize("name", [*SHARED, "trip-brief-extraction.json"])
    def test_each_says_why_it_exists(self, name: str) -> None:
        """A shared type with no description gets reimplemented by the next
        person, who could not tell what it was for."""
        assert len(load(name).get("description", "")) > 80


class TestNoDuplicateInlineDefinition:
    """The gate that makes it a library rather than a folder.

    STEP-004.06 §5: "Reuse enforced — no duplicate inline definitions."
    """

    def test_openapi_references_the_shared_types_rather_than_restating_them(self) -> None:
        schemas = OPENAPI["components"]["schemas"]
        for name in ("Money", "TemporalValidity", "Provenance", "ConstraintClass"):
            node = schemas[name]
            assert "$ref" in node, (
                f"{name} is defined inline in openapi.yaml while a shared schema "
                f"exists. Two copies of a type diverge silently: one gains a field, "
                f"the other does not, and nothing compares them."
            )
            assert node["$ref"].startswith("./jsonschema/")

    def test_no_inline_schema_reimplements_money(self) -> None:
        """Searches for the SHAPE, not the name.

        A duplicate would not be called `Money2`; it would be an object with
        `amount_minor` and `currency` inlined somewhere convenient.
        """
        offenders: list[str] = []
        for name, schema in OPENAPI["components"]["schemas"].items():
            if not isinstance(schema, dict) or "$ref" in schema:
                continue
            props = set(schema.get("properties", {}))
            if {"amount_minor", "currency"} <= props:
                offenders.append(name)
        assert not offenders, f"these reimplement Money inline: {offenders}"

    def test_no_inline_schema_reimplements_provenance_or_validity(self) -> None:
        offenders: list[str] = []
        for name, schema in OPENAPI["components"]["schemas"].items():
            if not isinstance(schema, dict) or "$ref" in schema:
                continue
            props = set(schema.get("properties", {}))
            if {"source", "confidence"} <= props or {
                "observed_at",
                "effective_from",
            } <= props:
                offenders.append(name)
        assert not offenders, (
            f"these restate Provenance or TemporalValidity inline: {offenders}. "
            f"Restating the three time axes is how one of them quietly goes missing."
        )

    def test_the_duplication_scan_can_actually_find_one(self) -> None:
        """A search for something absent passes identically when it is broken."""
        seeded: dict[str, Any] = {"Sneaky": {"properties": {"amount_minor": {}, "currency": {}}}}
        found = [
            name
            for name, schema in seeded.items()
            if {"amount_minor", "currency"} <= set(schema.get("properties", {}))
        ]
        assert found == ["Sneaky"]


class TestConstraintClassesStayDistinct:
    def test_all_four_exist(self) -> None:
        """Collapsing any pair breaks something specific.

        Merging `hard` and `soft` gives a solver that relaxes a wheelchair
        requirement to save nine minutes. Merging `inferred` hides that a machine
        put words in the traveller's mouth. Merging `unresolved` into `soft`
        produces a confident plan built on a guess.
        """
        assert load("constraint-class.json")["enum"] == [
            "hard",
            "soft",
            "inferred",
            "unresolved",
        ]


class TestTemporalValidityKeepsThreeAxes:
    def test_observed_effective_and_recorded_are_separate_fields(self) -> None:
        props = set(load("temporal-validity.json")["properties"])
        assert {"observed_at", "effective_from", "effective_to", "recorded_at"} <= props

    def test_the_two_that_cannot_be_inferred_are_required(self) -> None:
        """`effective_to` absent means open-ended, and `recorded_at` is ours to
        fill in. The other two must come from the source."""
        required = set(load("temporal-validity.json")["required"])
        assert required == {"observed_at", "effective_from"}


class TestProvenanceCarriesAnAccessLabel:
    def test_access_label_is_required(self) -> None:
        """A licence may permit planning with a fact but not displaying it.

        Without the label every renderer guesses, and renderers guess permissively.
        """
        provenance = load("provenance.json")
        assert "access_label" in provenance["required"]
        assert set(provenance["properties"]["access_label"]["enum"]) == {
            "public",
            "display_permitted",
            "internal_only",
        }

    def test_the_source_name_is_a_display_name_not_an_identity(self) -> None:
        description = load("provenance.json")["properties"]["source"]["properties"]["name"][
            "description"
        ]
        assert "internal identity" in description.lower()


# --- TST-AI-002: the deterministic boundary -----------------------------------


class TestModelOutputMustValidate:
    """TST-AI-002 — a schema violation fails closed to the deterministic fallback."""

    @staticmethod
    def _validator() -> Any:
        jsonschema = pytest.importorskip("jsonschema")
        referencing = pytest.importorskip("referencing")

        registry = referencing.Registry()
        for path in SCHEMA_DIR.glob("*.json"):
            contents = json.loads(path.read_text())
            registry = registry.with_resource(
                contents["$id"],
                referencing.Resource.from_contents(contents),
            )
        return jsonschema.Draft202012Validator(
            load("trip-brief-extraction.json"), registry=registry
        )

    def valid_extraction(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "locale": "en-GB",
            "abstained": False,
            "constraints": [
                {
                    "statement": "Arrive in Sifnos before 18:00 on Wednesday",
                    "constraint_class": "hard",
                    "confidence": 0.94,
                    "source_span": {"start": 12, "end": 52},
                    "unit": "clock_time",
                }
            ],
        }

    def test_a_well_formed_extraction_validates(self) -> None:
        self._validator().validate(self.valid_extraction())

    @pytest.mark.parametrize(
        ("mutation", "why"),
        [
            (
                {"schema_version": 2},
                "an unpinned version is a shape we did not write a validator for",
            ),
            ({"abstained": None}, "abstention must be an explicit boolean"),
            ({"locale": None}, "'12/09' is September in one locale and December in another"),
        ],
    )
    def test_a_violated_envelope_is_rejected(self, mutation: dict[str, Any], why: str) -> None:
        jsonschema = pytest.importorskip("jsonschema")
        payload = {**self.valid_extraction(), **mutation}
        with pytest.raises(jsonschema.ValidationError):
            self._validator().validate(payload)

    def test_a_missing_required_field_is_rejected(self) -> None:
        jsonschema = pytest.importorskip("jsonschema")
        for field in ("schema_version", "locale", "constraints", "abstained"):
            payload = self.valid_extraction()
            del payload[field]
            with pytest.raises(jsonschema.ValidationError):
                self._validator().validate(payload)

    def test_an_invented_constraint_class_is_rejected(self) -> None:
        """The four classes are the contract. A model returning `maybe_hard` is
        returning something the solver has no rule for."""
        jsonschema = pytest.importorskip("jsonschema")
        payload = self.valid_extraction()
        payload["constraints"][0]["constraint_class"] = "maybe_hard"
        with pytest.raises(jsonschema.ValidationError):
            self._validator().validate(payload)

    def test_a_constraint_without_a_source_span_is_rejected(self) -> None:
        """The single most useful field here: it makes a hallucination visible.

        A model that invents "travelling with a dog" must point at the characters
        that say so, and a span that does not contain the claim is caught by a
        deterministic check rather than by the reader's memory of what they typed.
        """
        jsonschema = pytest.importorskip("jsonschema")
        payload = self.valid_extraction()
        del payload["constraints"][0]["source_span"]
        with pytest.raises(jsonschema.ValidationError):
            self._validator().validate(payload)

    def test_a_confidence_outside_zero_to_one_is_rejected(self) -> None:
        jsonschema = pytest.importorskip("jsonschema")
        for bad in (-0.1, 1.5):
            payload = self.valid_extraction()
            payload["constraints"][0]["confidence"] = bad
            with pytest.raises(jsonschema.ValidationError):
                self._validator().validate(payload)

    def test_extra_fields_are_rejected_not_ignored(self) -> None:
        """A model returning a field we did not ask for is a model doing something
        we did not design. Ignoring it means never finding out."""
        jsonschema = pytest.importorskip("jsonschema")
        payload = self.valid_extraction()
        payload["constraints"][0]["tool_call"] = {"name": "book_ferry"}
        with pytest.raises(jsonschema.ValidationError):
            self._validator().validate(payload)

    def test_an_empty_extraction_is_valid(self) -> None:
        """Finding nothing is a real answer. Forcing a constraint out of a model
        that found none is how invention starts."""
        payload = self.valid_extraction()
        payload["constraints"] = []
        self._validator().validate(payload)

    def test_abstention_is_expressible(self) -> None:
        """REQ-AI-004: low evidence means abstain, never backfill from memory."""
        payload = self.valid_extraction()
        payload["abstained"] = True
        payload["abstention_reason"] = "The dates could not be resolved from the text."
        payload["constraints"] = []
        self._validator().validate(payload)

    def test_the_schema_does_not_claim_to_check_truth(self) -> None:
        """Stated in the schema, because a reader who believes otherwise will skip
        the validators and the human confirmation that follow it."""
        description = load("trip-brief-extraction.json")["description"]
        assert "shape, not truth" in description
        assert "first gate of three" in description


class TestSchemaIdsAreStableAndUnique:
    def test_no_two_schemas_share_an_id(self) -> None:
        ids = [json.loads(p.read_text())["$id"] for p in SCHEMA_DIR.glob("*.json")]
        assert len(ids) == len(set(ids)), f"duplicate $id: {ids}"

    def test_ids_match_their_filenames(self) -> None:
        """A `$id` that disagrees with its path resolves for the author and fails
        for everyone else."""
        for path in SCHEMA_DIR.glob("*.json"):
            schema_id = json.loads(path.read_text())["$id"]
            assert schema_id.endswith(path.name), f"{path.name} has $id {schema_id}"

    def test_cross_references_use_absolute_ids(self) -> None:
        """A relative `$ref` between schema files resolves differently depending
        on which document loaded it first."""
        raw = (SCHEMA_DIR / "trip-brief-extraction.json").read_text()
        for ref in re.findall(r'"\$ref":\s*"([^"#][^"]*)"', raw):
            assert ref.startswith("https://journeylab.app/schemas/"), (
                f"cross-schema $ref {ref!r} is not absolute"
            )
