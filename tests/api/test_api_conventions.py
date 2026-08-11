"""Global API conventions — TST-PLAT-005 · STEP-004.01.

The assertions that matter here are the ones about what CANNOT be expressed:
an error that is not in the register, a cursor carrying a tenant, a denial that
differs from a not-found, a command without an idempotency key. A convention
that can be bypassed is a suggestion.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest
import yaml
from conventions.concurrency import (
    ConcurrencyConflictError,
    IdempotencyConflictError,
    IdempotencyError,
    check_replay,
    correlation_id,
    etag_for,
    fingerprint,
    require_idempotency_key,
    require_if_match,
)
from conventions.error_codes import CLIENT_VISIBLE, ERROR_CODES
from conventions.pagination import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    CursorError,
    build_page,
    decode_cursor,
    encode_cursor,
    page_request,
)
from conventions.problem import (
    OPAQUE_CODE,
    OPAQUE_STATUS,
    PROBLEM_MEDIA_TYPE,
    ProblemError,
    opaque_denial,
    problem,
    safe_detail,
)
from error_model_source import parse_error_codes

REPO = pathlib.Path(__file__).resolve().parents[2]


# --- the register is generated, not written ----------------------------------


class TestRegisterIsGenerated:
    def test_matches_the_markdown_right_now(self) -> None:
        """ADR-012 for the second time: one document, one register."""
        from gen_error_codes import render_python, render_schema

        codes = parse_error_codes()
        on_disk = (REPO / "apps/api/src/conventions/error_codes.py").read_text()
        assert on_disk == render_python(codes), (
            "error_codes.py is stale — run: uv run python tools/gen_error_codes.py"
        )
        schema_on_disk = (REPO / "contracts/schemas/error-codes.json").read_text()
        assert schema_on_disk == render_schema(codes), (
            "error-codes.json is stale — run: uv run python tools/gen_error_codes.py"
        )

    def test_parser_refuses_an_unparseable_status_rather_than_guessing(self) -> None:
        """A regex that grabs the first number would silently mangle the register.

        `tenant.isolation_violation` is written "500 + **SEV1 alert**" and
        `evidence.conflicting_sources` as "200 + warning". Both are deliberate
        product statements; both must be resolved explicitly.
        """
        markdown = (
            "## 3. Error code register\n\n"
            "| Code | Status | Meaning | Remediation | Requirement |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| `made.up` | 500 when Mercury is retrograde | x | y | REQ-X-001 |\n"
        )
        with pytest.raises(ValueError, match="documented special case"):
            parse_error_codes(markdown)

    def test_parser_refuses_a_missing_section(self) -> None:
        with pytest.raises(ValueError, match=re.escape("no '## 3. Error code register'")):
            parse_error_codes("# Some other document\n")

    def test_internal_conditions_are_excluded_from_the_published_enum(self) -> None:
        """A code the client never sees must not appear in the contract."""
        published = json.loads((REPO / "contracts/schemas/error-codes.json").read_text())
        assert "ai.injection_detected" not in published["enum"]
        assert "evidence.conflicting_sources" not in published["enum"]
        assert "solver.infeasible" in published["enum"]
        assert set(published["enum"]) == CLIENT_VISIBLE


class TestTheTwoRegistersAgree:
    """The operation register and the error register must name the same codes.

    STEP-004.02's pre-change check found three that did not: two transpositions
    (`coverage.insufficient_evidence` for `evidence.insufficient_coverage`,
    `provider.unavailable` for `coverage.provider_degraded`) and one code with no
    entry at all (`validation.invalid_party`, against a Validation class that had
    been declared since the document was written).

    None of them would have failed anything. `API_CONTRACTS.md` is prose; nothing
    read it. The drift only became visible when the error register started
    generating code, and a client branching on a code the server can never send
    fails silently — it just never takes that branch.
    """

    def test_every_error_an_operation_declares_exists_in_the_register(self) -> None:
        import re

        text = (REPO / "docs/product/04-contracts/API_CONTRACTS.md").read_text()
        declared: set[str] = set()
        for line in text.splitlines():
            # Only rows that declare ERRORS. Audit rows name events like
            # `trip.created`, which are not error codes and must not be required
            # to exist in the register.
            if line.strip().startswith("| Errors |") or "Errors:" in line:
                declared |= set(re.findall(r"`([a-z][a-z0-9_]*\.[a-z0-9_.]+)`", line))

        assert declared, "found no error declarations — the parser is wrong, not the document"
        unregistered = sorted(declared - set(ERROR_CODES))
        assert not unregistered, (
            f"API_CONTRACTS.md declares error codes that ERROR_MODEL.md does not "
            f"define: {unregistered}. Either add the row to the register or "
            f"correct the operation — a client cannot branch on a code the server "
            f"can never send."
        )


# --- problem details ----------------------------------------------------------


class TestProblemDetails:
    def test_conforms_to_rfc_9457(self) -> None:
        doc = problem("solver.timeout", correlation_id="corr_abc12345")
        for field in ("type", "title", "status", "code", "correlation_id", "retryable"):
            assert field in doc, f"{field} missing"
        assert doc["type"].startswith("https://journeylab.app/problems/")
        assert PROBLEM_MEDIA_TYPE == "application/problem+json"

    def test_an_unregistered_code_cannot_be_raised(self) -> None:
        """The register is the only way in. Otherwise there are eighteen spellings."""
        with pytest.raises(ProblemError, match="unknown error code"):
            problem("something.i.invented", correlation_id="corr_abc12345")

    def test_an_internal_condition_cannot_be_returned_to_a_client(self) -> None:
        with pytest.raises(ProblemError, match="internal condition"):
            problem("ai.injection_detected", correlation_id="corr_abc12345")

    def test_correlation_id_is_required(self) -> None:
        with pytest.raises(ProblemError, match="correlation_id is required"):
            problem("solver.timeout", correlation_id="")

    def test_retryable_is_not_inferred_from_the_status(self) -> None:
        """Two 5xx codes, opposite answers — which is the whole point of the field."""
        assert problem("solver.timeout", correlation_id="c" * 8)["retryable"] is True
        assert problem("affiliate.unavailable", correlation_id="c" * 8)["retryable"] is True
        # A 422 is never retryable: the server understood and refused.
        assert problem("solver.infeasible", correlation_id="c" * 8)["retryable"] is False

    @pytest.mark.parametrize(
        ("leak", "why"),
        [
            ('File "/app/main.py", line 42', "traceback frame"),
            ("Traceback (most recent call last)", "traceback header"),
            ("postgresql://user:pw@db:5432/journeylab", "connection string"),
            ("contact traveller@example.com", "email address"),
            ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", "bearer token"),
            ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abc", "raw JWT"),
        ],
    )
    def test_detail_refuses_to_carry_what_error_model_section_5_forbids(
        self, leak: str, why: str
    ) -> None:
        """Raises rather than redacting.

        Redaction is friendlier and wrong: it turns a developer mistake into a
        silently-truncated message that still ships, and the next reader assumes
        the sanitiser covers cases it does not.
        """
        with pytest.raises(ProblemError):
            safe_detail(leak)
        with pytest.raises(ProblemError):
            problem("solver.timeout", correlation_id="c" * 8, detail=leak)

    def test_ordinary_detail_passes_through(self) -> None:
        assert safe_detail("The ferry timetable could not be reached.") is not None
        doc = problem(
            "coverage.unsupported_region",
            correlation_id="c" * 8,
            detail="The Cyclades are not in the Phase 1 destination pack.",
        )
        assert "Cyclades" in doc["detail"]


# --- REQ-SEC-004: enumeration -------------------------------------------------


class TestIndistinguishableDenial:
    def test_denial_is_404_not_403(self) -> None:
        """A 403 still discloses that something is there to be forbidden.

        The register writes the status as "403/404" because the two are meant to
        be indistinguishable; it does not say which is sent. The code sends 404,
        and this test is what stops a regeneration quietly changing that.
        """
        assert opaque_denial("corr_abc12345")["status"] == OPAQUE_STATUS == 404

    def test_every_denial_is_byte_identical(self) -> None:
        """Missing, forbidden and cross-tenant must be one response.

        Same correlation ID so the comparison is of the shape, not of the id —
        the id legitimately differs per request and is the one field support needs.
        """
        a = opaque_denial("corr_abc12345", instance="/v1/trips/trp_01")
        b = opaque_denial("corr_abc12345", instance="/v1/trips/trp_01")
        assert a == b
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

    def test_the_denial_carries_no_detail_field_at_all(self) -> None:
        """Not a constant detail — no detail.

        An optional detail argument is how indistinguishability erodes: one caller
        passes "wrong tenant" for debugging, it ships, and the oracle is back.
        Omitting the field entirely leaves nothing for a future edit to
        differentiate.
        """
        assert "detail" not in opaque_denial("corr_abc12345")

    def test_opaque_denial_takes_no_reason_parameter(self) -> None:
        import inspect

        params = set(inspect.signature(opaque_denial).parameters)
        assert params == {"correlation_id", "instance"}, (
            f"opaque_denial gained parameters: {params}. A reason argument is "
            f"exactly how the existence oracle comes back."
        )

    def test_the_published_contract_documents_the_indistinguishability(self) -> None:
        doc = yaml.safe_load((REPO / "contracts/openapi.yaml").read_text())
        described = doc["components"]["responses"]["NotFoundOrForbidden"]["description"]
        assert "indistinguishably" in described.lower()
        example = doc["components"]["responses"]["NotFoundOrForbidden"]["content"][
            "application/problem+json"
        ]["example"]
        assert example["status"] == 404
        assert example["code"] == OPAQUE_CODE


# --- pagination ----------------------------------------------------------------


class TestPagination:
    def test_round_trips_a_keyset(self) -> None:
        keyset = {"created_at": "2026-08-11T00:00:00Z", "id": "trp_01"}
        assert decode_cursor(encode_cursor(keyset)) == keyset

    def test_key_order_does_not_change_the_cursor(self) -> None:
        assert encode_cursor({"a": 1, "b": 2}) == encode_cursor({"b": 2, "a": 1})

    @pytest.mark.parametrize(
        "forbidden",
        ["tenant_id", "organization_id", "org", "user_id", "actor", "role", "scopes"],
    )
    def test_a_cursor_may_not_carry_identity(self, forbidden: str) -> None:
        """REQ-SEC-001: tenant comes from the token, never from client input.

        A cursor is base64, not encryption. A client that can read it can rewrite
        it, so a tenant in a cursor is a tenant the client chooses.
        """
        with pytest.raises(CursorError, match="may not carry"):
            encode_cursor({forbidden: "someone_else", "id": "x"})

    def test_identity_is_rejected_on_decode_as_well(self) -> None:
        """Encode-side validation catches our mistakes; decode-side catches theirs.

        Only one of those is an attacker. A hand-crafted cursor never passes
        through `encode_cursor`.
        """
        import base64

        hostile = base64.urlsafe_b64encode(b'{"tenant_id":"victim","id":"x"}').decode()
        with pytest.raises(CursorError):
            decode_cursor(hostile.rstrip("="))

    @pytest.mark.parametrize("bad", ["!!!", "not-base64!", "eyJ1bmNsb3NlZCI6", "z" * 3000])
    def test_a_malformed_cursor_is_rejected_identically(self, bad: str) -> None:
        """Every failure gives the same message — the caller learns nothing."""
        with pytest.raises(CursorError) as exc:
            decode_cursor(bad)
        assert str(exc.value) == "invalid cursor"

    def test_limit_is_clamped_not_rejected(self) -> None:
        """A hint about response size, not a semantic input."""
        assert page_request(None, None).limit == DEFAULT_LIMIT
        assert page_request(None, 5000).limit == MAX_LIMIT
        assert page_request(None, 0).limit == 1
        assert page_request(None, -3).limit == 1

    def test_a_malformed_cursor_is_always_rejected(self) -> None:
        """The asymmetry with `limit` is deliberate.

        Silently returning the first page for a bad cursor would show the caller
        data they had already seen as if it were new.
        """
        with pytest.raises(CursorError):
            page_request("!!!", 10)

    def test_a_short_page_emits_no_cursor(self) -> None:
        """A page shorter than the limit is the last page by definition.

        Emitting a cursor there costs one pointless round trip per list.
        """
        assert build_page([1, 2], 5, {"id": "x"}).next_cursor is None
        assert build_page([1, 2, 3, 4, 5], 5, {"id": "x"}).next_cursor is not None

    def test_there_is_no_offset_anywhere(self) -> None:
        """Offset pagination is not supported, structurally.

        A handler cannot accept one by copying the shape, because the shape has no
        such field.
        """
        source = (REPO / "apps/api/src/conventions/pagination.py").read_text()
        code = "\n".join(line for line in source.splitlines() if not line.strip().startswith("#"))
        # Strip the module docstring, which explains why offset is absent.
        body = code.split('"""', 2)[-1]
        assert "offset" not in body.lower()


