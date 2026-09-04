#!/usr/bin/env bash
# Cross-tenant isolation tests — TST-SEC-001, TST-SEC-002 · STEP-002.01
#
# THIS SUITE ESTABLISHES REGRESSION CHECK R7. From here on it runs at every
# sub-step, and R7 is the one check documented as non-negotiable.
#
# Applies BR-008 §9: pooling behaviour and FORCE RLS are TESTED, not assumed.
#
# Includes a META-TEST: a deliberately weakened policy must make the suite fail.
# A passing isolation suite that would also pass with RLS disabled is worse than
# no suite — it manufactures confidence. (BUG-004's lesson.)
#
# Requires a database. Locally: pnpm dev
#
# HOW IT CONNECTS, AND WHY THAT CHANGED (STEP-001.07, BUG-023)
#   This used `docker exec -i journeylab-postgres psql`, which requires a
#   container with that exact name on the same host. That works on a laptop and
#   nowhere else — so R7, the check CLAUDE.md calls non-negotiable, could not run
#   in CI and never had.
#
#   It now connects over TCP using a DSN, so the same script runs against the dev
#   stack, a GitHub Actions service container, or the mirror. `docker exec` is
#   kept only as a fallback for a machine with no psql client installed.
set -uo pipefail
cd "$(dirname "$0")/../.."

DSN="${JOURNEYLAB_DATABASE_URL:-${JOURNEYLAB_TEST_DSN:-postgresql://journeylab:journeylab_dev_only@127.0.0.1:5700/journeylab}}"

# BUG-030. A DECLARED TARGET IS NEVER SILENTLY SWAPPED.
#   The container fallback below exists so a developer without libpq is not
#   blocked. It used to apply whenever `psql` was absent — including when the
#   caller had explicitly named a database in the environment.
#
#   The consequence was that R7 printed "PASS — cross-tenant isolation enforced at
#   the database" while connected to a completely different database from the one
#   it was told to use. Pointed at a dead port it still passed, against the local
#   container, because the DSN was discarded rather than honoured.
#
#   R7 is the check this repository calls non-negotiable. A non-negotiable check
#   that can be aimed somewhere else without saying so is worse than one that
#   fails: it produces confident evidence about the wrong system. So an explicitly
#   declared DSN is now used or the run stops — the fallback applies only when
#   nobody declared anything.
DECLARED_DSN="${JOURNEYLAB_DATABASE_URL:-${JOURNEYLAB_TEST_DSN:-}}"

if command -v psql >/dev/null 2>&1; then
  PGC="psql -v ON_ERROR_STOP=1 $DSN"
  CONNECTION="psql -> $DSN"
elif [ -n "$DECLARED_DSN" ]; then
  echo "SKIP: a database was declared ($DECLARED_DSN) but psql is not installed."
  echo "      Refusing to fall back to the local container: R7 would report PASS"
  echo "      about a database nobody asked it to test (BUG-030)."
  echo "      (R7 cannot be evaluated here — this is a SKIP, not a PASS.)"
  exit 2
elif docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^journeylab-postgres$'; then
  # No psql, and nobody named a database. The container is the only candidate, so
  # using it invents nothing.
  PGC="docker exec -i journeylab-postgres psql -v ON_ERROR_STOP=1 -U journeylab -d journeylab"
  CONNECTION="docker exec journeylab-postgres (no DSN declared)"
else
  echo "SKIP: no psql client and no journeylab-postgres container."
  echo "      Start the stack with: pnpm dev"
  echo "      (R7 cannot be evaluated without the database — this is a SKIP, not a PASS.)"
  exit 2
fi

pass=0; fail=0

ok()   { echo "  ok   $1"; pass=$((pass+1)); }
bad()  { echo "  FAIL $1"; fail=$((fail+1)); }

