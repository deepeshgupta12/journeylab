#!/usr/bin/env bash
# Node runtime guard — added after BUG-013/BUG-014 (STEP-002.05 follow-up)
#
# WHY ENFORCEMENT RATHER THAN CONFIGURATION
#   Four CI failures came from the local environment differing from CI's. Node
#   version is one of those axes: .nvmrc and CI say 24, but a developer machine
#   may default to anything.
#
#   pnpm's `useNodeVersion` looked like the fix. pnpm RECOGNISES the key —
#   `pnpm config get useNodeVersion` returns it — but does not switch the runtime:
#   `pnpm exec node --version` still reported v25.9.0. That is BUG-013's shape
#   exactly, so the setting was removed rather than left looking effective.
#
#   This guard cannot silently pass. It compares the Node actually running against
#   .nvmrc and fails with the command to fix it.
set -uo pipefail
cd "$(dirname "$0")/../.."

want=$(tr -d ' \n' < .nvmrc)
have=$(node --version | sed 's/^v//')
have_major=${have%%.*}

if [ "$have_major" != "$want" ]; then
  echo "FAIL: running Node $have, but .nvmrc and CI use $want."
  echo ""
  echo "  Local and CI must share a Node major, or tests pass here and fail there."
  echo "  Fix for this shell:"
  echo "    export PATH=\"/opt/homebrew/opt/node@${want}/bin:\$PATH\""
  echo "  Or permanently, with a version manager:"
  echo "    nvm use    # or: fnm use"
  exit 1
fi
echo "PASS: Node $have matches .nvmrc ($want)."
