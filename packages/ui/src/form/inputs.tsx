'use client';

/**
 * Form primitives — STEP-003.02 (REQ-A11Y-001).
 *
 * Every primitive routes through `Field`, so label, description and error
 * association cannot be forgotten.
 *
 * DISABLED IS NOT READ-ONLY, AND THE DIFFERENCE MATTERS
 *   `disabled` removes the control from the tab order, excludes it from form
 *   submission, and in several screen readers makes it unreadable — the user
 *   cannot discover what the field even was.
 *   `readOnly` keeps it focusable, readable and submitted; it only refuses edits.
 *
 *   "You cannot change this right now, but here is its value" is almost always
 *   read-only. Reaching for `disabled` hides information from exactly the users
 *   who have the least other means of getting it, so both are exposed
 *   separately and never conflated.
 */

import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react';

import { Field, useFieldIds } from './field';
import { formatLocaleNumber, parseLocaleNumber } from './locale-number';
import { type CalendarDate, parseCalendarDate } from './zoned-date';

interface CommonProps {
  readonly label: ReactNode;
  readonly description?: ReactNode;
  readonly error?: ReactNode;
  readonly required?: boolean;
  readonly disabled?: boolean;
  readonly readOnly?: boolean;
}

// `CommonProps` owns disabled/readOnly/required, so they are removed here.
// Leaving them in both makes the interfaces non-identical (CommonProps marks them
// readonly) and TypeScript refuses the merge — which is the right complaint:
// two sources for one prop is exactly how disabled and readOnly get conflated.
// `required` is the NATIVE attribute, not aria-required: input[type=date] has no
// ARIA role, so aria-required is unsupported on it, and for every native control
// the HTML attribute already maps to the same accessibility property. aria-required
// is the fallback for elements that have no native equivalent — a custom widget.
type NativeInput = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  | 'id'
  | 'aria-describedby'
  | 'aria-invalid'
  | 'aria-required'
  | 'disabled'
  | 'readOnly'
  | 'required'
>;

export interface TextInputProps extends CommonProps, NativeInput {}

export function TextInput({
  label,
  description,
  error,
  required = false,
  disabled = false,
  readOnly = false,
  ...rest
}: TextInputProps) {
  const ids = useFieldIds({ description, error });
  return (
    <Field label={label} ids={ids} description={description} error={error} required={required}>
      <input
        {...rest}
        type={rest.type ?? 'text'}
        id={ids.inputId}
        aria-describedby={ids.describedBy}
        // `aria-invalid` must be absent, not "false", when valid: some screen
        // readers announce the attribute's presence regardless of its value.
        aria-invalid={ids.invalid || undefined}
        required={required}
        disabled={disabled}
        readOnly={readOnly}
      />
    </Field>
  );
}

export interface NumberInputProps extends CommonProps, Omit<NativeInput, 'onChange' | 'value'> {
  readonly locale: string;
  readonly value: string;
  readonly onValueChange: (raw: string, parsed: number | undefined) => void;
}

/**
 * Numeric entry that honours the locale's separators.
 *
 * `type="text"` with `inputMode="decimal"`, not `type="number"`. A native number
 * input silently discards characters the browser considers invalid — a German
 * user typing "1.234,56" can lose part of what they typed with no feedback — and
 * its spinner buttons are a known screen-reader nuisance.
 */
export function NumberInput({
  label,
  description,
  error,
  required = false,
  disabled = false,
  readOnly = false,
  locale,
  value,
  onValueChange,
  ...rest
}: NumberInputProps) {
  const ids = useFieldIds({ description, error });
  return (
    <Field label={label} ids={ids} description={description} error={error} required={required}>
      <input
        {...rest}
        type="text"
        inputMode="decimal"
        id={ids.inputId}
        value={value}
        onChange={(event) => {
          const raw = event.target.value;
          const result = parseLocaleNumber(raw, locale);
          onValueChange(raw, result.ok ? result.value : undefined);
        }}
        aria-describedby={ids.describedBy}
        aria-invalid={ids.invalid || undefined}
        required={required}
        disabled={disabled}
        readOnly={readOnly}
      />
    </Field>
  );
}

export { formatLocaleNumber };

export interface DateInputProps extends CommonProps, Omit<NativeInput, 'onChange' | 'value'> {
  readonly value: string;
  readonly onDateChange: (raw: string, parsed: CalendarDate | undefined) => void;
}

/**
 * Date entry that yields a CALENDAR DATE, never an instant.
 *
 * The callback hands back a `CalendarDate`, not a `Date`. Converting to an
 * instant requires a time zone, and this component does not have one — the trip's
 * zone does, and it lives in the domain layer. Returning a `Date` here would
 * silently attach the browser's zone, which is exactly the bug the sub-step
 * warns produces an infeasible itinerary in STEP-012.
 */
