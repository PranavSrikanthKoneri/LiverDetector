/** Shared with the chart selection; missing projection data never implies stage zero. */
export function projectionAtYear(progression, year, lifestyle) {
  const rows = lifestyle ? progression.intervention : progression.baseline;
  const stage = rows?.find(row => row.year === year)?.stage_value;
  return typeof stage === 'number' && Number.isFinite(stage) ? stage : null;
}

/** Display-only shading, with no changes to scan pixels or numerical measurements. */
export function projectionOpacity(stage) {
  return typeof stage === 'number' && Number.isFinite(stage)
    ? Math.max(0, Math.min(4, stage)) / 4 * 0.6 : 0;
}
