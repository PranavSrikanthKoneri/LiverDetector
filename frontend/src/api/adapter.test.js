import test from 'node:test';
import assert from 'node:assert/strict';
import { adaptResult } from './adapter.js';

test('backend QC and probabilities survive dashboard mapping', () => {
  const imaging = { warnings: ['negative_dixon_median_clipped_to_zero'], texture_quality: { quality: { status: 'review_required' } }, masks: { 17: { image: 'data:image/png;base64,test' } } };
  const risk = { stage: 'F0-F1', probs: [.8, .1, .05, .05], p_ge_F2: .2, tier: 'intermediate' };
  const result = adaptResult({ imaging, risk, projection: { typical: [{ years: 0, stage_value: .5 }], slower: [{ years: 0, stage_value: .5 }] }, recommendation: { headline: 'test' } }, { diabetes: 2 });
  assert.equal(result.segmentation, imaging);
  assert.equal(result.prediction, risk);
  assert.equal(result.progression.baseline[0].year, 0);
  assert.equal(result.patient.diabetes, 2);
});
