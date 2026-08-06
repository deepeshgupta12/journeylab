# Testing commands

Copy-paste reference for verifying JourneyLab from a VS Code terminal.

**Every command here has been run in this repository.** Where something is not yet
provable, it says so rather than offering a command that would give false comfort.

> **Node must be 24** — `pnpm verify` fails first if it is not, because local and CI
> running different Node majors is what produced three of the CI failures.
>
> Set up once, per-project, with [fnm](https://github.com/Schniz/fnm):
>
> ```bash
> brew install fnm
> fnm install 24
> fnm default system          # other projects keep their own Node
> ```
>
> then add to `~/.zshrc`:
>
> ```bash
> eval "$(fnm env --use-on-cd --shell zsh)"
> [ -f .nvmrc ] && fnm use --install-if-missing >/dev/null 2>&1
> ```
>
> The second line matters: `--use-on-cd` only fires on an actual `cd`, so a
> terminal that *opens* inside the project would otherwise keep the wrong Node.
>
> One-shot alternative: `export PATH="/opt/homebrew/opt/node@24/bin:$PATH"`

---

## 1. The one command before you push

```bash
pnpm ci:local
```

Runs CI's job **on Linux, from a clean checkout, with a cold install** — the three
conditions that made `BUG-008`, `BUG-013` and `BUG-014` invisible on a developer
machine. Takes ~2 minutes and needs Docker running.

`pnpm verify` alone is not equivalent: it runs against whatever is already in your
working directory, so it cannot see an install-time failure or a file you
accidentally staged.

---

## 2. Everything, quickly

```bash
pnpm verify
```

16 checks: guards, Biome lint + format, TypeScript typecheck, ruff lint + format,
mypy strict, then **292 Python tests and 41 TypeScript tests**.

Expected tail:

```
292 passed, 1 warning
Tests  41 passed (41)
```

---

## 3. Backend (Python)

**Start the stack first** — 16 tests are integration tests and will otherwise skip:

```bash
pnpm dev                       # Postgres, Redis, MinIO, NATS, OTEL on 5700-5707
docker compose -f docker-compose.dev.yml ps    # all should read "healthy"
```

```bash
uv run pytest                          # all Python tests
uv run pytest -v                       # one line per test name
uv run pytest tests/api -v             # API layer only
uv run pytest -k authorization -v      # authorization policy (176 matrix cells)
uv run pytest -k provisioning -v       # identity lifecycle
uv run pytest -k tenant_context -v     # tenant resolution and DB binding
uv run pytest --cov --cov-report=term-missing   # coverage
```

**A skip is not a pass.** If you see `16 skipped`, the stack is down and the
database guarantees were never exercised.

### Tenant isolation — regression check R7

```bash
pnpm test:security
```

Expected: `R7 assertions passed: 12` / `failed: 0`.

This is the non-negotiable one. It seeds two tenants and proves neither can read,
update or delete the other's rows, that a missing tenant context yields **zero**
rows rather than all of them, and that context does not survive `COMMIT` (the
pooled-connection leak). It also **weakens its own policy on purpose** to prove
the suite can fail — a green isolation suite that would also pass with RLS
disabled is worse than no suite.

---

## 4. Frontend (TypeScript)

```bash
pnpm --filter @journeylab/web test           # 41 tests
pnpm --filter @journeylab/web test -- --watch
pnpm --filter @journeylab/web typecheck      # tsc --noEmit, strict
```

Covers: tokens never JS-readable, sign-out clearing every cookie, 7-day guest
expiry enforced server-side, single-flight refresh, CSRF deny-by-default, PKCE
S256, and OIDC state verification.

---

## 5. The guards, and proof they work

```bash
pnpm verify                        # runs all guards
bash tests/guards/meta/run-all.sh  # 33 meta-tests
```

The meta-suite seeds a **real violation** for each guard and asserts it fails,
then removes it and asserts it passes. A guard that cannot fail is not a guard —
this suite is the evidence, and it has caught four guards that looked correct and
were not.

Individually:

```bash
bash tests/guards/pnpm-config.sh          # settings pnpm actually reads (BUG-013)
bash tests/guards/no-tracked-artifacts.sh # artifacts, key material, >512 KB files
bash tests/guards/typecheck.sh            # per-package tsconfig
bash tests/guards/module-boundaries.sh    # ADR-003 boundaries
bash tests/guards/change-impact-record.sh # REQ-KG-008 merge gate
```

---

## 6. Web app and Auth0

```bash
pnpm dev:web       # https://localhost:5709  (TLS via mkcert)
```

HTTPS is **required, not cosmetic**: session cookies use the `__Host-` prefix,
which browsers reject over plain HTTP. On `http://` sign-in appears to succeed and
silently has no session.

```bash
curl -sk https://localhost:5709/api/health
# {"status":"ok","secure":true,"cookiePolicy":"__Host- usable"}

curl -sk https://localhost:5709/api/auth/session
# {"kind":"none"}

curl -sk -o /dev/null -w '%{http_code} %{redirect_url}\n' https://localhost:5709/api/auth/login
# 302 https://journeylab-dev.eu.auth0.com/authorize?...

# every flow cookie must be HttpOnly + Secure
curl -sk -D - -o /dev/null https://localhost:5709/api/auth/login | grep -i '^set-cookie'
```

### Preflight — one command, before touching a browser

```bash
pnpm auth0:check
```

Checks config presence, tenant reachability, PKCE support, **credential validity**
and **callback-URL registration**, and names the exact Auth0 setting to fix for
each failure. Passing this is the precondition for a browser sign-in working.

### Verify Auth0 credentials by hand

```bash
set -a; . ./.env; set +a

# tenant reachable?
curl -s "${AUTH0_ISSUER}.well-known/openid-configuration" | python3 -m json.tool | head -20

# are the client id and secret valid?
curl -s -X POST "${AUTH0_ISSUER}oauth/token" \
  -H 'content-type: application/x-www-form-urlencoded' \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "client_id=${AUTH0_CLIENT_ID}" \
  --data-urlencode "client_secret=${AUTH0_CLIENT_SECRET}" \
  --data-urlencode "code=deliberately-invalid" \
  --data-urlencode "redirect_uri=${AUTH0_REDIRECT_URI}"
```

Reading the result:

| Response | Meaning |
| --- | --- |
| `"error":"invalid_grant"` | **Credentials are valid.** Auth0 accepted the client and rejected only the fake code |
| `"error":"invalid_client"` | Client ID or secret is wrong |

### Not yet provable

A **browser sign-in round trip** cannot be tested from the terminal, and is
currently blocked anyway: `https://localhost:5709/api/auth/callback` is not in
Auth0's *Allowed Callback URLs*, so `/authorize` returns

```
unauthorized_client: Callback URL mismatch.
```

Add it in Auth0 → Applications → Settings, then sign in at
`https://localhost:5709/api/auth/login` in a browser. Until that happens,
`STEP-002.05` stays `IN_PROGRESS` — see [BR-014](../10-logs/blast-radius/BR-014-browser-session.md) §9.

---

## 7. Knowledge graph

```bash
npx gitnexus status     # must match HEAD before any change
npx gitnexus analyze    # refresh after every commit
```

A stale graph invalidates the pre-change impact analysis that
[CHANGE_IMPACT_PROTOCOL](../05-knowledge-graph/CHANGE_IMPACT_PROTOCOL.md)
requires. Check `status` **before** starting work, not after.

---

## 8. Stack management

```bash
pnpm dev            # start
pnpm dev:logs       # follow logs
pnpm dev:down       # stop
pnpm dev:reset      # stop AND WIPE ALL DATA, then start clean
```

`pnpm dev:reset` destroys the database volume. Use it to reproduce a first-boot
state — that is how `BUG-009` (Postgres reporting healthy during init) was found.

---

## 9. What a good run looks like

| Command | Expected |
| --- | --- |
| `pnpm ci:local` | `PASS: CI's job succeeds on Linux, from a clean checkout, with a cold install.` |
| `pnpm verify` | `292 passed` + `Tests 41 passed (41)` |
| `pnpm test:security` | `R7 assertions passed: 12` / `failed: 0` |
| `bash tests/guards/meta/run-all.sh` | `meta-tests passed: 33` / `failed: 0` |

Anything else is a finding. `BLOCKED` and `SKIP` are acceptable answers; a
fabricated pass is not.