# A SKIP IS NOT A PASS, AND NOW SOMETHING OTHER THAN A HUMAN ENFORCES THAT.
# Where a database is declared to be expected, its absence is a failure. Without
# this, a renamed service or a moved port returns R7 to skipping under a green
# build — which is precisely how BUG-023 survived from STEP-002.01.
if ! $PGC -tAc "SELECT 1;" >/dev/null 2>&1; then
  if [ "${JOURNEYLAB_REQUIRE_DB:-}" != "" ] && [ "${JOURNEYLAB_REQUIRE_DB:-}" != "0" ]; then
    echo "FAIL: JOURNEYLAB_REQUIRE_DB is set but no database is reachable."
    echo "      Connection attempted: $CONNECTION"
    echo "      R7 is non-negotiable; refusing to report a skip as success."
    exit 1
  fi
  echo "SKIP: no database reachable via $CONNECTION"
  echo "      (R7 cannot be evaluated without the database — this is a SKIP, not a PASS.)"
  exit 2
fi
echo "  connection: $CONNECTION"

# STEP-006.01 ADDED 010. The FORCE-RLS assertion below is derived from the schema
# rather than a list, which means it only covers tables that EXIST when it runs. On
# a database where this script applies a subset of migrations, the domain tables
# would be absent, the derived query would find nothing to complain about, and the
# assertion would pass having checked thirteen tables that were not there.
#
# A derived check is only as complete as the schema in front of it. That is the
# half of "derived, not listed" the original comment did not say.
echo "=== applying migrations 001, 003 and 010 ==="
for mig in db/migrations/001_identity_tenancy.sql db/migrations/003_sessions.sql db/migrations/010_domain.sql; do
  if $PGC -q -f - < "$mig" >/tmp/jl_mig.log 2>&1; then
    echo "  applied $(basename "$mig")"
  else
    echo "  $(basename "$mig") reported errors (may be idempotent re-run):"; tail -3 /tmp/jl_mig.log | sed 's/^/    /'
  fi
done

# BUG-007: PRECONDITION GATE. Without this, a missing table makes every write
# assertion "pass" because the query ERRORS rather than being denied by policy.
# A security suite that passes when the schema is absent is worse than none.
# BUG-009: an unreachable database and a missing schema are DIFFERENT faults, and
# the first version conflated them — it swallowed stderr and fell back to "5 tables
# missing" whenever the query returned nothing. During the Postgres first-boot
# restart it printed "expected table(s) missing" while all the tables existed.
#
# STEP-002.08 raised the count 5 -> 6 for `sessions`. The literal appears in four
# places here; a mismatch fails closed with a nonsense count like -1, which is
# what happened when only two of them were updated.
# Fail-closed was right; the diagnosis sent the reader hunting the wrong problem.
if ! $PGC -tAc "SELECT 1;" >/dev/null 2>/tmp/jl_conn.err; then
  echo ""
  echo "ERROR: cannot reach the database — this is NOT a schema problem."
  echo "       $(head -1 /tmp/jl_conn.err)"
  echo "       If the stack just started, the server may still be restarting after"
  echo "       first-boot init (see BUG-009). Refusing to run: R7 is UNEVALUATED."
  exit 1
fi

missing=$($PGC -tAc "SELECT 6 - count(*) FROM pg_tables WHERE schemaname='public'
                     AND tablename IN ('organizations','users','roles','memberships','service_identities','sessions');" 2>/dev/null | tr -d ' ')
if [ "${missing:-6}" != "0" ]; then
  echo ""
  echo "ERROR: ${missing:-all 6} expected table(s) missing — the schema is not in place."
  echo "       Refusing to run isolation assertions: they would report false passes."
  exit 1
fi
echo "  precondition: all 6 tenant-scoped tables present"

echo ""
echo "=== seeding two tenants ==="
$PGC -q >/dev/null 2>&1 <<'SQL'
DELETE FROM sessions; DELETE FROM memberships; DELETE FROM service_identities;
DELETE FROM users WHERE email IN ('a@example.test','b@example.test');
DELETE FROM organizations WHERE slug IN ('tenant-a','tenant-b');
INSERT INTO organizations (id, slug, display_name) VALUES
  ('11111111-1111-1111-1111-111111111111','tenant-a','Tenant A'),
  ('22222222-2222-2222-2222-222222222222','tenant-b','Tenant B');
INSERT INTO users (id, email) VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','a@example.test'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','b@example.test');
INSERT INTO memberships (organization_id, user_id, role_key) VALUES
  ('11111111-1111-1111-1111-111111111111','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','trip_owner'),
  ('22222222-2222-2222-2222-222222222222','bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','trip_owner');
