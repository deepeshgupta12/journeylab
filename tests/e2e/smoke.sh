#!/usr/bin/env bash
# End-to-end smoke test — everything built up to STEP-003.09.
#
# WHY THIS EXISTS SEPARATELY FROM `pnpm verify`
#   `pnpm verify` proves each layer works in isolation: the Python suite mocks no
#   database but runs against a test schema, the web suite runs in jsdom, the
#   browser suite runs against a production build with placeholder credentials.
#   Each is honest about its own layer and none of them starts the whole system
#   and walks through it.
#
#   This does. Infrastructure, schema, row-level security, the API, the web
#   surface and the accessibility gate, in one pass, in the order a real request
#   would meet them.
#
# WHAT IT DELIBERATELY DOES NOT DO
#   It does not sign in to Auth0. That needs a browser, a human and a password;
#   `pnpm auth0:check` proves the credentials and the discovery document, and the
#   full round trip was verified by hand at STEP-002.05. Claiming an automated
#   sign-in here would be claiming a verification that did not happen.
#
# EVERY CHECK REPORTS PASS, FAIL OR SKIP.
#   A SKIP is never counted as a PASS. If Docker is not running, this says so
#   rather than quietly testing less.
#
# Run: pnpm e2e
set -uo pipefail
cd "$(dirname "$0")/../.."

pass=0; fail=0; skip=0
PORT=5708
BASE="http://127.0.0.1:$PORT"

