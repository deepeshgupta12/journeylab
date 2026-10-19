/**
 * @vitest-environment jsdom
 *
 * Requested per file rather than per package — see `planning-check.test.tsx` and
 * `vitest.config.ts` for why a package-wide default breaks `i18n.test.ts`.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test } from 'vitest';
import { CoverageTable } from './coverage-table';
import type { CoverageRegion } from './fetch-coverage';

/**
 * The empty state is a real answer — STEP-007.02 (REQ-TRIP-002).
 *
 * WHY THIS MOVED HERE FROM THE BROWSER SUITE
 *   Until BUG-038 the only assertion on this copy was a Playwright test that relied on
 *   the developer's database holding no regions at all. The browser suite now seeds
 *   its own region so it can actually submit the form, which makes the populated page
 *   what a browser test sees — and would have left "no region has been declared yet"
 *   asserted nowhere. The distinction it draws ("nothing declared" is a fact about
 *   coverage; "could not be loaded" is a fact about us) is a product rule, not a
 *   fixture, so it is asserted where it does not depend on anybody's database.
 */

const REGION: CoverageRegion = {
  region_id: 'ch-bo',
  display_name: 'Bernese Oberland',
  date_bounds: { start: '2026-01-01', end: '2026-12-31' },
  freshness: 'current',
  limitations: ['Mountain transport is seasonal'],
};

afterEach(() => {
  cleanup();
});

describe('an empty table says why it is empty', () => {
  test('the emptiness is about declarations, not about a failure', () => {
    render(<CoverageTable regions={[]} />);
    expect(screen.getByText(/no region has been declared yet/i)).toBeTruthy();
    expect(screen.getByText(/not because a request failed/i)).toBeTruthy();
    expect(screen.queryByText(/could not be loaded/i)).toBeNull();
  });
});

describe('a declared region is rendered verbatim', () => {
  test('name, window, freshness word and limitation all appear as text', () => {
    render(<CoverageTable regions={[REGION]} />);
    expect(screen.getByText('Bernese Oberland')).toBeTruthy();
    expect(screen.getByText('2026-01-01 to 2026-12-31')).toBeTruthy();
    // A word, not a coloured dot (WCAG 1.4.1).
    expect(screen.getByText('Current')).toBeTruthy();
    expect(screen.getByText('Mountain transport is seasonal')).toBeTruthy();
    expect(screen.queryByText(/no region has been declared yet/i)).toBeNull();
  });
});
