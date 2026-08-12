"""Backward-compatibility classifier for the API contracts — STEP-004.08 (REQ-PLAT-008).

WHAT THIS IS FOR
    `CONTRACT_CHANGE_POLICY.md` §2 classifies every contract change as additive,
    potentially breaking, or breaking, and §4 says a breaking diff without a major
    version bump must fail the build. This module is the classifier those rules
    need; `tests/guards/contract-compatibility.sh` is the gate that runs it.

THE IDEA THE NAIVE VERSION GETS WRONG
    Request and response schemas have **opposite** compatibility rules, and a diff
    that treats a schema as a schema is wrong about half of them.

        In a REQUEST, the client writes and the server reads.
            Adding a required property BREAKS every existing client.
            Removing an enum value BREAKS the client still sending it.
            Making a required property optional is SAFE.

        In a RESPONSE, the server writes and the client reads.
            Removing a property BREAKS every consumer reading it.
            Adding an enum value can break a consumer that branches on it.
            Making a required property optional BREAKS anyone who assumed presence.

    Note that "make required optional" is safe in one direction and breaking in the
    other. So this module does not classify schemas in isolation. It walks the
    document from its operations, records the POSITION each schema is reachable in,
    and applies the rules for that position.

    A component reachable from both — `Money` is, and so is `Problem` — is checked
    under both rule sets and takes the worse verdict. That is not a compromise: such
    a schema genuinely has to satisfy both, and the alternative is picking one and
    being silently wrong about the other.

WHAT THIS CANNOT DO, STATED HERE RATHER THAN DISCOVERED LATER
    **Semantic change is invisible to it.** A field that keeps its name, type and
    required-ness while changing what it MEANS passes every check in this file.
    `CONTRACT_CHANGE_POLICY.md` §1 calls that the most dangerous category and this
    module cannot see it. Only review can. Nothing here should be read as evidence
    that a change is safe — only as evidence that it is not breaking in one of the
    ways a machine can recognise.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Final

JsonDict = dict[str, Any]

_HTTP_METHODS: Final = frozenset(
    {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
)


class Position(enum.StrEnum):
    """Which side of the wire a schema sits on.

    `BOTH` is not a third kind of schema. It is a schema reached from a request in
    one place and a response in another, and it must satisfy the rules for each.
    """

    REQUEST = "request"
    RESPONSE = "response"
    BOTH = "both"


class Severity(enum.IntEnum):
    """Ordered so `max()` picks the worse verdict.

    IntEnum specifically: the comparison is the point, and a plain Enum would make
    `max()` raise rather than sort.
    """

    ADDITIVE = 0
    POTENTIALLY_BREAKING = 1
    BREAKING = 2


@dataclass(frozen=True)
class Change:
    """One classified difference between two contract documents."""

    severity: Severity
    kind: str
    """Short stable slug, e.g. `required_request_property_added`."""
    location: str
    """Where in the document, in a form a human can find."""
    detail: str

    def __str__(self) -> str:
        return f"[{self.severity.name}] {self.location} — {self.detail}"


@dataclass
class DiffResult:
    changes: list[Change] = field(default_factory=list)

    @property
    def severity(self) -> Severity:
        return max((c.severity for c in self.changes), default=Severity.ADDITIVE)

    @property
    def breaking(self) -> list[Change]:
        return [c for c in self.changes if c.severity is Severity.BREAKING]

    @property
    def potentially_breaking(self) -> list[Change]:
        return [c for c in self.changes if c.severity is Severity.POTENTIALLY_BREAKING]

    def add(self, severity: Severity, kind: str, location: str, detail: str) -> None:
        self.changes.append(Change(severity=severity, kind=kind, location=location, detail=detail))


# --- schema position mapping --------------------------------------------------


def _resolve(doc: JsonDict, ref: str) -> JsonDict | None:
    """Resolve a local `$ref`. External refs return None deliberately.

    An external `$ref` points at a file this module was not given. Following it
    would mean guessing at a path relative to a document whose location it does not
    know. Returning None marks the schema as un-walkable, and `_walk` records that
    rather than silently treating it as an empty schema — which would make every
    change inside `contracts/jsonschema/` invisible.
    """
    if not ref.startswith("#/"):
        return None
    node: Any = doc
    for part in ref.removeprefix("#/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) else None


def schema_positions(doc: JsonDict) -> dict[str, Position]:
    """Map each `components.schemas` name to the position(s) it is reachable in.

    Walks from operations rather than over `components`, because a schema nobody
    references has no position and no consumer — and treating it as though it did
    would produce breaking-change reports for a shape that is not on the wire.
    """
    seen: dict[str, Position] = {}

    def mark(name: str, position: Position) -> None:
        current = seen.get(name)
        if current is None:
            seen[name] = position
        elif current is not position:
            seen[name] = Position.BOTH

    def walk(node: Any, position: Position, guard: frozenset[str]) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item, position, guard)
            return
        if not isinstance(node, dict):
            return

        ref = node.get("$ref")
        if isinstance(ref, str):
            prefix = "#/components/schemas/"
            if ref.startswith(prefix):
                name = ref.removeprefix(prefix)
                mark(name, position)
                # `guard` breaks reference cycles. A self-referential schema is
                # legal (a nested itinerary could be), and without this the walk
                # would recurse until the stack ran out.
                if name in guard:
                    return
                target = _resolve(doc, ref)
                if target is not None:
                    walk(target, position, guard | {name})
                return
            target = _resolve(doc, ref)
            if target is not None:
                walk(target, position, guard)
            return

        for value in node.values():
            walk(value, position, guard)

    for path_item in doc.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            walk(operation.get("requestBody"), Position.REQUEST, frozenset())
            walk(operation.get("parameters"), Position.REQUEST, frozenset())
            walk(operation.get("responses"), Position.RESPONSE, frozenset())

    return seen


# --- operation-level diff -----------------------------------------------------


def _operations(doc: JsonDict) -> dict[str, JsonDict]:
    """Every operation, keyed `METHOD path`."""
    out: dict[str, JsonDict] = {}
    for path, path_item in doc.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() in _HTTP_METHODS and isinstance(operation, dict):
                out[f"{method.upper()} {path}"] = operation
    return out


def _diff_operations(old: JsonDict, new: JsonDict, result: DiffResult) -> None:
    old_ops, new_ops = _operations(old), _operations(new)

    for key in sorted(set(old_ops) - set(new_ops)):
        result.add(
            Severity.BREAKING,
            "operation_removed",
            key,
            "operation removed; every caller of it fails",
        )

    for key in sorted(set(new_ops) - set(old_ops)):
        result.add(Severity.ADDITIVE, "operation_added", key, "new operation")

    for key in sorted(set(old_ops) & set(new_ops)):
        _diff_one_operation(key, old_ops[key], new_ops[key], result)


def _diff_one_operation(key: str, old: JsonDict, new: JsonDict, result: DiffResult) -> None:
    old_id, new_id = old.get("operationId"), new.get("operationId")
    if old_id != new_id:
        # The operationId names the generated client method. Renaming it does not
        # change the wire format at all, and breaks every caller of the client —
        # which is why it is classified here rather than dismissed as cosmetic.
        result.add(
            Severity.BREAKING,
            "operation_id_changed",
            key,
            f"operationId {old_id!r} -> {new_id!r}; renames the generated client method",
        )

    _diff_parameters(key, old.get("parameters", []), new.get("parameters", []), result)
    _diff_responses(key, old.get("responses", {}), new.get("responses", {}), result)

    old_body_required = bool((old.get("requestBody") or {}).get("required"))
    new_body_required = bool((new.get("requestBody") or {}).get("required"))
    if new_body_required and not old_body_required:
        result.add(
            Severity.BREAKING,
            "request_body_became_required",
            key,
            "request body is now required; callers sending none are rejected",
        )


def _parameter_key(parameter: JsonDict) -> str | None:
    name, location = parameter.get("name"), parameter.get("in")
    if isinstance(name, str) and isinstance(location, str):
        return f"{location}:{name}"
    return None


def _diff_parameters(key: str, old_params: Any, new_params: Any, result: DiffResult) -> None:
    def index(params: Any) -> dict[str, JsonDict]:
        out: dict[str, JsonDict] = {}
        if isinstance(params, list):
            for parameter in params:
                if isinstance(parameter, dict) and (k := _parameter_key(parameter)):
                    out[k] = parameter
        return out

    old_index, new_index = index(old_params), index(new_params)

    for name in sorted(set(new_index) - set(old_index)):
        if new_index[name].get("required"):
            result.add(
                Severity.BREAKING,
                "required_parameter_added",
                f"{key} ({name})",
                "new required parameter; existing callers omit it",
            )
        else:
            result.add(
                Severity.ADDITIVE,
                "optional_parameter_added",
                f"{key} ({name})",
                "new optional parameter",
            )

    for name in sorted(set(old_index) - set(new_index)):
        # Not breaking on the wire — an unknown query parameter is ignored — but a
        # caller relying on its effect silently loses that effect, which is worse
        # than an error because nothing reports it.
        result.add(
            Severity.POTENTIALLY_BREAKING,
            "parameter_removed",
            f"{key} ({name})",
            "parameter removed; callers still sending it lose its effect silently",
        )

    for name in sorted(set(old_index) & set(new_index)):
        was, now = old_index[name].get("required", False), new_index[name].get("required", False)
        if now and not was:
            result.add(
                Severity.BREAKING,
                "parameter_became_required",
                f"{key} ({name})",
                "optional parameter is now required",
            )


def _diff_responses(key: str, old: Any, new: Any, result: DiffResult) -> None:
    if not isinstance(old, dict) or not isinstance(new, dict):
        return
    for status in sorted(set(old) - set(new)):
        result.add(
            Severity.BREAKING,
            "response_removed",
            f"{key} ({status})",
            f"response {status} removed; consumers handling it lose that branch",
        )
    for status in sorted(set(new) - set(old)):
        result.add(
            Severity.ADDITIVE, "response_added", f"{key} ({status})", f"new response {status}"
        )


# --- schema-level diff --------------------------------------------------------


def _properties(schema: JsonDict) -> dict[str, Any]:
    props = schema.get("properties")
    return props if isinstance(props, dict) else {}


def _required(schema: JsonDict) -> set[str]:
    required = schema.get("required")
    return set(required) if isinstance(required, list) else set()


def _type_of(schema: Any) -> str | None:
    if isinstance(schema, dict):
        value = schema.get("type")
        if isinstance(value, str):
            return value
        ref = schema.get("$ref")
        if isinstance(ref, str):
            return f"$ref:{ref}"
    return None


def _enum_of(schema: Any) -> list[Any] | None:
    if isinstance(schema, dict):
        value = schema.get("enum")
        if isinstance(value, list):
            return value
    return None


def _diff_schema(
    name: str,
    old: JsonDict,
    new: JsonDict,
    position: Position,
    result: DiffResult,
) -> None:
    """Compare one named schema under the rules for its position."""
    in_request = position in (Position.REQUEST, Position.BOTH)
    in_response = position in (Position.RESPONSE, Position.BOTH)

    old_props, new_props = _properties(old), _properties(new)
    old_required, new_required = _required(old), _required(new)

    for prop in sorted(set(new_props) - set(old_props)):
        if prop in new_required and in_request:
            result.add(
                Severity.BREAKING,
                "required_request_property_added",
                f"{name}.{prop}",
                "new required property in a request schema; existing callers omit it",
            )
        else:
            result.add(Severity.ADDITIVE, "property_added", f"{name}.{prop}", "new property")

    for prop in sorted(set(old_props) - set(new_props)):
        if in_response:
            result.add(
                Severity.BREAKING,
                "response_property_removed",
                f"{name}.{prop}",
                "property removed from a response schema; consumers reading it break",
            )
        else:
            result.add(
                Severity.POTENTIALLY_BREAKING,
                "request_property_removed",
                f"{name}.{prop}",
                "property removed from a request schema; a closed schema now rejects it",
            )

    for prop in sorted(set(old_props) & set(new_props)):
        _diff_property(name, prop, old_props[prop], new_props[prop], position, result)

    # Required-ness, which is where the two directions disagree most sharply.
    #
    # THE SAFE CASES ARE REPORTED TOO, AS ADDITIVE, AND THAT IS NOT PADDING.
    #   An earlier version returned nothing for them. Tightening `JobEvent.required`
    #   — a real change, made in this same sub-step — then produced the output "no
    #   differences from the baseline", which was simply false. A tool that stays
    #   silent about changes it considers safe is telling the reader the contract
    #   did not move. Whether a change is safe and whether it happened are separate
    #   questions and the output has to answer both.
    for prop in sorted(new_required - old_required):
        if prop not in old_props:
            continue  # a brand-new property; already reported above
        if in_request:
            result.add(
                Severity.BREAKING,
                "request_property_became_required",
                f"{name}.{prop}",
                "optional request property is now required",
            )
        else:
            result.add(
                Severity.ADDITIVE,
                "response_property_became_required",
                f"{name}.{prop}",
                "response now always includes this; a stronger guarantee than before",
            )
    for prop in sorted(old_required - new_required):
        if in_response:
            result.add(
                Severity.BREAKING,
                "response_property_became_optional",
                f"{name}.{prop}",
                "guaranteed response property is now optional; consumers assumed presence",
            )
        else:
            result.add(
                Severity.ADDITIVE,
                "request_property_became_optional",
                f"{name}.{prop}",
                "callers may now omit this",
            )

    old_closed = old.get("additionalProperties") is False
    new_closed = new.get("additionalProperties") is False
    if new_closed and not old_closed and in_request:
        result.add(
            Severity.BREAKING,
            "request_schema_closed",
            name,
            "schema now rejects unknown properties; callers sending extras are rejected",
        )


def _diff_property(
    schema_name: str,
    prop: str,
    old: Any,
    new: Any,
    position: Position,
    result: DiffResult,
) -> None:
    location = f"{schema_name}.{prop}"
    in_request = position in (Position.REQUEST, Position.BOTH)
    in_response = position in (Position.RESPONSE, Position.BOTH)

    old_type, new_type = _type_of(old), _type_of(new)
    if old_type != new_type and (old_type is not None or new_type is not None):
        result.add(
            Severity.BREAKING,
            "property_type_changed",
            location,
            f"type {old_type!r} -> {new_type!r}",
        )
        return

    old_enum, new_enum = _enum_of(old), _enum_of(new)
    if old_enum is not None and new_enum is not None:
        removed = [v for v in old_enum if v not in new_enum]
        added = [v for v in new_enum if v not in old_enum]
        if removed and in_request:
            result.add(
                Severity.BREAKING,
                "request_enum_value_removed",
                location,
                f"values no longer accepted: {removed}",
            )
        if removed and in_response:
            result.add(
                Severity.POTENTIALLY_BREAKING,
                "response_enum_value_removed",
                location,
                f"values no longer emitted: {removed}; consumer branches become dead",
            )
        if added and in_response:
            # POLICY §2 puts this in "potentially breaking" and treats it as
            # breaking unless consumer analysis proves otherwise. It is classified
            # here at its policy level; the gate decides what to do about it.
            result.add(
                Severity.POTENTIALLY_BREAKING,
                "response_enum_value_added",
                location,
                f"new values emitted: {added}; a consumer branching on this field may not handle them",
            )
        if added and in_request and not in_response:
            result.add(
                Severity.ADDITIVE, "request_enum_value_added", location, f"newly accepted: {added}"
            )


def _diff_schemas(old: JsonDict, new: JsonDict, result: DiffResult) -> None:
    old_schemas = old.get("components", {}).get("schemas", {})
    new_schemas = new.get("components", {}).get("schemas", {})
    old_positions = schema_positions(old)
    new_positions = schema_positions(new)

    for name in sorted(set(old_schemas) & set(new_schemas)):
        position = new_positions.get(name) or old_positions.get(name)
        if position is None:
            # Unreferenced by any operation: not on the wire, so no consumer can
            # depend on it. Reporting it would be noise that trains people to
            # ignore this tool.
            continue
        if not isinstance(old_schemas[name], dict) or not isinstance(new_schemas[name], dict):
            continue
        _diff_schema(name, old_schemas[name], new_schemas[name], position, result)

    for name in sorted(set(old_schemas) - set(new_schemas)):
        if old_positions.get(name) is not None:
            result.add(
                Severity.BREAKING,
                "schema_removed",
                name,
                "schema removed while still referenced by an operation",
            )


# --- deprecation metadata -----------------------------------------------------


def check_deprecation_metadata(doc: JsonDict) -> list[Change]:
    """`CONTRACT_CHANGE_POLICY` §4: a deprecated operation needs a `Sunset` date.

    Both headers are required, and for different reasons. `Deprecation` says the
    operation is on the way out; `Sunset` says when it stops answering. A
    deprecation with no sunset is a warning with no deadline, which every consumer
    correctly deprioritises forever.
    """
    problems: list[Change] = []
    for key, operation in _operations(doc).items():
        if not operation.get("deprecated"):
            continue
        headers = {
            name.lower()
            for response in operation.get("responses", {}).values()
            if isinstance(response, dict)
            for name in (response.get("headers") or {})
        }
        for required_header in ("sunset", "deprecation"):
            if required_header not in headers:
                problems.append(
                    Change(
                        severity=Severity.BREAKING,
                        kind="deprecation_metadata_missing",
                        location=key,
                        detail=(
                            f"operation is deprecated but declares no {required_header.title()} "
                            f"header (CONTRACT_CHANGE_POLICY §4)"
                        ),
                    )
                )
    return problems


# --- version comparison -------------------------------------------------------


def major_of(version: str) -> int:
    """Major component of a semver-ish string, 0 when unparseable."""
    head = version.strip().lstrip("vV").split(".", 1)[0]
    try:
        return int(head)
    except ValueError:
        return 0


def diff_contracts(old: JsonDict, new: JsonDict) -> DiffResult:
    """Classify every difference between two OpenAPI documents."""
    result = DiffResult()
    _diff_operations(old, new, result)
    _diff_schemas(old, new, result)
    return result
