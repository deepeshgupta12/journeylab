"""Generate the TypeScript authorization matrix — STEP-003.06.

ADR-012 predicted this file and set its constraint:

    "if the frontend later wants to grey out forbidden actions, it needs the same
     matrix in TypeScript. That must be generated from the same markdown, never
     hand-maintained — two hand-written copies of an authorization matrix will
     diverge, and the divergence will be silent."

So this is a SECOND EMITTER over the same parser, not a second source. It reads
`docs/product/04-contracts/AUTHORIZATION_MATRIX.md` through
`tools/authz_matrix_source.py`, exactly as the Python emitter does.

    python3 tools/gen_authz_matrix_ts.py

`packages/ui/src/nav/nav.test.tsx` re-parses the markdown and fails if the
generated file disagrees, so an edit without a regeneration cannot merge.
"""

from __future__ import annotations

import pathlib
import subprocess

from authz_matrix_source import REPO, parse_matrix

HEADER = """/**
 * GENERATED from docs/product/04-contracts/AUTHORIZATION_MATRIX.md — do not edit by hand.
 *
 * Regenerate: python3 tools/gen_authz_matrix_ts.py
 *
 * THIS IS PRESENTATION DATA. IT IS NOT AN AUTHORIZATION CONTROL.
 *   The server decides (apps/api/src/authz/policy.py, STEP-002.03). This copy
 *   exists so the interface can avoid offering an action that would be refused —
 *   a courtesy, not a gate. Anyone can edit the bundle that contains it.
 *
 * It is generated from the SAME markdown as the Python matrix (ADR-012), so the
 * two cannot drift apart. A drift test fails if they do.
 */

"""


def main() -> None:
    operations, roles, table = parse_matrix()

    lines = [HEADER, "export const OPERATIONS = ["]
    for op in operations:
        lines.append(f'  "{op.key}",')
    lines += ["] as const;", "", "export const ROLES = ["]
    for role in roles:
        lines.append(f'  "{role}",')
    lines += [
        "] as const;",
        "",
        "export type Operation = (typeof OPERATIONS)[number];",
        "export type Role = (typeof ROLES)[number];",
        "",
        "export interface Rule {",
        "  readonly allow: boolean;",
        "  readonly audit: boolean;",
        "  readonly condition: string | null;",
        "}",
        "",
        "export const MATRIX: Readonly<Record<string, Rule>> = {",
    ]
    for op in operations:
        for role in roles:
            cell = table[(op.key, role)]
            cond = "null" if cell.condition is None else f'"{cell.condition}"'
            allow = "true" if cell.allow else "false"
            audit = "true" if cell.audit else "false"
            lines.append(
                f'  "{op.key}:{role}": {{ allow: {allow}, audit: {audit}, condition: {cond} }},'
            )
    lines += [
        "};",
        "",
        "/** Presentation-only check. The server is the control. */",
        "export function mayAttempt(operation: Operation, role: Role): boolean {",
        "  const rule = MATRIX[`${operation}:${role}`];",
        "  // Unknown pairing hides the item. Deny-by-default matches the server, and a",
        "  // missing rule is a generation bug rather than a permission.",
        "  if (rule === undefined) return false;",
        "  return rule.allow;",
        "}",
        "",
    ]

    out = pathlib.Path(REPO / "packages/ui/src/nav/authz-matrix.ts")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))

    # BUG-012: a generator must emit code that passes the project's own checks.
    for cmd in (
        ["pnpm", "exec", "biome", "check", "--write", str(out)],
        ["pnpm", "exec", "biome", "format", "--write", str(out)],
    ):
        subprocess.run(cmd, cwd=REPO, check=False, capture_output=True)  # noqa: S603

    print(f"wrote {out.relative_to(REPO)}: {len(operations)}x{len(roles)} = {len(table)} cells")


if __name__ == "__main__":
    main()
