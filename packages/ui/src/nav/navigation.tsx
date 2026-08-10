'use client';

/**
 * Role-aware navigation — STEP-003.06 (REQ-A11Y-001, REQ-SEC-004).
 *
 * HIDING A NAV ITEM IS NOT AN AUTHORIZATION CONTROL
 *   This is the whole point of the sub-step, and it is worth being blunt about.
 *
 *   Everything here runs in the user's browser, in a bundle they can read and
 *   edit. Filtering the menu by role stops the interface OFFERING an action that
 *   would be refused; it does not stop anyone performing it. Typing the URL,
 *   editing the JavaScript, or calling the API with curl all bypass it entirely.
 *
 *   The control is `apps/api/src/authz/policy.py` (STEP-002.03), on the server.
 *   `FRONTEND_ARCHITECTURE` §6 says the same: "Client role checks are
 *   presentation only; the server is the control."
 *
 *   The sub-step record puts the consequence plainly: "a hidden nav item with an
 *   open endpoint is a vulnerability, not a UI bug." Hiding it makes the
 *   vulnerability harder to notice, not smaller.
 *
 * WHY THE MATRIX IS GENERATED, NOT WRITTEN
 *   `authz-matrix.ts` comes from the same markdown as the Python policy
 *   (`ADR-012`). Two hand-maintained copies of an authorization matrix diverge,
 *   and the divergence is silent: the menu starts offering something the server
 *   refuses, or hiding something it permits. Neither is discoverable by looking
 *   at either file alone.
 */

import { useCallback, useEffect, useId, useRef } from 'react';

import { mayAttempt, type Operation, type Role } from './authz-matrix';

export interface NavItem {
  readonly href: string;
  readonly label: string;
  /**
   * The operation this destination leads to.
   *
   * Required: an item with no operation cannot be filtered, and would therefore
   * be shown to every role including ones the server refuses.
   */
  readonly operation: Operation;
}

/**
 * Filter items to those the role may attempt.
 *
 * Named `visibleItems`, not `permittedItems`. The distinction is deliberate — the
 * return value describes what to DRAW, and nothing about what is allowed.
 */
export function visibleItems(items: readonly NavItem[], actorRole: Role): NavItem[] {
  return items.filter((item) => mayAttempt(item.operation, actorRole));
}

export interface NavigationProps {
  readonly items: readonly NavItem[];
  readonly actorRole: Role;
  /** Current pathname, for `aria-current`. */
  readonly currentPath: string;
  readonly label?: string;
}

export function Navigation({
  items,
  actorRole,
  currentPath,
  label = 'Main navigation',
}: NavigationProps) {
  const visible = visibleItems(items, actorRole);

  return (
    // A <nav> landmark with an accessible name. Two unnamed navs on a page are
    // indistinguishable when jumping by landmark.
    <nav aria-label={label} className="jl-nav">
      <ul className="jl-nav__list">
        {visible.map((item) => {
          const current = item.href === currentPath;
          return (
            <li key={item.href}>
              <a
                href={item.href}
                // aria-current="page" is what a screen reader announces. Styling
                // the active link differently conveys nothing without sight, and
                // REQ-A11Y-004 forbids colour as the only signal.
                aria-current={current ? 'page' : undefined}
                className="jl-nav__link"
              >
                {item.label}
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export interface MobileNavigationProps extends NavigationProps {
  readonly open: boolean;
  readonly onClose: () => void;
  readonly onOpen: () => void;
}

/**
 * Mobile drawer.
 *
 * Focus is trapped while open and restored on close, for the reasons set out in
 * `feedback/dialog.tsx`: without a trap, Tab walks into the page behind, which a
 * sighted user can see is covered and a screen-reader user cannot.
 */
export function MobileNavigation({
  items,
  actorRole,
  currentPath,
  label = 'Main navigation',
  open,
  onClose,
  onOpen,
}: MobileNavigationProps) {
  const drawerRef = useRef<HTMLDivElement | null>(null);
  const restoreTo = useRef<HTMLElement | null>(null);
  const drawerId = useId();
  const visible = visibleItems(items, actorRole);

  const focusable = useCallback(
    (): HTMLElement[] =>
      Array.from(drawerRef.current?.querySelectorAll<HTMLElement>('a[href], button') ?? []),
    [],
  );

  useEffect(() => {
    if (!open) return;
    restoreTo.current = document.activeElement as HTMLElement | null;
    focusable()[0]?.focus();
    return () => {
      const target = restoreTo.current;
      if (target && document.contains(target)) target.focus();
    };
  }, [open, focusable]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
        return;
      }
      if (event.key !== 'Tab') return;
      const elements = focusable();
      if (elements.length === 0) return;
      const first = elements[0] as HTMLElement;
      const last = elements[elements.length - 1] as HTMLElement;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', onKeyDown, true);
    return () => document.removeEventListener('keydown', onKeyDown, true);
  }, [open, onClose, focusable]);

  return (
    <>
      <button
        type="button"
        onClick={open ? onClose : onOpen}
        // aria-expanded tells a screen reader the state; aria-controls links the
        // button to what it operates. A button reading only "Menu" says nothing
        // about whether the menu is currently open.
        aria-expanded={open}
        aria-controls={drawerId}
        className="jl-nav__toggle"
      >
        Menu
      </button>

      {open ? (
        <div ref={drawerRef} id={drawerId} className="jl-nav__drawer">
          <nav aria-label={label}>
            <ul className="jl-nav__list">
              {visible.map((item) => (
                <li key={item.href}>
                  <a
                    href={item.href}
                    aria-current={item.href === currentPath ? 'page' : undefined}
                    className="jl-nav__link"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <button type="button" onClick={onClose} className="jl-nav__close">
            Close menu
          </button>
        </div>
      ) : null}
    </>
  );
}