-- STEP-002.08: sessions are tenant-scoped, so R7 covers them too. A live session
-- is the most direct cross-tenant target there is: reading one is reading a
-- credential's whereabouts, and revoking one is denial of service against
-- another tenant's user.
INSERT INTO sessions (organization_id, user_id, token_hash, expires_at) VALUES
  ('11111111-1111-1111-1111-111111111111','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','hash-a', now() + interval '1 hour'),
  ('22222222-2222-2222-2222-222222222222','bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','hash-b', now() + interval '1 hour');
SQL
echo "  2 organizations, 2 users, 2 memberships, 2 sessions"

# helper: run SQL as the non-owner application role with a tenant context
as_tenant() {
  local org="$1" sql="$2"
  # psql -c with multiple statements echoes a status line ("SET") per statement.
  # Take only the LAST line: the actual result. Without this, comparisons match
  # against "SET\nSET\n1" and every assertion fails for the wrong reason.
  $PGC -tAc "SET ROLE journeylab_app; SET LOCAL app.current_org = '$org'; $sql" 2>/dev/null | tail -1 | tr -d ' '
}

echo ""
echo "=== TST-SEC-002: cross-tenant read ==="
a_sees=$(as_tenant '11111111-1111-1111-1111-111111111111' "SELECT count(*) FROM memberships;")
[ "$a_sees" = "1" ] && ok "tenant A sees exactly its own 1 membership (saw $a_sees)" \
                    || bad "tenant A saw '$a_sees' rows, expected 1"

b_sees=$(as_tenant '22222222-2222-2222-2222-222222222222' "SELECT count(*) FROM memberships;")
[ "$b_sees" = "1" ] && ok "tenant B sees exactly its own 1 membership (saw $b_sees)" \
                    || bad "tenant B saw '$b_sees' rows, expected 1"

foreign=$(as_tenant '11111111-1111-1111-1111-111111111111' \
  "SELECT count(*) FROM memberships WHERE organization_id='22222222-2222-2222-2222-222222222222';")
[ "$foreign" = "0" ] && ok "tenant A cannot read tenant B rows even when naming them explicitly" \
                     || bad "tenant A read $foreign of tenant B's rows"

echo ""
echo "=== STEP-002.08: sessions are tenant-scoped (TST-SEC-001x) ==="
sess_a=$(as_tenant '11111111-1111-1111-1111-111111111111' "SELECT count(*) FROM sessions;")
[ "$sess_a" = "1" ] && ok "tenant A sees exactly its own 1 session (saw $sess_a)" \
                    || bad "tenant A saw '$sess_a' session rows, expected 1"

sess_foreign=$(as_tenant '11111111-1111-1111-1111-111111111111' \
  "SELECT count(*) FROM sessions WHERE organization_id='22222222-2222-2222-2222-222222222222';")
[ "$sess_foreign" = "0" ] && ok "tenant A cannot read tenant B's sessions even when naming them" \
                          || bad "tenant A read $sess_foreign of tenant B's sessions"

# Revoking across a tenant boundary is denial of service, not disclosure — a
# different harm from a cross-tenant read and worth its own assertion.
revoked_across=$(as_tenant '11111111-1111-1111-1111-111111111111' \
  "WITH u AS (UPDATE sessions SET revoked_at=now(), revoked_reason='administrative'
              WHERE organization_id='22222222-2222-2222-2222-222222222222' RETURNING 1)
   SELECT count(*) FROM u;")
