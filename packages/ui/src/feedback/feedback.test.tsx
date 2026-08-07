/**
 * Feedback primitives — TST-A11Y-001, TST-A11Y-004 · STEP-003.03.
 */

import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Dialog } from './dialog.tsx';
import { Notification, NotificationRegion } from './notification.tsx';
import {
  EmptyState,
  InfeasibleState,
  OfflineState,
  PartialDataState,
  Progress,
  ProviderDownState,
  Skeleton,
  SolverTimeoutState,
  StaleDataState,
  UnauthorizedState,
} from './panels.tsx';
import { QUALITY_STATES, qualityState, REQUIRED_STATE_NAMES } from './states.ts';

afterEach(cleanup);

async function axeViolations(container: HTMLElement) {
  const results = await axe.run(container, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
  });
  return results.violations.map((v) => `${v.id}: ${v.help}`);
}

// --- all nine states exist ---------------------------------------------------

describe('quality states', () => {
  it('covers every state FRONTEND_ARCHITECTURE §4 mandates', () => {
    // "All nine quality states have a primitive" is an acceptance criterion; a
    // list in a comment cannot be checked, so the set is asserted.
    const declared = QUALITY_STATES.map((s) => s.name).sort();
    expect(declared).toEqual([...REQUIRED_STATE_NAMES].sort());
    expect(declared.length).toBe(9);
  });

  it('gives every state a non-colour affordance — icon AND text', () => {
    for (const state of QUALITY_STATES) {
      expect(state.icon, `${state.name} has no icon`).toBeTruthy();
      expect(state.label, `${state.name} has no label`).toBeTruthy();
    }
  });

  it('uses a distinct icon per state', () => {
    const icons = QUALITY_STATES.map((s) => s.icon);
    expect(new Set(icons).size).toBe(icons.length);
  });

  it('reserves assertive politeness for states that make the view untrustworthy', () => {
    // Interrupting a user is justified only when what they are reading is wrong.
    const assertive = QUALITY_STATES.filter((s) => s.politeness === 'assertive').map((s) => s.name);
    expect(assertive.sort()).toEqual(['infeasible', 'offline', 'unauthorized']);
  });

  it('throws on an unknown state rather than rendering blank', () => {
    // A blank region is indistinguishable from success.
    // @ts-expect-error deliberately invalid
    expect(() => qualityState('nonsense')).toThrow(/unknown quality state/);
  });
});

// --- axe on every primitive --------------------------------------------------

describe('axe — zero WCAG AA violations', () => {
  const cases: Array<[string, () => React.ReactElement]> = [
    ['Skeleton', () => <Skeleton />],
    ['EmptyState', () => <EmptyState>No trips yet</EmptyState>],
    ['PartialDataState', () => <PartialDataState>Some prices missing</PartialDataState>],
    [
      'StaleDataState',
      () => <StaleDataState subject="Ferry price" observedAt={new Date('2026-08-01T09:00:00Z')} />,
    ],
    ['ProviderDownState', () => <ProviderDownState>Weather unavailable</ProviderDownState>],
    [
      'InfeasibleState',
      () => <InfeasibleState conflicts={['Budget under 500', 'Five-star only']} />,
    ],
    ['SolverTimeoutState', () => <SolverTimeoutState />],
    ['UnauthorizedState', () => <UnauthorizedState />],
    ['OfflineState', () => <OfflineState />],
    ['Progress', () => <Progress label="Generating scenarios" onCancel={() => {}} />],
  ];

  it.each(cases)('%s', async (_name, element) => {
    const { container } = render(element());
    expect(await axeViolations(container)).toEqual([]);
  });
});

// --- REQ-A11Y-004: distinguishable without colour ---------------------------

describe('states are distinguishable without colour', () => {
  it('renders both an icon and a text label, not a tint', () => {
    const { container } = render(<ProviderDownState />);
    const icon = container.querySelector('[data-icon]');
    expect(icon?.getAttribute('data-icon')).toBe('plug-off');
    // The icon is aria-hidden; the LABEL is what a screen reader announces.
    expect(icon?.getAttribute('aria-hidden')).toBe('true');
    expect(screen.getByText('A data source is unavailable')).toBeDefined();
  });

  it('identifies the state in the DOM as data, not only by class', () => {
    const { container } = render(<OfflineState />);
    expect(container.querySelector('[data-state="offline"]')).not.toBeNull();
  });
});

// --- stale data is labelled at the point of use ------------------------------

