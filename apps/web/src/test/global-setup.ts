import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { DATABASE_URL } from './dsn';

/**
 * The browser suite owns its own data — BUG-038.
 *
 * Seeds one reserved region (`e2e-bern`) before any test runs, through the same
 * Python tool teardown uses to remove it. The suite used to ASSUME an empty coverage
 * table — not as a fixture it made, but as a fact about whichever database it was
 * pointed at — and that assumption held only because no region had ever been
 * declared. See `tools/e2e_region.py` for what is reserved and why.
 */

/** apps/web/src/test → repository root. */
const REPO_ROOT = fileURLToPath(new URL('../../../../', import.meta.url));

export function runRegionTool(action: 'seed' | 'remove'): void {
  const output = execFileSync('uv', ['run', 'python', 'tools/e2e_region.py', action], {
    cwd: REPO_ROOT,
    env: { ...process.env, JOURNEYLAB_DATABASE_URL: DATABASE_URL },
    encoding: 'utf8',
  });
  process.stdout.write(`[e2e region] ${output.trim()}\n`);
}

export default function globalSetup(): void {
  runRegionTool('seed');
}
