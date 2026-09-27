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

import { describeTextureQuality } from './textureDisplay.js';

test('case identity comes from upload, not slice number or generic input_scan ID', () => {
  const payload = {
    imaging: { masks: {33: {}}, texture_quality: {case_id: 'input_scan'} },
    projection: {typical: [], slower: []},
  };
  const result = adaptResult(payload, {}, 'C:\\data\\chaos_patient1.zip');
  assert.equal(result.scanIdentity.label, 'chaos_patient1');
  assert.equal(result.scanIdentity.filename, 'chaos_patient1.zip');
  assert.equal(adaptResult(payload, {}).scanIdentity.label, 'Unidentified upload');
});

test('patient-level review survives an unflagged displayed slice', () => {
  const report = {
    quality: {status: 'review_required', flags: ['boundary_sensitive', 'spacing_sensitive']},
    slices: [{slice_index: 17, status: 'no_flags_detected', flags: []}],
  };
  const qc = describeTextureQuality(report);
  assert.equal(qc.label, 'Review required');
  assert.equal(qc.needsReview, true);
  assert.deepEqual(qc.flags, ['boundary sensitive', 'spacing sensitive']);
  assert.equal(describeTextureQuality(undefined).label, 'Unavailable');
  assert.equal(describeTextureQuality({quality: {status: 'invalid'}}).label, 'Not evaluable');
  assert.equal(describeTextureQuality({quality: {status: 'no_flags_detected'}}).label, 'No flags detected');
});

test('alcohol category stays separate from model risk in results', () => {
  const risk = {p_ge_F2: .02, tier: 'low'};
  const alcohol = {category: 'critical', label: 'Critical', drinks_week: 20};
  const result = adaptResult({imaging: {}, risk, alcohol_consumption: alcohol, projection: {typical: [], slower: []}}, {});
  assert.equal(result.prediction, risk);
  assert.equal(result.alcoholConsumption, alcohol);
  assert.equal(result.prediction.tier, 'low');
});