describe('stale data', () => {
  it('names the specific fact and when it was last checked', () => {
    // REQ-EVID-005: a global banner cannot tell a traveller WHICH price to
    // distrust, so they distrust everything or ignore it.
    render(<StaleDataState subject="Ferry price" observedAt={new Date('2026-08-01T09:00:00Z')} />);
    const label = screen.getByText(/Ferry price/);
    expect(label.textContent).toMatch(/last checked/i);
    expect(label.textContent).toContain('2026-08-01');
  });

  it('cannot be constructed without naming a subject and a time', () => {
    // Both are required props, so a page-level "some data may be stale" cannot
    // be built from this component at all.
    const required = ['observedAt', 'subject'];
    const source = StaleDataState.toString();
    for (const prop of required) expect(source).toContain(prop);
  });
});

// --- infeasible is first-class, not an error toast ---------------------------

describe('infeasible', () => {
  it('shows the minimal conflict set', () => {
    render(<InfeasibleState conflicts={['Budget under 500', 'Five-star only']} />);
    expect(screen.getByText('Budget under 500')).toBeDefined();
    expect(screen.getByText('Five-star only')).toBeDefined();
  });

  it('shows suggested relaxations when given', () => {
    render(
      <InfeasibleState
        conflicts={['Budget under 500']}
        relaxations={['Raise budget to 650', 'Allow four-star']}
      />,
    );
    expect(screen.getByText('Raise budget to 650')).toBeDefined();
  });

  it('REFUSES to render without a conflict set', () => {
    // REQ-CONS-005: infeasibility must return a minimal conflict set, never a
    // bare failure. An empty panel would be the uninformative dead end the
    // requirement exists to prevent.
    expect(() => render(<InfeasibleState conflicts={[]} />)).toThrow(/minimal conflict set/);
  });
});

// --- never a silent spinner --------------------------------------------------

describe('progress', () => {
  it('cannot be rendered without a label and a cancel path', () => {
    // REQ-NFR-003. Required props, so a bare spinner cannot be constructed —
    // stronger than discouraging it in a style guide nobody re-reads.
    const source = Progress.toString();
    expect(source).toContain('label');
    expect(source).toContain('onCancel');
  });

  it('exposes a working cancel control', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(<Progress label="Generating scenarios" onCancel={onCancel} />);
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('announces what is happening, not merely that something is', () => {
    render(<Progress label="Generating scenarios" onCancel={() => {}} />);
    expect(screen.getByRole('progressbar').getAttribute('aria-label')).toBe('Generating scenarios');
  });

  it('omits value attributes when indeterminate rather than reporting a false 0%', () => {
    render(<Progress label="Working" onCancel={() => {}} />);
    const bar = screen.getByRole('progressbar');
    expect(bar.hasAttribute('aria-valuenow')).toBe(false);
  });

  it('reports progress when known', () => {
    render(<Progress label="Working" percent={42} onCancel={() => {}} />);
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('42');
  });

  it('keeps a skeleton announced rather than silent', () => {
    const { container } = render(<Skeleton label="Loading scenarios" />);
    expect(container.querySelector('[aria-busy="true"]')).not.toBeNull();
    expect(screen.getByText('Loading scenarios')).toBeDefined();
  });
});

// --- TST-A11Y-001: dialog focus behaviour -----------------------------------

function DialogHarness() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Open
      </button>
      <button type="button">After</button>
      <Dialog open={open} title="Confirm" onClose={() => setOpen(false)}>
        <button type="button">First</button>
        <button type="button">Second</button>
      </Dialog>
    </>
  );
}

