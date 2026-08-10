#!/usr/bin/env bash
# Guard: the component gallery must be unreachable without its flag — STEP-003.08.
#
# WHY A GUARD AND NOT A PLAYWRIGHT TEST
#   The accessibility harness SETS `JOURNEYLAB_ENABLE_GALLERY=1`, because it has
#   to walk the gallery. It can therefore only ever prove the route works WITH
#   the flag. The property that matters in production is the opposite one, and
#   nothing inside that harness can establish it.
#
#   `/dev/gallery` enumerates every internal component, every error string and
#   the shape of the route tree. That is a small information-disclosure surface,
#   and the only thing keeping it out of a deployment is an environment check.
#   An environment check nobody tests is an environment check that is wrong.
#
# NO `lsof`, AND THE REASON MATTERS
#   The first version used `lsof` to detect and clean up the port. `lsof` is not
#   installed in node:24-bookworm, so in `pnpm ci:local` the cleanup silently did
#   nothing, this guard still reported PASS, and the accessibility run that comes
#   next died with "127.0.0.1:5708 is already used". A cleanup that depends on a
#   tool that may be absent is a cleanup that fails silently on the machine you
#   were not testing on.
#
#   Liveness is therefore decided by asking the server, with curl, which is
#   already a hard dependency of this repository's scripts.
#
# Contract: FAILS (exit 1) if the gallery answers anything but 404 unflagged.
# Run: bash tests/guards/gallery-gate.sh
set -uo pipefail
cd "$(dirname "$0")/../.."

PORT=5708
APP="apps/web"
BASE="http://127.0.0.1:$PORT"

alive() { curl -fsS -o /dev/null --max-time 2 "$BASE/api/health" 2>/dev/null; }

if [ ! -d "$APP/.next" ]; then
  echo "SKIP: no production build at $APP/.next. This is a SKIP, not a PASS."
  echo "      Run 'pnpm build' first; 'pnpm verify' does so before this guard."
  exit 2
fi

# Something already answering on this port would serve a DIFFERENT build, and the
# result would be meaningless. Refuse rather than measure the wrong server.
if alive; then
  echo "FAIL: something is already serving $BASE; cannot trust a result from it."
  exit 1
fi

# `exec` so that $SERVER is the Next process itself rather than a wrapper whose
# death would orphan the child listening on the port.
# Deliberately NOT setting JOURNEYLAB_ENABLE_GALLERY. The placeholder Auth0
# values only let the server boot; nothing here signs in.
(
  cd "$APP" || exit 1
  AUTH0_ISSUER=https://gate.invalid/ \
  AUTH0_CLIENT_ID=gate \
  AUTH0_CLIENT_SECRET=gate \
  AUTH0_REDIRECT_URI=https://gate.invalid/cb \
  exec node_modules/.bin/next start --port "$PORT"
) >/tmp/journeylab-gallery-gate.log 2>&1 &
SERVER=$!

cleanup() {
  kill "$SERVER" 2>/dev/null
  # Give it a moment to release the socket, then escalate. The port MUST be free
  # when this returns: `pnpm a11y` runs next and starts its own server here.
  for _ in $(seq 1 20); do
    alive || return 0
    sleep 0.25
  done
  kill -9 "$SERVER" 2>/dev/null
  for _ in $(seq 1 20); do
    alive || return 0
    sleep 0.25
  done
  echo "WARNING: $BASE is still answering after cleanup; the next step will fail." >&2
}
trap cleanup EXIT

for _ in $(seq 1 60); do
  alive && break
  sleep 0.5
done

if ! alive; then
  echo "FAIL: server did not become healthy. See /tmp/journeylab-gallery-gate.log"
  exit 1
fi

gallery=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$BASE/dev/gallery")
if [ "$gallery" != "404" ]; then
  echo "FAIL: /dev/gallery returned $gallery without JOURNEYLAB_ENABLE_GALLERY; expected 404."
  echo "      A gated dev route that answers in production discloses every internal"
  echo "      component name, error string and route to anyone who guesses the path."
  exit 1
fi

# 403 would be a failure too, and this states why: it confirms the path exists.
echo "PASS: /dev/gallery is 404 without its flag (health 200, so the server was up)."
exit 0
