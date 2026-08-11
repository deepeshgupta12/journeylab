/**
 * Compile-time assertions over the generated client — STEP-004.07.
 *
 * WHY THIS FILE EXISTS
 *   The Python side of the contract is tested by 470+ assertions in tests/api/.
 *   The TypeScript side had nothing: `tsc --noEmit` proved only that the
 *   generated file PARSES, which it would do just as happily if every schema had
 *   collapsed to `unknown`.
 *
 *   That is not hypothetical. STEP-004.06 moved four schemas into external
 *   JSON Schema files, and an external `$ref` the generator fails to resolve does
 *   not error — it degrades. `Money` becoming `unknown` would typecheck cleanly
 *   in this package and then accept a float at every call site in the product.
 *
 * WHY COMPILE-TIME AND NOT A TEST RUNNER
 *   These are statements about types, and types do not exist at runtime. A vitest
 *   suite could only re-check what the YAML says, which tests/api/ already does
 *   better. The failure mode being guarded here is specifically "the contract is
 *   right and the client does not reflect it", so the check belongs where the
 *   client is compiled.
 *
 *   The whole file therefore emits no JavaScript. It fails the build or it says
 *   nothing.
 */

import type { Schemas } from './index.ts';

/** Fails to compile unless T and U are the same type, invariantly. */
type Exact<T, U> =
  (<G>() => G extends T ? 1 : 2) extends <G>() => G extends U ? 1 : 2 ? true : false;

// Each `_Name = Assert<...>` below is unused BY DESIGN — the type-checking of the
// alias is the whole test. If one is ever "cleaned up" as dead code, the property
// it protects stops being checked silently.
type Assert<T extends true> = T;

// --- REQ-EVID-001: a volatile value cannot arrive without its evidence -------
//
// Written as Exact<> rather than `extends`, because `extends` is satisfied by
// `unknown` on the right-hand side — which is precisely the degradation being
// guarded against.

type _MoneyIsIntegerMinorUnits = Assert<
  Exact<Schemas['Money'], { amount_minor: number; currency: string }>
>;

type _EvidencedRequiresProvenanceAndValidity = Assert<
  Exact<
    keyof Omit<Schemas['Evidenced'], 'conflicts'>,
    'value' | 'status' | 'provenance' | 'validity'
  >
>;

// REQ-EVID-003. If `status` ever widens to `string`, an estimate can be labelled
// anything, and "never rendered as confirmed" stops being checkable at all.
type _StatusIsAClosedPair = Assert<
  Exact<Schemas['Evidenced']['status'], 'confirmed' | 'estimated'>
>;

// BUG-020. A retained conflict has to be attributable and time-stamped, or it is
// a number with no argument attached to it.
type _ConflictCarriesFullEvidence = Assert<
  Exact<
    keyof NonNullable<Schemas['Evidenced']['conflicts']>[number],
    'value' | 'provenance' | 'validity'
  >
>;

// REQ-EVID-001 again, one level down: `internal_only` is the member that decides
// whether a value may be DISPLAYED as opposed to merely used, so it is the one
// whose loss would be silent and expensive.
type _AccessLabelSurvivesGeneration = Assert<
  Exact<
    Schemas['Evidenced']['provenance']['access_label'],
    'public' | 'display_permitted' | 'internal_only'
  >
>;

// --- The generated error register reaches the TypeScript client --------------
//
// tools/gen_error_codes.py emits contracts/schemas/error-codes.json from
// ERROR_MODEL.md §3, and openapi.yaml `$ref`s it. This asserts the whole chain
// arrived: a client branching on a code the server can never send does not error,
// it just never takes that branch (BR-029 §4).

type ErrorCode = Schemas['Problem']['code'];

type _RegisterIsAUnionNotAString = Assert<Exact<Exclude<ErrorCode, string>, never>> &
  Assert<Exact<string extends ErrorCode ? true : false, false>>;

type _KnownCodesArePresent = Assert<
  'solver.infeasible' extends ErrorCode
    ? 'authz.forbidden' extends ErrorCode
      ? true
      : false
    : false
>;

// Internal-only codes must NOT be publishable. ai.injection_detected has no
// client-facing status and cannot be emitted (BR-028 §6.1); if it appears in the
// client's union, the register's filter has stopped working.
type _InternalCodesAreNotPublished = Assert<
  'ai.injection_detected' extends ErrorCode ? false : true
>;
