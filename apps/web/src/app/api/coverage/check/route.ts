import { forward } from '../_proxy';

/** `POST /api/coverage/check` → `POST /coverage:check` (`API-019`). BUG-038, ADR-022. */

export const dynamic = 'force-dynamic';

export function POST(request: Request): Promise<Response> {
  return forward(request, '/coverage:check');
}
