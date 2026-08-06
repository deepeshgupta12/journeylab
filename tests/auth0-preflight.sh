#!/usr/bin/env bash
# Auth0 configuration preflight — STEP-002.05.
#
# Checks everything that can be checked WITHOUT a browser, so a failed sign-in is
# never a mystery. Each check names the exact Auth0 setting to fix.
#
# The client secret is read but never printed.
#
# Usage: bash tests/auth0-preflight.sh
set -uo pipefail
cd "$(dirname "$0")/.."

pass=0; fail=0
ok()  { echo "  ok   $1"; pass=$((pass+1)); }
bad() { echo "  FAIL $1"; fail=$((fail+1)); }

if [ ! -f .env ]; then
  echo "ERROR: no .env. Copy .env.example to .env and fill in the Auth0 values."
  exit 1
fi
set -a; . ./.env; set +a

echo "=== 1. configuration present ==="
[ -n "${AUTH0_ISSUER:-}" ]        && ok "AUTH0_ISSUER=$AUTH0_ISSUER"                  || bad "AUTH0_ISSUER missing"
[ -n "${AUTH0_CLIENT_ID:-}" ]     && ok "AUTH0_CLIENT_ID set (${#AUTH0_CLIENT_ID} chars)" || bad "AUTH0_CLIENT_ID missing"
[ -n "${AUTH0_CLIENT_SECRET:-}" ] && ok "AUTH0_CLIENT_SECRET set (${#AUTH0_CLIENT_SECRET} chars, never printed)" \
                                  || bad "AUTH0_CLIENT_SECRET missing"
[ -n "${AUTH0_REDIRECT_URI:-}" ]  && ok "AUTH0_REDIRECT_URI=$AUTH0_REDIRECT_URI"      || bad "AUTH0_REDIRECT_URI missing"

case "${AUTH0_REDIRECT_URI:-}" in
  https://*) ok "redirect URI is https (required: __Host- cookies are rejected over plain HTTP)" ;;
  *) bad "redirect URI must be https — sign-in would appear to work and silently have no session" ;;
esac
[ "$fail" -eq 0 ] || { echo ""; echo "RESULT: FAIL — fix .env first."; exit 1; }

echo ""
echo "=== 2. tenant reachable (OIDC discovery) ==="
disco=$(curl -s --max-time 15 "${AUTH0_ISSUER}.well-known/openid-configuration" 2>/dev/null)
if echo "$disco" | grep -q '"issuer"'; then
  ok "discovery document returned"
  echo "$disco" | grep -q '"S256"' && ok "PKCE S256 supported" || bad "PKCE S256 NOT advertised"
else
  bad "discovery failed — is the tenant name right? ${AUTH0_ISSUER}"
  echo ""; echo "RESULT: FAIL"; exit 1
fi

echo ""
echo "=== 3. client id and secret valid ==="
# A deliberately invalid code distinguishes the two failures:
#   invalid_client -> credentials wrong
#   invalid_grant  -> credentials RIGHT, only the fake code was rejected
err=$(curl -s --max-time 15 -X POST "${AUTH0_ISSUER}oauth/token" \
  -H 'content-type: application/x-www-form-urlencoded' \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "client_id=${AUTH0_CLIENT_ID}" \
  --data-urlencode "client_secret=${AUTH0_CLIENT_SECRET}" \
  --data-urlencode "code=preflight-invalid-code" \
  --data-urlencode "redirect_uri=${AUTH0_REDIRECT_URI}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('error','?'))" 2>/dev/null)
case "$err" in
  invalid_grant)  ok "credentials VALID (Auth0 accepted the client, rejected only the fake code)" ;;
  invalid_client) bad "credentials REJECTED — check Client ID and Client Secret in Application Settings" ;;
  *)              bad "unexpected token-endpoint error: '$err'" ;;
esac

echo ""
echo "=== 4. callback URL registered ==="
enc=$(python3 -c "import urllib.parse,os;print(urllib.parse.quote(os.environ['AUTH0_REDIRECT_URI'],safe=''))")
body=$(curl -s --max-time 15 \
  "${AUTH0_ISSUER}authorize?response_type=code&client_id=${AUTH0_CLIENT_ID}&redirect_uri=${enc}&scope=openid&state=preflight&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256")
if echo "$body" | grep -qi 'Callback URL mismatch'; then
  bad "NOT registered: ${AUTH0_REDIRECT_URI}"
  echo "       Auth0 -> Applications -> your app -> Settings -> Allowed Callback URLs"
  echo "       Add exactly:  ${AUTH0_REDIRECT_URI}"
elif echo "$body" | grep -qiE 'Unauthorized|access_denied|Service not found'; then
  bad "authorize rejected the request:"
  echo "$body" | python3 -c "
import sys,re,html
t=re.sub(r'<[^>]+>',' ',sys.stdin.read())
print('      ', html.unescape(re.sub(r'\s+',' ',t)).strip()[:200])"
else
  ok "callback URL accepted by Auth0"
fi

echo ""
echo "=== 5. local HTTPS dev server ==="
if curl -sk --max-time 5 -o /dev/null "https://localhost:5709/api/health" 2>/dev/null; then
  secure=$(curl -sk --max-time 5 https://localhost:5709/api/health | grep -o '"secure":[a-z]*' || echo "")
  [ "$secure" = '"secure":true' ] && ok "dev server up on https://localhost:5709 (TLS confirmed)" \
                                  || bad "dev server responded but NOT over TLS: $secure"
else
  echo "  note dev server not running — start it with: pnpm dev:web"
fi

echo ""
echo "════════════════════════════════════════"
echo "  checks passed: $pass"
echo "  checks failed: $fail"
if [ "$fail" -gt 0 ]; then
  echo "  RESULT: FAIL — browser sign-in will not work until the above are fixed."
  exit 1
fi
echo "  RESULT: PASS — open https://localhost:5709/api/auth/login in a browser."
exit 0