# --- idempotency and concurrency ------------------------------------------------


class TestIdempotency:
    def test_the_key_is_required(self) -> None:
        with pytest.raises(IdempotencyError, match="required"):
            require_idempotency_key({})

    def test_header_lookup_is_case_insensitive(self) -> None:
        """HTTP header names are; a dict is not. A miss here creates duplicates."""
        assert require_idempotency_key({"idempotency-key": "a" * 10}) == "a" * 10
        assert require_idempotency_key({"IDEMPOTENCY-KEY": "b" * 10}) == "b" * 10

    @pytest.mark.parametrize("bad", ["", "   ", "short", "x" * 300, "has spaces"])
    def test_a_malformed_key_is_refused(self, bad: str) -> None:
        with pytest.raises(IdempotencyError):
            require_idempotency_key({"Idempotency-Key": bad})

    def test_same_request_replays(self) -> None:
        stored = fingerprint("k" * 10, {"a": 1, "b": 2})
        incoming = fingerprint("k" * 10, {"b": 2, "a": 1})
        assert check_replay(stored, incoming) is True

    def test_different_body_is_a_client_defect(self) -> None:
        stored = fingerprint("k" * 10, {"a": 1})
        with pytest.raises(IdempotencyConflictError):
            check_replay(stored, fingerprint("k" * 10, {"a": 2}))

    def test_a_string_and_a_number_are_different_requests(self) -> None:
        """They mean different things to whatever validates them next."""
        a = fingerprint("k" * 10, {"amount": 1})
        b = fingerprint("k" * 10, {"amount": "1"})
        assert a.digest != b.digest

    def test_an_unseen_key_is_not_a_replay(self) -> None:
        assert check_replay(None, fingerprint("k" * 10, {"a": 1})) is False


