'use client';

/**
 * Error boundaries — STEP-003.05 (REQ-NFR-013).
 *
 * WHY THIS IS A CLASS COMPONENT
 *   React provides no hook equivalent of `componentDidCatch`. A class is not a
 *   style choice here; it is the only way to catch a render error at all.
 *
 * THE PRODUCT REQUIREMENT, NOT A CONVENTION
 *   Blueprint §8.114 and FRONTEND_ARCHITECTURE §4: "a map or chart failure must
 *   not remove itinerary text." A single boundary at the root satisfies neither —
 *   it converts one component's failure into a blank page, which is the outcome
 *   the requirement exists to prevent.
 *
 *   So the unit of containment is the FEATURE. A chart that throws leaves the
 *   itinerary beside it readable, because the boundary sits between them rather
 *   than above both.
 *
 * NO ROLE ON THE PANEL
 *   It is content, not a grouping of form controls. Biome suggests <fieldset>
 *   for role="group", which would be wrong here, and role="alert" would
 *   interrupt the rest of the page — the opposite of what containment is for.
 *
 * RECOVERY IS OFFERED, NOT PERFORMED
 *   `onReset` lets the user retry. It is not automatic: a boundary that re-renders
 *   itself on failure loops silently, burning battery and never telling anyone.
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';

export interface FeatureErrorBoundaryProps {
  /**
   * What failed, in the user's terms.
   *
   * Required. "Something went wrong" beside an itinerary tells the traveller
   * nothing about whether their plan is intact. "The map could not load" does.
   */
  readonly feature: string;
  readonly children: ReactNode;
  /** Called with the error so the caller can report it. Never called with PII. */
  readonly onError?: (error: Error, info: ErrorInfo) => void;
  readonly onReset?: () => void;
  readonly retryLabel?: string;
}

interface State {
  readonly error: Error | null;
}

export class FeatureErrorBoundary extends Component<FeatureErrorBoundaryProps, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    this.props.onError?.(error, info);
  }

  readonly #reset = (): void => {
    this.setState({ error: null });
    this.props.onReset?.();
  };

  override render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="jl-feature-error" data-feature={this.props.feature}>
        {/*
          role="alert" would interrupt whatever the user is reading elsewhere on
          the page. A contained failure is not urgent enough for that — the point
          of containment is that the rest of the page still works.
        */}
        <p className="jl-feature-error__message">{this.props.feature} could not be displayed.</p>
        {/*
          The error MESSAGE is deliberately not rendered. It can contain a URL, a
          stack frame or a provider response, none of which help a traveller and
          any of which may carry data they should not see. It goes to `onError`
          for reporting instead.
        */}
        <button type="button" onClick={this.#reset}>
          {this.props.retryLabel ?? 'Try again'}
        </button>
      </div>
    );
  }
}

export interface GlobalErrorBoundaryProps {
  readonly children: ReactNode;
  readonly onError?: (error: Error, info: ErrorInfo) => void;
}

/**
 * The last resort, for a failure no feature boundary contained.
 *
 * This one is `role="alert"`: if the whole page is gone there is nothing else for
 * the announcement to interrupt, and the user needs to know immediately rather
 * than discovering it by exploring an empty document.
 */
export class GlobalErrorBoundary extends Component<GlobalErrorBoundaryProps, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    this.props.onError?.(error, info);
  }

  override render(): ReactNode {
    if (!this.state.error) return this.props.children;
    return (
      <div className="jl-global-error" role="alert">
        <h1>JourneyLab could not load this page</h1>
        <p>Your trips are saved. Reloading usually fixes this.</p>
        <button type="button" onClick={() => window.location.reload()}>
          Reload
        </button>
      </div>
    );
  }
}