export function DateInput({
  label,
  description,
  error,
  required = false,
  disabled = false,
  readOnly = false,
  value,
  onDateChange,
  ...rest
}: DateInputProps) {
  const ids = useFieldIds({ description, error });
  return (
    <Field label={label} ids={ids} description={description} error={error} required={required}>
      <input
        {...rest}
        type="date"
        id={ids.inputId}
        value={value}
        onChange={(event) => {
          const raw = event.target.value;
          const result = parseCalendarDate(raw);
          onDateChange(raw, result.ok ? result.date : undefined);
        }}
        aria-describedby={ids.describedBy}
        aria-invalid={ids.invalid || undefined}
        required={required}
        disabled={disabled}
        readOnly={readOnly}
      />
    </Field>
  );
}

export interface SelectOption {
  readonly value: string;
  readonly label: string;
}

export interface SelectProps
  extends CommonProps,
    Omit<
      SelectHTMLAttributes<HTMLSelectElement>,
      'id' | 'aria-describedby' | 'aria-invalid' | 'disabled' | 'required'
    > {
  readonly options: readonly SelectOption[];
}

export function Select({
  label,
  description,
  error,
  required = false,
  disabled = false,
  options,
  ...rest
}: SelectProps) {
  const ids = useFieldIds({ description, error });
  return (
    <Field label={label} ids={ids} description={description} error={error} required={required}>
      <select
        {...rest}
        id={ids.inputId}
        aria-describedby={ids.describedBy}
        aria-invalid={ids.invalid || undefined}
        required={required}
        disabled={disabled}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </Field>
  );
}

export interface CheckboxProps extends CommonProps, NativeInput {}

export function Checkbox({
  label,
  description,
  error,
  required = false,
  disabled = false,
  readOnly = false,
  ...rest
}: CheckboxProps) {
  const ids = useFieldIds({ description, error });
  return (
    <Field label={label} ids={ids} description={description} error={error} required={required}>
      <input
        {...rest}
        type="checkbox"
        id={ids.inputId}
        aria-describedby={ids.describedBy}
        aria-invalid={ids.invalid || undefined}
        required={required}
        disabled={disabled}
        // `readOnly` has no effect on a checkbox in HTML. Expressing it as
        // aria-readonly at least conveys the intent to assistive technology
        // instead of appearing to work and doing nothing.
        aria-readonly={readOnly || undefined}
      />
    </Field>
  );
}

export interface RadioGroupProps extends CommonProps {
  readonly name: string;
  readonly options: readonly SelectOption[];
  readonly value?: string;
  readonly onValueChange?: (value: string) => void;
}

/**
 * A radio group is a `fieldset` with a `legend`, not a div with a label.
 *
 * Each radio has its own label; the group's question ("Trip pace") belongs to the
 * legend. Without the fieldset, a screen reader announces "Relaxed, radio button"
 * with no indication of what is being asked.
 */
export function RadioGroup({
  label,
  description,
  error,
  required = false,
  disabled = false,
  name,
  options,
  value,
  onValueChange,
}: RadioGroupProps) {
  const ids = useFieldIds({ description, error });
  return (
    // No aria-required and no role override here. A fieldset maps to role="group",
    // which does not support aria-required; role="radiogroup" does, but putting an
    // interactive role on a non-interactive element trades one violation for
    // another. The native mechanism avoids both: per the HTML spec, `required` on a
    // radio button makes its whole same-named group required, and screen readers
    // announce it. Reaching for ARIA when HTML already says it is how these
    // elements end up over-annotated and less accessible, not more.
    <fieldset
      className="jl-field"
      aria-describedby={ids.describedBy}
      aria-invalid={ids.invalid || undefined}
      disabled={disabled}
      data-invalid={ids.invalid || undefined}
    >
      <legend className="jl-field__label">
        {label}
        {required ? <span className="jl-visually-hidden"> (required)</span> : null}
      </legend>

      {description ? (
        <div id={ids.descriptionId} className="jl-field__description">
          {description}
        </div>
      ) : null}

      {options.map((option) => {
        const optionId = `${ids.inputId}-${option.value}`;
        return (
          <div key={option.value} className="jl-radio">
            <input
              type="radio"
              id={optionId}
              name={name}
              value={option.value}
              checked={value === option.value}
              required={required}
              onChange={() => onValueChange?.(option.value)}
            />
            <label htmlFor={optionId}>{option.label}</label>
          </div>
        );
      })}

      <div id={ids.errorId} className="jl-field__error" aria-live="polite" aria-atomic="true">
        {error}
      </div>
    </fieldset>
  );
}
