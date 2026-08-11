/**
 * @journeylab/contracts — the public surface of the generated API client.
 *
 * WHY A BARREL RATHER THAN IMPORTING ./generated/openapi.ts DIRECTLY
 *   The generated file's shape is decided by openapi-typescript, not by us. It
 *   exports `paths`, `components` and `operations` — names that say how the
 *   generator organises an OpenAPI document, not what a caller wants. If every
 *   consumer reached into that file, changing generators (or the generator
 *   changing its own output between majors, which is exactly what forced the v6
 *   pin — see tools/gen_clients.py) would be a breaking change everywhere at once.
 *
 *   This file is the one place that has to absorb that. It is hand-written and
 *   NOT covered by the no-hand-edit guard, which only watches src/generated/.
 *
 * HOW TO NAME A RESPONSE OR REQUEST TYPE
 *   Prefer `Schemas["Trip"]` over reaching through `operations`. A schema is a
 *   thing the product has; an operation is one way of moving it. Types tied to
 *   schemas survive an endpoint being renamed or split.
 */

export type { components, operations, paths, webhooks } from './generated/openapi.ts';

import type { components } from './generated/openapi.ts';

/** Every named schema in contracts/openapi.yaml, keyed by its contract name. */
export type Schemas = components['schemas'];

/** Every reusable response, keyed by its contract name. */
export type Responses = components['responses'];

/** Every reusable parameter, keyed by its contract name. */
export type Parameters = components['parameters'];
