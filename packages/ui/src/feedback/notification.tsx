/**
 * Notification / toast — STEP-003.03 (REQ-A11Y-001).
 *
 * POLITENESS IS A PROPERTY OF THE MESSAGE, NOT OF THE COMPONENT
 *   A toast that always interrupts is hostile; one that never does can hide a
 *   failure the user needs to know about. So `politeness` is required and has no
 *   default, the same reasoning as `conservative` on a feature flag: the safe
 *   direction differs per message and the author is the only one who knows it.
 *
 * THE CONTAINER IS RENDERED BEFORE THE MESSAGE EXISTS
 *   A live region created at the moment it gains content is frequently never
 *   announced — the screen reader must already be observing the node. So
 *   `NotificationRegion` is mounted once and always, and notifications are
 *   inserted into it.
 *
 * AUTO-DISMISS IS OPT-IN, NEVER THE DEFAULT
 *   WCAG 2.2.1 requires the user to be able to turn off, adjust or extend a time
 *   limit. A toast that vanishes on a timer is unreadable to anyone using a screen
 *   reader, magnification, or simply reading slowly.
 */

import type { ReactNode } from 'react';

export interface NotificationProps {
  readonly politeness: 'polite' | 'assertive';
  readonly title: string;
  readonly children?: ReactNode;
  readonly onDismiss?: () => void;
  readonly dismissLabel?: string;
}

export function Notification({
  politeness,
  title,
  children,
  onDismiss,
  dismissLabel = 'Dismiss',
}: NotificationProps) {
  return (
    <div
      className="jl-notification"
      data-politeness={politeness}
      // role="status" maps to polite, role="alert" to assertive. Setting the role
      // rather than only aria-live gives better support in older screen readers.
      role={politeness === 'assertive' ? 'alert' : 'status'}
      aria-live={politeness}
      aria-atomic="true"
    >
      <span className="jl-notification__title">{title}</span>
      {children ? <div className="jl-notification__body">{children}</div> : null}
      {onDismiss ? (
        <button type="button" onClick={onDismiss} className="jl-notification__dismiss">
          {dismissLabel}
        </button>
      ) : null}
    </div>
  );
}

/**
 * The always-mounted host for notifications.
 *
 * Two regions, not one: a polite and an assertive container. A single region
 * whose `aria-live` value changes as messages arrive is unreliable — screen
 * readers read the attribute when the region is created, not when it mutates.
 */
export function NotificationRegion({
  polite,
  assertive,
}: {
  readonly polite?: ReactNode;
  readonly assertive?: ReactNode;
}) {
  return (
    <>
      <div
        className="jl-notifications jl-notifications--polite"
        aria-live="polite"
        aria-atomic="false"
      >
        {polite}
      </div>
      <div
        className="jl-notifications jl-notifications--assertive"
        role="alert"
        aria-live="assertive"
        aria-atomic="false"
      >
        {assertive}
      </div>
    </>
  );
}