[ "$revoked_across" = "0" ] && ok "tenant A cannot revoke tenant B's session (0 rows affected)" \
                            || bad "tenant A revoked $revoked_across of tenant B's sessions"

still_live=$(as_tenant '22222222-2222-2222-2222-222222222222' \
  "SELECT count(*) FROM sessions WHERE revoked_at IS NULL;")
[ "$still_live" = "1" ] && ok "tenant B's session is still live after A's attempt" \
                        || bad "tenant B has '$still_live' live sessions, expected 1"

# No DELETE privilege at all: "revocation never deletes" is enforced by the
# grant, not by remembering to write UPDATE.
del=$($PGC -tAc "SET ROLE journeylab_app; SET LOCAL app.current_org='11111111-1111-1111-1111-111111111111';
                 DELETE FROM sessions;" 2>&1 | tail -1)
case "$del" in
  *"permission denied"*) ok "the application role cannot DELETE a session at all" ;;
  *) bad "DELETE on sessions was not refused by privilege (got: $del)" ;;
esac

echo ""
echo "=== REQ-SEC-001: missing tenant context denies access (deny-by-default) ==="
nocontext=$($PGC -tAc "SET ROLE journeylab_app; SELECT count(*) FROM memberships;" 2>/dev/null | tail -1 | tr -d ' ')
[ "$nocontext" = "0" ] && ok "no tenant context -> 0 rows visible" \
                       || bad "no context returned '$nocontext' rows, expected 0"