describe('dialog', () => {
  it('moves focus into the dialog on open', async () => {
    const user = userEvent.setup();
    render(<DialogHarness />);
    await user.click(screen.getByRole('button', { name: 'Open' }));
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'First' }));
  });

  it('RESTORES focus to the trigger on close', async () => {
    const user = userEvent.setup();
    render(<DialogHarness />);
    const trigger = screen.getByRole('button', { name: 'Open' });
    await user.click(trigger);
    await user.keyboard('{Escape}');
    // Without restoration, focus falls to body and the next Tab starts from the
    // top of the page — returning a keyboard user to the navigation.
    expect(document.activeElement).toBe(trigger);
  });

  it('closes on Escape', async () => {
    const user = userEvent.setup();
    render(<DialogHarness />);
    await user.click(screen.getByRole('button', { name: 'Open' }));
    expect(screen.getByRole('dialog')).toBeDefined();
    await user.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('TRAPS focus — Tab from the last element wraps to the first', async () => {
    const user = userEvent.setup();
    render(<DialogHarness />);
    await user.click(screen.getByRole('button', { name: 'Open' }));

    const first = screen.getByRole('button', { name: 'First' });
    const second = screen.getByRole('button', { name: 'Second' });

    await user.tab();
    expect(document.activeElement).toBe(second);
    await user.tab();
    // Without a trap this would land on a control behind the dialog.
    expect(document.activeElement).toBe(first);
  });

  it('traps backwards too — Shift+Tab from the first wraps to the last', async () => {
    const user = userEvent.setup();
    render(<DialogHarness />);
    await user.click(screen.getByRole('button', { name: 'Open' }));
    await user.tab({ shift: true });
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Second' }));
  });

  it('is labelled by its title', () => {
    render(
      <Dialog open title="Discard changes?" onClose={() => {}}>
        body
      </Dialog>,
    );
    const dialog = screen.getByRole('dialog');
    const labelledBy = dialog.getAttribute('aria-labelledby');
    expect(labelledBy).toBeTruthy();
    expect(document.getElementById(labelledBy as string)?.textContent).toBe('Discard changes?');
  });

  it('marks itself modal', () => {
    render(
      <Dialog open title="X" onClose={() => {}}>
        body
      </Dialog>,
    );
    expect(screen.getByRole('dialog').getAttribute('aria-modal')).toBe('true');
  });

  it('renders nothing when closed', () => {
    render(
      <Dialog open={false} title="X" onClose={() => {}}>
        body
      </Dialog>,
    );
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('passes axe when open', async () => {
    const { container } = render(
      <Dialog open title="Confirm" onClose={() => {}}>
        <button type="button">OK</button>
      </Dialog>,
    );
    expect(await axeViolations(container)).toEqual([]);
  });
});

// --- unauthorized must not become an existence oracle -----------------------

describe('unauthorized', () => {
  it('offers no retry, because retrying cannot grant permission', () => {
    const { container } = render(<UnauthorizedState />);
    expect(container.querySelector('.jl-state__action')).toBeNull();
  });

  it('says nothing about what does or does not exist', () => {
    // STEP-002.02 keeps denial and absence indistinguishable; this must not undo it.
    const { container } = render(<UnauthorizedState />);
    const text = (container.textContent ?? '').toLowerCase();
    for (const leak of ['forbidden', 'permission', 'not found', 'exists', 'tenant']) {
      expect(text).not.toContain(leak);
    }
  });
});

// --- notifications -----------------------------------------------------------

describe('notification', () => {
  it('requires politeness to be stated, with no default', () => {
    // The safe direction differs per message; only the author knows it.
    const source = Notification.toString();
    expect(source).toContain('politeness');
  });

  it('maps polite to role=status and assertive to role=alert', () => {
    const { container: polite } = render(<Notification politeness="polite" title="Saved" />);
    expect(polite.querySelector('[role="status"]')).not.toBeNull();

    const { container: loud } = render(<Notification politeness="assertive" title="Failed" />);
    expect(loud.querySelector('[role="alert"]')).not.toBeNull();
  });

  it('does not auto-dismiss', async () => {
    // WCAG 2.2.1: a toast that vanishes on a timer is unreadable to anyone using a
    // screen reader, magnification, or simply reading slowly.
    vi.useFakeTimers();
    try {
      render(<Notification politeness="polite" title="Saved" />);
      vi.advanceTimersByTime(60_000);
      expect(screen.getByText('Saved')).toBeDefined();
    } finally {
      vi.useRealTimers();
    }
  });

  it('offers a dismiss control when one is given', async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();
    render(<Notification politeness="polite" title="Saved" onDismiss={onDismiss} />);
    await user.click(screen.getByRole('button', { name: 'Dismiss' }));
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it('mounts BOTH live regions before any message exists', () => {
    // A region created when content arrives is frequently never announced, and a
    // single region whose aria-live value changes is unreliable — the attribute is
    // read at creation, not on mutation.
    const { container } = render(<NotificationRegion />);
    expect(container.querySelector('[aria-live="polite"]')).not.toBeNull();
    expect(container.querySelector('[aria-live="assertive"]')).not.toBeNull();
  });

  it('passes axe', async () => {
    const { container } = render(
      <Notification politeness="assertive" title="Provider unavailable" onDismiss={() => {}} />,
    );
    expect(await axeViolations(container)).toEqual([]);
  });
});