class TestOptimisticConcurrency:
    def test_etag_is_strong_not_weak(self) -> None:
        """`If-Match` requires strong comparison."""
        tag = etag_for(3, "trp_01")
        assert tag.startswith('"') and tag.endswith('"')
        assert not tag.startswith("W/")

    def test_etag_binds_to_the_resource_not_just_the_version(self) -> None:
        """Otherwise a tag from one resource satisfies a precondition on another."""
        assert etag_for(3, "trp_01") != etag_for(3, "trp_02")
        assert etag_for(3, "trp_01") != etag_for(4, "trp_01")

    def test_missing_if_match_is_refused_not_treated_as_consent(self) -> None:
        """Treating absence as "no opinion" loses an update on the first request
        that forgets the header."""
        with pytest.raises(ConcurrencyConflictError, match="If-Match is required"):
            require_if_match({}, etag_for(1, "trp_01"))

    def test_stale_if_match_conflicts(self) -> None:
        with pytest.raises(ConcurrencyConflictError, match="changed since you read it"):
            require_if_match({"If-Match": etag_for(1, "trp_01")}, etag_for(2, "trp_01"))

    def test_matching_if_match_passes(self) -> None:
        tag = etag_for(7, "trp_01")
        require_if_match({"if-match": tag}, tag)

    def test_star_means_overwrite_whatever_is_there(self) -> None:
        require_if_match({"If-Match": "*"}, etag_for(9, "trp_01"))


