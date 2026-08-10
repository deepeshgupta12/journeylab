/**
 * Role-aware navigation — TST-A11Y-001, TST-SEC-004 · STEP-003.06.
 *
 * The security assertions matter more than the rendering ones. The sub-step says
 * it directly: "a hidden nav item with an open endpoint is a vulnerability, not a
 * UI bug." So the tests below establish two things about hiding:
 *   1. It matches the server's matrix, so the interface does not offer refused
 *      actions.
 *   2. It is NOT relied on as a control, and cannot become one by accident.
 */

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { useState } from 'react';
import { afterEach, describe, expect, it } from 'vitest';

import { MATRIX, mayAttempt, OPERATIONS, ROLES } from './authz-matrix';
import { MobileNavigation, type NavItem, Navigation, visibleItems } from './navigation';

afterEach(cleanup);

const here = dirname(fileURLToPath(import.meta.url));
const REPO = join(here, '../../../..');

async function axeViolations(container: HTMLElement) {
  const results = await axe.run(container, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
  });
  return results.violations.map((v) => `${v.id}: ${v.help}`);
}

const ITEMS: NavItem[] = [
  { href: '/trips', label: 'Trips', operation: 'read_trip' },
  { href: '/trips/new', label: 'New trip', operation: 'create_trip' },
  { href: '/admin/destinations', label: 'Destinations', operation: 'override_destination_fact' },
  { href: '/admin/providers', label: 'Providers', operation: 'disable_provider_roll_back_model' },
];

// --- the generated matrix must match its source ------------------------------

describe('generated matrix', () => {
  it('is generated from the SAME markdown as the Python policy', () => {
    // ADR-012: two hand-maintained copies diverge, and the divergence is silent —
    // the menu starts offering something the server refuses, or hiding something
    // it permits, and neither is visible from either file alone.
    const markdown = readFileSync(
      join(REPO, 'docs/product/04-contracts/AUTHORIZATION_MATRIX.md'),
      'utf8',
    );
    const section = markdown.split('## 3. Operation matrix')[1]?.split('## 4.')[0] ?? '';
    const rows = section.split('\n').filter((line) => line.trim().startsWith('|'));
    const dataRows = rows.slice(2).filter((r) => r.trim());

    expect(OPERATIONS.length, 'operation count drifted from the markdown').toBe(dataRows.length);
    expect(Object.keys(MATRIX).length).toBe(OPERATIONS.length * ROLES.length);
  });

  it('covers every operation x role pairing', () => {
    for (const operation of OPERATIONS) {
      for (const role of ROLES) {
        expect(MATRIX[`${operation}:${role}`], `${operation}:${role} missing`).toBeDefined();
      }
    }
  });

  it('agrees with hand-verified cells from the markdown', () => {
    // Pins specific values so a uniformly-wrong generator cannot agree with itself.
    expect(mayAttempt('select_canonical_scenario', 'trip_owner')).toBe(true);
    expect(mayAttempt('select_canonical_scenario', 'trip_editor')).toBe(false);
    expect(mayAttempt('override_destination_fact', 'curator')).toBe(true);
    expect(mayAttempt('override_destination_fact', 'trip_owner')).toBe(false);
  });

  it('hides an unknown pairing rather than showing it', () => {
    // Deny-by-default matches the server; a missing rule is a generation bug.
    // @ts-expect-error deliberately invalid
    expect(mayAttempt('nonexistent_operation', 'trip_owner')).toBe(false);
  });
});

// --- TST-SEC-004: hiding is presentation, not protection ---------------------

describe('hiding is not an authorization control', () => {
  it('filters items to what the role may attempt', () => {
    const forOwner = visibleItems(ITEMS, 'trip_owner').map((i) => i.href);
    expect(forOwner).toContain('/trips');
    expect(forOwner).not.toContain('/admin/destinations');

    const forCurator = visibleItems(ITEMS, 'curator').map((i) => i.href);
    expect(forCurator).toContain('/admin/destinations');
  });

  it('matches the authorization matrix for EVERY role, not a sampled few', () => {
    for (const role of ROLES) {
      for (const item of ITEMS) {
        const shown = visibleItems(ITEMS, role).some((i) => i.href === item.href);
        expect(shown, `${role} / ${item.href}`).toBe(mayAttempt(item.operation, role));
      }
    }
  });

  it('leaves the href intact — the route is NOT removed, only the link', () => {
    // The route still exists and is still reachable by typing the URL. That is
    // exactly why the server must refuse it: hiding makes the vulnerability
    // harder to notice, not smaller.
    render(<Navigation items={ITEMS} actorRole="trip_owner" currentPath="/trips" />);
    expect(screen.queryByRole('link', { name: 'Destinations' })).toBeNull();
    // Nothing in this module blocks a request to /admin/destinations.
    const source = visibleItems.toString();
    expect(source).not.toMatch(/fetch|redirect|throw/);
  });

  it('names itself for what it is', () => {
    // `visibleItems`, not `permittedItems` — the return value describes what to
    // draw and nothing about what is allowed.
    expect(typeof visibleItems).toBe('function');
    const module = readFileSync(join(here, 'navigation.tsx'), 'utf8');
    expect(module).toContain('HIDING A NAV ITEM IS NOT AN AUTHORIZATION CONTROL');
    expect(module).toContain('the server is the control');
  });

  it('states in the generated matrix that it is presentation data', () => {
    const generated = readFileSync(join(here, 'authz-matrix.ts'), 'utf8');
    expect(generated).toContain('IT IS NOT AN AUTHORIZATION CONTROL');
  });
});

