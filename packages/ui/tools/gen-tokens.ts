/**
 * Generate tokens.css from tokens.ts — STEP-003.01.
 *
 * Run: pnpm --filter @journeylab/ui tokens:build
 *
 * BUG-012: a generator must emit output that passes the project's own checks.
 * CSS is not linted by Biome here, but the output is still deterministic — the
 * drift test in tokens.test.ts regenerates and compares, so an edit to tokens.ts
 * without a rebuild fails CI.
 */

import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { ELEVATION, MOTION, MOTION_REDUCED, PALETTES, SPACING, TYPOGRAPHY } from '../src/tokens';

function block(entries: Record<string, string>, indent = '  '): string {
  return Object.entries(entries)
    .map(([key, value]) => `${indent}--${key}: ${value};`)
    .join('\n');
}

export function renderCss(): string {
  const light = PALETTES.light;
  const dark = PALETTES.dark;
  const highContrast = PALETTES['high-contrast'];

  return `/* GENERATED from src/tokens.ts — do not edit by hand.
 * Rebuild: pnpm --filter @journeylab/ui tokens:build
 * STEP-003.01 · REQ-A11Y-004, REQ-NFR-013
 *
 * Contrast ratios for every declared pairing are computed and asserted in
 * src/tokens.test.ts, so these values cannot drift below WCAG 2.2 AA silently.
 */

:root {
${block(light)}

${block(SPACING)}

${block(TYPOGRAPHY)}

${block(ELEVATION)}

${block(MOTION)}
}

/* Dark theme. Applied by user preference, or forced with [data-theme="dark"]. */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
${block(dark, '    ')}
  }
}

:root[data-theme="dark"] {
${block(dark)}
}

/* High contrast is a DISTINCT palette held to AAA, not dark mode intensified.
 * forced-colors covers Windows High Contrast Mode; prefers-contrast covers the
 * platform-agnostic signal. Both are honoured. */
@media (prefers-contrast: more), (forced-colors: active) {
  :root {
${block(highContrast, '    ')}
  }
}

:root[data-theme="high-contrast"] {
${block(highContrast)}
}

/* Reduced motion SUPPRESSES animation rather than shortening it — vestibular
 * safety, not a preference. Durations are 0ms, and the catch-all below stops any
 * component that hard-codes its own duration from animating anyway. */
@media (prefers-reduced-motion: reduce) {
  :root {
${block(MOTION_REDUCED, '    ')}
  }

  *,
  *::before,
  *::after {
    animation-duration: 0ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0ms !important;
    scroll-behavior: auto !important;
  }
}
`;
}

/**
 * Only write when run directly.
 *
 * The drift test imports `renderCss` to compare against the committed file. With
 * an unguarded top-level write, merely running the tests rewrote tokens.css —
 * so the test could never fail: it regenerated the file it was about to check.
 * A test that repairs the thing it verifies proves nothing.
 */
const invokedDirectly =
  process.argv[1] !== undefined && import.meta.url === pathToFileURL(process.argv[1]).href;

if (invokedDirectly) {
  const here = dirname(fileURLToPath(import.meta.url));
  writeFileSync(join(here, '../src/tokens.css'), renderCss());
  process.stdout.write('wrote src/tokens.css\n');
}
