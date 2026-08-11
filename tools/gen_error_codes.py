"""Emit the error-code register into code and schema — STEP-004.01.

Run: uv run python tools/gen_error_codes.py

Two emitters over one parser (`error_model_source.py`), which is `ADR-012` for the
second time. The Python module is what the API raises; the JSON Schema is what the
contract publishes. Both come from `ERROR_MODEL.md`, so a code cannot exist in one
and not the other.

BUG-012: a generator must emit output that passes the project's own checks. The
Python here is written to satisfy `ruff format` and `ruff check` as configured,
and the drift test regenerates and compares — so an edit to the markdown without a
rebuild fails CI rather than silently diverging.
"""

from __future__ import annotations

import json

from error_model_source import REPO, ErrorCode, parse_error_codes

PY_OUT = REPO / "apps/api/src/conventions/error_codes.py"
SCHEMA_OUT = REPO / "contracts/schemas/error-codes.json"


def render_python(codes: list[ErrorCode]) -> str:
    lines: list[str] = [
        '"""GENERATED from docs/product/04-contracts/ERROR_MODEL.md — do not edit by hand.',
        "",
        "Rebuild: uv run python tools/gen_error_codes.py",
        "STEP-004.01 · REQ-PLAT-005",
        "",
        "The register is a product document; this module is its machine form. A code",
        "that is not in the markdown cannot be raised, and a code in the markdown that",
        "is never raised is still declared here — the contract is the document.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Final, NamedTuple",
        "",
        "",
        "class ErrorCodeSpec(NamedTuple):",
        '    """One row of the register, as data."""',
        "",
        "    code: str",
        "    status: int | None",
        "    meaning: str",
        "    remediation: str",
        "    requirement: str | None",
        "",
        "    @property",
        "    def type_uri(self) -> str:",
        '        """RFC 9457 `type`. Stable forever once published."""',
        '        return f"https://journeylab.app/problems/{self.code}"',
        "",
        "    @property",
        "    def client_visible(self) -> bool:",
        '        """False when the condition never reaches the caller as an HTTP error."""',
        "        return self.status is not None",
        "",
        "",
        "ERROR_CODES: Final[dict[str, ErrorCodeSpec]] = {",
    ]
    for c in codes:
        status = "None" if c.status is None else str(c.status)
        requirement = "None" if c.requirement is None else f'"{c.requirement}"'
        lines += [
            f'    "{c.code}": ErrorCodeSpec(',
            f'        code="{c.code}",',
            f"        status={status},",
            f"        meaning={_py_str(c.meaning)},",
            f"        remediation={_py_str(c.remediation)},",
            f"        requirement={requirement},",
            "    ),",
        ]
    lines += [
        "}",
        "",
        "#: Codes an API response may carry. The rest are internal conditions that",
        "#: surface as a fallback or a warning, never as an error to the caller.",
        "CLIENT_VISIBLE: Final[frozenset[str]] = frozenset(",
        "    code for code, spec in ERROR_CODES.items() if spec.client_visible",
        ")",
        "",
    ]
    return "\n".join(lines)


def _py_str(value: str) -> str:
    """Quote a cell for Python, stripping the markdown emphasis the table uses."""
    cleaned = value.replace("**", "").replace("`", "").strip()
    return json.dumps(cleaned)


def render_schema(codes: list[ErrorCode]) -> str:
    """The published enum of error codes.

    JSON Schema 2020-12, matching OpenAPI 3.1's dialect so `contracts/openapi.yaml`
    can reference it without a translation step.
    """
    visible = [c for c in codes if c.client_visible]
    document = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://journeylab.app/schemas/error-codes.json",
        "title": "JourneyLab error codes",
        "description": (
            "GENERATED from docs/product/04-contracts/ERROR_MODEL.md — do not edit by "
            "hand. Rebuild: uv run python tools/gen_error_codes.py. Only "
            "client-visible codes appear here; internal conditions surface as a "
            "fallback or a warning and are never returned to a caller."
        ),
        "type": "string",
        "enum": [c.code for c in visible],
        "x-journeylab-codes": {
            c.code: {
                "status": c.status,
                "type": c.type_uri,
                "meaning": c.meaning.replace("**", "").replace("`", ""),
                "remediation": c.remediation.replace("**", "").replace("`", ""),
                "requirement": c.requirement,
            }
            for c in visible
        },
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    codes = parse_error_codes()

    PY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_OUT.parent.mkdir(parents=True, exist_ok=True)

    PY_OUT.write_text(render_python(codes), encoding="utf-8")
    SCHEMA_OUT.write_text(render_schema(codes), encoding="utf-8")

    visible = sum(1 for c in codes if c.client_visible)
    print(f"wrote {PY_OUT.relative_to(REPO)} ({len(codes)} codes)")
    print(f"wrote {SCHEMA_OUT.relative_to(REPO)} ({visible} client-visible)")


if __name__ == "__main__":
    main()
