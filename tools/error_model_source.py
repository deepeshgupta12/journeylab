"""Parse ERROR_MODEL.md into the error-code register — STEP-004.01.

Single parser, imported by `gen_error_codes.py` (which writes the generated
module and the JSON Schema) and by the drift test (which proves both still match
the markdown). One implementation, so the generator and the drift gate cannot
disagree about what the document says.

This is `ADR-012` applied a second time. That ADR predicted the pattern would
recur — it said the shared parser made a second emitter additive — and STEP-003.06
already proved it once for the authorization matrix. The reasoning is identical:
two hand-maintained copies of an error register diverge, and the divergence is
silent. A client branches on a `code` the server no longer sends, or the document
promises a remediation the API never returns, and neither file looks wrong on its
own.

WHY THE DOCUMENT IS THE SOURCE AND NOT THE CODE
    `ERROR_MODEL.md` §3 is a product artefact: it states, per code, the HTTP
    status, the meaning, the remediation and the requirement it serves. That last
    column is the reason. An error code exists to satisfy a requirement, and the
    traceability belongs where a product owner will read it, not in a Python
    literal.
"""

from __future__ import annotations

import pathlib
import re
from typing import Final, NamedTuple

REPO: Final = pathlib.Path(__file__).resolve().parents[1]
ERROR_MODEL_MD: Final = REPO / "docs/product/04-contracts/ERROR_MODEL.md"

#: Codes whose row states something other than a bare integer status.
#:
#: The register is a product document and says useful things a machine cannot
#: parse — "200 + warning", "500 (internal), user-invisible", "internal",
#: "202 + tracked". Each is a deliberate statement about how the condition
#: surfaces, and each is resolved here EXPLICITLY rather than by a regex that
#: grabs the first number it sees.
#:
#: `None` means the condition never reaches the client as an HTTP error at all.
NON_NUMERIC_STATUS: Final[dict[str, int | None]] = {
    # "200 + warning" — sources disagreeing is not a failure. REQ-EVID-002 requires
    # both values stay visible, so this is a successful response carrying a warning.
    "evidence.conflicting_sources": None,
    # "500 (internal), user-invisible" — the model returned invalid structure. The
    # user sees the non-AI fallback, never this.
    "ai.schema_violation": None,
    # "503 (internal)" — budget exhausted; the user sees degraded output.
    "ai.budget_exceeded": None,
    # "internal" — injection detected in retrieved content. Dropped and alerted;
    # never surfaced.
    "ai.injection_detected": None,
    # "202 + tracked" — deletion is accepted and queued, not refused.
    "privacy.deletion_failed": 202,
    # "500 + **SEV1 alert**" — the client gets a plain 500 carrying nothing but a
    # correlation ID. The SEV1 is an operational consequence, not part of the
    # response: telling a caller that their request tripped a cross-tenant
    # detector confirms the boundary they were probing.
    "tenant.isolation_violation": 500,
}


class ErrorCode(NamedTuple):
    """One row of the register."""

    code: str
    """Machine-stable, dot-namespaced. Clients branch on this."""

    status: int | None
    """HTTP status, or None when the condition never reaches the client."""

    meaning: str
    remediation: str
    requirement: str | None
    """The requirement the code exists to serve, when the register names one."""

    @property
    def type_uri(self) -> str:
        """The RFC 9457 `type`. Stable forever once published.

        Derived from the code rather than stored, so the two cannot drift. The
        document says of `type`: "never changes meaning once published" — which
        makes deriving it from the code the safest possible construction, since
        changing the URI would require changing the code, and changing a code is
        already a breaking change under CONTRACT_CHANGE_POLICY.
        """
        return f"https://journeylab.app/problems/{self.code}"

    @property
    def client_visible(self) -> bool:
        return self.status is not None


_ROW = re.compile(r"^\|\s*`([a-z0-9_.]+)`\s*\|(.+)$")
_REQ = re.compile(r"REQ-[A-Z]+-\d+")


def _cells(row_body: str) -> list[str]:
    """Split the remainder of a markdown row into trimmed cells."""
    parts = [c.strip() for c in row_body.split("|")]
    # A trailing empty cell from the row's closing pipe.
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def parse_error_codes(markdown: str | None = None) -> list[ErrorCode]:
    """Read §3 of ERROR_MODEL.md into rows.

    Raises rather than returning a short list if the section cannot be found. A
    parser that silently yields nothing produces a generated file with no codes
    in it, a drift test that passes, and an API that cannot report any error by
    name — the exact vacuous-pass shape this repository keeps finding.
    """
    text = markdown if markdown is not None else ERROR_MODEL_MD.read_text(encoding="utf-8")

    if "## 3. Error code register" not in text:
        raise ValueError(
            "ERROR_MODEL.md has no '## 3. Error code register' section. "
            "The parser is keyed to that heading; if the document was "
            "restructured, this parser must be updated deliberately."
        )
    section = text.split("## 3. Error code register", 1)[1].split("\n## ", 1)[0]

    codes: list[ErrorCode] = []
    for line in section.splitlines():
        match = _ROW.match(line.strip())
        if match is None:
            continue
        code = match.group(1)
        cells = _cells(match.group(2))
        if len(cells) < 3:
            raise ValueError(f"register row for `{code}` has too few columns: {line!r}")

        raw_status, meaning, remediation = cells[0], cells[1], cells[2]
        requirement_cell = cells[3] if len(cells) > 3 else ""

        if code in NON_NUMERIC_STATUS:
            status = NON_NUMERIC_STATUS[code]
        elif raw_status.isdigit():
            status = int(raw_status)
        elif "/" in raw_status and all(p.strip().isdigit() for p in raw_status.split("/")):
            # "403/404" — the register states both because the two are deliberately
            # indistinguishable. The first is the one actually sent.
            status = int(raw_status.split("/")[0])
        else:
            raise ValueError(
                f"`{code}` has status {raw_status!r}, which is neither a number nor "
                f"a documented special case. Add it to NON_NUMERIC_STATUS with the "
                f"reason, rather than making the regex looser."
            )

        found = _REQ.search(requirement_cell)
        codes.append(
            ErrorCode(
                code=code,
                status=status,
                meaning=meaning,
                remediation=remediation,
                requirement=found.group(0) if found else None,
            )
        )

    if not codes:
        raise ValueError("parsed zero error codes from the register — the format changed")
    return codes
