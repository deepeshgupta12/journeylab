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
# Requires the local stack: pnpm dev
set -uo pipefail
cd "$(dirname "$0")/../.."

PGC="docker exec -i journeylab-postgres psql -v ON_ERROR_STOP=1 -U journeylab -d journeylab"
pass=0; fail=0

ok()   { echo "  ok   $1"; pass=$((pass+1)); }
bad()  { echo "  FAIL $1"; fail=$((fail+1)); }

if ! docker ps --format '{{.Names}}' | grep -q '^journeylab-postgres$'; then
  echo "SKIP: local stack not running. Start with: pnpm dev"
  echo "      (R7 cannot be evaluated without the database — this is a SKIP, not a PASS.)"
  exit 2
fi

echo "=== applying migration 001 ==="
if $PGC -q -f - < db/migrations/001_identity_tenancy.sql >/tmp/jl_mig.log 2>&1; then
  echo "  migration applied"
else
  echo "  migration reported errors (may be idempotent re-run):"; tail -3 /tmp/jl_mig.log | sed 's/^/    /'
fi

# BUG-007: PRECONDITION GATE. Without this, a missing table makes every write
# assertion "pass" because the query ERRORS rather than being denied by policy.
# A security suite that passes when the schema is absent is worse than none.
missing=$($PGC -tAc "SELECT 5 - count(*) FROM pg_tables WHERE schemaname='public'
                     AND tablename IN ('organizations','users','roles','memberships','service_identities');" 2>/dev/null | tr -d ' ')
if [ "${missing:-5}" != "0" ]; then
  echo ""
  echo "ERROR: $missing expected table(s) missing — the schema is not in place."
  echo "       Refusing to run isolation assertions: they would report false passes."
  exit 1
fi
echo "  precondition: all 5 tables present"

echo ""
echo "=== seeding two tenants ==="
$PGC -q >/dev/null 2>&1 <<'SQL'
DELETE FROM memberships; DELETE FROM service_identities;
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
SQL
echo "  2 organizations, 2 users, 2 memberships"

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

forced=$($PGC -tAc "SELECT count(*) FROM pg_class WHERE relname IN ('memberships','service_identities','organizations') AND relforcerowsecurity;" 2>/dev/null | tr -d ' ')
[ "$forced" = "3" ] && ok "FORCE ROW LEVEL SECURITY set on all 3 tenant tables" \
                    || bad "only $forced of 3 tables have FORCE RLS"

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
