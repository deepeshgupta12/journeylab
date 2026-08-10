/** JourneyLab design system — STEP-003.01 delivers tokens; components follow in .02-.04. */

export {
  type A11yCounter,
  type A11yEvent,
  type A11ySignal,
  type A11ySink,
  countUnnamedControls,
  createA11yCounter,
  observeFocusLoss,
} from './a11y/counter';
export {
  AA_LARGE_TEXT_AND_UI,
  AA_NORMAL_TEXT,
  AAA_NORMAL_TEXT,
  contrastRatio,
  meetsContrast,
  parseHex,
  type Rgb,
  relativeLuminance,
} from './contrast';
export {
  type CsvColumn,
  type CsvOptions,
  downloadCsv,
  escapeCell,
  toCsv,
} from './data/csv';
export {
  DataList,
  type DataListProps,
  DataTable,
  type DataTableProps,
  type SortDirection,
  type TableColumn,
} from './data/table';
export { Dialog, type DialogProps } from './feedback/dialog';
export {
  Notification,
  type NotificationProps,
  NotificationRegion,
} from './feedback/notification';
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
} from './feedback/panels';
export {
  QUALITY_STATES,
  type QualityState,
  type QualityStateName,
  qualityState,
  REQUIRED_STATE_NAMES,
} from './feedback/states';
export { Field, type FieldIds, type FieldProps, useFieldIds } from './form/field';
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
} from './form/inputs';
export {
  formatLocaleNumber,
  type ParseResult,
  parseLocaleNumber,
  type Separators,
  separatorsFor,
} from './form/locale-number';
export {
  type CalendarDate,
  type DateParseResult,
  isValidTimeZone,
  parseCalendarDate,
  startOfDayUtc,
} from './form/zoned-date';
export {
  crossesDstTransition,
  elapsedHours,
  type FormatOptions,
  formatDate,
  formatDateTime,
  formatNumber,
  formatRelative,
  formatTime,
  hoursInDay,
  MILLIS_PER_HOUR,
  zonedTimeToUtc,
} from './i18n/datetime';
export {
  createTranslator,
  FALLBACK_LOCALE,
  interpolate,
  type MessageCatalogue,
  resolveLocale,
  type Translator,
} from './i18n/messages';
export {
  addMoney,
  formatMoney,
  type Money,
  MoneyError,
  minorUnitExponent,
  money,
  parseMoney,
  sumMoney,
} from './i18n/money';
export {
  MATRIX as AUTHZ_MATRIX,
  mayAttempt,
  OPERATIONS as AUTHZ_OPERATIONS,
  type Operation,
  ROLES as AUTHZ_ROLES,
  type Role,
  type Rule as AuthzRule,
} from './nav/authz-matrix';
export {
  MobileNavigation,
  type MobileNavigationProps,
  type NavItem,
  Navigation,
  type NavigationProps,
  visibleItems,
} from './nav/navigation';
export {
  FeatureErrorBoundary,
  type FeatureErrorBoundaryProps,
  GlobalErrorBoundary,
  type GlobalErrorBoundaryProps,
} from './shell/error-boundary';
export {
  type Direction,
  type DocumentLocale,
  documentLocale,
  isRightToLeft,
} from './shell/locale';
export { SkipLink, type SkipLinkProps } from './shell/skip-link';
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
} from './tokens';
