'use client';

/**
 * Quality-state primitives — STEP-003.03 (REQ-A11Y-001, REQ-A11Y-004).
 *
 * One component per state, so features cannot invent inconsistent ones. Each
 * renders its icon AND its label, because colour alone is never the signal.
 */

import type { ReactNode } from 'react';

import { type QualityStateName, qualityState } from './states';

interface PanelProps {
  readonly children?: ReactNode;
  readonly action?: ReactNode;
}

function StatePanel({
  name,
  children,
  action,
  extraLabel,
}: PanelProps & { name: QualityStateName; extraLabel?: string }) {
  const state = qualityState(name);
  return (
    <div
      className={`jl-state jl-state--${name}`}
      data-state={name}
      // The state name is on the element as data AND announced as text. A test can
      // assert the former; a user hears the latter.
      role="status"
      aria-live={state.politeness}
      aria-atomic="true"
    >
      <span className="jl-state__icon" data-icon={state.icon} aria-hidden="true" />
      <span className="jl-state__label">{extraLabel ?? state.label}</span>
      {children ? <div className="jl-state__detail">{children}</div> : null}
      {action ? <div className="jl-state__action">{action}</div> : null}
    </div>
  );
}

export function Skeleton({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="jl-state jl-state--skeleton" data-state="skeleton" aria-busy="true">
      {/* aria-busy on the region, and the label in a live region: a skeleton with
          no accessible text is a silent wait, which is what REQ-NFR-003 forbids. */}
      <span className="jl-state__label" role="status" aria-live="polite">
        {label}
      </span>
    </div>
  );
}

export function EmptyState({ children, action }: PanelProps) {
  return (
    <StatePanel name="empty" action={action}>
      {children}
    </StatePanel>
  );
}

export function PartialDataState({ children, action }: PanelProps) {
  return (
    <StatePanel name="partial-data" action={action}>
      {children}
    </StatePanel>
  );
}

export interface StaleDataProps extends PanelProps {
  /** When the underlying fact was last observed. Required — see below. */
  readonly observedAt: Date;
  /** What is stale. Required, so staleness is attached to a THING, not a page. */
  readonly subject: string;
  readonly formatObserved?: (observedAt: Date) => string;
}

/**
 * Stale data, labelled at the point of use.
 *
 * `REQ-EVID-005` and FRONTEND_ARCHITECTURE §4 both require this: staleness is
 * marked where the fact is shown, not only in a global banner. A page-level
 * "some data may be out of date" tells a traveller nothing about WHICH price or
 * WHICH opening time to distrust, so they either distrust everything or ignore it.
 *
 * `subject` and `observedAt` are therefore required arguments. The component
 * cannot be rendered as a generic page-level warning, because there is no way to
 * construct it without naming the thing and the time.
 */
export function StaleDataState({
  observedAt,
  subject,
  formatObserved,
  children,
  action,
}: StaleDataProps) {
  const when = formatObserved
    ? formatObserved(observedAt)
    : observedAt.toISOString().replace('T', ' ').slice(0, 16);
  return (
    <StatePanel name="stale-data" action={action} extraLabel={`${subject} — last checked ${when}`}>
      {children}
    </StatePanel>
  );
}

export function ProviderDownState({ children, action }: PanelProps) {
  return (
    <StatePanel name="provider-down" action={action}>
      {children}
    </StatePanel>
  );
}

export interface InfeasibleProps extends PanelProps {
  /**
   * The minimal set of constraints that cannot hold together.
   *
   * Required and non-empty. `REQ-CONS-005` forbids returning "infeasible" without
   * one — a bare failure tells the traveller nothing about what to change, and
   * FRONTEND_ARCHITECTURE §4 makes this a first-class state rather than an error
   * toast for exactly that reason.
   */
  readonly conflicts: readonly string[];
  readonly relaxations?: readonly string[];
}

export function InfeasibleState({ conflicts, relaxations, children, action }: InfeasibleProps) {
  if (conflicts.length === 0) {
    // Fail loudly rather than rendering an empty "infeasible" panel, which would
    // be exactly the uninformative dead end REQ-CONS-005 exists to prevent.
    throw new Error('InfeasibleState requires a non-empty minimal conflict set (REQ-CONS-005)');
  }
  return (
    <StatePanel name="infeasible" action={action}>
      <p>These cannot all hold at once:</p>
      <ul className="jl-state__conflicts">
        {conflicts.map((conflict) => (
          <li key={conflict}>{conflict}</li>
        ))}
      </ul>
      {relaxations && relaxations.length > 0 ? (
        <>
          <p>Relaxing any one of these would help:</p>
          <ul className="jl-state__relaxations">
            {relaxations.map((relaxation) => (
              <li key={relaxation}>{relaxation}</li>
            ))}
          </ul>
        </>
      ) : null}
      {children}
    </StatePanel>
  );
}

export function SolverTimeoutState({ children, action }: PanelProps) {
  return (
    <StatePanel name="solver-timeout" action={action}>
      {children}
    </StatePanel>
  );
}

export function UnauthorizedState({ children }: PanelProps) {
  // No retry affordance: retrying will not grant permission, and offering one
  // implies it might. Also carries no detail about what exists — STEP-002.02 keeps
  // denial and absence indistinguishable, and this must not undo that.
  return <StatePanel name="unauthorized">{children}</StatePanel>;
}

export function OfflineState({ children, action }: PanelProps) {
  return (
    <StatePanel name="offline" action={action}>
      {children}
    </StatePanel>
  );
}

export interface ProgressProps {
  /** What is happening. Required — a spinner with no label is a silent wait. */
  readonly label: string;
  /**
   * How to abandon it. Required.
   *
   * `REQ-NFR-003` and FRONTEND_ARCHITECTURE §4: "Never a blank map or a silent
   * spinner for long work — always progress plus cancel/retry." Making this a
   * required prop means a bare spinner cannot be constructed, rather than being
   * discouraged in a style guide nobody re-reads.
   */
  readonly onCancel: () => void;
  readonly cancelLabel?: string;
  /** 0-100 when known. Omitted for indeterminate work, which stays announced. */
  readonly percent?: number;
}

export function Progress({ label, onCancel, cancelLabel = 'Cancel', percent }: ProgressProps) {
  const determinate = typeof percent === 'number';
  return (
    <div className="jl-progress">
      <div
        role="progressbar"
        aria-label={label}
        aria-valuenow={determinate ? percent : undefined}
        aria-valuemin={determinate ? 0 : undefined}
        aria-valuemax={determinate ? 100 : undefined}
        className="jl-progress__bar"
      />
      <span className="jl-progress__label" role="status" aria-live="polite">
        {label}
      </span>
      <button type="button" onClick={onCancel} className="jl-progress__cancel">
        {cancelLabel}
      </button>
    </div>
  );
}