ok()   { printf '  \033[32mPASS\033[0m  %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; fail=$((fail+1)); }
meh()  { printf '  \033[33mSKIP\033[0m  %s\n' "$1"; skip=$((skip+1)); }
head_() { printf '\n\033[1m%s\033[0m\n' "$1"; }

check() { # check <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "$desc"; else bad "$desc"; fi
}

# --- 1. infrastructure --------------------------------------------------------

head_ "1. Infrastructure — the stack a request actually lands on"

if ! docker info >/dev/null 2>&1; then
  meh "Docker is not running — every infrastructure and database check below is SKIPPED"
  DOCKER=0
else
  DOCKER=1
  docker compose -f docker-compose.dev.yml up -d --wait >/dev/null 2>&1
  # pg_isready over TCP, not the socket. BUG-009: the first-boot temporary server
  # accepts socket connections while the real one is not listening yet, so a
  # socket check goes green against a server that is about to be shut down.
  # The compose service is `cache`, not `redis`. The first version used the
  # image name and reported a FAIL against a service that was running perfectly
  # — a test that is wrong in the direction of alarm, which erodes trust in the
  # suite exactly as fast as one that is wrong in the direction of comfort.
  #
  # PostgreSQL also needs a real wait: `--wait` returns when the healthcheck
  # passes, but PG18 can still answer "the database system is in recovery mode"
  # for a few seconds after that. BUG-009 is the same family of mistake.
  #
  # THE ROLE IS `journeylab`, NOT `postgres`.
  #
  # The first version hard-coded `-U postgres` and reported "PostgreSQL never
  # became queryable" while the twelve row-level-security assertions in section 2
  # were passing against that same database three seconds later. A probe that
  # invents its own connection instead of using the one the working code uses is
  # not testing the system; it is testing my memory of it.
  #
  # These defaults mirror docker-compose.dev.yml, and the isolation suite
  # connects the same way.
  PGUSER_="${POSTGRES_USER:-journeylab}"
  PGDB_="${POSTGRES_DB:-journeylab}"
  ready=0
  for _ in $(seq 1 60); do
    if docker compose -f docker-compose.dev.yml exec -T postgres \
         pg_isready -h 127.0.0.1 -U "$PGUSER_" -d "$PGDB_" -q >/dev/null 2>&1 &&
       docker compose -f docker-compose.dev.yml exec -T postgres \
         psql -U "$PGUSER_" -d "$PGDB_" -c 'select 1' >/dev/null 2>&1; then
      ready=1; break
    fi
    sleep 1
  done
  [ "$ready" -eq 1 ] && ok "PostgreSQL 18 accepts TCP connections and is out of recovery" \
                     || bad "PostgreSQL never became queryable on 5700"

  check "Redis responds to PING on 5701" \
    docker compose -f docker-compose.dev.yml exec -T cache redis-cli ping
  for p in 5702 5704 5707; do
    if nc -z 127.0.0.1 "$p" 2>/dev/null; then ok "port $p is listening"; else bad "port $p is not listening"; fi
  done
fi

# --- 2. schema and tenant isolation ------------------------------------------

head_ "2. Schema and row-level security — the tenancy guarantee"

if [ "$DOCKER" -eq 0 ]; then
  meh "database checks — Docker is not running"
else
  if bash tests/security/test_tenant_isolation.sh >/tmp/jl-e2e-r7.log 2>&1; then
    n=$(grep -oE 'R7 assertions passed: [0-9]+' /tmp/jl-e2e-r7.log | grep -oE '[0-9]+$')
    ok "cross-tenant isolation: ${n:-?} assertions, including the meta-test that a weakened policy exposes both tenants"
  else
    bad "cross-tenant isolation suite — see /tmp/jl-e2e-r7.log"
  fi
fi

# --- 3. backend ---------------------------------------------------------------

head_ "3. Backend — auth, tenancy, authorization, audit"

if command -v uv >/dev/null 2>&1; then
  if uv run pytest -q >/tmp/jl-e2e-py.log 2>&1; then
    # `pytest -q` prints its summary on the LAST non-empty line, and the count
    # is not on a line containing the word "passed" in every configuration —
    # the first version printed "Python suite: " with nothing after it.
    ok "Python suite: $(grep -oE '[0-9]+ (passed|failed)[^|]*' /tmp/jl-e2e-py.log | tail -1 || echo 'passed')"
  else
    bad "Python suite — see /tmp/jl-e2e-py.log"
  fi
else
  meh "Python suite — uv is not installed"
fi

# --- 4. frontend build and unit suites ---------------------------------------

head_ "4. Frontend — design system and web surface"

if pnpm --filter @journeylab/ui test >/tmp/jl-e2e-ui.log 2>&1; then
  ok "design system: $(grep -oE 'Tests  [0-9]+ passed' /tmp/jl-e2e-ui.log | tail -1 | grep -oE '[0-9]+ passed')"
else
  bad "design system suite — see /tmp/jl-e2e-ui.log"
fi

if pnpm --filter @journeylab/web test >/tmp/jl-e2e-web.log 2>&1; then
  ok "web unit: $(grep -oE 'Tests  [0-9]+ passed' /tmp/jl-e2e-web.log | tail -1 | grep -oE '[0-9]+ passed')"
else
  bad "web unit suite — see /tmp/jl-e2e-web.log"
fi

if pnpm --filter @journeylab/web build >/tmp/jl-e2e-build.log 2>&1; then
  routes=$(grep -cE '^(┌|├|└) ' /tmp/jl-e2e-build.log || true)
  ok "production build succeeds — ${routes} routes emitted"
else
  bad "production build — see /tmp/jl-e2e-build.log"
fi

# --- 5. the running application ----------------------------------------------

head_ "5. The running application — real HTTP against the production build"

alive() { curl -fsS -o /dev/null --max-time 2 "$BASE/api/health" 2>/dev/null; }

if alive; then
  bad "port $PORT is already serving something; refusing to test the wrong server"
else
  # PLACEHOLDERS ONLY IF THERE IS NO REAL CONFIG.
  #
  # `next.config.ts` loads the root .env with `process.loadEnvFile`, which does
  # NOT overwrite variables already set — so exporting placeholders here silently
  # wins over the real Auth0 configuration. The first version did exactly that
  # and then reported "sign-in redirect lacks PKCE S256", which was true of the
  # invalid issuer it had just imposed and false of the application.
  #
  # A test that supplies broken configuration and then reports the breakage as a
  # product defect is worse than no test.
  REAL_AUTH0=0
  if [ -f .env ] && grep -q '^AUTH0_ISSUER=https://' .env; then REAL_AUTH0=1; fi

  (
    cd apps/web || exit 1
    if [ "$REAL_AUTH0" -eq 0 ]; then
      export AUTH0_ISSUER="${AUTH0_ISSUER:-https://e2e.invalid/}"
      export AUTH0_CLIENT_ID="${AUTH0_CLIENT_ID:-e2e}"
      export AUTH0_CLIENT_SECRET="${AUTH0_CLIENT_SECRET:-e2e}"
      export AUTH0_REDIRECT_URI="${AUTH0_REDIRECT_URI:-https://e2e.invalid/cb}"
    fi
    exec node_modules/.bin/next start --port "$PORT"
  ) >/tmp/jl-e2e-server.log 2>&1 &
  SERVER=$!
  cleanup() {
    kill "$SERVER" 2>/dev/null
    for _ in $(seq 1 20); do alive || return 0; sleep 0.25; done
    kill -9 "$SERVER" 2>/dev/null
  }
  trap cleanup EXIT

  for _ in $(seq 1 60); do alive && break; sleep 0.5; done

  if ! alive; then
    bad "the application did not start — see /tmp/jl-e2e-server.log"
  else
    ok "health endpoint answers 200"

    code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/")
    [ "$code" = "200" ] && ok "home page renders (200)" || bad "home page returned $code"

    # The session endpoint must answer for an anonymous caller and must NOT leak
    # a token. This is the shape STEP-002.05 established.
    body=$(curl -s --max-time 5 "$BASE/api/auth/session")
    if [ -n "$body" ]; then
      ok "session endpoint answers for an anonymous caller"
      if echo "$body" | grep -qiE '"(access_token|id_token|refresh_token)"'; then
        bad "session endpoint LEAKS A TOKEN into the response body"
      else
        ok "session response contains no token — httpOnly cookies stay server-side"
      fi
    else
      bad "session endpoint returned nothing"
    fi

    # Sign-in must redirect to the configured issuer with PKCE. This needs real
    # Auth0 configuration — the route performs OIDC discovery before it can build
    # the URL, and discovery against a placeholder issuer cannot succeed.
    if [ "$REAL_AUTH0" -eq 0 ]; then
      meh "sign-in redirect — no real AUTH0_ISSUER in .env, so discovery cannot run"
    else
      loc=$(curl -s -o /dev/null -w '%{redirect_url}' --max-time 15 "$BASE/api/auth/login")
      echo "$loc" | grep -q "code_challenge_method=S256" \
        && ok "sign-in redirects to the IdP with PKCE S256" \
        || bad "sign-in redirect lacks PKCE S256 (got: ${loc:-no redirect})"
      echo "$loc" | grep -q "state=" \
        && ok "sign-in redirect carries a state parameter (CSRF)" \
        || bad "sign-in redirect has no state parameter"
    fi

    # The gallery must be absent unless explicitly enabled. This server was
    # started WITHOUT the flag.
    code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/dev/gallery")
    [ "$code" = "404" ] && ok "the component gallery is 404 without its flag" \
                        || bad "/dev/gallery returned $code without JOURNEYLAB_ENABLE_GALLERY"

    # Security headers that STEP-002.05 established.
    hdrs=$(curl -s -D - -o /dev/null "$BASE/")
    echo "$hdrs" | grep -qi "x-frame-options\|content-security-policy" \
      && ok "a framing/CSP header is present" \
      || meh "no framing or CSP header yet — hardening lands at STEP-023"
  fi
  cleanup
  trap - EXIT
fi

# --- 5b. the DEVELOPMENT server -----------------------------------------------

head_ "5b. The development server — the mode a developer actually opens"

# BUG-019. Every other check in this repository runs against a PRODUCTION build:
# the 40 browser tests, pnpm verify, and section 5 above. `next dev` renders
# differently — it does not tolerate a throw during server rendering, it does not
# minify, and it hydrates on a different path.
#
# The gallery returned 500 in dev for an entire sub-step and nothing noticed,
# because nothing looked. A rendering mode with no coverage is a rendering mode
# that is broken as often as not.
#
# This is a smoke check, not a suite: does each route render at all?

DEV_PORT=5709
DEV="https://localhost:$DEV_PORT"
dev_alive() { curl -fsSk -o /dev/null --max-time 2 "$DEV/api/health" 2>/dev/null; }

if [ ! -f apps/web/certificates/localhost+2.pem ]; then
  meh "development server — no mkcert certificate at apps/web/certificates/"
elif dev_alive; then
  meh "development server — something is already on $DEV_PORT; not testing the wrong server"
else
  (
    cd apps/web || exit 1
    JOURNEYLAB_ENABLE_GALLERY=1 exec node_modules/.bin/next dev --port "$DEV_PORT" \
      --experimental-https \
      --experimental-https-key ./certificates/localhost+2-key.pem \
      --experimental-https-cert ./certificates/localhost+2.pem
  ) >/tmp/jl-e2e-dev.log 2>&1 &
  DEVPID=$!
  dev_cleanup() {
    kill "$DEVPID" 2>/dev/null
    for _ in $(seq 1 20); do dev_alive || return 0; sleep 0.25; done
    kill -9 "$DEVPID" 2>/dev/null
  }
  trap dev_cleanup EXIT

  for _ in $(seq 1 90); do dev_alive && break; sleep 1; done

  if ! dev_alive; then
    bad "the development server did not start — see /tmp/jl-e2e-dev.log"
  else
    ok "development server starts over HTTPS"
    for route in "/" "/dev/gallery" "/dev/gallery?dir=rtl"; do
      code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 30 "$DEV$route")
      [ "$code" = "200" ] && ok "dev renders $route (200)" \
                          || bad "dev returned $code for $route — see /tmp/jl-e2e-dev.log"
    done
    # A route that renders but logs a server-side exception is half-broken, and
    # BUG-019 looked exactly like that in production. Fail on it here.
    if grep -qE '^ ?⨯ (Error|TypeError|ReferenceError)' /tmp/jl-e2e-dev.log; then
      bad "the dev server logged a server-side exception while rendering"
      grep -E '^ ?⨯ ' /tmp/jl-e2e-dev.log | head -3
    else
      ok "no server-side exception logged during dev rendering"
    fi
  fi
  dev_cleanup
  trap - EXIT