echo ""
echo "=== TST-SEC-002: cross-tenant WRITE must be rejected ==="
# BUG-007: assert on the ERROR TEXT, not merely on non-zero exit. A failed query
# and a policy denial both exit non-zero; only one of them is the security control.
ins_err=$($PGC -tAc "SET ROLE journeylab_app; SET LOCAL app.current_org = '11111111-1111-1111-1111-111111111111';
  INSERT INTO memberships (organization_id,user_id,role_key)
  VALUES ('22222222-2222-2222-2222-222222222222','aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','trip_owner');" 2>&1)
if echo "$ins_err" | grep -qi 'row-level security'; then
  ok "tenant A INSERT into tenant B denied BY POLICY (row-level security violation)"
elif echo "$ins_err" | grep -qiE 'does not exist|relation'; then
  bad "INSERT failed because of a schema error, not a policy denial: $(echo "$ins_err" | head -1)"
else
  bad "tenant A INSERT was not denied by policy — got: $(echo "$ins_err" | head -1)"
fi

updated=$(as_tenant '11111111-1111-1111-1111-111111111111' \
  "WITH u AS (UPDATE memberships SET role_key='trip_viewer'
   WHERE organization_id='22222222-2222-2222-2222-222222222222' RETURNING 1)
   SELECT count(*) FROM u;")
[ "$updated" = "0" ] && ok "tenant A cannot UPDATE tenant B rows (0 affected)" \
                     || bad "tenant A updated $updated tenant B row(s)"

deleted=$(as_tenant '11111111-1111-1111-1111-111111111111' \
  "WITH d AS (DELETE FROM memberships
   WHERE organization_id='22222222-2222-2222-2222-222222222222' RETURNING 1)
   SELECT count(*) FROM d;")
[ "$deleted" = "0" ] && ok "tenant A cannot DELETE tenant B rows (0 affected)" \
                     || bad "tenant A deleted $deleted tenant B row(s)"

echo ""
echo "=== BR-008 §9: FORCE RLS — the application role cannot bypass ==="
bypass=$($PGC -tAc "SELECT rolbypassrls FROM pg_roles WHERE rolname='journeylab_app';" 2>/dev/null | tr -d ' ')
[ "$bypass" = "f" ] && ok "journeylab_app has NOBYPASSRLS" || bad "journeylab_app can bypass RLS (rolbypassrls=$bypass)"

# DERIVED, NOT LISTED. This asserted a hardcoded list of three tables, so adding
# `sessions` in STEP-002.08 would have left the new table's FORCE RLS unchecked
# while the assertion still passed — the same "asserting the current extent of
# something designed to extend" pattern as BUG-021.
#
# The property is: every table carrying a tenant column must FORCE RLS. Derive the
# set from the schema and the next tenant-scoped table is covered on the day it is
# created, by whoever creates it, without them having to know this file exists.
unforced=$($PGC -tAc "
  SELECT coalesce(string_agg(c.relname, ','), '')
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
  WHERE c.relkind = 'r'
    AND NOT c.relforcerowsecurity
    AND EXISTS (SELECT 1 FROM information_schema.columns col
                WHERE col.table_schema='public' AND col.table_name=c.relname
                  AND col.column_name='organization_id');" 2>/dev/null | tr -d ' ')
[ -z "$unforced" ] && ok "every table with an organization_id has FORCE ROW LEVEL SECURITY" \
                   || bad "tenant-scoped tables WITHOUT FORCE RLS: $unforced"

# `organizations` is tenant-scoped by its own id rather than by organization_id,
# so the derived query above cannot see it. Named explicitly for that reason.
org_forced=$($PGC -tAc "SELECT relforcerowsecurity FROM pg_class WHERE relname='organizations';" 2>/dev/null | tr -d ' ')
[ "$org_forced" = "t" ] && ok "organizations forces RLS (scoped by id, not organization_id)" \
                        || bad "organizations does not force RLS"

echo ""
echo "=== BR-008 §9: pooling — context must NOT leak across transactions ==="
# SET LOCAL is transaction-scoped. On the SAME connection, a later transaction
# without context must see nothing. This is the pooled-connection leak scenario.
leak=$($PGC -tAc "
  SET ROLE journeylab_app;
  BEGIN; SET LOCAL app.current_org = '11111111-1111-1111-1111-111111111111';
  SELECT count(*) FROM memberships; COMMIT;
  SELECT count(*) FROM memberships;" 2>/dev/null | tail -1 | tr -d ' ')
[ "$leak" = "0" ] && ok "tenant context does not survive COMMIT (no pooled leak)" \
                  || bad "context leaked past COMMIT — saw $leak rows, expected 0"

echo ""
echo "=== META-TEST: a weakened policy MUST make this suite fail ==="
$PGC -q -c "DROP POLICY IF EXISTS memberships_tenant_isolation ON memberships;
            CREATE POLICY memberships_tenant_isolation ON memberships USING (true) WITH CHECK (true);" >/dev/null 2>&1
weak=$(as_tenant '11111111-1111-1111-1111-111111111111' "SELECT count(*) FROM memberships;")
$PGC -q -c "DROP POLICY IF EXISTS memberships_tenant_isolation ON memberships;
            CREATE POLICY memberships_tenant_isolation ON memberships
              USING (organization_id = app_current_org())
              WITH CHECK (organization_id = app_current_org());" >/dev/null 2>&1
if [ "$weak" = "2" ]; then
  ok "weakened policy exposed both tenants ($weak rows) — suite has real detection power"
else
  bad "weakened policy still returned '$weak' rows: the tests may not be measuring RLS at all"
fi
restored=$(as_tenant '11111111-1111-1111-1111-111111111111' "SELECT count(*) FROM memberships;")
[ "$restored" = "1" ] && ok "policy restored, isolation intact" || bad "policy not restored (saw $restored)"

echo ""
echo "════════════════════════════════════════"
echo "  R7 assertions passed: $pass"
echo "  R7 assertions failed: $fail"
[ "$fail" -gt 0 ] && { echo "  RESULT: FAIL — tenant isolation is not intact. This is SEV1."; exit 1; }
echo "  RESULT: PASS — cross-tenant isolation enforced at the database."
exit 0