class TestCorrelation:
    def test_a_usable_client_id_is_honoured(self) -> None:
        assert correlation_id({"X-Correlation-Id": "client-abc-123"}) == "client-abc-123"

    @pytest.mark.parametrize(
        "hostile",
        ["short", "x" * 300, "bad\nheader", "has spaces", "<script>", "a;b|c"],
    )
    def test_an_unusable_one_is_replaced_not_rejected(self, hostile: str) -> None:
        """It is echoed into responses and written to logs, so an unbounded
        client-controlled string is a log-injection primitive. But a bad
        correlation header should not fail an otherwise fine request.
        """
        generated = correlation_id({"X-Correlation-Id": hostile})
        assert generated.startswith("corr_")
        assert hostile not in generated

    def test_one_is_minted_when_absent(self) -> None:
        assert correlation_id({}).startswith("corr_")
        assert correlation_id({}) != correlation_id({})


# --- the published contract -----------------------------------------------------


class TestPublishedContract:
    def test_openapi_is_3_1(self) -> None:
        doc = yaml.safe_load((REPO / "contracts/openapi.yaml").read_text())
        assert doc["openapi"].startswith("3.1")

    def test_the_conventions_exist_independently_of_any_operation(self) -> None:
        """STEP-004.01 defined the vocabulary; .02 onward speak it.

        This asserted `paths == {}` while .01 was the only sub-step, which was
        true and became wrong the moment .02 declared an operation. The durable
        property is not "there are no operations" — it is that the shared
        components exist and are reusable, which is what made .02 cheap.
        """
        doc = yaml.safe_load((REPO / "contracts/openapi.yaml").read_text())
        components = doc["components"]
        for name in ("Problem", "Page", "Money", "ZonedTimestamp", "Cursor"):
            assert name in components["schemas"], f"{name} missing"
        for name in ("Problem", "NotFoundOrForbidden", "Conflict", "RateLimited"):
            assert name in components["responses"], f"{name} missing"

    def test_the_error_enum_is_referenced_not_inlined(self) -> None:
        """A copy of the code list here would be a second source of truth."""
        raw = (REPO / "contracts/openapi.yaml").read_text()
        assert "./schemas/error-codes.json" in raw
        for code in list(CLIENT_VISIBLE)[:5]:
            # The codes appear only inside example values, never as an enum.
            assert f"- {code}" not in raw, f"{code} looks inlined as an enum member"

    def test_money_is_declared_as_integer_minor_units(self) -> None:
        """Checks the declared TYPES, not the serialised document.

        A first version asserted `"float" not in json.dumps(money)` and failed
        against the schema's own description, which explains why floats are
        forbidden. Searching prose for a keyword finds the warning as readily as
        the violation — the same mistake made three times before in this
        repository, and the fix is always to assert on structure instead.
        """
        doc = yaml.safe_load((REPO / "contracts/openapi.yaml").read_text())
        # STEP-004.06 moved Money into `contracts/jsonschema/`, so the assertion
        # follows the reference. Reading the OpenAPI node directly would now pass
        # vacuously against a `$ref` with no `properties` at all — which is how a
        # test survives a refactor while checking nothing.
        node = doc["components"]["schemas"]["Money"]
        assert "$ref" in node, "Money should be shared, not inline (STEP-004.06)"
        money = json.loads((REPO / "contracts" / node["$ref"][2:]).read_text())
        assert money["properties"]["amount_minor"]["type"] == "integer"
        declared = {p.get("type") for p in money["properties"].values()}
        assert "number" not in declared, "money must never be declared as a float"
        assert money.get("additionalProperties") is False, (
            "an open Money object lets a float amount in through an undeclared field"
        )

    def test_every_registered_client_visible_code_is_publishable(self) -> None:
        """No code in the register is unusable — the contract and the code agree."""
        for code in CLIENT_VISIBLE:
            doc = problem(code, correlation_id="c" * 8)
            assert doc["code"] == code
            assert ERROR_CODES[code].status == doc["status"]
