'use client';

import { DataTable, type TableColumn } from '@journeylab/ui';

import type { CoverageRegion } from './fetch-coverage';

/**
 * The region table — STEP-007.02 (REQ-A11Y-002, REQ-A11Y-003).
 *
 * BUILT BEFORE ANY MAP, AND THAT ORDERING IS THE POINT
 *   `REQ-A11Y-003` says no core action may require the map. A table added after a
 *   map inherits the map's decisions and becomes a translation of them; a table
 *   built first is the surface, and the map — when STEP-013.04 adds one — is
 *   additive to something already complete.
 *
 * CSV COMES FROM THE COMPONENT, NOT FROM THIS PAGE
 *   `DataTable` already exports the rows it is sorted by (`STEP-003.04`). Writing
 *   a second exporter here would be a second thing to keep in step with the table,
 *   and the two would disagree the first time a column changed.
 */

const columns: readonly TableColumn<CoverageRegion>[] = [
  {
    key: 'display_name',
    header: 'Region',
    cell: (row) => row.display_name,
    value: (row) => row.display_name,
  },
  {
    key: 'dates',
    header: 'Planning window',
    cell: (row) => `${row.date_bounds.start} to ${row.date_bounds.end}`,
    value: (row) => row.date_bounds.start,
  },
  {
    key: 'freshness',
    header: 'Data freshness',
    // Text, not a coloured dot. Colour alone fails WCAG 1.4.1, and a screen
    // reader is given the same word a sighted reader sees rather than a label
    // invented for it.
    cell: (row) => FRESHNESS_LABEL[row.freshness],
    value: (row) => FRESHNESS_LABEL[row.freshness],
  },
  {
    key: 'limitations',
    header: 'Known limitations',
    // Verbatim. REQ-TRIP-002 wants an honest scope statement, and a limitation
    // summarised to fit a column is a limitation the traveller did not read.
    // `limitations` is OPTIONAL in the contract, so a region may omit it entirely
    // rather than send an empty array. The handler always sends one, and coding to
    // that would make this page correct only against today's server.
    cell: (row) => {
      const limitations = row.limitations ?? [];
      return limitations.length === 0 ? (
        'None recorded'
      ) : (
        <ul>
          {limitations.map((limitation: string) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      );
    },
    value: (row) => (row.limitations ?? []).join('; '),
  },
];

const FRESHNESS_LABEL: Record<CoverageRegion['freshness'], string> = {
  current: 'Current',
  degraded: 'Degraded — some sources are behind',
  stale: 'Unavailable — not accepting new trips',
};

export function CoverageTable({ regions }: { readonly regions: readonly CoverageRegion[] }) {
  return (
    <DataTable
      caption="Supported regions, their planning windows and known limitations"
      columns={columns}
      rows={regions}
      rowKey={(row) => row.region_id}
      csvFilename="journeylab-coverage"
      emptyMessage="No region has been declared yet. This page lists what JourneyLab can plan; it is empty because nothing has been declared, not because a request failed."
    />
  );
}
