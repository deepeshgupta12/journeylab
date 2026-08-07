/**
 * Shell primitives — TST-A11Y-001 · STEP-003.05.
 */

import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { FeatureErrorBoundary, GlobalErrorBoundary } from './error-boundary';
import { documentLocale, isRightToLeft } from './locale';
import { SkipLink } from './skip-link';

afterEach(cleanup);

async function axeViolations(container: HTMLElement) {
  const results = await axe.run(container, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
  });
  return results.violations.map((v) => `${v.id}: ${v.help}`);
}

function Boom({ message = 'boom' }: { message?: string }): never {
  throw new Error(message);
}

// React logs caught errors to console.error; silence it so a passing run is not
// full of red text that trains people to ignore red text.
let consoleError: ReturnType<typeof vi.spyOn>;
beforeEach(() => {
  consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => consoleError.mockRestore());

// --- the requirement: a feature failure must not remove neighbouring content --

describe('feature error boundary', () => {
  it('contains the failure and LEAVES SIBLINGS INTACT', () => {
    // Blueprint §8.114: a map or chart failure must not remove itinerary text.
    render(
      <div>
        <p>Day 1: ferry to the island</p>
        <FeatureErrorBoundary feature="The map">
          <Boom />
        </FeatureErrorBoundary>
        <p>Day 2: coastal walk</p>
      </div>,
    );
    expect(screen.getByText('Day 1: ferry to the island')).toBeDefined();
    expect(screen.getByText('Day 2: coastal walk')).toBeDefined();
    expect(screen.getByText(/The map could not be displayed/)).toBeDefined();
  });

  it('names the feature rather than saying "something went wrong"', () => {
    render(
      <FeatureErrorBoundary feature="The budget chart">
        <Boom />
      </FeatureErrorBoundary>,
    );
    // "Something went wrong" beside an itinerary tells a traveller nothing about
    // whether their plan is intact.
    expect(screen.getByText(/The budget chart could not be displayed/)).toBeDefined();
  });

  it('does NOT render the error message to the user', () => {
    const { container } = render(
      <FeatureErrorBoundary feature="The map">
        <Boom message="ECONNREFUSED https://provider.internal/key=abc123" />
      </FeatureErrorBoundary>,
    );
    const text = container.textContent ?? '';
    // An error string can carry a URL, a stack frame or a provider response.
    expect(text).not.toContain('ECONNREFUSED');
    expect(text).not.toContain('abc123');
  });

  it('reports the error to the caller instead', () => {
    const onError = vi.fn();
    render(
      <FeatureErrorBoundary feature="The map" onError={onError}>
        <Boom message="detail for the log" />
      </FeatureErrorBoundary>,
    );
    expect(onError).toHaveBeenCalledOnce();
    const [reported] = onError.mock.calls[0] ?? [];
    expect((reported as Error).message).toBe('detail for the log');
  });

  it('offers recovery without performing it automatically', async () => {
    // A boundary that re-renders itself on failure loops silently.
    const user = userEvent.setup();
    const onReset = vi.fn();
    render(
      <FeatureErrorBoundary feature="The map" onReset={onReset}>
        <Boom />
      </FeatureErrorBoundary>,
    );
    expect(onReset).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(onReset).toHaveBeenCalledOnce();
  });

  it('renders children untouched when nothing throws', () => {
    render(
      <FeatureErrorBoundary feature="The map">
        <p>the map</p>
      </FeatureErrorBoundary>,
    );
    expect(screen.getByText('the map')).toBeDefined();
    expect(screen.queryByRole('button', { name: 'Try again' })).toBeNull();
  });

  it('does not interrupt the rest of the page with role="alert"', () => {
    // The whole point of containment is that the rest of the page still works,
    // so a contained failure is not urgent enough to interrupt what the user is
    // reading elsewhere.
    const { container } = render(
      <FeatureErrorBoundary feature="The map">
        <Boom />
      </FeatureErrorBoundary>,
    );
    expect(container.querySelector('[role="alert"]')).toBeNull();
  });

  it('passes axe in its failed state', async () => {
    const { container } = render(
      <FeatureErrorBoundary feature="The map">
        <Boom />
      </FeatureErrorBoundary>,
    );
    expect(await axeViolations(container)).toEqual([]);
  });
});

describe('global error boundary', () => {
  it('DOES interrupt, because there is nothing left to interrupt', () => {
    const { container } = render(
      <GlobalErrorBoundary>
        <Boom />
      </GlobalErrorBoundary>,
    );
    expect(container.querySelector('[role="alert"]')).not.toBeNull();
  });

  it('reassures that data is not lost', () => {
    render(
      <GlobalErrorBoundary>
        <Boom />
      </GlobalErrorBoundary>,
    );
    expect(screen.getByText(/Your trips are saved/)).toBeDefined();
  });

  it('passes axe in its failed state', async () => {
    const { container } = render(
      <GlobalErrorBoundary>
        <Boom />
      </GlobalErrorBoundary>,
    );
    expect(await axeViolations(container)).toEqual([]);
  });
});

// --- skip link ---------------------------------------------------------------

describe('skip link', () => {
  it('is the FIRST focusable element in the document', async () => {
    const user = userEvent.setup();
    render(
      <>
        <SkipLink targetId="main" />
        <nav>
          <a href="/trips">Trips</a>
        </nav>
        <main id="main" tabIndex={-1}>
          content
        </main>
      </>,
    );
    await user.tab();
    // A skip link placed after the navigation skips nothing.
    expect(document.activeElement?.getAttribute('data-skip-link')).not.toBeNull();
    expect(document.activeElement?.textContent).toBe('Skip to main content');
  });

  it('points at the main landmark', () => {
    render(<SkipLink targetId="main" />);
    expect(screen.getByRole('link').getAttribute('href')).toBe('#main');
  });

  it('remains in the tab order — it is not display:none', async () => {
    // A permanently hidden skip link cannot be focused, which makes it decoration.
    const user = userEvent.setup();
    render(
      <>
        <SkipLink targetId="main" />
        <main id="main" tabIndex={-1}>
          content
        </main>
      </>,
    );
    await user.tab();
    expect(document.activeElement?.tagName).toBe('A');
  });

  it('passes axe', async () => {
    const { container } = render(
      <>
        <SkipLink targetId="main" />
        <main id="main" tabIndex={-1}>
          content
        </main>
      </>,
    );
    expect(await axeViolations(container)).toEqual([]);
  });
});

// --- language and direction --------------------------------------------------

describe('document locale', () => {
  it('derives direction rather than requiring it to be configured', () => {
    // A mismatched pair (lang="ar" with dir="ltr") is worse than either alone,
    // and that mismatch is what a hand-maintained setting drifts into.
    expect(documentLocale('en-GB')).toEqual({ lang: 'en-gb', dir: 'ltr' });
    expect(documentLocale('ar-EG')).toEqual({ lang: 'ar-eg', dir: 'rtl' });
  });

  it('matches on the primary subtag', () => {
    expect(isRightToLeft('ar')).toBe(true);
    expect(isRightToLeft('ar-MA')).toBe(true);
    expect(isRightToLeft('he_IL')).toBe(true);
  });

  it('covers the RTL languages a traveller product plausibly meets', () => {
    for (const tag of ['ar', 'he', 'fa', 'ur', 'ps', 'dv', 'yi', 'ku']) {
      expect(isRightToLeft(tag), `${tag} not treated as RTL`).toBe(true);
    }
  });

  it('defaults an unknown tag to LTR', () => {
    expect(isRightToLeft('xx')).toBe(false);
    expect(isRightToLeft('ja')).toBe(false);
  });

  it('never yields an empty lang', () => {
    // An empty lang is worse than a wrong one: screen readers fall back to the
    // system voice, which mispronounces every place name.
    expect(documentLocale('')).toEqual({ lang: 'en', dir: 'ltr' });
    expect(documentLocale('   ')).toEqual({ lang: 'en', dir: 'ltr' });
  });
});