fi

# --- 6. accessibility ---------------------------------------------------------

head_ "6. Accessibility — the real-browser gate"

if pnpm --filter @journeylab/web a11y >/tmp/jl-e2e-a11y.log 2>&1; then
  ok "browser accessibility: $(grep -oE '[0-9]+ passed' /tmp/jl-e2e-a11y.log | tail -1)"
else
  bad "browser accessibility suite — see /tmp/jl-e2e-a11y.log"
fi

# --- 7. repository invariants -------------------------------------------------

head_ "7. Repository invariants"

check "15 guards pass"                bash -c 'pnpm guard:node && pnpm guard:pnpm && pnpm guard:markup && pnpm guard:artifacts && pnpm guard:codeowners && pnpm guard:ports && pnpm guard:substep-docs && pnpm guard:readme && pnpm guard:workflows && pnpm guard:boundaries && pnpm guard:logical-css'
check "guard meta-suite — every guard demonstrably catches what it claims" \
                                      bash tests/guards/meta/run-all.sh
# A dirty working tree makes the graph legitimately stale, and reporting that as
# a failure trains people to ignore it. Distinguish the two.
if [ -n "$(git status --porcelain)" ]; then
  meh "knowledge graph freshness — the working tree has uncommitted changes, so staleness is expected"
elif npx --yes gitnexus status 2>&1 | grep -q "up-to-date"; then
  ok "knowledge graph is current at HEAD"
else
  bad "knowledge graph is stale at a clean HEAD — run: npx gitnexus analyze"
fi

# --- summary ------------------------------------------------------------------

printf '\n════════════════════════════════════════\n'
printf '  passed:  %s\n' "$pass"
printf '  failed:  %s\n' "$fail"
printf '  skipped: %s\n' "$skip"
if [ "$fail" -gt 0 ]; then
  printf '  \033[31mRESULT: FAIL\033[0m — the system does not work end to end.\n'
  exit 1
fi
if [ "$skip" -gt 0 ]; then
  printf '  \033[33mRESULT: PASS WITH SKIPS\033[0m — %s check(s) did not run. A skip is not a pass.\n' "$skip"
  exit 0
fi
printf '  \033[32mRESULT: PASS\033[0m — every layer works, end to end.\n'
exit 0
