'use client';

/**
 * Dialog with focus trap and restoration — STEP-003.03 (REQ-A11Y-001).
 *
 * THREE THINGS A DIALOG MUST DO, AND WHY EACH IS EASY TO MISS
 *   1. TRAP focus. Without it, Tab walks out of the dialog into the page behind,
 *      which a sighted user can see is inert but a screen-reader or keyboard-only
 *      user cannot — they simply end up somewhere unrelated with no way back.
 *   2. RESTORE focus on close. Without it, focus falls to `document.body` and the
 *      next Tab starts from the top of the page. A keyboard user who opened a
 *      dialog from a button halfway down a list is returned to the navigation.
 *   3. Close on ESCAPE. WCAG 2.1.2 (No Keyboard Trap) is not satisfied by a trap
 *      with no exit.
 *
 * `aria-modal` alone does none of this. It tells assistive technology the content
 * behind is inert; it does not move or constrain focus.
 */

import type { ReactNode } from 'react';
import { useCallback, useEffect, useId, useRef } from 'react';

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

export interface DialogProps {
  readonly open: boolean;
  readonly title: string;
  readonly onClose: () => void;
  readonly children: ReactNode;
  /** Rendered in the footer. Kept separate so the primary action can be focused first. */
  readonly actions?: ReactNode;
}

export function Dialog({ open, title, onClose, children, actions }: DialogProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const restoreTo = useRef<HTMLElement | null>(null);
  const titleId = useId();

  const focusable = useCallback((): HTMLElement[] => {
    const root = ref.current;
    if (!root) return [];
    // Visibility is checked WITHOUT `offsetParent`. That property is null for
    // `position: fixed` elements — which a dialog usually is — and jsdom never
    // computes layout at all, so it is null there for everything. Either way the
    // filter would silently return an empty list and the trap would do nothing.
    return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((element) => {
      if (element.hasAttribute('hidden')) return false;
      if (element.getAttribute('aria-hidden') === 'true') return false;
      if (element.closest('[inert]')) return false;
      return true;
    });
  }, []);

  // Remember where focus was BEFORE the dialog opens, and put it back on close.
  useEffect(() => {
    if (!open) return;
    restoreTo.current = document.activeElement as HTMLElement | null;

    const first = focusable()[0] ?? ref.current;
    first?.focus();

    return () => {
      // Guard against restoring to a node that has since left the document —
      // focusing a detached element silently does nothing and leaves focus on
      // body, which is the very failure this exists to prevent.
      const target = restoreTo.current;
      if (target && document.contains(target)) target.focus();
    };
  }, [open, focusable]);

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.stopPropagation();
        onClose();
        return;
      }
      if (event.key !== 'Tab') return;

      const elements = focusable();
      if (elements.length === 0) {
        // Nothing focusable inside: keep focus on the dialog itself rather than
        // letting Tab escape to the page behind.
        event.preventDefault();
        ref.current?.focus();
        return;
      }

      const first = elements[0] as HTMLElement;
      const last = elements[elements.length - 1] as HTMLElement;
      const active = document.activeElement;

      if (event.shiftKey && (active === first || active === ref.current)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown, true);
    return () => document.removeEventListener('keydown', onKeyDown, true);
  }, [open, onClose, focusable]);

  if (!open) return null;

  return (
    <div className="jl-dialog__backdrop">
      {/* role="dialog" on a div is the standard pattern: no native element
          provides focus trapping, and <dialog> is not yet consistent across the
          browsers in the support matrix. No suppression is needed — the lint rule
          does not fire here, and a comment claiming otherwise would mislead. */}
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        // tabIndex -1 makes the container programmatically focusable as a fallback
        // when it holds nothing focusable, without adding it to the tab order.
        tabIndex={-1}
        className="jl-dialog"
      >
        <h2 id={titleId} className="jl-dialog__title">
          {title}
        </h2>
        <div className="jl-dialog__body">{children}</div>
        {actions ? <div className="jl-dialog__actions">{actions}</div> : null}
      </div>
    </div>
  );
}