// --- accessibility -----------------------------------------------------------

describe('navigation semantics', () => {
  it('is a named landmark', () => {
    render(<Navigation items={ITEMS} actorRole="trip_owner" currentPath="/trips" />);
    // Two unnamed navs on a page are indistinguishable when jumping by landmark.
    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeDefined();
  });

  it('announces the current page with aria-current', () => {
    render(<Navigation items={ITEMS} actorRole="trip_owner" currentPath="/trips" />);
    // Styling the active link differently conveys nothing without sight.
    expect(screen.getByRole('link', { name: 'Trips' }).getAttribute('aria-current')).toBe('page');
    expect(screen.getByRole('link', { name: 'New trip' }).hasAttribute('aria-current')).toBe(false);
  });

  it('is reachable by keyboard alone', async () => {
    const user = userEvent.setup();
    render(<Navigation items={ITEMS} actorRole="trip_owner" currentPath="/trips" />);
    await user.tab();
    expect(document.activeElement).toBe(screen.getByRole('link', { name: 'Trips' }));
    await user.tab();
    expect(document.activeElement).toBe(screen.getByRole('link', { name: 'New trip' }));
  });

  it('passes axe', async () => {
    const { container } = render(
      <Navigation items={ITEMS} actorRole="curator" currentPath="/admin/destinations" />,
    );
    expect(await axeViolations(container)).toEqual([]);
  });
});

// --- mobile drawer -----------------------------------------------------------

function MobileHarness({ actorRole = 'trip_owner' as const }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <MobileNavigation
        items={ITEMS}
        actorRole={actorRole}
        currentPath="/trips"
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
      />
      <a href="/behind">Behind the drawer</a>
    </>
  );
}

describe('mobile drawer', () => {
  it('reports its state with aria-expanded', async () => {
    const user = userEvent.setup();
    render(<MobileHarness />);
    const toggle = screen.getByRole('button', { name: 'Menu' });
    // A button reading only "Menu" says nothing about whether the menu is open.
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    await user.click(toggle);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
  });

  it('links the toggle to what it controls', () => {
    render(<MobileHarness />);
    expect(screen.getByRole('button', { name: 'Menu' }).getAttribute('aria-controls')).toBeTruthy();
  });

  it('moves focus into the drawer on open', async () => {
    const user = userEvent.setup();
    render(<MobileHarness />);
    await user.click(screen.getByRole('button', { name: 'Menu' }));
    expect(document.activeElement).toBe(screen.getByRole('link', { name: 'Trips' }));
  });

  it('TRAPS focus so Tab does not walk into the page behind', async () => {
    const user = userEvent.setup();
    render(<MobileHarness />);
    await user.click(screen.getByRole('button', { name: 'Menu' }));

    await user.tab(); // New trip
    await user.tab(); // Close menu
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Close menu' }));
    await user.tab(); // wraps
    expect(document.activeElement, 'focus escaped the drawer to a link behind it').toBe(
      screen.getByRole('link', { name: 'Trips' }),
    );
  });

  it('restores focus to the toggle on close', async () => {
    const user = userEvent.setup();
    render(<MobileHarness />);
    const toggle = screen.getByRole('button', { name: 'Menu' });
    await user.click(toggle);
    await user.keyboard('{Escape}');
    expect(document.activeElement).toBe(toggle);
  });

  it('closes on Escape', async () => {
    const user = userEvent.setup();
    render(<MobileHarness />);
    await user.click(screen.getByRole('button', { name: 'Menu' }));
    expect(screen.getByRole('link', { name: 'Trips' })).toBeDefined();
    await user.keyboard('{Escape}');
    expect(screen.queryByRole('link', { name: 'Trips' })).toBeNull();
  });

  it('applies the same role filtering as desktop', async () => {
    const user = userEvent.setup();
    render(<MobileHarness actorRole="trip_owner" />);
    await user.click(screen.getByRole('button', { name: 'Menu' }));
    // A drawer that shows more than the desktop nav would be a second, divergent
    // implementation of the same filter.
    expect(screen.queryByRole('link', { name: 'Destinations' })).toBeNull();
  });

  it('passes axe when open', async () => {
    const user = userEvent.setup();
    const { container } = render(<MobileHarness />);
    await user.click(screen.getByRole('button', { name: 'Menu' }));
    expect(await axeViolations(container)).toEqual([]);
  });
});
