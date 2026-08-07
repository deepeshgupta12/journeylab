'use client';

/**
 * Field association — STEP-003.02 (REQ-A11Y-001).
 *
 * WHY THIS IS ONE COMPONENT RATHER THAN A CONVENTION
 *   Label, description and error association is easy to get right once and easy
 *   to forget on the fourteenth form. Centralising it means every primitive built
 *   on `Field` is associated correctly by construction, and a component author
 *   cannot accidentally ship an input whose error is invisible to a screen reader.
 *
 * ERRORS ARE ANNOUNCED WITHOUT STEALING FOCUS
 *   The error node is `aria-live="polite"`, not `role="alert"`. Alert is
 *   assertive: it interrupts whatever the screen reader is currently saying,
 *   which for a user mid-way through typing means being cut off by a message
 *   about a field they have not finished. Polite waits for a pause.
 *
 *   Focus is never moved. Moving focus to an invalid field on every keystroke or
 *   blur traps a keyboard user in the field they are trying to leave.
 */

import type { ReactNode } from 'react';
import { useId } from 'react';

export interface FieldIds {
  readonly inputId: string;
  readonly labelId: string;
  readonly descriptionId: string | undefined;
  readonly errorId: string | undefined;
  /** Value for the input's `aria-describedby`, or undefined when nothing describes it. */
  readonly describedBy: string | undefined;
  readonly invalid: boolean;
}

export function useFieldIds(options: { description?: ReactNode; error?: ReactNode }): FieldIds {
  const base = useId();
  const hasDescription = Boolean(options.description);
  const hasError = Boolean(options.error);

  const descriptionId = hasDescription ? `${base}-description` : undefined;
  const errorId = hasError ? `${base}-error` : undefined;

  // Order matters: the description is read before the error, which is the order a
  // sighted user reads them on screen.
  const describedBy = [descriptionId, errorId].filter(Boolean).join(' ') || undefined;

  return {
    inputId: `${base}-input`,
    labelId: `${base}-label`,
    descriptionId,
    errorId,
    describedBy,
    invalid: hasError,
  };
}

export interface FieldProps {
  readonly label: ReactNode;
  readonly ids: FieldIds;
  readonly description?: ReactNode;
  readonly error?: ReactNode;
  readonly required?: boolean;
  readonly children: ReactNode;
}

export function Field({ label, ids, description, error, required = false, children }: FieldProps) {
  return (
    <div className="jl-field" data-invalid={ids.invalid || undefined}>
      <label id={ids.labelId} htmlFor={ids.inputId} className="jl-field__label">
        {label}
        {required ? (
          <>
            {' '}
            <span aria-hidden="true">*</span>
            {/* The asterisk is decorative; the input carries aria-required, and
                this text is what a screen reader announces. A lone "*" is
                meaningless without sight of the legend explaining it. */}
            <span className="jl-visually-hidden"> (required)</span>
          </>
        ) : null}
      </label>

      {description ? (
        <div id={ids.descriptionId} className="jl-field__description">
          {description}
        </div>
      ) : null}

      {children}

      {/* Always rendered, even when empty. A live region that is inserted at the
          moment it gains content is frequently not announced at all — the screen
          reader must be observing the node before the text arrives. */}
      <div id={ids.errorId} className="jl-field__error" aria-live="polite" aria-atomic="true">
        {error}
      </div>
    </div>
  );
}
