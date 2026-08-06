"""Generate apps/api/src/authz/matrix.py from AUTHORIZATION_MATRIX.md.

Run manually after editing the matrix; the output is committed. The drift gate in
tests/api/test_authorization_matrix_sync.py fails CI if the two disagree.

    python3 tools/gen_authz_matrix.py
"""

from __future__ import annotations

import pathlib

from authz_matrix_source import REPO, parse_matrix

HEADER = '''"""GENERATED from docs/product/04-contracts/AUTHORIZATION_MATRIX.md — do not edit by hand.

Regenerate with `python3 tools/gen_authz_matrix.py`.
`tests/api/test_authorization_matrix_sync.py` re-parses the markdown and fails if this
file and the matrix disagree on any cell, so a matrix change without a regeneration
cannot merge (STEP-002.03, REQ-SEC-004).
"""

from __future__ import annotations

from .roles import Operation, Role, Rule

'''


def main() -> None:
    operations, roles, table = parse_matrix()
    lines = [HEADER, "OPERATIONS: dict[Operation, str] = {"]
    for op in operations:
        lines.append(f'    Operation.{op.key.upper()}: "{op.api}",')
    lines += ["}", "", "MATRIX: dict[tuple[Operation, Role], Rule] = {"]
    for op in operations:
        for role in roles:
            cell = table[(op.key, role)]
            cond = "None" if cell.condition is None else f'"{cell.condition}"'
            lines.append(
                f"    (Operation.{op.key.upper()}, Role.{role.upper()}): "
                f"Rule(allow={cell.allow}, audit={cell.audit}, condition={cond}),"
            )
    lines += ["}", ""]

    out = pathlib.Path(REPO / "apps/api/src/authz/matrix.py")
    out.write_text("\n".join(lines))
    print(
        f"wrote {out.relative_to(REPO)}: {len(operations)} operations x {len(roles)} roles "
        f"= {len(table)} cells"
    )


if __name__ == "__main__":
    main()
