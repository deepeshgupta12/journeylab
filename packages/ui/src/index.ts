/** JourneyLab design system — STEP-003.01 delivers tokens; components follow in .02-.04. */

export {
  AA_LARGE_TEXT_AND_UI,
  AA_NORMAL_TEXT,
  AAA_NORMAL_TEXT,
  contrastRatio,
  meetsContrast,
  parseHex,
  type Rgb,
  relativeLuminance,
} from './contrast.ts';
export { Dialog, type DialogProps } from './feedback/dialog.tsx';
export {
  Notification,
  type NotificationProps,
  NotificationRegion,
} from './feedback/notification.tsx';
export {
  EmptyState,
  type InfeasibleProps,
  InfeasibleState,
  OfflineState,
  PartialDataState,
  Progress,
  type ProgressProps,
  ProviderDownState,
  Skeleton,
  SolverTimeoutState,
  type StaleDataProps,
  StaleDataState,
  UnauthorizedState,
} from './feedback/panels.tsx';
export {
  QUALITY_STATES,
  type QualityState,
  type QualityStateName,
  qualityState,
  REQUIRED_STATE_NAMES,
} from './feedback/states.ts';
export { Field, type FieldIds, type FieldProps, useFieldIds } from './form/field.tsx';
export {
  Checkbox,
  type CheckboxProps,
  DateInput,
  type DateInputProps,
  NumberInput,
  type NumberInputProps,
  RadioGroup,
  type RadioGroupProps,
  Select,
  type SelectOption,
  type SelectProps,
  TextInput,
  type TextInputProps,
} from './form/inputs.tsx';
export {
  formatLocaleNumber,
  type ParseResult,
  parseLocaleNumber,
  type Separators,
  separatorsFor,
} from './form/locale-number.ts';
export {
  type CalendarDate,
  type DateParseResult,
  isValidTimeZone,
  parseCalendarDate,
  startOfDayUtc,
} from './form/zoned-date.ts';
export {
  type ContrastPair,
  contrastPairs,
  ELEVATION,
  MOTION,
  MOTION_REDUCED,
  PALETTES,
  SPACING,
  STATUS_TOKENS,
  type StatusToken,
  type ThemeName,
  TYPOGRAPHY,
} from './tokens.ts';
